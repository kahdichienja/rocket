"""Bounded retry with exponential backoff and full jitter. Idempotency is decided by the caller."""

from __future__ import annotations

import random
from collections.abc import Iterator
from dataclasses import dataclass

TRANSIENT_STATUSES = frozenset({408, 429, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_seconds: float = 0.5
    cap_seconds: float = 8.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")

    def delays(self, rng: random.Random | None = None) -> Iterator[float]:
        """One delay per *retry* (so `max_attempts - 1` values), full-jitter."""
        r = rng or random
        for attempt in range(self.max_attempts - 1):
            yield r.uniform(0, min(self.cap_seconds, self.base_seconds * 2**attempt))

    @staticmethod
    def is_transient_status(status: int) -> bool:
        return status in TRANSIENT_STATUSES


DEFAULT_RETRY = RetryPolicy()
NO_RETRY = RetryPolicy(max_attempts=1)
