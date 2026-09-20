from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Timezone-aware current time."""
        ...

    def monotonic(self) -> float:
        """Monotonic seconds, for expiries and backoff."""
        ...
