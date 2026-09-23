"""Port implementations over the wire Transport. One class per port role."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from sha_claim.adapters.wire import mappers, requests
from sha_claim.adapters.wire.error_translator import raise_for_status
from sha_claim.adapters.wire.schemas.authorization import AuthorizationWire
from sha_claim.adapters.wire.schemas.benefits import (
    BedOccupancyWire,
    BenefitPackageWire,
    InterventionWire,
    SubBenefitWire,
    UtilizationWire,
)
from sha_claim.adapters.wire.schemas.claim import (
    ClaimAttachmentWire,
    ClaimDiagnosisWire,
    ClaimInterventionWire,
    ClaimLineWire,
    LineResubmissionWire,
    MessageWire,
    NextOfKinContactWire,
    PayerClaimWire,
    VirtualClaimWire,
)
from sha_claim.adapters.wire.schemas.common import Page
from sha_claim.adapters.wire.schemas.eligibility import EligibilityWire
from sha_claim.adapters.wire.schemas.emergency import EmergencyProtocolWire
from sha_claim.adapters.wire.schemas.files import DownloadLinkWire, StoredFileWire
from sha_claim.adapters.wire.schemas.preauth import DoctorConsentWire, PreauthorizationWire
from sha_claim.adapters.wire.schemas.prescription import DispenseWire, PrescriptionWire
from sha_claim.adapters.wire.schemas.registry import PatientContactWire, PatientRecordWire
from sha_claim.adapters.wire.transport import Transport, WireResponse
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.benefits import (
    BedOccupancy,
    BenefitPackage,
    InterventionCoverage,
    SubBenefit,
    UtilizationBalance,
)
from sha_claim.domain.claim import (
    ClaimAttachment,
    ClaimDiagnosis,
    ClaimIntervention,
    ClaimLine,
    CoverageSelection,
    Discharge,
    LineEdit,
    LineResubmission,
    NewClaimLine,
    NextOfKin,
    NextOfKinContact,
    PayerClaimRecord,
    Submission,
    VirtualClaim,
)
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.consent import Authorization, ConsentProof, Otp
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.emergency import EmergencyCase, EmergencyProtocol, EmtClaim, ProtocolLine
from sha_claim.domain.enums import CancelReason, IdentificationType, ServiceType
from sha_claim.domain.files import DownloadLink, StoredFile
from sha_claim.domain.identifiers import (
    AttachmentId,
    ClaimGuid,
    ConsentToken,
    FacilityCode,
    FileId,
    LineGuid,
    PatientId,
)
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.domain.preauth import DoctorConsentRequest, Preauthorization, PreauthRequest
from sha_claim.domain.prescription import Dispense, DispenseRequest, Prescription, PrescriptionRequest
from sha_claim.domain.registry import PatientContact, PatientRecord
from sha_claim.errors import UnexpectedResponseError

M = TypeVar("M", bound=BaseModel)


def parse_as(model: type[M], response: WireResponse) -> M:
    raise_for_status(response)
    try:
        payload: Any = response.json()
        return model.model_validate(payload)
    except (ValueError, ValidationError) as exc:
        raise UnexpectedResponseError(f"{model.__name__}: {exc}") from exc


class HttpRegistryGateway:
    """Client Registry: `/patients` and `/patients/contacts`."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def find_patient(
        self, identification_number: str, identification_type: IdentificationType
    ) -> PatientRecord | None:
        response = await self._transport.send(
            requests.find_patient(identification_number, identification_type)
        )
        if response.status == 404:
            return None
        return mappers.to_patient_record(parse_as(PatientRecordWire, response))

    async def contacts(self, patient: PatientId) -> tuple[PatientContact, ...]:
        page = parse_as(
            Page[PatientContactWire], await self._transport.send(requests.patient_contacts(patient))
        )
        return tuple(mappers.to_patient_contact(c) for c in page.results)


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

    async def utilization(
        self, patient: PatientId, intervention: InterventionCode
    ) -> tuple[UtilizationBalance, ...]:
        response = await self._transport.send(requests.utilization(patient, intervention))
        raise_for_status(response)
        # Observed on UAT (2026-09-22): a bare list of records, one per limit scope; the portal documents a
        # single object, and a `{pageSize, results}` page is the house style. Accept all three.
        try:
            payload: Any = response.json()
            rows = payload.get("results", [payload]) if isinstance(payload, dict) else payload
            return tuple(mappers.to_utilization(UtilizationWire.model_validate(r)) for r in rows)
        except (ValueError, ValidationError) as exc:
            raise UnexpectedResponseError(f"{UtilizationWire.__name__}: {exc}") from exc

    async def pomsf_balances(
        self, patient: PatientId, policy_year: str, principal_member_number: str | None
    ) -> Mapping[str, Any]:
        """POMSF (civil-servant scheme) balances. Returned raw: the shape is large and NaCare has no POMSF members yet."""
        response = await self._transport.send(
            requests.pomsf_balances(patient, policy_year, principal_member_number)
        )
        raise_for_status(response)
        payload = response.json()
        return dict(payload) if isinstance(payload, dict) else {"results": payload}

    async def bed_occupancy(self, facility: FacilityCode) -> BedOccupancy:
        response = await self._transport.send(requests.bed_occupancy(facility))
        return mappers.to_bed_occupancy(parse_as(BedOccupancyWire, response))


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

    async def send_otp(self, patient: PatientId, interventions: Sequence[InterventionCode]) -> str:
        response = await self._transport.send(requests.send_visit_otp(patient, interventions))
        return parse_as(MessageWire, response).message

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

    async def list(self, beneficiary: PatientId) -> tuple[Authorization, ...]:
        """Observed on UAT: DHA ignores `beneficiary_code` and returns the whole facility's authorizations,
        so the filter is applied here. Never trust the server-side filter for anything that mutates."""
        response = await self._transport.send(requests.list_authorizations(beneficiary))
        raise_for_status(response)
        payload = response.json()
        records = payload if isinstance(payload, list) else [payload] if payload else []
        try:
            everything = tuple(mappers.to_authorization(AuthorizationWire.model_validate(r)) for r in records)
        except ValidationError as exc:
            raise UnexpectedResponseError(f"AuthorizationWire: {exc}") from exc
        return tuple(a for a in everything if a.beneficiary == beneficiary)

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

    async def switch_intervention(
        self,
        token: ConsentToken,
        existing: InterventionCode,
        new: InterventionCode,
        retain_bill_items: bool,
        bill_from: datetime | None,
        bill_to: datetime | None,
    ) -> None:
        request = requests.switch_intervention(token, existing, new, retain_bill_items, bill_from, bill_to)
        raise_for_status(await self._transport.send(request))

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

    async def submit(self, token: ConsentToken, submission: Submission) -> VirtualClaim:
        response = await self._transport.send(requests.submit(token, submission))
        return mappers.to_virtual_claim(parse_as(VirtualClaimWire, response))

    async def close(self, token: ConsentToken, reason: CancelReason, text: str) -> VirtualClaim:
        response = await self._transport.send(requests.close(token, reason, text))
        return mappers.to_virtual_claim(parse_as(VirtualClaimWire, response))

    async def payer_status(self, claim: ClaimGuid, provider_claim_no: str) -> tuple[PayerClaimRecord, ...]:
        page = parse_as(
            Page[PayerClaimWire], await self._transport.send(requests.payer_status(claim, provider_claim_no))
        )
        return tuple(mappers.to_payer_record(r) for r in page.results)

    async def add_doctor(self, token: ConsentToken, doctor: PractitionerRef) -> str:
        response = await self._transport.send(requests.add_emergency_doctor(token, doctor))
        return parse_as(MessageWire, response).message

    async def send_discharge_otp(self, token: ConsentToken, patient: PatientId) -> str:
        response = await self._transport.send(requests.send_discharge_otp(token, patient))
        return parse_as(MessageWire, response).message

    async def discharge(self, token: ConsentToken, discharge: Discharge) -> VirtualClaim:
        response = await self._transport.send(requests.discharge(token, discharge))
        return mappers.to_virtual_claim(parse_as(VirtualClaimWire, response))

    async def add_next_of_kin(self, token: ConsentToken, next_of_kin: NextOfKin) -> NextOfKinContact:
        response = await self._transport.send(requests.add_next_of_kin(token, next_of_kin))
        return mappers.to_next_of_kin_contact(parse_as(NextOfKinContactWire, response))

    async def resubmit_lines(self, token: ConsentToken) -> LineResubmission:
        response = await self._transport.send(requests.resubmit_lines(token))
        return mappers.to_line_resubmission(parse_as(LineResubmissionWire, response))

    async def set_coverage(self, token: ConsentToken, selection: CoverageSelection) -> None:
        raise_for_status(await self._transport.send(requests.set_coverage(token, selection)))


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


