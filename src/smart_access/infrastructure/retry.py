"""Retry policy for idempotent calls."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    """Configures retry behavior on transient network or 5xx failures."""

    max_attempts: int = 3
    base_backoff_seconds: float = 0.5
    max_backoff_seconds: float = 4.0

    def backoff_for(self, attempt: int) -> float:
        """Computes exponential backoff with full jitter."""
        temp = min(self.max_backoff_seconds, self.base_backoff_seconds * (2 ** (attempt - 1)))
        return random.uniform(0, temp)

    def should_retry(self, method: str, status_code: int | None, attempt: int) -> bool:
        if attempt >= self.max_attempts:
            return False
        # Only retry idempotent safe reads (GET)
        if method.upper() != "GET":
            return False
        # Retry network errors (None status) or transient server errors
        return status_code is None or status_code in (408, 429, 502, 503, 504)


DEFAULT_RETRY = RetryPolicy()
