"""Wire shapes for the status-callbacks management API."""

from __future__ import annotations

from pydantic import Field

from sha_claim.adapters.wire.schemas.common import WireModel


class CallbackEndpointWire(WireModel):
    """`/tenants/{tenant_id}/endpoints`. DHA names the key `endpoint_id`; `id` is accepted as a fallback
    because the delete and list responses have been seen to use it."""

    endpoint_id: str = ""
    id: str = ""
    name: str = ""
    base_url: str = ""
    entity_type: str = ""
    environment: str = ""
    auth_type: str = ""
    is_active: bool = True
    facility_fr_code: str = ""
    tenant_code: str = ""
    timeout_ms: int | None = None
    headers: dict[str, str] = Field(default_factory=dict)


class CallbackOperationWire(WireModel):
    operation_id: str = ""
    id: str = ""
    name: str = ""
    action: str = ""
    method: str = ""
    path: str = ""
    path_url_override: str = ""
    is_active: bool = True
    request_content_type: str = "application/json"
    timeout_ms: int | None = None
    headers: dict[str, str] = Field(default_factory=dict)
