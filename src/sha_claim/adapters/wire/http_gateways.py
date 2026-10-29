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
from sha_claim.adapters.wire.schemas.biometrics import (
    CaptureJobWire,
    EnrollmentStatusWire,
    MatchAttemptWire,
    MatchResultWire,
)
from sha_claim.adapters.wire.schemas.callbacks import CallbackEndpointWire, CallbackOperationWire
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
from sha_claim.adapters.wire.schemas.facility import FacilityRecordWire, FacilitySearchWire
from sha_claim.adapters.wire.schemas.files import DownloadLinkWire, StoredFileWire
from sha_claim.adapters.wire.schemas.preauth import DoctorConsentWire, PreauthorizationWire
from sha_claim.adapters.wire.schemas.prescription import DispenseWire, PrescriptionWire
from sha_claim.adapters.wire.schemas.registry import HealthWorkerWire, PatientContactWire, PatientRecordWire
from sha_claim.adapters.wire.schemas.shr import (
    ShrBundleReceiptWire,
    ShrConsentStatusWire,
    ShrConsentWire,
    ShrOpenVisitsWire,
    ShrRefreshWire,
    ShrSecurityLabelsWire,
    ShrSecurityLabelWire,
    ShrVerificationWire,
    ShrVisitClosedWire,
)
from sha_claim.adapters.wire.transport import Transport, WireResponse
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.benefits import (
    BedOccupancy,
    BenefitPackage,
    InterventionCoverage,
    SubBenefit,
    UtilizationBalance,
)
from sha_claim.domain.biometrics import (
    ANY_FINGER,
    CaptureJob,
    CaptureStation,
    EnrollmentStatus,
    MatchAttempt,
    MatchRequestId,
    MatchResult,
)
from sha_claim.domain.callbacks import (
    CallbackEndpoint,
    CallbackEndpointUpdate,
    CallbackEntityType,
    CallbackOperation,
    CallbackOperationUpdate,
    NewCallbackEndpoint,
    NewCallbackOperation,
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
from sha_claim.domain.consent import (
    Authorization,
    BiometricContext,
    ConsentProof,
    Otp,
    OtpWhitelistRequest,
)
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.emergency import EmergencyCase, EmergencyProtocol, EmtClaim, ProtocolLine
from sha_claim.domain.enums import CancelReason, IdentificationType, ServiceType
from sha_claim.domain.facility import FacilityIdentifierType, FacilityRecord
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
from sha_claim.domain.practitioner import HealthWorker, PractitionerRef
from sha_claim.domain.preauth import DoctorConsentRequest, Preauthorization, PreauthRequest
from sha_claim.domain.prescription import Dispense, DispenseRequest, Prescription, PrescriptionRequest
from sha_claim.domain.registry import PatientContact, PatientRecord
from sha_claim.domain.shr import (
    ShrBundleReceipt,
    ShrConsent,
    ShrConsentRequest,
    ShrConsentState,
    ShrConsentTokenValue,
    ShrReferralQuery,
    ShrSecurityLabel,
    ShrVerification,
    ShrVisitClosed,
)
from sha_claim.errors import UnexpectedResponseError

M = TypeVar("M", bound=BaseModel)


def _as_mapping(response: WireResponse) -> Mapping[str, Any]:
    """DHA's answer as given, or empty when it sent no body.

    Passed through rather than modelled: SHA's whitelist verdict is reviewed by a person and its shape
    is not published, so inventing a schema here would mean dropping whatever it actually says.
    """
    try:
        payload: Any = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, Mapping) else {}


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
        # "Nobody by that document" is not an error: UAT answers 400 "zero results found in client registry"
        # rather than 404, and a caller asking "do we know this person?" wants None, not an exception.
        if response.status == 404 or (
            response.status == 400 and b"zero results found" in response.body.lower()
        ):
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
        self, patient: PatientId, sub_benefit_code: str = "", *, code: str = ""
    ) -> tuple[InterventionCoverage, ...]:
        response = await self._transport.send(requests.interventions(patient, sub_benefit_code, code=code))
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


def _matching(records: Sequence[Any], key: str, wanted: str) -> Any | None:
    """The first record whose `key` is `wanted`, compared case-insensitively. None when nothing is asked."""
    if not wanted:
        return None
    for record in records:
        if isinstance(record, Mapping) and str(record.get(key) or "").strip().casefold() == wanted:
            return record
    return None


