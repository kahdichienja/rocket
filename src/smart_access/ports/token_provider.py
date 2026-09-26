"""TokenProvider port."""

from __future__ import annotations

from typing import Protocol


class TokenProvider(Protocol):
    """Provides a valid OAuth2 bearer token for the Smart Provider API."""

    async def access_token(self) -> str:
        """Returns a cached or freshly minted access token."""
        ...
