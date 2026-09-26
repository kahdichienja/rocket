"""Clock port."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Provides time abstraction for deterministic testing."""

    def now(self) -> datetime:
        """Current datetime in UTC."""
        ...