def _requested_record(records: Sequence[Any], guid: str, token: str) -> Any:
    """Out of what `GET /claims/authorizations` returned, the authorization that was actually asked for.

    **The endpoint answers with a list, and its filters cannot be trusted.** `list_authorizations` in this
    same class is documented from UAT: DHA ignores `beneficiary_code` and hands back the whole facility's
    authorizations, which is why that method filters again on arrival. `tests/contract/test_client.py::
    test_consent_list_filters_out_other_beneficiaries` pins exactly that, on exactly this endpoint.

    This lookup used to take `records[0]` on the strength of the `token`/`guid` filter it sent. Where that
    filter is as loose as its neighbour, a beneficiary holding more than one authorization gets a *different*
    row — and an older `PENDING` one is indistinguishable from a capture the server is still working on. A
    discharge then waits for ever on a capture that has already succeeded, for some patients and not others,
    depending only on how many authorization records the member happens to have (suspected in prod,
    2026-10-29: the eKYC page reported success while the claim panel stayed on PENDING).

    **Falls back to `records[0]`, deliberately.** Returning nothing when no row matches would be asserting
    that `guid` is always present and always spelled the same way on every record SHA returns — and this
    function sits under the check-in consent path, which works today. A wrong guess there would break a
    working flow to fix a suspected one. So the selection can only ever improve: a matching row is used, and
    where none can be told apart the caller gets precisely what it got before. NaCare reports when that
    fallback fires (`record_matches` on the discharge capture view), which is how we learn whether the loose
    filter was ever real.

    Matched on the guid first and the token second, because the guid identifies one authorization while a
    caller may pass an empty token — `StartVisit.open` sends `journey.consent_token or ""`, and the
    `by-token` route defaults `guid` to empty, so each is sometimes the only half available.
    """
    return (
        _matching(records, "guid", guid.strip().casefold())
        or _matching(records, "token", token.strip().casefold())
        or records[0]
    )


class HttpConsentGateway:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def authorize(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        otp: Otp | None,
        biometrics: BiometricContext | None = None,
    ) -> Authorization:
        response = await self._transport.send(
            requests.authorize(patient, service_type, interventions, otp, biometrics)
        )
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
        # The row we asked about, not merely the first row — see `_requested_record`. Still exactly one
        # record is validated, so a malformed authorization belonging to somebody else cannot turn our
        # own lookup into an `UnexpectedResponseError`.
        try:
            return mappers.to_authorization(
                AuthorizationWire.model_validate(_requested_record(records, guid, token))
            )
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

    async def create_otp_whitelist(self, request: OtpWhitelistRequest) -> Mapping[str, Any]:
        response = await self._transport.send(requests.create_otp_whitelist(request))
        raise_for_status(response)
        return _as_mapping(response)

    async def get_otp_whitelist(self, beneficiary: PatientId, facility_fr_code: str) -> Mapping[str, Any]:
        response = await self._transport.send(requests.get_otp_whitelist(beneficiary, facility_fr_code))
        raise_for_status(response)
        return _as_mapping(response)


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

    async def payer_status(
        self, claim: ClaimGuid | None, provider_claim_no: str
    ) -> tuple[PayerClaimRecord, ...]:
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


