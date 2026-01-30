"""
Retry utilities with exponential backoff.

Provides decorators and utilities for retrying failed operations
with configurable backoff strategies.
"""

import time
import functools
from typing import Callable, TypeVar, Any
from utils.logger import get_logger

logger = get_logger('retry')

T = TypeVar('T')


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Exception = None):
        super().__init__(message)
        self.last_exception = last_exception


class RateLimitError(Exception):
    """Raised when API returns 429 Too Many Requests."""

    def __init__(self, retry_after: int = 60, message: str = None):
        self.retry_after = retry_after
        super().__init__(message or f"Rate limited. Retry after {retry_after}s")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Callable[[Exception, int], None] = None
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.
        exceptions: Tuple of exception types to catch and retry.
        on_retry: Optional callback called on each retry with (exception, attempt).

    Returns:
        Decorated function that retries on failure.

    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def fetch_data():
            return requests.get(url)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)

                except RateLimitError as e:
                    # Special handling for rate limits
                    logger.warning(
                        f"{func.__name__}: Rate limited, waiting {e.retry_after}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(e.retry_after)
                    last_exception = e

                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries - 1:
                        # Calculate delay with exponential backoff
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )

                        logger.warning(
                            f"{func.__name__}: Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {delay:.1f}s"
                        )

                        # Call retry callback if provided
                        if on_retry:
                            on_retry(e, attempt)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__}: All {max_retries} attempts failed. "
                            f"Last error: {e}"
                        )

            raise RetryError(
                f"{func.__name__} failed after {max_retries} attempts",
                last_exception
            )

        return wrapper
    return decorator


def retry_on_exception(
    func: Callable[..., T],
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> T:
    """
    Retry a function call with fixed delay.

    Non-decorator version for one-off retry needs.

    Args:
        func: Function to call.
        max_retries: Maximum retry attempts.
        delay: Fixed delay between retries in seconds.
        exceptions: Exception types to catch.

    Returns:
        Result of successful function call.

    Raises:
        RetryError: If all attempts fail.
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(delay)

    raise RetryError(f"Failed after {max_retries} attempts", last_exception)
