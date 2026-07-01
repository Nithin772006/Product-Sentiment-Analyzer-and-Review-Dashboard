"""
app/api/routes/reports.py
─────────────────────────
Export endpoints to generate CSV, Excel, and PDF reports of product reviews and sentiment analysis datasets.
"""

from __future__ import annotations

import io
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Path
from fastapi.responses import StreamingResponse

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.sentiment_repository import SentimentRepository

router = APIRouter(prefix="/reports", tags=["reports"])


# ── Helper to compile dataset ──────────────────────────────────────────────────

async def compile_export_data(product_id: str) -> list[dict]:
    """Compile reviews and sentiments for a specific product into a unified list of dicts."""
    review_repo = ReviewRepository()
    sentiment_repo = SentimentRepository()

    # Fetch all reviews for product
    reviews, _ = await review_repo.find(filter_query={"product_id": product_id}, limit=5000)
    if not reviews:
        return []

    # Fetch sentiments for product
    sentiments, _ = await sentiment_repo.find(filter_query={"product_id": product_id}, limit=5000)
    sentiment_map = {s["review_id"]: s for s in sentiments}

    rows = []
    for r in reviews:
        s = sentiment_map.get(r["id"], {})
        
        rd = r.get("review_date")
        if hasattr(rd, "isoformat"):
            rd_str = rd.isoformat()
        elif rd:
            rd_str = str(rd)
        else:
            rd_str = ""

        rows.append({
            "Reviewer": r.get("reviewer") or "Anonymous",
            "Rating": r.get("rating") or 5,
            "Review Date": rd_str,
            "Verified Purchase": "Yes" if r.get("verified_purchase") else "No",
            "Source Platform": r.get("source", "Unknown").capitalize(),
            "Review Text": r.get("review_text", ""),
            "Sentiment Class": s.get("sentiment", "neutral").capitalize(),
            "VADER Score": s.get("vader_compound", 0.0),
            "TextBlob Polarity": s.get("polarity", 0.0),
            "Subjectivity": s.get("subjectivity", 0.0),
        })
    return rows


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/export/csv/{product_id}")
async def export_csv(
    product_id: str = Path(..., description="Product ID to export")
) -> StreamingResponse:
    """Export reviews and sentiment scores to a CSV file."""
    product_repo = ProductRepository()
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = await compile_export_data(product_id)
    if not data:
        raise HTTPException(status_code=400, detail="No reviews available to export")

    df = pd.DataFrame(data)
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    filename = f"Reviews_Report_{product_id}.csv"
    response = StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8"
    )
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Content-Length"] = str(len(csv_bytes))
    return response


@router.get("/export/excel/{product_id}")
async def export_excel(
    product_id: str = Path(...)
) -> StreamingResponse:
    """Export reviews and sentiment scores to an Excel file."""
    product_repo = ProductRepository()
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = await compile_export_data(product_id)
    if not data:
        raise HTTPException(status_code=400, detail="No reviews available to export")

    df = pd.DataFrame(data)

    # Write to memory bytes buffer
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Reviews Data", index=False)

    stream.seek(0)
    excel_bytes = stream.read()
    filename = f"Reviews_Report_{product_id}.xlsx"
    response = StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Content-Length"] = str(len(excel_bytes))
    return response


@router.get("/export/pdf/{product_id}")
async def export_pdf(
    product_id: str = Path(...)
) -> StreamingResponse:
    """Export product sentiment analysis summary report as a PDF."""
    product_repo = ProductRepository()
    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = await compile_export_data(product_id)
    
    # Calculate stats
    total_revs = len(data)
    avg_rating = product.get("average_rating", 0.0)
    
    pos_count = sum(1 for r in data if r["Sentiment Class"] == "Positive")
    neg_count = sum(1 for r in data if r["Sentiment Class"] == "Negative")
    neu_count = sum(1 for r in data if r["Sentiment Class"] == "Neutral")

    # Generate PDF in-memory using ReportLab
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="DocTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#161b27"),
        spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        name="DocSubtitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#8892b0"),
        spaceAfter=25
    )
    heading_style = ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading3"],
        fontSize=14,
        textColor=colors.HexColor("#3361ff"),
        spaceBefore=15,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        name="NormalText",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    elements = []

    # Title Banner
    elements.append(Paragraph(f"Product Sentiment Summary Report", title_style))
    elements.append(Paragraph(f"Product: {product['product_name']} | Brand: {product.get('brand', 'Generic')}", subtitle_style))
    elements.append(Spacer(1, 10))

    # Metrics Stats Table
    stats_data = [
        ["Total Reviews", "Average Rating", "Positive Sentiment Ratio"],
        [str(total_revs), f"{avg_rating:.2f} / 5.0", f"{(pos_count/total_revs*100):.1f}%" if total_revs else "0%"],
    ]
    t_stats = Table(stats_data, colWidths=[150, 150, 180])
    t_stats.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#161b27")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8892b0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa")]),
    ]))
    
    elements.append(Paragraph("System Summary Statistics", heading_style))
    elements.append(t_stats)
    elements.append(Spacer(1, 20))

    # Sentiment distribution Table
    sentiment_data = [
        ["Sentiment Class", "Count", "Percentage"],
        ["Positive", str(pos_count), f"{(pos_count/total_revs*100):.1f}%" if total_revs else "0%"],
        ["Neutral", str(neu_count), f"{(neu_count/total_revs*100):.1f}%" if total_revs else "0%"],
        ["Negative", str(neg_count), f"{(neg_count/total_revs*100):.1f}%" if total_revs else "0%"],
    ]
    t_sent = Table(sentiment_data, colWidths=[160, 160, 160])
    t_sent.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3361ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8892b0")),
    ]))
    
    elements.append(Paragraph("Sentiment Breakdown", heading_style))
    elements.append(t_sent)
    elements.append(Spacer(1, 20))

    # Top Reviews Table (up to top 5)
    elements.append(Paragraph("Sample Reviews Log", heading_style))
    sample_rows = [["Reviewer", "Rating", "Sentiment", "Comment Summary"]]
    for r in data[:5]:
        text_summary = r["Review Text"][:80] + "..." if len(r["Review Text"]) > 80 else r["Review Text"]
        sample_rows.append([
            r["Reviewer"],
            str(r["Rating"]),
            r["Sentiment Class"],
            text_summary
        ])
    t_samples = Table(sample_rows, colWidths=[100, 50, 80, 250])
    t_samples.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#161b27")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (2, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_samples)

    # Build document
    doc.build(elements)
    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.read()

    filename = f"Sentiment_Report_{product_id}.pdf"
    response = StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf"
    )
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Content-Length"] = str(len(pdf_bytes))
    return response
