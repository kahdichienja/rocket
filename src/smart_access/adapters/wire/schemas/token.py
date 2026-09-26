"""OAuth token wire model for Smart API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TokenResponseWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    scope: str | None = None
