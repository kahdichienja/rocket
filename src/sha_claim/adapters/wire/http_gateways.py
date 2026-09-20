"""Port implementations over the wire Transport. One class per port role."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from sha_claim.adapters.wire import mappers, requests
from sha_claim.adapters.wire.error_translator import raise_for_status
from sha_claim.adapters.wire.schemas.authorization import AuthorizationWire
from sha_claim.adapters.wire.schemas.benefits import BenefitPackageWire, InterventionWire, SubBenefitWire
from sha_claim.adapters.wire.schemas.claim import (
    ClaimAttachmentWire,
    ClaimDiagnosisWire,
    ClaimInterventionWire,
    ClaimLineWire,
    PayerClaimWire,
    VirtualClaimWire,
)
from sha_claim.adapters.wire.schemas.common import Page
from sha_claim.adapters.wire.schemas.eligibility import EligibilityWire
from sha_claim.adapters.wire.schemas.preauth import DoctorConsentWire, PreauthorizationWire
from sha_claim.adapters.wire.transport import Transport, WireResponse
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.benefits import BenefitPackage, InterventionCoverage, SubBenefit
from sha_claim.domain.claim import (
    ClaimAttachment,
    ClaimDiagnosis,
    ClaimIntervention,
    ClaimLine,
    LineEdit,
    NewClaimLine,
    PayerClaimRecord,
    VirtualClaim,
)
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.consent import Authorization, ConsentProof, Otp
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.enums import CancelReason, IdentificationType, ServiceType
from sha_claim.domain.identifiers import (
    AttachmentId,
    ClaimGuid,
    ConsentToken,
    InvoiceNumber,
    LineGuid,
    PatientId,
)
from sha_claim.domain.preauth import DoctorConsentRequest, Preauthorization, PreauthRequest
from sha_claim.errors import UnexpectedResponseError

M = TypeVar("M", bound=BaseModel)


def parse_as(model: type[M], response: WireResponse) -> M:
    raise_for_status(response)
    try:
        payload: Any = response.json()
        return model.model_validate(payload)
    except (ValueError, ValidationError) as exc:
        raise UnexpectedResponseError(f"{model.__name__}: {exc}") from exc


class HttpEligibilityGateway:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def check(self, identification_number: str, identification_type: IdentificationType) -> Eligibility:
        response = await self._transport.send(
            requests.eligibility_check(identification_number, identification_type)
        )
        return mappers.to_eligibility(parse_as(EligibilityWire, response))

    async def benefits(self, patient: PatientId) -> tuple[BenefitPackage, ...]:
        page = parse_as(Page[BenefitPackageWire], await self._transport.send(requests.benefits(patient)))
        return tuple(mappers.to_benefit_package(b) for b in page.results)

    async def sub_benefits(self, patient: PatientId) -> tuple[SubBenefit, ...]:
        page = parse_as(Page[SubBenefitWire], await self._transport.send(requests.sub_benefits(patient)))
        return tuple(mappers.to_sub_benefit(s) for s in page.results)

    async def interventions(
        self, patient: PatientId, sub_benefit_code: str
    ) -> tuple[InterventionCoverage, ...]:
        response = await self._transport.send(requests.interventions(patient, sub_benefit_code))
        page = parse_as(Page[InterventionWire], response)
        return tuple(mappers.to_intervention_coverage(i) for i in page.results)


class HttpConsentGateway:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def authorize(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        otp: Otp | None,
    ) -> Authorization:
        response = await self._transport.send(requests.authorize(patient, service_type, interventions, otp))
        return mappers.to_authorization(parse_as(AuthorizationWire, response))

    async def get(self, token: str, guid: str, beneficiary: PatientId | None) -> Authorization | None:
        response = await self._transport.send(requests.get_authorization(token, guid, beneficiary))
        raise_for_status(response)
        payload = response.json()
        # The server returns a list for this lookup; tolerate a bare object too.
        records = payload if isinstance(payload, list) else [payload] if payload else []
        if not records:
            return None
        try:
            return mappers.to_authorization(AuthorizationWire.model_validate(records[0]))
        except ValidationError as exc:
            raise UnexpectedResponseError(f"AuthorizationWire: {exc}") from exc

    async def reject(self, token: str) -> None:
        raise_for_status(await self._transport.send(requests.reject_authorization(token)))


class HttpVirtualClaimGateway:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def open_visit(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        proof: ConsentProof,
    ) -> VirtualClaim:
        response = await self._transport.send(
            requests.open_visit(patient, service_type, interventions, proof)
        )
        return mappers.to_virtual_claim(parse_as(VirtualClaimWire, response))

    async def add_intervention(self, token: ConsentToken, code: InterventionCode) -> ClaimIntervention:
        response = await self._transport.send(requests.add_intervention(token, code))
        return mappers.to_claim_intervention(parse_as(ClaimInterventionWire, response))

    async def retire_intervention(self, token: ConsentToken, code: InterventionCode) -> None:
        raise_for_status(await self._transport.send(requests.retire_intervention(token, code)))

    async def restore_intervention(self, token: ConsentToken, code: InterventionCode) -> None:
        raise_for_status(await self._transport.send(requests.restore_intervention(token, code)))

    async def add_diagnosis(
        self, token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
    ) -> ClaimDiagnosis:
        response = await self._transport.send(requests.add_diagnosis(token, icd, intervention))
        return mappers.to_claim_diagnosis(parse_as(ClaimDiagnosisWire, response))

    async def remove_diagnosis(
        self, token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
    ) -> None:
        raise_for_status(await self._transport.send(requests.remove_diagnosis(token, icd, intervention)))

    async def add_line(self, token: ConsentToken, line: NewClaimLine) -> ClaimLine:
        response = await self._transport.send(requests.add_line(token, line))
        return mappers.to_claim_line(parse_as(ClaimLineWire, response))

    async def remove_line(self, token: ConsentToken, line: LineGuid) -> None:
        raise_for_status(await self._transport.send(requests.remove_line(token, line)))

    async def edit_line(self, edit: LineEdit) -> ClaimLine:
        response = await self._transport.send(requests.edit_line(edit))
        return mappers.to_claim_line(parse_as(ClaimLineWire, response))

    async def add_attachment(
        self, token: ConsentToken, attachment: Attachment, intervention: InterventionCode
    ) -> ClaimAttachment:
        response = await self._transport.send(requests.add_attachment(token, attachment, intervention))
        return mappers.to_claim_attachment(parse_as(ClaimAttachmentWire, response))

    async def remove_attachment(
        self, token: ConsentToken, attachment: AttachmentId, intervention: InterventionCode
    ) -> None:
        raise_for_status(
            await self._transport.send(requests.remove_attachment(token, attachment, intervention))
        )

    async def preview(self, token: ConsentToken) -> VirtualClaim:
        response = await self._transport.send(requests.preview(token))
        return mappers.to_virtual_claim(parse_as(VirtualClaimWire, response))

    async def submit(
        self, token: ConsentToken, invoice: InvoiceNumber | None, reason_for_unknown_patient: str | None
    ) -> VirtualClaim:
        response = await self._transport.send(requests.submit(token, invoice, reason_for_unknown_patient))
        return mappers.to_virtual_claim(parse_as(VirtualClaimWire, response))

    async def close(self, token: ConsentToken, reason: CancelReason, text: str) -> VirtualClaim:
        response = await self._transport.send(requests.close(token, reason, text))
        return mappers.to_virtual_claim(parse_as(VirtualClaimWire, response))

    async def payer_status(self, claim: ClaimGuid, provider_claim_no: str) -> tuple[PayerClaimRecord, ...]:
        page = parse_as(
            Page[PayerClaimWire], await self._transport.send(requests.payer_status(claim, provider_claim_no))
        )
        return tuple(mappers.to_payer_record(r) for r in page.results)


class HttpPreauthGateway:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def create(self, token: ConsentToken, request: PreauthRequest) -> Preauthorization:
        response = await self._transport.send(requests.create_preauth(token, request))
        return mappers.to_preauthorization(parse_as(PreauthorizationWire, response))

    async def list(self, token: ConsentToken) -> tuple[Preauthorization, ...]:
        response = await self._transport.send(requests.list_preauths(token))
        raise_for_status(response)
        payload = response.json()
        # Observed on UAT: a page `{pageSize, results}`; the portal documents a bare object. Accept both.
        if isinstance(payload, dict) and "results" in payload:
            page = parse_as(Page[PreauthorizationWire], response)
            return tuple(mappers.to_preauthorization(p) for p in page.results)
        if isinstance(payload, list):
            return tuple(mappers.to_preauthorization(PreauthorizationWire.model_validate(p)) for p in payload)
        if payload:
            return (mappers.to_preauthorization(PreauthorizationWire.model_validate(payload)),)
        return ()

    async def remove_diagnosis(
        self, token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
    ) -> Preauthorization:
        response = await self._transport.send(requests.remove_preauth_diagnosis(token, icd, intervention))
        return mappers.to_preauthorization(parse_as(PreauthorizationWire, response))

    async def remove_doctor(
        self, token: ConsentToken, intervention: InterventionCode, registration_number: str
    ) -> None:
        raise_for_status(
            await self._transport.send(
                requests.remove_preauth_doctor(token, intervention, registration_number)
            )
        )

    async def cancel(self, token: ConsentToken, intervention: InterventionCode) -> Preauthorization:
        response = await self._transport.send(requests.cancel_preauth(token, intervention))
        return mappers.to_preauthorization(parse_as(PreauthorizationWire, response))

    async def request_doctor_consent(self, token: ConsentToken, request: DoctorConsentRequest) -> str:
        response = await self._transport.send(requests.doctor_consent(token, request))
        return parse_as(DoctorConsentWire, response).message
