from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class WireModel(BaseModel):
    """Base for server payloads: tolerant of unknown fields, accepts camelCase or snake_case."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, alias_generator=to_camel, frozen=True)

    def unmodelled(self) -> dict[str, object]:
        return dict(self.model_extra or {})


class ErrorEnvelope(BaseModel):
    """`{error, message, trace_id}` — every 4xx/5xx from the middleware."""

    model_config = ConfigDict(extra="ignore")

    error: str = ""
    message: str = ""
    trace_id: str | None = None