class HttpPrescriptionGateway:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def create(self, token: ConsentToken, request: PrescriptionRequest) -> Prescription:
        response = await self._transport.send(requests.create_prescription(token, request))
        return mappers.to_prescription(parse_as(PrescriptionWire, response))

    async def get(self, token: ConsentToken) -> Prescription | None:
        response = await self._transport.send(requests.get_prescription(token))
        raise_for_status(response)
        payload = response.json()
        if not payload:
            return None
        if isinstance(payload, list):
            payload = payload[0] if payload else None
        elif isinstance(payload, dict) and "results" in payload:
            results = payload.get("results") or []
            payload = results[0] if results else None
        if not payload:
            return None
        try:
            return mappers.to_prescription(PrescriptionWire.model_validate(payload))
        except ValidationError as exc:
            raise UnexpectedResponseError(f"PrescriptionWire: {exc}") from exc

    async def dispense(self, token: ConsentToken, request: DispenseRequest) -> Dispense:
        response = await self._transport.send(requests.create_dispense(token, request))
        return mappers.to_dispense(parse_as(DispenseWire, response))

    async def remove_doctor(
        self, token: ConsentToken, intervention: InterventionCode, registration_number: str
    ) -> None:
        raise_for_status(
            await self._transport.send(
                requests.remove_prescription_doctor(token, intervention, registration_number)
            )
        )


