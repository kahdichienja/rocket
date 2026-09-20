from __future__ import annotations

from typing import Protocol


class TokenProvider(Protocol):
    async def access_token(self) -> str:
        """A currently valid bearer token, fetching or refreshing as needed."""
        ...

    async def invalidate(self) -> None:
        """Forget the cached token (the server rejected it)."""
        ...