class HttpShrGateway:
    """The Shared Health Record, over HTTP.

    Reads and writes carry the per-visit consent token; the consent calls that issue it do not.
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def request_consent(self, request: ShrConsentRequest) -> ShrConsent:
        response = await self._transport.send(requests.request_shr_consent(request))
        return mappers.to_shr_consent(parse_as(ShrConsentWire, response))

    async def verify_consent(self, consent_id: str, otp: str, otp_record: str) -> ShrVerification:
        response = await self._transport.send(requests.verify_shr_consent(consent_id, otp, otp_record))
        return mappers.to_shr_verification(parse_as(ShrVerificationWire, response))

    async def consent_status(self, consent_id: str) -> ShrConsentState:
        response = await self._transport.send(requests.shr_consent_status(consent_id))
        return mappers.to_shr_consent_state(parse_as(ShrConsentStatusWire, response))

    async def resend_otp(self, consent_id: str) -> ShrConsent:
        response = await self._transport.send(requests.resend_shr_otp(consent_id))
        return mappers.to_shr_consent(parse_as(ShrConsentWire, response))

    async def open_visits(self, cr_id: str, facility_id: str) -> list[str]:
        response = await self._transport.send(requests.shr_open_visits(cr_id, facility_id))
        return mappers.to_shr_open_visits(parse_as(ShrOpenVisitsWire, response))

    async def refresh(self, visit_id: str) -> ShrConsentTokenValue:
        response = await self._transport.send(requests.refresh_shr_consent(visit_id))
        return ShrConsentTokenValue(parse_as(ShrRefreshWire, response).consent_token)

    async def close_visit(self, visit_id: str) -> ShrVisitClosed:
        response = await self._transport.send(requests.close_shr_visit(visit_id))
        return mappers.to_shr_visit_closed(parse_as(ShrVisitClosedWire, response))

    async def patient_records(
        self,
        token: ShrConsentTokenValue,
        cr_id: str,
        practitioner_id: str,
        resources: Sequence[str] = (),
        *,
        resource_id: str = "",
        page_token: str = "",
        search: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        """The FHIR search result, passed through exactly as DHA returned it.

        Not modelled: DHA forwards the upstream result unchanged and the caller already speaks FHIR, so
        parsing it here would only add a second, worse FHIR implementation to keep in step.
        """
        response = await self._transport.send(
            requests.fetch_shr_records(
                token,
                cr_id,
                practitioner_id,
                resources,
                resource_id=resource_id,
                page_token=page_token,
                search=search,
            )
        )
        raise_for_status(response)
        body = response.json()
        return body if isinstance(body, Mapping) else {}

    async def submit_bundle(
        self, token: ShrConsentTokenValue, bundle: Mapping[str, Any], *, callback_url: str = ""
    ) -> ShrBundleReceipt:
        response = await self._transport.send(
            requests.submit_shr_bundle(token, bundle, callback_url=callback_url)
        )
        return mappers.to_shr_bundle_receipt(parse_as(ShrBundleReceiptWire, response))

    async def resource_labels(self, resource_name: str = "", code: str = "") -> Mapping[str, Any]:
        response = await self._transport.send(requests.shr_resource_labels(resource_name, code))
        raise_for_status(response)
        body = response.json()
        return body if isinstance(body, Mapping) else {}

    async def query_referrals(self, query: ShrReferralQuery) -> Mapping[str, Any]:
        """The FHIR `searchset` of referrals, passed through exactly as DHA returned it.

        No consent token: this is a query over referrals addressed to an organisation, not a read of one
        patient's record. Paging is by the bundle's own `next` link, whose `page_token` the caller feeds
        back in.
        """
        response = await self._transport.send(requests.query_shr_referrals(query))
        raise_for_status(response)
        body = response.json()
        return body if isinstance(body, Mapping) else {}

    async def query_observations(
        self,
        token: ShrConsentTokenValue,
        subject: str,
        practitioner_uid: str,
        *,
        page_token: str = "",
    ) -> Mapping[str, Any]:
        """A patient's observations as a FHIR `searchset`, passed through unchanged."""
        response = await self._transport.send(
            requests.query_shr_observations(token, subject, practitioner_uid, page_token=page_token)
        )
        raise_for_status(response)
        body = response.json()
        return body if isinstance(body, Mapping) else {}

    async def security_labels(self) -> tuple[ShrSecurityLabel, ...]:
        """The label catalogue, modelled — unlike the FHIR passthroughs above.

        Worth modelling because it is *reference* data a screen has to reason about: which codes mean
        "restricted", which are sensitivity rather than confidentiality. Entries with no code are dropped,
        since a label that cannot be matched against a resource's `meta.security` has no use.
        """
        response = await self._transport.send(requests.shr_security_labels())
        raise_for_status(response)
        return tuple(
            mappers.to_shr_security_label(w) for w in self._label_wires(response.json()) if w.code or w.label
        )

    @staticmethod
    def _label_wires(body: Any) -> list[ShrSecurityLabelWire]:
        """The catalogue, out of whichever envelope DHA wrapped it in.

        Three shapes have been seen — a bare list, `{"labels": [...]}`, and `{"data": {"labels": [...]}}` —
        so all three are unwrapped here rather than one being assumed and the others silently yielding an
        empty catalogue, which would make every sensitivity label render as a bare code.
        """
        if isinstance(body, list):
            return [ShrSecurityLabelWire.model_validate(item) for item in body if isinstance(item, Mapping)]
        if not isinstance(body, Mapping):
            return []
        envelope = ShrSecurityLabelsWire.model_validate(body)
        if envelope.labels:
            return envelope.labels
        data = envelope.data
        if isinstance(data, list):
            return [ShrSecurityLabelWire.model_validate(item) for item in data if isinstance(item, Mapping)]
        if isinstance(data, Mapping):
            inner = data.get("labels") or data.get("results") or data.get("security_labels")
            if isinstance(inner, list):
                return [ShrSecurityLabelWire.model_validate(i) for i in inner if isinstance(i, Mapping)]
        return []


