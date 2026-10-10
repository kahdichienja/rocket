"""Composition root and public facade."""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self

import httpx

from sha_claim.adapters.wire.http_gateways import (
    HttpCallbackGateway,
    HttpConsentGateway,
    HttpEligibilityGateway,
    HttpEmergencyGateway,
    HttpFacilityRegistryGateway,
    HttpFileGateway,
    HttpHealthWorkerGateway,
    HttpPreauthGateway,
    HttpPrescriptionGateway,
    HttpRegistryGateway,
    HttpShrGateway,
    HttpVirtualClaimGateway,
)
from sha_claim.adapters.wire.transport import Transport
from sha_claim.domain.benefits import (
    BedOccupancy,
    BenefitPackage,
    InterventionCoverage,
    SubBenefit,
    UtilizationBalance,
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
from sha_claim.domain.claim import PayerClaimRecord
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.consent import Authorization, BiometricContext, ConsentProof, Otp
from sha_claim.domain.eligibility import Eligibility
from sha_claim.domain.emergency import EmergencyCase, EmergencyProtocol
from sha_claim.domain.enums import BroughtBy, IdentificationType, ModeOfArrival, ServiceType
from sha_claim.domain.facility import FacilityIdentifierType, FacilityRecord
from sha_claim.domain.files import DownloadLink, StoredFile
from sha_claim.domain.identifiers import ConsentToken, FacilityCode, FileId, PatientId
from sha_claim.domain.identity import BearerToken, Identity
from sha_claim.domain.pomsf import PomsfBalance, parse_pomsf_balances, policy_year_for
from sha_claim.domain.practitioner import HealthWorker, PractitionerRef
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
    ShrVisitType,
)
from sha_claim.errors import RequestValidationError, Violation
from sha_claim.events import EventHook
from sha_claim.facility import FacilityScope
from sha_claim.infrastructure.auth import OAuth2ClientCredentials
from sha_claim.infrastructure.clock import SystemClock
from sha_claim.infrastructure.retry import DEFAULT_RETRY, RetryPolicy
from sha_claim.infrastructure.transport import HttpxTransport
from sha_claim.ports.claim_gateways import ClaimGateways
from sha_claim.ports.clock import Clock
from sha_claim.ports.consent_gateway import ConsentGateway
from sha_claim.ports.eligibility_gateway import EligibilityGateway
from sha_claim.ports.file_gateway import FileGateway
from sha_claim.ports.registry_gateway import RegistryGateway
from sha_claim.ports.token_provider import TokenProvider
from sha_claim.session import ClaimSession
from sha_claim.settings import SHASettings
from sha_claim.use_cases.capture_consent import CaptureConsent
from sha_claim.use_cases.open_visit import OpenVisit
from sha_claim.use_cases.verify_eligibility import VerifyEligibility


class AuthResource:
    """Credentials and identity. The SDK authenticates implicitly; this is for health checks and 'which facility am I'."""

    def __init__(self, tokens: TokenProvider) -> None:
        self._tokens = tokens

    async def identity(self) -> Identity:
        """`POST /tenants/token` (cached) → the facility/tenant the credentials belong to. Never returns the token."""
        token = await self._tokens.access_token()
        return _identity_from_jwt(token)

    async def check(self) -> bool:
        """True if a token can be obtained. Raises AuthenticationError/TransportError otherwise."""
        await self._tokens.access_token()
        return True

    async def token(self) -> BearerToken:
        """The raw grant (`access_token`, remaining `expires_in`, `token_type`), from the cache when still valid.

        For callers that must hit the HIE directly (legacy code, bots). Prefer the SDK's own methods:
        they never need the token.
        """
        token = await self._tokens.access_token()
        remaining = _identity_from_jwt(token).seconds_remaining
        return BearerToken(access_token=token, expires_in=remaining if remaining is not None else 0)


