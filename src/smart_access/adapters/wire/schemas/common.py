"""Common wire response envelopes for Smart API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class SmartEnvelopeWire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str | int | None = None
    message: str | None = None
    response_type: str | None = None
    object_type: str | None = None
    content: Any = None
