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