def _identity_from_jwt(token: str) -> Identity:
    claims: dict[str, object] = {}
    parts = token.split(".")
    if len(parts) == 3:
        try:
            payload = parts[1] + "=" * (-len(parts[1]) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            if isinstance(decoded, dict):
                claims = decoded
        except (ValueError, UnicodeDecodeError):
            claims = {}
    facility = str(claims.get("facility_id") or "").strip()
    return Identity(
        facility=FacilityCode(facility) if facility else None,
        facility_id_type=str(claims.get("facility_id_type") or ""),
        tenant_id=str(claims.get("tenant_id") or ""),
        tenant_name=str(claims.get("tenant_name") or ""),
        issuer=str(claims.get("iss") or ""),
        client_id=str(claims.get("client_id") or claims.get("azp") or ""),
        issued_at=_epoch(claims.get("iat")),
        expires_at=_epoch(claims.get("exp")),
    )


def _epoch(value: object) -> datetime | None:
    return datetime.fromtimestamp(int(value), tz=UTC) if isinstance(value, (int, float)) else None


class EligibilityResource:
    """Who is covered, and for what. All reads; safe to retry."""

    def __init__(self, gateway: EligibilityGateway) -> None:
        self._gateway = gateway
        self._verify = VerifyEligibility(gateway)

    async def check(self, identification_number: str, identification_type: IdentificationType) -> Eligibility:
        """`GET /patients/eligibility` — is this person an SHA beneficiary, and under which schemes?"""
        return await self._verify.execute(identification_number, identification_type)

    async def benefits(self, patient: PatientId | str) -> tuple[BenefitPackage, ...]:
        """`GET /patients/benefits` — top-level packages (SHA-08, SHA-12, …) available to the patient."""
        return await self._gateway.benefits(PatientId.of(patient))

    async def sub_benefits(self, patient: PatientId | str) -> tuple[SubBenefit, ...]:
        """`GET /patients/sub-benefits` — sub-benefit codes (SHA-12-SC-01, …) with access points."""
        return await self._gateway.sub_benefits(PatientId.of(patient))

    async def interventions(
        self, patient: PatientId | str, sub_benefit_code: str = "", *, code: InterventionCode | str = ""
    ) -> tuple[InterventionCoverage, ...]:
        """`GET /patients/benefits/interventions` — billable interventions, with tariffs and preauth flags.

        Both filters are optional. `code` fetches one intervention's coverage without knowing its
        sub-benefit, which is how a caller holding only a code — off a claim, where the sub-benefit is
        not carried — reaches `required_preauth_document_types`. That list is published nowhere else,
        and without it a pre-auth is filed blind and refused for documents nobody was asked for.
        """
        return await self._gateway.interventions(
            PatientId.of(patient), sub_benefit_code, code=str(code) if code else ""
        )

    async def utilization(
        self, patient: PatientId | str, intervention: InterventionCode | str
    ) -> tuple[UtilizationBalance, ...]:
        """`GET /patients/benefits/utilization` — remaining limits for one intervention.

        One record per limit scope (individual, household, fund …); UAT returns a bare list.
        """
        return await self._gateway.utilization(PatientId.of(patient), InterventionCode.of(intervention))

    async def pomsf_balances(
        self,
        patient: PatientId | str,
        policy_year: str | None = None,
        *,
        principal_member_number: str | None = None,
    ) -> PomsfBalance | None:
        """`GET /patients/pomsf-balances` — what a civil servant's household has left to spend.

        POMSF gives a household a pot against a policy rather than a limit per intervention, and dependants
        draw on the principal's pot — so pass `principal_member_number` for a dependant, or the balance read
        is not the one that will be spent.

        `policy_year` defaults to the year covering today (financial years turn on 1 July; see
        `policy_year_for`). `None` comes back when the server had nothing to say, which is **not** a zero
        balance — see `PomsfBalance.remaining`.
        """
        payload = await self._gateway.pomsf_balances(
            PatientId.of(patient), policy_year or policy_year_for(), principal_member_number
        )
        return parse_pomsf_balances(payload)

    async def pomsf_balances_raw(
        self, patient: PatientId | str, policy_year: str, *, principal_member_number: str | None = None
    ) -> Mapping[str, Any]:
        """The same call, unparsed — for support when a field this SDK does not model is in question."""
        return await self._gateway.pomsf_balances(PatientId.of(patient), policy_year, principal_member_number)

    async def bed_occupancy(self, facility: FacilityCode | str) -> BedOccupancy:
        """`GET /facilities/{code}/beds/occupancy`."""
        return await self._gateway.bed_occupancy(FacilityCode.of(facility))


class FilesResource:
    """Standalone uploads. Claim attachments normally go inline via `ClaimSession.attach`."""

    def __init__(self, gateway: FileGateway) -> None:
        self._gateway = gateway

    async def upload(
        self, filename: str, content: bytes, content_type: str = "application/octet-stream"
    ) -> StoredFile:
        return await self._gateway.upload(filename, content, content_type)

    async def download_link(self, file_id: FileId | str) -> DownloadLink:
        return await self._gateway.download_link(FileId.of(file_id))


class ConsentResource:
    """Patient consent. `authorize` sends the OTP; `open_visit` (on `claims`) consumes it."""

    def __init__(self, gateway: ConsentGateway) -> None:
        self._gateway = gateway
        self._capture = CaptureConsent(gateway)

    async def authorize(
        self,
        patient: PatientId | str,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode | str],
        otp: Otp | None = None,
    ) -> Authorization:
        """`POST /claims/authorize` — creates a PENDING authorization and triggers the OTP to the beneficiary.

        Use `InterventionCoverage.service_type_for_authorization` to pick `service_type`: CAPITATION
        interventions are rejected under OUTPATIENT.
        """
        codes = [InterventionCode.of(c) for c in interventions]
        return await self._capture.execute(PatientId.of(patient), service_type, codes, otp)

    async def authorize_biometric(
        self,
        patient: PatientId | str,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode | str],
        biometrics: BiometricContext,
    ) -> Authorization:
        """`POST /claims/authorize` with eKYC factors — the path for a member SHA will not OTP.

        Returns a PENDING authorization carrying `verification.request_url`: send the beneficiary there to
        prove who they are, then poll `get()` until `is_verified`, and open the visit with `.proof`.

        The capture URL is short-lived (`verification.embed_expiry`, 120s on UAT). If it lapses the
        authorization stays PENDING **and blocks a new one for the same patient and interventions**, so call
        `reject(authorization.token)` before trying again — otherwise the desk is wedged.
        """
        codes = [InterventionCode.of(c) for c in interventions]
        return await self._capture.execute(PatientId.of(patient), service_type, codes, None, biometrics)

    async def send_otp(
        self, patient: PatientId | str, interventions: Sequence[InterventionCode | str]
    ) -> str:
        """`POST /claims/otp` — (re)send the visit OTP to the beneficiary's registered phone.

        `authorize` already triggers the first OTP; use this to resend. On UAT the response message
        contains the OTP itself (sandbox behaviour) — never rely on that in production.
        """
        codes = [InterventionCode.of(c) for c in interventions]
        return await self._gateway.send_otp(PatientId.of(patient), codes)

    async def get(
        self, token: str, guid: str, patient: PatientId | str | None = None
    ) -> Authorization | None:
        """`GET /claims/authorizations` — re-read an authorization; `None` if the server knows nothing."""
        return await self._gateway.get(token, guid, PatientId.of(patient) if patient else None)

    async def list(self, patient: PatientId | str) -> tuple[Authorization, ...]:
        """`GET /claims/authorizations?beneficiary_code=…` — every authorization for a beneficiary (undocumented; live on UAT).

        Use it to find a dangling PENDING authorization (which blocks the OTP path) and `reject` it.
        """
        return await self._gateway.list(PatientId.of(patient))

    async def reject(self, token: str) -> None:
        """`POST /claims/authorizations/{token}/reject` — close a pending authorization."""
        await self._gateway.reject(token)