class HttpFacilityRegistryGateway:
    """The Facility Registry — `GET /facilities/search`.

    Separate from `HttpBenefitGateway`'s bed-occupancy call, which asks about *our* facility. This one names
    somebody else's, which is what a referral needs.
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def search(
        self,
        identifier: str = "",
        identifier_type: FacilityIdentifierType = FacilityIdentifierType.FR_CODE,
        name: str = "",
    ) -> tuple[FacilityRecord, ...]:
        """Matching facilities, newest DHA envelope or oldest — see `_records`.

        An empty tuple means the registry holds no match, which is an answer a picker should show as "no
        such facility" rather than as a failure.
        """
        response = await self._transport.send(requests.search_facilities(identifier, identifier_type, name))
        raise_for_status(response)
        return tuple(
            mappers.to_facility_record(w) for w in self._records(response.json()) if w.fr_code or w.name
        )

    @staticmethod
    def _records(body: Any) -> list[FacilityRecordWire]:
        """The facilities out of the envelope.

        An identifier lookup answers with a bare object (one facility), a name search with a list or a
        `data`/`results` wrapper. Treating the single-object case as a list is the bug to avoid: pydantic
        would validate the *envelope* against the record model, every aliased field would miss, and the
        caller would get one facility with no FR code — a picker entry that cannot be referred to.
        """
        if isinstance(body, list):
            return [FacilityRecordWire.model_validate(i) for i in body if isinstance(i, Mapping)]
        if not isinstance(body, Mapping):
            return []
        envelope = FacilitySearchWire.model_validate(body)
        if envelope.results:
            return envelope.results
        data = envelope.data
        if isinstance(data, list):
            return [FacilityRecordWire.model_validate(i) for i in data if isinstance(i, Mapping)]
        if isinstance(data, Mapping):
            inner = data.get("results") or data.get("facilities")
            if isinstance(inner, list):
                return [FacilityRecordWire.model_validate(i) for i in inner if isinstance(i, Mapping)]
            return [FacilityRecordWire.model_validate(data)]
        # A bare facility object, which is what an identifier lookup returns.
        return [FacilityRecordWire.model_validate(body)]


class HttpHealthWorkerGateway:
    """The Health Worker Registry — `GET /api/v1/professionals`."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def find(
        self,
        identification_number: str,
        identification_type: IdentificationType,
        regulator: str = "",
    ) -> HealthWorker | None:
        response = await self._transport.send(
            requests.find_health_worker(identification_number, identification_type, regulator)
        )
        # "No practitioner membership" is a 400, but it is an *answer* — the registry holds nobody with
        # that number — and a desk needs to be told that rather than shown a transport failure.
        if response.status >= 400:
            body_text = response.body.decode(errors="replace")
            if "no practitioner membership" in body_text.lower():
                return None
        raise_for_status(response)
        # DHA answers with a bare object for some lookups and a paged list for others.
        body: Any = response.json()
        # DHA wraps the practitioner in `message.membership`; `results` and a bare list are kept for the
        # shapes the documentation implies. Unwrapped in that order, because the real one is the one that
        # arrives: validating the envelope itself succeeds — every field is optional — and yields a
        # practitioner with no registry id, which downstream cannot tell from "no such practitioner".
        if isinstance(body, Mapping) and isinstance(body.get("message"), Mapping):
            body = body["message"]
        if isinstance(body, Mapping) and isinstance(body.get("membership"), Mapping):
            body = body["membership"]
        if isinstance(body, Mapping):
            results = body.get("results")
            if isinstance(results, list):
                body = results[0] if results else None
        elif isinstance(body, list):
            body = body[0] if body else None
        if not isinstance(body, Mapping) or not body:
            return None
        return mappers.to_health_worker(HealthWorkerWire.model_validate(body))


