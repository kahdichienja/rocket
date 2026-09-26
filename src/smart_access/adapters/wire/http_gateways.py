"""HTTP implementations of Smart Access ports over Transport."""

from __future__ import annotations

from collections.abc import Sequence

from smart_access.adapters.wire.mappers import (
    map_claim_status_feedback,
    map_claim_submission_result,
    map_copayment_rule,
    map_preauth_response,
    map_preauth_status_feedback,
    map_rules_validation_result,
    map_session_close_result,
    map_session_link_result,
    map_smart_members,
    map_visit_sessions,
)
from smart_access.adapters.wire.requests import (
    build_admission_request,
    build_claim_request,
    build_claim_status_request,
    build_clinical_record_request,
    build_clinical_requests_request,
    build_close_session_request,
    build_discharge_request,
    build_get_copayment_request,
    build_get_member_request,
    build_interim_claim_request,
    build_item_mapping_request,
    build_link_session_request,
    build_list_sessions_request,
    build_preauth_attachment_request,
    build_preauth_request,
    build_preauth_status_request,
    build_rules_request,
)
from smart_access.adapters.wire.transport import Transport
from smart_access.domain.claim import (
    ClaimStatusFeedback,
    ClaimSubmissionResult,
    SmartClaim,
)
from smart_access.domain.clinical import (
    AdmissionDetails,
    ClinicalRecord,
    ClinicalRequests,
    DischargeDetails,
    ItemMapping,
)
from smart_access.domain.enums import SessionStatus
from smart_access.domain.identifiers import (
    InvoiceNumber,
    PatientNumber,
    PreauthRequestId,
    SessionId,
    VisitNumber,
)
from smart_access.domain.member import (
    CopaymentRule,
    SmartMember,
)
from smart_access.domain.preauth import (
    PreauthAttachment,
    PreauthRequest,
    PreauthResponse,
    PreauthStatusFeedback,
)
from smart_access.domain.rules import (
    RulesCheckRequest,
    RuleValidationResult,
)
from smart_access.domain.session import (
    SessionCloseResult,
    SessionLinkResult,
    VisitSession,
)
from smart_access.ports.claim_gateway import ClaimGateway
from smart_access.ports.clinical_gateway import ClinicalGateway
from smart_access.ports.member_gateway import MemberGateway
from smart_access.ports.preauth_gateway import PreauthGateway
from smart_access.ports.rules_gateway import RulesGateway
from smart_access.ports.visit_gateway import VisitGateway


class HttpVisitGateway(VisitGateway):
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def list_sessions(
        self, patient_number: PatientNumber, status: SessionStatus | str = SessionStatus.PENDING
    ) -> tuple[VisitSession, ...]:
        spec = build_list_sessions_request(patient_number, status)
        data = await self._transport.request(spec.method, spec.path, params=spec.params)
        return map_visit_sessions(data)

    async def link_session(self, session_id: SessionId, visit_number: VisitNumber) -> SessionLinkResult:
        spec = build_link_session_request(session_id, visit_number)
        data = await self._transport.request(spec.method, spec.path)
        return map_session_link_result(data if isinstance(data, dict) else {"code": "200"})

    async def close_session(
        self, session_id: SessionId, session_number: str | None = None
    ) -> SessionCloseResult:
        spec = build_close_session_request(session_id, session_number)
        data = await self._transport.request(spec.method, spec.path, json_body=spec.json_body)
        return map_session_close_result(data if isinstance(data, dict) else {"code": "200"})


class HttpMemberGateway(MemberGateway):
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def get_member_details(
        self, patient_number: PatientNumber, session_id: SessionId
    ) -> tuple[SmartMember, ...]:
        spec = build_get_member_request(patient_number, session_id)
        data = await self._transport.request(spec.method, spec.path, params=spec.params)
        return map_smart_members(data)

    async def get_copayment_rule(
        self, benefit_id: int, provider_key: str, visit_number: VisitNumber
    ) -> CopaymentRule | None:
        key = provider_key or self._transport.provider_key
        spec = build_get_copayment_request(benefit_id, key, visit_number)
        data = await self._transport.request(spec.method, spec.path, params=spec.params)
        if not data or not isinstance(data, dict):
            return None
        return map_copayment_rule(data, benefit_id)