class ClaimsResource:
    """Virtual claims. `open_visit` starts one; `resume` re-attaches to one you already hold the token for."""

    def __init__(self, gateways: ClaimGateways) -> None:
        self._gateways = gateways
        self._open_visit = OpenVisit(gateways.claims)

    async def open_visit(
        self,
        patient: PatientId | str,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode | str],
        proof: ConsentProof | Authorization,
    ) -> ClaimSession:
        """`POST /claims/visit` — opens the server-side virtual claim and returns a session bound to its consent token.

        `proof` is the OTP the beneficiary read out, a `BiometricGuid`/`MatchId` from the biometric path, or
        the `Authorization` that `consent.authorize()` returned (its guid is used).
        """
        codes = [InterventionCode.of(c) for c in interventions]
        claim = await self._open_visit.execute(
            PatientId.of(patient),
            service_type,
            codes,
            proof.proof if isinstance(proof, Authorization) else proof,
        )
        return ClaimSession(self._gateways, claim.consent_token, claim)

    def resume(self, consent_token: ConsentToken | str) -> ClaimSession:
        """Re-attach to an existing virtual claim (e.g. from a token persisted by NaCare). No network call."""
        return ClaimSession(self._gateways, ConsentToken.of(consent_token))

    def before_visit(self, authorization: Authorization | ConsentToken | str) -> ClaimSession:
        """The pre-visit phase of an elective pre-authorisation. No network call.

        An elective operation is approved **before** the patient arrives: consent is captured, the pre-auth
        is filed and the payer finalises it, and only then is the visit opened on the day. DHA's elective
        scenario does this with the token `POST /claims/authorize` returns — the same token `POST /preauths`
        takes as its `consent_token`, with no virtual claim behind it.

        This library used to say that could not be done, on the grounds that only `/claims/visit` issues a
        consent token. It does not: `/claims/authorize` issues one too, and the whole pre-visit half of the
        elective flow hangs off that one fact.

        The session it returns is for `request_preauth()` and `preauths()` only. There is no claim yet, so
        `add_line`, `preview`, `submit` and `discharge` will be refused by SHA — on the day, open the visit
        with `open_visit()` and bill against *that* session, using the **same patient and the same
        intervention code**, which is how SHA links the approval to the new claim.

            auth = await sha.consent.authorize(patient, ServiceType.INPATIENT, [code], otp)
            pre = sha.claims.before_visit(auth)
            await pre.request_preauth(code, ...)            # PENDING_DOCTOR_APPROVAL
            ...                                             # doctor signs → ACTIVE → payer → FINALISED
            session = await sha.claims.open_visit(patient, ServiceType.INPATIENT, [code], auth)
        """
        token = authorization.token if isinstance(authorization, Authorization) else authorization
        if not str(token).strip():
            raise ValueError("authorization has no token to raise a pre-authorisation against")
        return ClaimSession(self._gateways, ConsentToken.of(token))

    async def payer_status(self, provider_claim_no: str) -> tuple[PayerClaimRecord, ...]:
        """`GET /claims/preview/payer` — how the payer sees a submitted claim, **without a consent token**.

        Here rather than only on the session because asking how a claim is going is a read about a claim
        that is already finished, often days later. A consent token authorises *acting on a visit*; it is
        short-lived by design, so requiring one to check a status makes the answer unobtainable exactly
        when it is wanted. This takes the claim number and nothing else.

        DHA has no webhook and no bulk read, so this one call is how a payment, a rejection or a request
        for correction is ever discovered.
        """
        if not provider_claim_no.strip():
            raise RequestValidationError([Violation("provider_claim_no", "cannot be empty")])
        return await self._gateways.claims.payer_status(None, provider_claim_no)


