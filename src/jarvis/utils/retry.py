"""Retry utilities with exponential backoff."""

import asyncio
import random
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


async def retry_async(
    func: Callable[P, R],
    *args: P.args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: P.kwargs,
) -> R:
    """Execute async function with exponential backoff retry.
    
    Args:
        func: Async function to execute
        *args: Positional arguments for func
        max_attempts: Maximum number of attempts (default 3)
        base_delay: Initial delay in seconds (default 1.0)
        max_delay: Maximum delay in seconds (default 30.0)
        exponential_base: Exponential base for backoff (default 2.0)
        jitter: Add random jitter to delay (default True)
        retryable_exceptions: Exception types to retry (default all)
        **kwargs: Keyword arguments for func
    
    Returns:
        Result of func
    
    Raises:
        Last exception if all attempts fail
    """
    last_exception: Exception | None = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == max_attempts:
                log.error(
                    "retry_exhausted",
                    func=func.__name__,
                    attempts=max_attempts,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise
            
            delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
            if jitter:
                delay *= (0.5 + random.random())  # 0.5-1.5x jitter
            
            log.warning(
                "retry_attempt",
                func=func.__name__,
                attempt=attempt,
                max_attempts=max_attempts,
                delay_seconds=round(delay, 2),
                error=str(e),
                error_type=type(e).__name__,
            )
            
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")


def retry_sync(
    func: Callable[P, R],
    *args: P.args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: P.kwargs,
) -> R:
    """Execute sync function with exponential backoff retry.
    
    Args:
        func: Sync function to execute
        *args: Positional arguments for func
        max_attempts: Maximum number of attempts (default 3)
        base_delay: Initial delay in seconds (default 1.0)
        max_delay: Maximum delay in seconds (default 30.0)
        exponential_base: Exponential base for backoff (default 2.0)
        jitter: Add random jitter to delay (default True)
        retryable_exceptions: Exception types to retry (default all)
        **kwargs: Keyword arguments for func
    
    Returns:
        Result of func
    
    Raises:
        Last exception if all attempts fail
    """
    import time
    
    last_exception: Exception | None = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == max_attempts:
                log.error(
                    "retry_exhausted",
                    func=func.__name__,
                    attempts=max_attempts,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise
            
            delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
            if jitter:
                delay *= (0.5 + random.random())  # 0.5-1.5x jitter
            
            log.warning(
                "retry_attempt",
                func=func.__name__,
                attempt=attempt,
                max_attempts=max_attempts,
                delay_seconds=round(delay, 2),
                error=str(e),
                error_type=type(e).__name__,
            )
            
            time.sleep(delay)
    
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


# Predefined retry configs for common scenarios
MT5_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    retryable_exceptions=(ConnectionError, TimeoutError, IOError),
)

LLM_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    retryable_exceptions=(ConnectionError, TimeoutError),
)

NEWS_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=15.0,
    retryable_exceptions=(ConnectionError, TimeoutError),
)

HTTP_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    retryable_exceptions=(ConnectionError, TimeoutError),
)