class HttpCallbackGateway:
    """Status-callback registration — `/tenants/.../endpoints` and their operations.

    The one part of the API that configures DHA to call *us*. Listings come back as a bare JSON array
    here, not the `Page` envelope the rest of the API uses, and both shapes are tolerated because a
    middleware that changed once can change again.
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    @staticmethod
    def _rows(response: WireResponse) -> list[Any]:
        raise_for_status(response)
        try:
            payload: Any = response.json()
        except ValueError as exc:
            raise UnexpectedResponseError(f"callback listing: {exc}") from exc
        if isinstance(payload, list):
            return payload
        if isinstance(payload, Mapping):
            # `{results: [...]}` (the Page envelope) or `{data: [...]}` (what delete returns).
            for key in ("results", "data", "endpoints", "operations"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        raise UnexpectedResponseError(f"callback listing: expected a list, got {type(payload).__name__}")

    async def list_endpoints(
        self, tenant: str, entity_type: CallbackEntityType | None = None
    ) -> tuple[CallbackEndpoint, ...]:
        response = await self._transport.send(
            requests.list_callback_endpoints(tenant, entity_type.value if entity_type else "")
        )
        return tuple(
            mappers.to_callback_endpoint(CallbackEndpointWire.model_validate(row))
            for row in self._rows(response)
        )

    async def register_endpoint(self, tenant: str, endpoint: NewCallbackEndpoint) -> CallbackEndpoint:
        response = await self._transport.send(requests.register_callback_endpoint(tenant, endpoint))
        return mappers.to_callback_endpoint(parse_as(CallbackEndpointWire, response))

    async def update_endpoint(self, endpoint_id: str, changes: CallbackEndpointUpdate) -> CallbackEndpoint:
        response = await self._transport.send(requests.update_callback_endpoint(endpoint_id, changes))
        return mappers.to_callback_endpoint(parse_as(CallbackEndpointWire, response))

    async def delete_endpoint(self, endpoint_id: str) -> None:
        raise_for_status(await self._transport.send(requests.delete_callback_endpoint(endpoint_id)))

    async def list_operations(
        self, tenant: str, endpoint_id: str, action: str = ""
    ) -> tuple[CallbackOperation, ...]:
        response = await self._transport.send(requests.list_callback_operations(tenant, endpoint_id, action))
        return tuple(
            mappers.to_callback_operation(CallbackOperationWire.model_validate(row))
            for row in self._rows(response)
        )

    async def register_operation(
        self, tenant: str, endpoint_id: str, operation: NewCallbackOperation
    ) -> CallbackOperation:
        response = await self._transport.send(
            requests.register_callback_operation(tenant, endpoint_id, operation)
        )
        return mappers.to_callback_operation(parse_as(CallbackOperationWire, response))

    async def read_operation(self, operation_id: str) -> CallbackOperation:
        response = await self._transport.send(requests.read_callback_operation(operation_id))
        return mappers.to_callback_operation(parse_as(CallbackOperationWire, response))

    async def update_operation(
        self, operation_id: str, changes: CallbackOperationUpdate
    ) -> CallbackOperation:
        response = await self._transport.send(requests.update_callback_operation(operation_id, changes))
        return mappers.to_callback_operation(parse_as(CallbackOperationWire, response))

    async def delete_operation(self, operation_id: str) -> None:
        raise_for_status(await self._transport.send(requests.delete_callback_operation(operation_id)))


class HttpBiometricsGateway:
    """Minors fingerprint consent: `/biometrics/enrollments`, `/enrollment-status` and `/matches`.

    Every write here dispatches a capture to a physical reader at a named workstation and returns `202`
    with an id, not an outcome. Nothing in this class waits for a verdict, and nothing in it should ever
    grow a retry loop around `match_status`: DHA delivers the verdict by callback and says the read "should
    not be called in a loop". It is a reconciliation read, and the caller decides when reconciling is due.
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def enrol(
        self,
        beneficiary: PatientId,
        position: int,
        station: CaptureStation,
        deadline_seconds: int | None = None,
    ) -> CaptureJob:
        response = await self._transport.send(
            requests.enrol_minor_fingerprint(beneficiary, position, station, deadline_seconds)
        )
        return mappers.to_capture_job(parse_as(CaptureJobWire, response))

    async def verify(
        self,
        beneficiary: PatientId,
        position: int,
        station: CaptureStation,
        deadline_seconds: int | None = None,
    ) -> CaptureJob:
        response = await self._transport.send(
            requests.verify_minor_fingerprint(beneficiary, position, station, deadline_seconds)
        )
        return mappers.to_capture_job(parse_as(CaptureJobWire, response))

    async def enrollment_status(self, beneficiary: PatientId) -> EnrollmentStatus:
        response = await self._transport.send(requests.minor_enrollment_status(beneficiary))
        # The beneficiary is passed through: DHA does not always echo the code, and a status whose subject
        # is unknown cannot safely be attributed to the child at the desk.
        return mappers.to_enrollment_status(parse_as(EnrollmentStatusWire, response), beneficiary)

    async def match(
        self,
        beneficiary: PatientId,
        station: CaptureStation,
        position: int = ANY_FINGER,
        deadline_seconds: int | None = None,
    ) -> MatchAttempt:
        response = await self._transport.send(
            requests.match_minor_fingerprint(beneficiary, station, position, deadline_seconds)
        )
        return mappers.to_match_attempt(parse_as(MatchAttemptWire, response))

    async def match_status(self, match_id: MatchRequestId) -> MatchResult:
        response = await self._transport.send(requests.minor_match_status(match_id))
        return mappers.to_match_result(parse_as(MatchResultWire, response))
