"""Transport protocol for wire adapters."""

from collections.abc import Mapping
from typing import Any, Protocol


class Transport(Protocol):
    """Abstract HTTP transport interface for Smart API calls."""

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
        json_body: Any = None,
    ) -> Any:
        """Executes an authenticated HTTP call and returns decoded JSON."""
        ...

    @property
    def provider_key(self) -> str:
        """The active provider key."""
        ...
