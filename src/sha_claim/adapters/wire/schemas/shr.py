from __future__ import annotations

from typing import Any

from pydantic import Field

from sha_claim.adapters.wire.schemas.common import WireModel


class ShrConsentWire(WireModel):
    """`POST /shr/consents` and `POST /shr/consents/{id}/resend-otp`."""

    consent_id: str = ""
    consent_status: str = ""
    otp_record: str = ""
    visit_type: str = ""
    message: str = ""
    status: str = ""


class ShrVerificationWire(WireModel):
    """`POST /shr/consents/{id}/verify`."""

    consent_token: str = ""
    visit_id: str = ""
    message: str = ""
    status: str = ""


class ShrConsentStatusWire(WireModel):
    """`GET /shr/consents/{id}/status`."""

    consent_id: str = ""
    consent_status: str = ""
    visit_id: str = ""
    message: str = ""
    status: str = ""


class ShrVisitClosedWire(WireModel):
    """`POST /shr/visits/{id}/close`."""

    visit_id: str = ""
    consent_id: str = ""
    end_date: str = ""
    message: str = ""
    status: str = ""


class ShrBundleReceiptWire(WireModel):
    """`POST /shr/bundles`."""

    mediator_id: str = ""
    message: str = ""
    status: str = ""


class ShrRefreshWire(WireModel):
    """`POST /shr/visits/{id}/refresh`."""

    consent_token: str = ""
    message: str = ""
    status: str = ""


class ShrResourceLabelsWire(WireModel):
    """`GET /shr/resource-labels` — DHA publishes no shape for this, so it is kept whole."""

    labels: list[dict[str, Any]] = Field(default_factory=list)


class ShrSecurityLabelWire(WireModel):
    """One entry from `GET /shr/security-labels`.

    DHA's key names for these are not settled across the catalogue — `display` has also appeared as
    `name`, and `code` as `label` — so both spellings are accepted rather than one being guessed at. An
    entry whose code cannot be read is dropped by the mapper, because a label with no code cannot be
    matched against `meta.security` and would only pad the catalogue.
    """

    code: str = ""
    label: str = ""
    display: str = ""
    name: str = ""
    system: str = ""
    category: str = ""
    description: str = ""


class ShrSecurityLabelsWire(WireModel):
    """`GET /shr/security-labels`.

    The catalogue has arrived both as a bare list and wrapped in `data`; `data` is a list in one and an
    object holding `labels` in another, so all three shapes are accepted here instead of the mapper
    discovering the difference in production.
    """

    labels: list[ShrSecurityLabelWire] = Field(default_factory=list)
    data: Any = None
    message: str = ""
    status: str = ""