class HttpRulesGateway(RulesGateway):
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def validate_rules(self, request: RulesCheckRequest) -> RuleValidationResult:
        spec = build_rules_request(request)
        data = await self._transport.request(spec.method, spec.path, json_body=spec.json_body)
        return map_rules_validation_result(data if isinstance(data, dict) else {"code": "200", "content": []})


class HttpPreauthGateway(PreauthGateway):
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def submit_preauth(self, request: PreauthRequest) -> PreauthResponse:
        spec = build_preauth_request(request, self._transport.provider_key)
        data = await self._transport.request(spec.method, spec.path, json_body=spec.json_body)
        raw = data[0] if isinstance(data, list) and data else data
        return map_preauth_response(raw if isinstance(raw, dict) else {})

    async def get_preauth_status(
        self,
        visit_number: VisitNumber,
        patient_file_no: PatientNumber | None = None,
        invoice_no: InvoiceNumber | None = None,
    ) -> tuple[PreauthStatusFeedback, ...]:
        spec = build_preauth_status_request(visit_number, patient_file_no, invoice_no)
        data = await self._transport.request(spec.method, spec.path, params=spec.params)
        return map_preauth_status_feedback(data)

    async def add_attachment(
        self, preauth_request_id: PreauthRequestId, attachments: Sequence[PreauthAttachment]
    ) -> bool:
        spec = build_preauth_attachment_request(preauth_request_id, attachments)
        data = await self._transport.request(spec.method, spec.path, json_body=spec.json_body)
        if isinstance(data, dict):
            return str(data.get("code") or "200") in ("200", "201")
        return True


class HttpClaimGateway(ClaimGateway):
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def post_claim(self, claim: SmartClaim) -> ClaimSubmissionResult:
        spec = build_claim_request(claim)
        data = await self._transport.request(
            spec.method, spec.path, params=spec.params, json_body=spec.json_body
        )
        return map_claim_submission_result(data if isinstance(data, dict) else {"code": "200"})

    async def post_interim_claim(self, claim: SmartClaim) -> ClaimSubmissionResult:
        spec = build_interim_claim_request(claim)
        data = await self._transport.request(spec.method, spec.path, json_body=spec.json_body)
        return map_claim_submission_result(data if isinstance(data, dict) else {"code": "200"})

    async def check_claim_status(
        self, invoice_number: InvoiceNumber, visit_number: VisitNumber
    ) -> tuple[ClaimStatusFeedback, ...]:
        spec = build_claim_status_request(invoice_number, visit_number)
        data = await self._transport.request(spec.method, spec.path, params=spec.params)
        return map_claim_status_feedback(data)


class HttpClinicalGateway(ClinicalGateway):
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def post_clinical_record(self, record: ClinicalRecord) -> bool:
        spec = build_clinical_record_request(record)
        data = await self._transport.request(spec.method, spec.path, json_body=spec.json_body)
        return bool(data)

    async def post_clinical_requests(self, requests: ClinicalRequests) -> bool:
        spec = build_clinical_requests_request(requests)
        data = await self._transport.request(spec.method, spec.path, json_body=spec.json_body)
        return bool(data)

    async def post_admission(self, admission: AdmissionDetails) -> bool:
        spec = build_admission_request(admission)
        data = await self._transport.request(spec.method, spec.path, json_body=spec.json_body)
        return bool(data)

    async def post_discharge(self, discharge: DischargeDetails) -> bool:
        spec = build_discharge_request(discharge)
        data = await self._transport.request(spec.method, spec.path, json_body=spec.json_body)
        return bool(data)

    async def post_item_mapping(self, mapping: ItemMapping) -> bool:
        spec = build_item_mapping_request(mapping)
        data = await self._transport.request(
            spec.method, spec.path, params=spec.params, json_body=spec.json_body
        )
        return bool(data)
