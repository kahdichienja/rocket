from __future__ import annotations

from typing import Any

from sha_claim.adapters.wire.schemas.common import WireModel

Number = float | int | str | None


class PreauthorizationWire(WireModel):
    id: int | None = None
    guid: str = ""
    token: str = ""
    intervention_code: str = ""
    status: str = ""
    doctor_review_status: str = ""
    needs_doctor_approval: bool = False
    doctor_approved: bool = False
    number_of_preauth_doctors_required: int = 0
    is_request_phase: bool = False
    is_response_phase: bool = False
    total_estimated_amount_for_preauth: Number = None
    total_interim_approved_amount_for_preauth: Number = None
    final_approved_amount: Number = None
    service_start: str = ""
    service_end: str = ""
    provider_notification_email: str = ""
    member_name: str = ""
    description: str = ""
    countdown: int | None = None
    provider_currency: str = ""


class DoctorConsentWire(WireModel):
    message: str = ""
    data: Any = None
