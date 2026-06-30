"""
tests/test_db.py
─────────────────
Standalone database layer test script.

Tests the complete CRUD lifecycle for all four collections:
  products    → create → read → update → search → delete
  reviews     → create → read by product → rating distribution → delete
  sentiments  → create → get stats → upsert → delete
  scrape_logs → create → mark completed / failed → get summary

Run from the backend/ directory:
    python tests/test_db.py

Or using Python module syntax:
    python -m tests.test_db
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from pathlib import Path

# Support Unicode characters in Windows terminal output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure the backend/ directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.init_db import init_db, shutdown_db
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.scrape_log_repository import ScrapeLogRepository
from app.repositories.sentiment_repository import SentimentRepository
from app.utils.bson import format_response, to_json
from app.utils.logger import configure_logging, logger


# ── Helpers ────────────────────────────────────────────────────────────────────

def _section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def _ok(msg: str) -> None:
    print(f"  ✅ {msg}")


def _info(msg: str, data: object = None) -> None:
    if data is not None:
        print(f"  ℹ  {msg}: {to_json(data) if isinstance(data, (dict, list)) else data}")
    else:
        print(f"  ℹ  {msg}")


# ── Test suites ────────────────────────────────────────────────────────────────

async def test_products(repo: ProductRepository) -> str:
    """Full CRUD cycle for the products collection. Returns inserted product_id."""
    _section("PRODUCTS — CRUD test")

    # ── Insert ─────────────────────────────────────────────────────────────────
    product = await repo.create({
        "product_name": "Apple iPhone 15 Pro [TEST]",
        "brand": "Apple",
        "category": "Smartphones",
        "source": "amazon",
        "product_url": "https://www.amazon.in/dp/TEST-IPHONE15PRO-DB-TEST",
        "average_rating": 4.5,
        "total_reviews": 3200,
    })
    _ok(f"Created product | id={product['id']}")
    product_id: str = product["id"]

    # ── Read back ──────────────────────────────────────────────────────────────
    fetched = await repo.get_by_id(product_id)
    assert fetched is not None, "get_by_id returned None"
    assert fetched["product_name"] == "Apple iPhone 15 Pro [TEST]"
    _ok(f"Read back OK | name={fetched['product_name']}")

    # ── Update ─────────────────────────────────────────────────────────────────
    updated = await repo.update(product_id, {
        "average_rating": 4.7,
        "total_reviews": 3350,
    })
    assert updated is not None
    assert updated["average_rating"] == 4.7
    _ok(f"Updated | average_rating={updated['average_rating']}")

    # ── Exists ─────────────────────────────────────────────────────────────────
    exists = await repo.exists({"product_name": "Apple iPhone 15 Pro [TEST]"})
    assert exists
    _ok("exists() returned True")

    # ── Count ──────────────────────────────────────────────────────────────────
    count = await repo.count()
    _ok(f"Total products in collection: {count}")

    # ── Find + pagination ──────────────────────────────────────────────────────
    docs, total = await repo.find(limit=5)
    _ok(f"find() returned {len(docs)} docs (total={total})")

    # ── Search by name ──────────────────────────────────────────────────────────
    results = await repo.search_by_name("iPhone")
    _ok(f"search_by_name('iPhone') → {len(results)} result(s)")

    # ── Upsert ─────────────────────────────────────────────────────────────────
    upserted = await repo.upsert_by_url({
        "product_name": "Apple iPhone 15 Pro [TEST]",
        "brand": "Apple",
        "category": "Smartphones",
        "source": "amazon",
        "product_url": "https://www.amazon.in/dp/TEST-IPHONE15PRO-DB-TEST",
        "average_rating": 4.8,
        "total_reviews": 3400,
    })
    _ok(f"upsert_by_url | average_rating={upserted['average_rating']}")

    # ── Distinct ────────────────────────────────────────────────────────────────
    categories = await repo.get_distinct_categories()
    _ok(f"Distinct categories: {categories}")

    # ── Top rated ────────────────────────────────────────────────────────────────
    top = await repo.get_top_rated(limit=3, min_reviews=100)
    _ok(f"Top-rated products (min 100 reviews): {len(top)} result(s)")

    return product_id


async def test_reviews(
    repo: ReviewRepository,
    product_id: str,
) -> str:
    """Full CRUD cycle for the reviews collection. Returns inserted review_id."""
    _section("REVIEWS — CRUD test")

    # ── Insert ─────────────────────────────────────────────────────────────────
    review = await repo.create({
        "product_id": product_id,
        "reviewer": "Test User [DB Test]",
        "rating": 5.0,
        "review_text": "Absolutely amazing product. The camera is stunning and battery life is exceptional.",
        "review_date": "2024-03-15T10:30:00",
        "helpful_votes": 42,
        "verified_purchase": True,
        "source": "amazon",
        "review_url": "https://www.amazon.in/review/TEST-REVIEW-DB-123",
    })
    _ok(f"Created review | id={review['id']}")
    review_id: str = review["id"]

    # ── Read back ──────────────────────────────────────────────────────────────
    fetched = await repo.get_by_id(review_id)
    assert fetched is not None
    assert fetched["rating"] == 5.0
    _ok(f"Read back OK | rating={fetched['rating']}")

    # ── Insert second review for aggregation testing ───────────────────────────
    review2 = await repo.create({
        "product_id": product_id,
        "reviewer": "Another Tester",
        "rating": 3.0,
        "review_text": "Good product but overpriced.",
        "review_date": "2024-04-01T09:00:00",
        "helpful_votes": 5,
        "verified_purchase": False,
        "source": "amazon",
        "review_url": "https://www.amazon.in/review/TEST-REVIEW-DB-456",
    })
    _ok(f"Created second review | id={review2['id']}")

    # ── Get by product ─────────────────────────────────────────────────────────
    reviews_list, total = await repo.get_by_product_id(product_id)
    _ok(f"get_by_product_id → {len(reviews_list)} review(s) (total={total})")

    # ── Average rating ─────────────────────────────────────────────────────────
    avg = await repo.get_average_rating(product_id)
    _ok(f"Average rating for product: {avg}")

    # ── Rating distribution ────────────────────────────────────────────────────
    dist = await repo.get_rating_distribution(product_id)
    _ok(f"Rating distribution: {dist}")

    # ── Count ─────────────────────────────────────────────────────────────────
    count = await repo.count_by_product(product_id)
    _ok(f"count_by_product: {count}")

    # ── Search ────────────────────────────────────────────────────────────────
    found = await repo.search_reviews("camera", product_id=product_id)
    _ok(f"search_reviews('camera') → {len(found)} result(s)")

    # ── Update ────────────────────────────────────────────────────────────────
    updated = await repo.update(review2["id"], {"helpful_votes": 12})
    assert updated["helpful_votes"] == 12
    _ok(f"Updated review | helpful_votes={updated['helpful_votes']}")

    # ── Delete second review ───────────────────────────────────────────────────
    deleted = await repo.delete(review2["id"])
    assert deleted
    _ok("Deleted second review")

    return review_id


async def test_sentiments(
    repo: SentimentRepository,
    product_id: str,
    review_id: str,
) -> str:
    """Full CRUD cycle for the sentiments collection. Returns inserted sentiment_id."""
    _section("SENTIMENTS — CRUD test")

    # ── Insert ────────────────────────────────────────────────────────────────
    sentiment = await repo.create({
        "review_id": review_id,
        "product_id": product_id,
        "sentiment": "positive",
        "confidence": 0.96,
        "polarity": 0.82,
        "subjectivity": 0.65,
    })
    _ok(f"Created sentiment | id={sentiment['id']}")
    sentiment_id: str = sentiment["id"]

    # ── Read by review_id ──────────────────────────────────────────────────────
    by_review = await repo.get_by_review_id(review_id)
    assert by_review is not None
    assert by_review["sentiment"] == "positive"
    _ok(f"get_by_review_id → sentiment={by_review['sentiment']}")

    # ── Read by product_id ─────────────────────────────────────────────────────
    sentiments, total = await repo.get_by_product_id(product_id)
    _ok(f"get_by_product_id → {len(sentiments)} result(s) (total={total})")

    # ── Get stats ─────────────────────────────────────────────────────────────
    stats = await repo.get_sentiment_stats(product_id)
    _info("Sentiment stats", stats)
    assert stats["total_analysed"] >= 1
    _ok("get_sentiment_stats OK")

    # ── Upsert (re-run analysis) ───────────────────────────────────────────────
    upserted = await repo.upsert_by_review_id(review_id, {
        "product_id": product_id,
        "sentiment": "positive",
        "confidence": 0.98,   # re-analysis improved confidence
        "polarity": 0.85,
        "subjectivity": 0.60,
    })
    assert upserted["confidence"] == 0.98
    _ok(f"upsert_by_review_id | confidence={upserted['confidence']}")

    # ── Count by label ────────────────────────────────────────────────────────
    pos_count = await repo.count_by_product_and_label(product_id, "positive")
    _ok(f"Positive count for product: {pos_count}")

    # ── High-confidence filter ─────────────────────────────────────────────────
    hc = await repo.get_high_confidence(product_id, min_confidence=0.9)
    _ok(f"High-confidence results (≥0.9): {len(hc)}")

    return sentiment_id


async def test_scrape_logs(repo: ScrapeLogRepository) -> str:
    """Full CRUD cycle for the scrape_logs collection. Returns inserted log_id."""
    _section("SCRAPE LOGS — CRUD test")

    # ── Insert ────────────────────────────────────────────────────────────────
    log = await repo.create({
        "product_name": "Apple iPhone 15 Pro [TEST]",
        "source": "amazon",
        "status": "running",
        "total_reviews_found": 0,
    })
    _ok(f"Created scrape log | id={log['id']}")
    log_id: str = log["id"]

    # ── Mark completed ─────────────────────────────────────────────────────────
    completed = await repo.mark_completed(log_id, total_reviews_found=325)
    assert completed["status"] == "completed"
    assert completed["total_reviews_found"] == 325
    _ok(f"mark_completed | status={completed['status']} reviews={completed['total_reviews_found']}")

    # ── Create a failed log ────────────────────────────────────────────────────
    failed_log = await repo.create({
        "product_name": "Samsung Galaxy S24 [TEST]",
        "source": "flipkart",
        "status": "running",
        "total_reviews_found": 0,
    })
    failed = await repo.mark_failed(
        failed_log["id"],
        error_message="Connection timeout after 30s — Flipkart blocked the request",
        total_reviews_found=12,
    )
    assert failed["status"] == "failed"
    _ok(f"mark_failed | status={failed['status']}")

    # ── Recent logs ────────────────────────────────────────────────────────────
    recent = await repo.get_recent_logs(limit=5)
    _ok(f"get_recent_logs → {len(recent)} log(s)")

    # ── By status ─────────────────────────────────────────────────────────────
    failed_list, failed_total = await repo.get_failed_logs()
    _ok(f"get_failed_logs → {failed_total} total failed job(s)")

    # ── Job summary ────────────────────────────────────────────────────────────
    summary = await repo.get_job_summary()
    _info("Job summary", summary)

    # ── Cleanup failed log ─────────────────────────────────────────────────────
    await repo.delete(failed_log["id"])
    _ok("Deleted failed test log")

    return log_id


async def test_cleanup(
    product_repo: ProductRepository,
    review_repo: ReviewRepository,
    sentiment_repo: SentimentRepository,
    log_repo: ScrapeLogRepository,
    product_id: str,
    review_id: str,
    sentiment_id: str,
    log_id: str,
) -> None:
    """Delete all test documents created during the test run."""
    _section("CLEANUP — removing test documents")

    # Delete in dependency order: sentiment → review → product → log
    await sentiment_repo.delete(sentiment_id)
    _ok(f"Deleted sentiment | id={sentiment_id}")

    deleted_reviews = await review_repo.delete_by_product_id(product_id)
    _ok(f"Cascade deleted {deleted_reviews} review(s) for product")

    await product_repo.delete(product_id)
    _ok(f"Deleted product | id={product_id}")

    await log_repo.delete(log_id)
    _ok(f"Deleted scrape log | id={log_id}")


# ── Main runner ────────────────────────────────────────────────────────────────

async def run_all_tests() -> None:
    configure_logging()

    print("\n" + "=" * 60)
    print("  PRODUCT SENTIMENT DB — DATABASE LAYER TESTS")
    print("=" * 60)

    await init_db()

    product_repo   = ProductRepository()
    review_repo    = ReviewRepository()
    sentiment_repo = SentimentRepository()
    log_repo       = ScrapeLogRepository()

    product_id = review_id = sentiment_id = log_id = None

    try:
        product_id   = await test_products(product_repo)
        review_id    = await test_reviews(review_repo, product_id)
        sentiment_id = await test_sentiments(sentiment_repo, product_id, review_id)
        log_id       = await test_scrape_logs(log_repo)

        await test_cleanup(
            product_repo,
            review_repo,
            sentiment_repo,
            log_repo,
            product_id,
            review_id,
            sentiment_id,
            log_id,
        )

        print("\n" + "=" * 60)
        print("  ✅ ALL DATABASE TESTS PASSED")
        print("=" * 60 + "\n")

    except Exception:
        print("\n" + "=" * 60)
        print("  ❌ TEST SUITE FAILED")
        print("=" * 60)
        traceback.print_exc()

        # Best-effort cleanup even on failure
        if product_id:
            try:
                await review_repo.delete_by_product_id(product_id)
                await sentiment_repo.delete_by_product_id(product_id)
                await product_repo.delete(product_id)
                print("\n  ⚠  Partial cleanup performed.")
            except Exception:
                pass

        sys.exit(1)

    finally:
        await shutdown_db()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
