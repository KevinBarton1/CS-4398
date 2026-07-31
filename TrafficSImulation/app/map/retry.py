"""One jittered retry for transient upstream transport failures."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

from app.config import (
    UPSTREAM_RETRY_JITTER_MAX_SECONDS,
    UPSTREAM_RETRY_JITTER_MIN_SECONDS,
    UPSTREAM_RETRY_MAX,
)

T = TypeVar("T")


def _is_retryable(error: BaseException) -> bool:
    if isinstance(error, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code >= 500
    return False


async def with_upstream_retry(operation: Callable[[], Awaitable[T]]) -> T:
    last_error: BaseException | None = None
    for attempt in range(UPSTREAM_RETRY_MAX + 1):
        try:
            return await operation()
        except BaseException as error:
            if not _is_retryable(error):
                raise
            last_error = error
            if attempt >= UPSTREAM_RETRY_MAX:
                break
            delay = random.uniform(
                UPSTREAM_RETRY_JITTER_MIN_SECONDS,
                UPSTREAM_RETRY_JITTER_MAX_SECONDS,
            )
            await asyncio.sleep(delay)
    assert last_error is not None
    raise last_error


__all__ = ["with_upstream_retry"]
