"""Public facade and composition root for the Smart Access SDK."""

from __future__ import annotations

from collections.abc import Sequence
from types import TracebackType
from typing import Self

import httpx

from smart_access.adapters.wire.http_gateways import (
    HttpClaimGateway,
    HttpClinicalGateway,
    HttpMemberGateway,
    HttpPreauthGateway,
    HttpRulesGateway,
    HttpVisitGateway,
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
from smart_access.infrastructure.auth import SmartOAuth2TokenProvider
from smart_access.infrastructure.clock import SystemClock
from smart_access.infrastructure.retry import DEFAULT_RETRY, RetryPolicy
from smart_access.infrastructure.transport import SmartTransport
from smart_access.ports.claim_gateway import ClaimGateway
from smart_access.ports.clinical_gateway import ClinicalGateway
from smart_access.ports.clock import Clock
from smart_access.ports.member_gateway import MemberGateway
from smart_access.ports.preauth_gateway import PreauthGateway
from smart_access.ports.rules_gateway import RulesGateway
from smart_access.ports.token_provider import TokenProvider
from smart_access.ports.visit_gateway import VisitGateway
from smart_access.session import SmartClaimSession
from smart_access.settings import SmartSettings
from smart_access.use_cases.check_member import GetCopaymentRule, GetMemberDetails
from smart_access.use_cases.check_rules import ValidateRules
from smart_access.use_cases.clinical_records import (
    PostAdmission,
    PostClinicalRecord,
    PostClinicalRequests,
    PostDischarge,
    PostItemMapping,
)
from smart_access.use_cases.manage_session import (
    CloseSession,
    FetchPendingSession,
    LinkSession,
    ListSessions,
)
from smart_access.use_cases.process_claim import (
    CheckClaimStatus,
    SubmitClaim,
    SubmitInterimClaim,
)
from smart_access.use_cases.process_preauth import (
    AddPreauthAttachment,
    GetPreauthFeedback,
    SubmitPreauth,
)


class AuthResource:
    """Authentication checks and token retrieval."""

    def __init__(self, tokens: TokenProvider) -> None:
        self._tokens = tokens

    async def token(self) -> str:
        """Returns the active OAuth2 access token."""
        return await self._tokens.access_token()

    async def check(self) -> bool:
        """Verifies that credentials are valid and a token can be acquired."""
        await self._tokens.access_token()
        return True


class SessionsResource:
    """Card swipe session initiation, polling, and lifecycle linking."""

    def __init__(self, client: AsyncSmartClient, gateway: VisitGateway) -> None:
        self._client = client
        self._gateway = gateway
        self._fetch_pending = FetchPendingSession(gateway)
        self._list_sessions = ListSessions(gateway)
        self._link_session = LinkSession(gateway)
        self._close_session = CloseSession(gateway)

    async def fetch_pending(self, patient_number: PatientNumber | str) -> SmartClaimSession | None:
        """Fetch the pending swipe session for a patient and wrap in a SmartClaimSession."""
        session = await self._fetch_pending.execute(patient_number)
        if not session:
            return None
        return SmartClaimSession(
            client=self._client,
            session_id=session.id,
            patient_number=session.patient_number,
            session=session,
        )

    async def list(
        self, patient_number: PatientNumber | str, status: SessionStatus | str = SessionStatus.PENDING
    ) -> tuple[VisitSession, ...]:
        """List all biometric sessions open for a patient."""
        return await self._list_sessions.execute(patient_number, status)

    async def link(
        self, session_id: SessionId | int, visit_number: VisitNumber | str
    ) -> SessionLinkResult:
        """Link an HMIS encounter number to activate a session."""
        return await self._link_session.execute(session_id, visit_number)

    async def close(
        self, session_id: SessionId | int, session_number: str | None = None
    ) -> SessionCloseResult:
        """End an active session."""
        return await self._close_session.execute(session_id, session_number)

    def resume(
        self, session_id: SessionId | int, patient_number: PatientNumber | str
    ) -> SmartClaimSession:
        """Attach to an existing session without an upfront network call."""
        return SmartClaimSession(
            client=self._client,
            session_id=SessionId.of(session_id),
            patient_number=PatientNumber.of(patient_number),
        )


class MembersResource:
    """Patient scheme benefits, balance pools, and copay rules."""

    def __init__(self, gateway: MemberGateway, default_provider_key: str) -> None:
        self._gateway = gateway
        self._default_provider_key = default_provider_key
        self._get_details = GetMemberDetails(gateway)
        self._get_copay = GetCopaymentRule(gateway)

    async def get_details(
        self, patient_number: PatientNumber | str, session_id: SessionId | int
    ) -> tuple[SmartMember, ...]:
        """Fetch member bio, scheme name, copay indicators, and benefit pools."""
        return await self._get_details.execute(patient_number, session_id)

    async def get_copayment_rule(
        self, benefit_id: int, visit_number: VisitNumber | str, provider_key: str = ""
    ) -> CopaymentRule | None:
        """Query specific copayment rules from `/api/copayment`."""
        key = provider_key or self._default_provider_key
        return await self._get_copay.execute(benefit_id, key, visit_number)


class RulesResource:
    """Pre-billing item validation against payer rules engine."""

    def __init__(self, gateway: RulesGateway) -> None:
        self._gateway = gateway
        self._validate = ValidateRules(gateway)

    async def validate(self, request: RulesCheckRequest) -> RuleValidationResult:
        """Run planned billing items against payer rules for exclusions/pre-auth."""
        return await self._validate.execute(request)


class PreauthResource:
    """Pre-authorization creation, attachment upload, and feedback query."""

    def __init__(self, gateway: PreauthGateway) -> None:
        self._gateway = gateway
        self._submit = SubmitPreauth(gateway)
        self._feedback = GetPreauthFeedback(gateway)
        self._add_attachment = AddPreauthAttachment(gateway)

    async def submit(self, request: PreauthRequest) -> PreauthResponse:
        """Submit a pre-authorization request."""
        return await self._submit.execute(request)

    async def get_feedback(
        self,
        visit_number: VisitNumber | str,
        patient_file_no: PatientNumber | str | None = None,
        invoice_no: InvoiceNumber | str | None = None,
    ) -> tuple[PreauthStatusFeedback, ...]:
        """Query insurer pre-authorization decision feedback."""
        return await self._feedback.execute(visit_number, patient_file_no, invoice_no)

    async def add_attachment(
        self, preauth_request_id: PreauthRequestId | str, attachments: Sequence[PreauthAttachment]
    ) -> bool:
        """Upload additional attachments for a pre-authorization."""
        return await self._add_attachment.execute(preauth_request_id, attachments)


class ClaimsResource:
    """Claims submission, interim billing, and settlement status polling."""

    def __init__(self, gateway: ClaimGateway) -> None:
        self._gateway = gateway
        self._submit = SubmitClaim(gateway)
        self._submit_interim = SubmitInterimClaim(gateway)
        self._check_status = CheckClaimStatus(gateway)

    async def submit(self, claim: SmartClaim) -> ClaimSubmissionResult:
        """Post a finalized claim invoice to Smart."""
        return await self._submit.execute(claim)

    async def submit_interim(self, claim: SmartClaim) -> ClaimSubmissionResult:
        """Post an interim bill for long admissions."""
        return await self._submit_interim.execute(claim)

    async def check_status(
        self, invoice_number: InvoiceNumber | str, visit_number: VisitNumber | str
    ) -> ClaimStatusFeedback | None:
        """Query biometric validation status (returns effective status, prioritizing Billed)."""
        return await self._check_status.execute(invoice_number, visit_number)

    async def list_status_attempts(
        self, invoice_number: InvoiceNumber | str, visit_number: VisitNumber | str
    ) -> tuple[ClaimStatusFeedback, ...]:
        """Retrieve the raw list of all claim status attempts."""
        return await self._gateway.check_claim_status(
            InvoiceNumber.of(invoice_number), VisitNumber.of(visit_number)
        )


class ClinicalResource:
    """Clinical diagnostic notes, requests, inpatient flow, and item mappings."""

    def __init__(self, gateway: ClinicalGateway) -> None:
        self._gateway = gateway
        self._record = PostClinicalRecord(gateway)
        self._requests = PostClinicalRequests(gateway)
        self._admission = PostAdmission(gateway)
        self._discharge = PostDischarge(gateway)
        self._mapping = PostItemMapping(gateway)

    async def post_record(self, record: ClinicalRecord) -> bool:
        """Post patient diagnoses to `/api/clinic-record`."""
        return await self._record.execute(record)

    async def post_requests(self, requests: ClinicalRequests) -> bool:
        """Post orders (prescriptions, labs, radiology) to `/api/requests`."""
        return await self._requests.execute(requests)

    async def post_admission(self, admission: AdmissionDetails) -> bool:
        """Post admission details to `/api/admission`."""
        return await self._admission.execute(admission)

    async def post_discharge(self, discharge: DischargeDetails) -> bool:
        """Post discharge summary to `/api/discharge`."""
        return await self._discharge.execute(discharge)

    async def post_mapping(self, mapping: ItemMapping) -> bool:
        """Post item or group for Smart Master List mapping to `/api/new-mapping`."""
        return await self._mapping.execute(mapping)


class AsyncSmartClient:
    """Top-level client for the Smart Access integration API.

    Example:
    ```python
    async with AsyncSmartClient.from_env() as smart:
        session = await smart.sessions.fetch_pending("PT000001")
        if session:
            await session.link("AC000001")
            members = await session.get_members()
    ```
    """

    def __init__(
        self,
        settings: SmartSettings,
        *,
        transport: Transport | None = None,
        tokens: TokenProvider | None = None,
        clock: Clock | None = None,
        retry: RetryPolicy = DEFAULT_RETRY,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self._clock = clock or SystemClock()
        self._owns_http = http is None and transport is None
        self._http = http or httpx.AsyncClient(headers={"User-Agent": "smart-access/0.1"})

        token_url = f"{settings.base_url}/oauth/token"
        self._tokens = tokens or SmartOAuth2TokenProvider(
            token_url=token_url,
            provider_key=settings.provider_key,
            username=settings.username,
            password=settings.password,
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            language=settings.language,
            http=self._http,
            clock=self._clock,
            expiry_skew_seconds=settings.token_expiry_skew_seconds,
        )

        self._transport: Transport = transport or SmartTransport(
            base_url=settings.base_url,
            provider_key=settings.provider_key,
            tokens=self._tokens,
            http=self._http,
            timeouts=settings.timeouts,
            language=settings.language,
            retry=retry,
        )

        # Wire HTTP gateways
        visit_gw = HttpVisitGateway(self._transport)
        member_gw = HttpMemberGateway(self._transport)
        rules_gw = HttpRulesGateway(self._transport)
        preauth_gw = HttpPreauthGateway(self._transport)
        claim_gw = HttpClaimGateway(self._transport)
        clinical_gw = HttpClinicalGateway(self._transport)

        # High-level resources
        self.auth = AuthResource(self._tokens)
        self.sessions = SessionsResource(self, visit_gw)
        self.members = MembersResource(member_gw, settings.provider_key)
        self.rules = RulesResource(rules_gw)
        self.preauth = PreauthResource(preauth_gw)
        self.claims = ClaimsResource(claim_gw)
        self.clinical = ClinicalResource(clinical_gw)

    @classmethod
    def from_env(cls) -> Self:
        return cls(SmartSettings.from_env())

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        await self.aclose()
