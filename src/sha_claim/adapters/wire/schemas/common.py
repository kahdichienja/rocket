from __future__ import annotations

import json
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class WireModel(BaseModel):
    """Base for server payloads: tolerant of unknown fields, accepts camelCase or snake_case."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, alias_generator=to_camel, frozen=True)

    @model_validator(mode="before")
    @classmethod
    def _null_means_absent(cls, data: object) -> object:
        """UAT sends `null` where the docs promise `[]`/`""`; treat null as missing so field defaults apply."""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data

    def unmodelled(self) -> dict[str, object]:
        return dict(self.model_extra or {})


T = TypeVar("T")


class Page(WireModel, Generic[T]):
    """List envelope used by benefits, sub-benefits, interventions, preauths, payer preview."""

    count: int | None = None
    page_size: int | None = None
    current_page: int | None = None
    total_pages: int | None = None
    results: list[T] = Field(default_factory=list)


class ErrorEnvelope(BaseModel):
    """`{error, message, trace_id, details?}` — every 4xx/5xx from the middleware.

    `error` is sometimes a JSON-encoded string from the upstream engine, e.g.
    `{"error": "{\\"error\\": \\"Kindly note ...\\"}"}`; `detail()` unwraps that.
    """

    model_config = ConfigDict(extra="ignore")

    error: str = ""
    message: str = ""
    trace_id: str | None = None
    details: list[str] = Field(default_factory=list)

    def detail(self) -> str:
        """The most specific human-readable explanation available.

        Preference: an upstream JSON blob in `error`, then `details`, then `message` (with any
        trailing JSON unwrapped), then `error` as plain status text.
        """
        if self.error.lstrip().startswith("{"):
            return _unwrap(self.error) or self.message
        for d in self.details:
            if text := _unwrap(d):
                return text
        return _unwrap_suffix(self.message) or self.error

    @property
    def status_text(self) -> str:
        return "" if self.error.lstrip().startswith("{") else self.error


def _unwrap_suffix(message: str) -> str:
    """'failed to start visit: {"Edi Error":{"detail":"X"}}' → 'failed to start visit: X'."""
    brace = message.find("{")
    if brace == -1:
        return message
    inner = _unwrap(message[brace:])
    return (message[:brace] + inner).strip() if inner else message


def _unwrap(text: str, depth: int = 3) -> str:
    """Peel nested JSON strings: '{"error":"{\\"error\\":\\"X\\"}"}' → 'X'."""
    current = text.strip()
    for _ in range(depth):
        if not current.startswith("{"):
            return current
        try:
            obj = json.loads(current)
        except ValueError:
            return current
        if not isinstance(obj, dict):
            return current
        inner = obj.get("error") or obj.get("detail") or obj.get("message")
        if inner is None and len(obj) == 1:
            only = next(iter(obj.values()))
            if isinstance(only, dict) or (isinstance(only, str) and only.lstrip().startswith("{")):
                inner = only  # a wrapper such as {"Edi Error": {...}}
        if inner is None:
            # DRF-style field errors: {"notes": ["This field may not be blank."]} → "notes: This field may not be blank."
            return "; ".join(f"{k}: {_join(v)}" for k, v in obj.items() if v not in (None, "", [], {}))
        current = _join(inner)
    return current


def _join(value: object) -> str:
    """A list of messages reads as one line; anything else as its string form."""
    if isinstance(value, list):
        return "; ".join(_join(v) for v in value)
    if isinstance(value, dict):
        return _unwrap(json.dumps(value))
    return str(value).strip()
