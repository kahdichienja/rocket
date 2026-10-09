"""Status callbacks: asking DHA to tell us, instead of us asking DHA.

Everything else in this SDK is a read or a write the caller initiates. This is the one place DHA calls
*us*: register a URL, attach a `status_changed` operation to it, and the HIE POSTs there whenever a
claim, pre-auth or authorization changes state.

**This replaces a premise the rest of the tracking design was built on.** The certification notes and
NaCare's own design doc both record "the HIE API has no push/webhook; tracking is poll-based" — true when
they were written, and no longer true. A poller that asks every claim once a day exists only because
nothing could tell it sooner.

What DHA has *not* published is the payload it delivers, or the status values that payload carries. So
this models the management API — which is fully specified — and deliberately stops there. Turning an
undocumented body into claim state is the caller's decision to make, not the SDK's to guess at, and the
safe reading of a callback is "something changed, go and ask".

Two shapes, nested. An **endpoint** is where to deliver (one per entity type per facility); an
**operation** is what to deliver and by which method. Registering an endpoint alone delivers nothing:
the operation is required, and that catches people out.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sha_claim.domain.enums import LenientStrEnum


class CallbackEntityType(LenientStrEnum):
    """What a registered endpoint receives. One endpoint per type per facility."""

    CLAIM = "claim"
    PREAUTH = "preauth"
    AUTHORIZATION = "authorization"


class CallbackEnvironment(LenientStrEnum):
    """DHA accepts these two spellings and refuses `prod`, which is the obvious thing to try."""

    PRODUCTION = "production"
    SANDBOX = "sandbox"


class CallbackAuthType(LenientStrEnum):
    """How the HIE authenticates *to us* when it delivers.

    Only `NONE` can be set without a `secret_ref`, and the HIE issues that reference out of band — it is
    never sent through this API.
    """

    NONE = "none"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    BEARER_STATIC = "bearer_static"
    BEARER_LOGIN = "bearer_login"


#: The only `action` DHA defines for status callbacks.
STATUS_CHANGED = "status_changed"


@dataclass(frozen=True, slots=True)
class CallbackEndpoint:
    """A registered delivery target. `endpoint_id` is what every later call is keyed on — keep it."""

    endpoint_id: str
    name: str
    base_url: str
    entity_type: CallbackEntityType | None
    environment: CallbackEnvironment | None
    auth_type: CallbackAuthType | None
    is_active: bool = True
    facility_fr_code: str = ""
    tenant_code: str = ""
    timeout_ms: int | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class CallbackOperation:
    """What gets delivered to an endpoint, and how.

    `path` is appended to the endpoint's `base_url`; `path_url_override` replaces both and is the way to
    point one operation somewhere else entirely.
    """

    operation_id: str
    name: str
    action: str
    method: str
    path: str = ""
    path_url_override: str = ""
    is_active: bool = True
    request_content_type: str = "application/json"
    timeout_ms: int | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class NewCallbackEndpoint:
    """What `POST /tenants/{tenant_id}/endpoints` needs, validated before it is sent."""

    name: str
    base_url: str
    entity_type: CallbackEntityType
    environment: CallbackEnvironment
    auth_type: CallbackAuthType = CallbackAuthType.NONE
    secret_ref: str = ""
    facility_fr_code: str = ""
    tenant_code: str = ""
    timeout_ms: int | None = None
    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("a callback endpoint needs a name")
        if not self.base_url.strip():
            raise ValueError("base_url cannot be empty")
        # DHA requires an absolute URL it can reach: a relative path, or a host only this machine knows,
        # registers cleanly and then never delivers.
        if not self.base_url.strip().lower().startswith(("http://", "https://")):
            raise ValueError("base_url must be absolute (http:// or https://) and reachable from the HIE")
        # Only `none` can be chosen freely. The rest need a reference the HIE issued out of band, and
        # registering one without it produces an endpoint that cannot authenticate.
        if self.auth_type is not CallbackAuthType.NONE and not self.secret_ref.strip():
            raise ValueError(f"auth_type {self.auth_type.value} requires a secret_ref issued by the HIE")


@dataclass(frozen=True, slots=True)
class NewCallbackOperation:
    """What `POST /tenants/{tenant_id}/endpoints/{endpoint_id}/operations` needs.

    **An endpoint without one of these receives nothing.** That is the single easiest way to register a
    callback, see a 201, and then wonder for a day why nothing arrives.
    """

    name: str
    action: str = STATUS_CHANGED
    method: str = "POST"
    path: str = ""
    path_url_override: str = ""
    request_content_type: str = "application/json"
    timeout_ms: int | None = None
    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("a callback operation needs a name")
        if not self.path.strip() and not self.path_url_override.strip():
            raise ValueError("either path or path_url_override is required")
        # DHA lists DELETE among the methods and then fails on delivery with it.
        if self.method.strip().upper() == "DELETE":
            raise ValueError("DELETE is accepted at registration but fails at delivery; use POST")


@dataclass(frozen=True, slots=True)
class CallbackEndpointUpdate:
    """A `PATCH`. Every field is optional, but an empty body is a 400 — hence `has_changes`.

    `headers` replaces the whole map rather than merging into it.
    """

    name: str | None = None
    base_url: str | None = None
    entity_type: CallbackEntityType | None = None
    environment: CallbackEnvironment | None = None
    auth_type: CallbackAuthType | None = None
    secret_ref: str | None = None
    tenant_code: str | None = None
    timeout_ms: int | None = None
    headers: Mapping[str, str] | None = None
    #: `False` pauses delivery without deleting anything — the reversible way to stop callbacks.
    is_active: bool | None = None

    @property
    def has_changes(self) -> bool:
        return any(
            value is not None
            for value in (
                self.name,
                self.base_url,
                self.entity_type,
                self.environment,
                self.auth_type,
                self.secret_ref,
                self.tenant_code,
                self.timeout_ms,
                self.headers,
                self.is_active,
            )
        )


@dataclass(frozen=True, slots=True)
class CallbackOperationUpdate:
    """A `PATCH` on one operation. Same rules as `CallbackEndpointUpdate`."""

    name: str | None = None
    action: str | None = None
    method: str | None = None
    path: str | None = None
    path_url_override: str | None = None
    request_content_type: str | None = None
    timeout_ms: int | None = None
    headers: Mapping[str, str] | None = None
    is_active: bool | None = None

    @property
    def has_changes(self) -> bool:
        return any(
            value is not None
            for value in (
                self.name,
                self.action,
                self.method,
                self.path,
                self.path_url_override,
                self.request_content_type,
                self.timeout_ms,
                self.headers,
                self.is_active,
            )
        )
