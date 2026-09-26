"""SystemClock implementation for infrastructure."""

from __future__ import annotations

from datetime import UTC, datetime

from smart_access.ports.clock import Clock


class SystemClock(Clock):
    """Standard system clock returning timezone-aware UTC datetimes."""

    def now(self) -> datetime:
        return datetime.now(UTC)
