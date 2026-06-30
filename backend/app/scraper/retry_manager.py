"""
app/scraper/retry_manager.py
────────────────────────────
Provides retry logic using tenacity.
"""
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from playwright.async_api import TimeoutError as PlaywrightTimeout
from app.utils.logger import logger

def log_retry_attempt(retry_state):
    """Log when a retry happens."""
    logger.warning(
        f"[RetryManager] Retrying {retry_state.fn.__name__} "
        f"after exception: {retry_state.outcome.exception()}. "
        f"Attempt {retry_state.attempt_number}"
    )

def async_retry(max_attempts=3):
    """Decorator to retry async functions with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((PlaywrightTimeout, Exception)),
        before_sleep=log_retry_attempt,
        reraise=True
    )