class HttpEmergencyGateway:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def open_case(self, case: EmergencyCase) -> VirtualClaim:
        response = await self._transport.send(requests.open_emergency_case(case))
        return mappers.to_virtual_claim(parse_as(VirtualClaimWire, response))

    async def protocols(self, intervention: InterventionCode, active: bool) -> tuple[EmergencyProtocol, ...]:
        response = await self._transport.send(requests.emergency_protocols(intervention, active))
        page = parse_as(Page[EmergencyProtocolWire], response)
        return tuple(mappers.to_emergency_protocol(p) for p in page.results)

    async def add_protocol(self, token: ConsentToken, line: ProtocolLine) -> ClaimLine:
        response = await self._transport.send(requests.add_emergency_protocol(token, line))
        return mappers.to_claim_line(parse_as(ClaimLineWire, response))

    async def add_doctor(self, token: ConsentToken, doctor: PractitionerRef) -> str:
        response = await self._transport.send(requests.add_emergency_doctor(token, doctor))
        return parse_as(MessageWire, response).message

    async def remove_doctor(self, token: ConsentToken) -> None:
        raise_for_status(await self._transport.send(requests.remove_emergency_doctor(token)))

    async def open_emt(self, token: ConsentToken, claim: EmtClaim) -> VirtualClaim:
        response = await self._transport.send(requests.open_emt_claim(token, claim))
        return mappers.to_virtual_claim(parse_as(VirtualClaimWire, response))


class HttpFileGateway:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def upload(self, filename: str, content: bytes, content_type: str) -> StoredFile:
        response = await self._transport.send(requests.upload(filename, content, content_type))
        return mappers.to_stored_file(parse_as(StoredFileWire, response))

    async def download_link(self, file_id: FileId) -> DownloadLink:
        response = await self._transport.send(requests.download_link(file_id))
        return mappers.to_download_link(parse_as(DownloadLinkWire, response))