class RegistryResource:
    """The Client Registry: turn an identity document into a CR number, and check the member is reachable.

    Worth calling before consent: SHA sends the visit OTP only to a confirmed, active phone contact, and a
    member with none cannot consent by OTP at all — `contacts()` says so without a failed attempt.
    """

    def __init__(self, gateway: RegistryGateway) -> None:
        self._gateway = gateway

    async def find_patient(
        self,
        identification_number: str,
        identification_type: IdentificationType = IdentificationType.NATIONAL_ID,
    ) -> PatientRecord | None:
        """`GET /patients` — None when the registry holds nobody with that document."""
        return await self._gateway.find_patient(identification_number, identification_type)

    async def contacts(self, patient: PatientId | str) -> tuple[PatientContact, ...]:
        """`GET /patients/contacts` — an empty tuple means the OTP path is closed for this member."""
        return await self._gateway.contacts(PatientId.of(patient))

    async def can_consent_by_otp(self, patient: PatientId | str) -> bool:
        """Whether `consent.send_otp` can work: SHA needs a confirmed, active phone on record."""
        return any(c.can_receive_otp for c in await self.contacts(patient))


class EmergencyResource:
    """Emergency case claims: opened without prior OTP consent, billed by protocol."""

    def __init__(self, gateways: ClaimGateways) -> None:
        self._gateways = gateways

    async def open_case(
        self,
        attending: PractitionerRef,
        reference_number: str,
        brought_by: BroughtBy,
        mode_of_arrival: ModeOfArrival,
        interventions: Sequence[InterventionCode | str],
        *,
        patient: PatientId | str | None = None,
        otp: Otp | None = None,
        notes: str,
    ) -> ClaimSession:
        """`POST /claims/emergency` — `patient=None` for an unidentified casualty.

        `notes` is required by SHA. Interventions must belong to the emergency fund (see
        `InterventionCoverage.is_emergency`); the facility must be accredited for emergency services.
        """
        try:
            case = EmergencyCase(
                attending,
                reference_number,
                brought_by,
                mode_of_arrival,
                tuple(InterventionCode.of(c) for c in interventions),
                PatientId.of(patient) if patient is not None else None,
                otp,
                notes,
            )
        except ValueError as exc:
            raise RequestValidationError([Violation("emergency", str(exc))]) from exc
        claim = await self._gateways.emergency.open_case(case)
        return ClaimSession(self._gateways, claim.consent_token, claim)

    async def protocols(
        self, intervention: InterventionCode | str, *, active: bool = True
    ) -> tuple[EmergencyProtocol, ...]:
        """`GET /claims/emergency/protocols` — billable treatment protocols for an intervention."""
        return await self._gateways.emergency.protocols(InterventionCode.of(intervention), active)


class HealthWorkersResource:
    """The Health Worker Registry.

    Resolves a regulator's registration number to the registry id the SHR wants as `practitioner_id`, and
    checks a number belongs to somebody real before a pre-auth is filed against it.
    """

    def __init__(self, gateway: HttpHealthWorkerGateway) -> None:
        self._gateway = gateway

    async def find(
        self,
        registration_number: str,
        identification_type: IdentificationType = IdentificationType.REGISTRATION_NUMBER,
        regulator: str = "",
    ) -> HealthWorker | None:
        """`None` when the registry holds nobody with that number — which is an answer, not an error."""
        return await self._gateway.find(registration_number, identification_type, regulator)


class ShrResource:
    """The Shared Health Record — the patient's history from *other* facilities.

    Separate from everything else on this client, and separately consented: a member who agreed to the
    visit has not agreed to their records being read, and DHA sends a second OTP for that.

    The usual order is `request_consent` → patient reads out the code → `verify` → `records`. The token
    `verify` returns is a credential: it opens one patient's history across every facility that has treated
    them, so it belongs server-side and should never be handed to a browser.
    """

    def __init__(self, gateway: HttpShrGateway) -> None:
        self._gateway = gateway

    async def request_consent(
        self,
        cr_id: str,
        facility_id: str,
        requested_by: str,
        visit_type: ShrVisitType = ShrVisitType.OUTPATIENT,
    ) -> ShrConsent:
        """Ask DHA to text the patient a code. Answers with the `consent_id` and `otp_record`."""
        return await self._gateway.request_consent(
            ShrConsentRequest(
                cr_id=cr_id, facility_id=facility_id, requested_by=requested_by, visit_type=visit_type
            )
        )

    async def verify(self, consent_id: str, otp: str, otp_record: str) -> ShrVerification:
        """Exchange the code for the per-visit token.

        `otp_record` must be the one from the *most recent* request or resend — a resend issues a new one
        and the old value stops working.
        """
        return await self._gateway.verify_consent(consent_id, otp, otp_record)

    async def status(self, consent_id: str) -> ShrConsentState:
        return await self._gateway.consent_status(consent_id)

    async def resend_otp(self, consent_id: str) -> ShrConsent:
        """Send the code again. **Use the `otp_record` this returns**, not the original."""
        return await self._gateway.resend_otp(consent_id)

    async def refresh(self, visit_id: str) -> ShrConsentTokenValue:
        """A fresh token for a visit that is still open."""
        return await self._gateway.refresh(visit_id)

    async def close(self, visit_id: str) -> ShrVisitClosed:
        """Close the visit. The token cannot be refreshed afterwards."""
        return await self._gateway.close_visit(visit_id)

    async def records(
        self,
        token: ShrConsentTokenValue | str,
        cr_id: str,
        practitioner_id: str,
        resources: Sequence[str] = (),
        *,
        resource_id: str = "",
        page_token: str = "",
        search: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        """The patient's records, as the FHIR search result DHA returned.

        `practitioner_id` is the **Health Worker Registry** id of the clinician asking — not their KMPDC
        registration number, which is what a claim uses. DHA records who read the record.
        """
        return await self._gateway.patient_records(
            _shr_token(token),
            cr_id,
            practitioner_id,
            resources,
            resource_id=resource_id,
            page_token=page_token,
            search=search,
        )

    async def submit(
        self,
        token: ShrConsentTokenValue | str,
        bundle: Mapping[str, Any],
        *,
        callback_url: str = "",
    ) -> ShrBundleReceipt:
        """Push a FHIR `collection` Bundle into the SHR.

        A `success` means DHA accepted the envelope. The contents are validated upstream and
        asynchronously, so it is **not** confirmation that the resources were stored — pass
        `callback_url` if you need to hear the real outcome.
        """
        return await self._gateway.submit_bundle(_shr_token(token), bundle, callback_url=callback_url)

    async def referrals(
        self,
        *,
        performer: str = "",
        requester: str = "",
        status: str = "",
        count: int = 0,
        page_token: str = "",
    ) -> Mapping[str, Any]:
        """Referrals as a FHIR `searchset`, passed through exactly as DHA returned it.

        **This one takes no consent token.** Every other read on this resource asks what is in a patient's
        record and needs their say-so; this asks which referrals point at an *organisation*, which is a
        question about a facility's own workload. That distinction is what makes a referral inbox possible —
        a receiving desk can see a patient is coming before the patient, and their OTP, has arrived.

        Direction is which argument you pass, and mixing them up silently shows the wrong list:

            performer=<our FR code>   → referrals sent **to** us   (inbox)
            requester=<our FR code>   → referrals we **raised**    (outbox)

        One of the two is required. Page by feeding the `page_token` from the bundle's `next` link back in.
        """
        return await self._gateway.query_referrals(
            ShrReferralQuery(
                performer_fr_code=performer,
                requester_fr_code=requester,
                status=status,
                count=count,
                page_token=page_token,
            )
        )

    async def observations(
        self,
        token: ShrConsentTokenValue | str,
        subject: str,
        practitioner_uid: str,
        *,
        page_token: str = "",
    ) -> Mapping[str, Any]:
        """A patient's observations, as the FHIR `searchset` DHA returned.

        `practitioner_uid` travels in the `X-PUID` **header** on this endpoint, where `records()` sends the
        same fact as a `practitioner_id` query parameter. DHA rejects it in the wrong place, so the two are
        not interchangeable despite being the same identifier.

        `records(resources=["Observation"])` answers the same question; this exists because DHA publishes it
        and because paging one resource type is cheaper than paging the whole record.
        """
        return await self._gateway.query_observations(
            _shr_token(token), subject, practitioner_uid, page_token=page_token
        )

    async def security_labels(self) -> tuple[ShrSecurityLabel, ...]:
        """The catalogue of confidentiality and sensitivity labels.

        Fetch once and keep: it is static reference data, and it is what turns a resource's `meta.security`
        from `["PSY"]` into something a clinician can act on.
        """
        return await self._gateway.security_labels()

    async def resource_labels(self, resource_name: str = "", code: str = "") -> Mapping[str, Any]:
        """What a consent grants access to. DHA requires at least one of the two filters."""
        if not resource_name and not code:
            raise ValueError("resource_labels needs a resource_name or a code")
        return await self._gateway.resource_labels(resource_name, code)


class CallbacksResource:
    """Where the HIE should deliver status changes — the one API that configures DHA to call us.

    `register` does both halves in one go, because an endpoint without an operation is registered,
    returns 201, and then silently delivers nothing — the single easiest way to lose a day. Call the
    individual methods if you need them apart.
    """

    def __init__(self, gateway: HttpCallbackGateway) -> None:
        self._gateway = gateway

    async def endpoints(
        self, tenant: str, entity_type: CallbackEntityType | None = None
    ) -> tuple[CallbackEndpoint, ...]:
        """`GET /tenants/{tenant}/endpoints`. **Paused endpoints are omitted** — use `operation()` to
        tell "paused" from "never registered". A tenant *code* returns an empty list where the tenant
        *id* returns rows."""
        return await self._gateway.list_endpoints(tenant, entity_type)

    async def register(
        self,
        tenant: str,
        endpoint: NewCallbackEndpoint,
        operation: NewCallbackOperation | None = None,
    ) -> tuple[CallbackEndpoint, CallbackOperation | None]:
        """Register an endpoint and, unless told otherwise, the `status_changed` operation it needs.

        `tenant` should be the facility FR code: on the operation call DHA uses that path segment to
        backfill the endpoint's `facility_fr_code` when it is empty.
        """
        created = await self._gateway.register_endpoint(tenant, endpoint)
        if operation is None:
            return created, None
        attached = await self._gateway.register_operation(tenant, created.endpoint_id, operation)
        return created, attached

    async def update_endpoint(self, endpoint_id: str, changes: CallbackEndpointUpdate) -> CallbackEndpoint:
        """`PATCH`. An empty change set is a 400 from DHA, so it is refused here instead."""
        if not changes.has_changes:
            raise RequestValidationError([Violation("changes", "nothing to update")])
        return await self._gateway.update_endpoint(endpoint_id, changes)

    async def pause_endpoint(self, endpoint_id: str) -> CallbackEndpoint:
        """Stop delivery without deleting. Reversible, unlike `delete_endpoint`."""
        return await self._gateway.update_endpoint(endpoint_id, CallbackEndpointUpdate(is_active=False))

    async def resume_endpoint(self, endpoint_id: str) -> CallbackEndpoint:
        return await self._gateway.update_endpoint(endpoint_id, CallbackEndpointUpdate(is_active=True))

    async def delete_endpoint(self, endpoint_id: str) -> None:
        """Takes every operation under it as well. Prefer `pause_endpoint` for anything temporary."""
        await self._gateway.delete_endpoint(endpoint_id)

    async def operations(
        self, tenant: str, endpoint_id: str, action: str = ""
    ) -> tuple[CallbackOperation, ...]:
        """Only *active* operations. A missing one may be paused rather than absent — `operation()` says."""
        return await self._gateway.list_operations(tenant, endpoint_id, action)

    async def add_operation(
        self, tenant: str, endpoint_id: str, operation: NewCallbackOperation
    ) -> CallbackOperation:
        return await self._gateway.register_operation(tenant, endpoint_id, operation)

    async def operation(self, operation_id: str) -> CallbackOperation:
        """`GET` one. Returns inactive ones too, which is what makes it the way to check for a pause."""
        return await self._gateway.read_operation(operation_id)

    async def update_operation(
        self, operation_id: str, changes: CallbackOperationUpdate
    ) -> CallbackOperation:
        if not changes.has_changes:
            raise RequestValidationError([Violation("changes", "nothing to update")])
        return await self._gateway.update_operation(operation_id, changes)

    async def delete_operation(self, operation_id: str) -> None:
        """Leaves the endpoint standing."""
        await self._gateway.delete_operation(operation_id)


class FacilitiesResource:
    """The Facility Registry — naming a facility that is **not** us.

    Everywhere else a facility is implied by the credential or by `activate_facility`. A referral has to
    name its destination, and the SHR addresses referrals by FR code (`Organization/FID-17-116073-1`), so a
    desk that only knows a hospital's name needs this to get a code.
    """

    def __init__(self, gateway: HttpFacilityRegistryGateway) -> None:
        self._gateway = gateway

    async def search(
        self,
        *,
        name: str = "",
        identifier: str = "",
        identifier_type: FacilityIdentifierType = FacilityIdentifierType.FR_CODE,
    ) -> tuple[FacilityRecord, ...]:
        """Facilities matching a name or an identifier. Empty means the registry holds no match.

        A returned facility is not necessarily one a patient can be sent to — check
        `FacilityRecord.is_referable`, which is operational **and** SHA-contracted. Both failures are worth
        showing rather than hiding: a suspended facility cannot treat the patient, an uncontracted one will
        bill them privately, and some referrals are clinically necessary regardless.
        """
        return await self._gateway.search(identifier, identifier_type, name)

    async def find_by_fr_code(self, fr_code: str) -> FacilityRecord | None:
        """One facility by its FR code, or `None` when the registry has no such code — an answer, not an error."""
        found = await self._gateway.search(fr_code, FacilityIdentifierType.FR_CODE, "")
        return found[0] if found else None


def _shr_token(token: ShrConsentTokenValue | str) -> ShrConsentTokenValue:
    return token if isinstance(token, ShrConsentTokenValue) else ShrConsentTokenValue(token)


class AsyncSHAClient:
    """Entry point. Use as `async with AsyncSHAClient.from_env() as sha:`.

    Every collaborator is injectable for tests; defaults wire httpx + OAuth2 + retries.
    """

    def __init__(
        self,
        settings: SHASettings,
        *,
        transport: Transport | None = None,
        tokens: TokenProvider | None = None,
        clock: Clock | None = None,
        retry: RetryPolicy = DEFAULT_RETRY,
        http: httpx.AsyncClient | None = None,
        on_event: EventHook | None = None,
    ) -> None:
        self.settings = settings
        self._clock = clock or SystemClock()
        self._owns_http = http is None and transport is None
        self._http = http or httpx.AsyncClient(headers={"User-Agent": "sha-claim/0.1"})
        self._tokens = tokens or OAuth2ClientCredentials(
            token_url=f"{settings.api_root}/tenants/token",
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            http=self._http,
            clock=self._clock,
            expiry_skew_seconds=settings.token_expiry_skew_seconds,
            on_event=on_event,
        )
        self._transport: Transport = transport or HttpxTransport(
            http=self._http,
            api_root=settings.api_root,
            tokens=self._tokens,
            timeouts=settings.timeouts,
            retry=retry,
            on_event=on_event,
            clock=self._clock,
            default_facility=FacilityScope(FacilityCode(settings.facility), settings.facility_id_type)
            if settings.facility
            else None,
        )
        self.auth = AuthResource(self._tokens)
        self.eligibility = EligibilityResource(HttpEligibilityGateway(self._transport))
        self.registries = RegistryResource(HttpRegistryGateway(self._transport))
        self.consent = ConsentResource(HttpConsentGateway(self._transport))
        gateways = ClaimGateways(
            claims=HttpVirtualClaimGateway(self._transport),
            preauths=HttpPreauthGateway(self._transport),
            prescriptions=HttpPrescriptionGateway(self._transport),
            emergency=HttpEmergencyGateway(self._transport),
        )
        self.claims = ClaimsResource(gateways)
        self.emergency = EmergencyResource(gateways)
        self.files = FilesResource(HttpFileGateway(self._transport))
        self.shr = ShrResource(HttpShrGateway(self._transport))
        self.facilities = FacilitiesResource(HttpFacilityRegistryGateway(self._transport))
        self.health_workers = HealthWorkersResource(HttpHealthWorkerGateway(self._transport))
        self.callbacks = CallbacksResource(HttpCallbackGateway(self._transport))

    @classmethod
    def from_env(cls, *, on_event: EventHook | None = None) -> Self:
        return cls(SHASettings.from_env(), on_event=on_event)

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        await self.aclose()
