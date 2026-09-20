# sha-claim — Architecture

> Companion to [../PLAN.md](../PLAN.md). API contract: [api/README.md](api/README.md) (endpoint
> reference) and [api/WORKFLOWS.md](api/WORKFLOWS.md) (how calls chain). Follows the DRY + OOP +
> Clean mandate used across NaCare (see `Nacare/payments/`). This is an **SDK**: no web framework,
> no database, no workers — a library that drives the AfyaConnect HIE eClaims API correctly.

**Revision 2 (2026-09-20)** — rewritten after reading the official docs. Two assumptions from
revision 1 were wrong and are corrected here: the API is **not FHIR** (custom REST, JSON +
multipart), and the **claim is owned by the server**, not built locally.

---

## 1. Tech stack (the "framework" question)

There is no application framework in this package. It is a plain library:

| Concern | Choice | Why |
|---|---|---|
| Language | Python ≥ 3.11 | Matches NaCare; `Self`, `ExceptionGroup`, fast asyncio |
| HTTP | `httpx` (async) | Typed, async-native, multipart support, `respx` for tests; same as NaCare payments |
| Wire schemas | `pydantic` v2 | Strict parsing of the API's JSON at the boundary; alias generators handle `snake_case`/`camelCase` drift |
| Domain models | stdlib `dataclasses` (frozen), `enum.StrEnum`, `decimal.Decimal` | Dependency rule — the domain imports nothing third-party |
| Tests | `pytest`, `pytest-asyncio`, `respx`, `hypothesis` | Boundary mocking only; property tests for value objects |
| Quality | `ruff`, `mypy --strict`, `import-linter`, `pre-commit` | Layer rule enforced by CI, not by review comments |
| Build/publish | `hatchling`, `src/` layout, `py.typed`, PyPI trusted publishing | Standard modern packaging, no `setup.py` |

(For the record: the DHA developer portal itself is Next.js + MUI + Apollo GraphQL; we scraped its
server-side props to obtain the OpenAPI-derived spec now stored in `docs/api/spec/`.)

---

## 2. Design goals

| Goal | Consequence |
|---|---|
| Never lose a claim handle | `ConsentToken` is a first-class value object; every operation that needs it takes it explicitly or via a `ClaimSession` that owns it |
| Reject locally what the server will certainly reject | Request-level invariants (enums, ICD format, positive quantities, Decimal money) validated before any HTTP call; claim *completeness* is the server's job (`/claims/preview`) |
| Survive a flaky gateway | Timeouts everywhere; retries only for GETs and transient errors; `submit` is never blindly retried (see §8) |
| Swap wire details without touching workflow logic | pydantic schemas + mappers live in `adapters/`; use cases see domain types only |
| Testable offline | Ports are `Protocol`s; use cases are tested with fakes; only `infrastructure/` touches httpx |
| Small, discoverable public API | Resource-style facade: `sha.eligibility`, `sha.claims`, `sha.preauths`, `sha.files` |

Non-goals: persistence, UI, FHIR, generic HTTP client.

---

## 3. Layer map (dependencies point inward →)

```
 infrastructure ─► adapters ─► use_cases ─► domain
      │               │            │
      │               │            └── ports (Protocols owned by use cases)
      │               └── wire schemas (pydantic), request builders, response mappers, error translation
      └── httpx transport, OAuth2 token provider, retry policy, logging, settings, clock

 client.py (composition root) assembles infrastructure → adapters → use cases and exposes the facade.
```

Rules (enforced by `import-linter`):
- `domain/` → stdlib only. `use_cases/` → `domain`, `ports`. `adapters/` → `domain`, `ports`, pydantic.
  `infrastructure/` → anything. Nothing imports `client.py` except consumers.
- Data crossing inward is frozen dataclasses; data crossing outward is pydantic models or plain dicts/bytes.

---

## 4. Package layout

```
src/sha_claim/
├── __init__.py                      # public API (§7)
├── py.typed
├── errors.py                        # exception hierarchy (§9)
├── settings.py                      # SHASettings from env; fail fast
├── client.py                        # AsyncSHAClient facade + composition root
│
├── domain/                          # ── stdlib only ──
│   ├── identifiers.py               # ConsentToken, PatientId (CR number), FacilityCode, PractitionerRef, ClaimGuid, LineGuid, FileId
│   ├── codes.py                     # Icd11Code, InterventionCode, SchemeCode, ProtocolCode, DocumentType(StrEnum), RegulationBody(StrEnum)
│   ├── money.py                     # Money (Decimal, KES), arithmetic, quantisation
│   ├── enums.py                     # ServiceType, CancelReason, DischargeReason, IdentificationType, BroughtBy, ModeOfArrival, NextOfKinIdType, DoctorConsentRequestType
│   ├── eligibility.py               # Eligibility, Scheme, BenefitPackage, InterventionCoverage, UtilizationBalance
│   ├── consent.py                   # Authorization (from /claims/authorize), ConsentStrategy = Otp | BiometricGuid
│   ├── claim.py                     # VirtualClaim (server snapshot, rich read model), ClaimLine, ClaimDiagnosis, Invoice, WorkflowState(+Unknown)
│   ├── preauth.py                   # Preauthorization snapshot, PreauthItem, PreauthDoctor, PreauthStatus(+Unknown)
│   ├── attachments.py               # Attachment (bytes|path, filename, DocumentType)
│   └── policies.py                  # RequestValidationPolicy: everything we can prove wrong before an HTTP call
│
├── ports/
│   ├── eligibility_gateway.py       # check(), benefits(), interventions(), utilization(), sub_benefits()
│   ├── consent_gateway.py           # authorize(), get_authorization(), reject()
│   ├── virtual_claim_gateway.py     # open_visit(), add/remove intervention|diagnosis|line|attachment, preview(), submit(), close(), discharge(), send_discharge_otp(), payer_status(), add_next_of_kin()
│   ├── preauth_gateway.py           # create(), get(), remove_diagnosis(), remove_doctor(), cancel(), request_doctor_consent()
│   ├── file_gateway.py              # upload(), download_url()
│   ├── token_provider.py            # access_token()
│   └── clock.py                     # now()
│
├── use_cases/
│   ├── eligibility/verify_eligibility.py
│   ├── consent/capture_consent.py
│   ├── claims/open_visit.py
│   ├── claims/build_claim.py        # AddIntervention, AddDiagnosis, AddLine, AddAttachment (+ removals) — one class each, tiny
│   ├── claims/preview_claim.py
│   ├── claims/submit_claim.py       # the only non-idempotent money-moving call; guarded (§8)
│   ├── claims/close_claim.py
│   ├── claims/discharge_inpatient.py
│   ├── claims/track_payer_claim.py
│   └── preauth/request_preauthorization.py
│
├── adapters/wire/                   # ── knows JSON/multipart, never the network ──
│   ├── schemas/                     # pydantic: token.py, eligibility.py, authorization.py, claim.py, preauth.py, common.py (ErrorEnvelope)
│   ├── requests.py                  # domain → (method, path, json|data|files) request specs
│   ├── mappers.py                   # pydantic response → domain snapshots; camelCase/snake_case normalisation
│   ├── multipart.py                 # the one place that knows "diagnoses is a JSON string in a form field"
│   ├── error_translator.py          # (status, ErrorEnvelope) → SDK exception
│   └── http_gateways.py             # implements every port over a Transport
│
└── infrastructure/
    ├── transport.py                 # Transport protocol + HttpxTransport (timeouts, bearer, correlation id, redaction)
    ├── auth.py                      # OAuth2ClientCredentials: POST /tenants/token, expiry-skew cache, single-flight refresh
    ├── retry.py                     # RetryPolicy — idempotency-aware
    ├── logging.py                   # stdlib logging + contextvars correlation id + PII redaction filter
    └── clock.py                     # SystemClock

tests/
├── unit/domain/  unit/use_cases/  contract/adapters/  contract/infrastructure/  live/
└── fixtures/                        # recorded UAT payloads (sanitised) + docs/api/spec/*.json used to assert path/field drift
```

Out of v1 (added later as new modules behind new ports, no domain edits): emergency & EMT claims,
ePrescriptions/dispensing, POMSF balances, bed occupancy.

---

## 5. Domain model — the server owns the claim

### 5.1 `ConsentToken`
The `authorization_code` returned by `POST /claims/visit`. Frozen VO, redacted in `repr`/logs
(it is both an identifier and a credential). Everything after visit creation takes it.

### 5.2 `VirtualClaim` — a rich **read model**, not an aggregate
The server holds the truth; the SDK holds a snapshot mapped from the response of
`visit / preview / submit`. It is behavioural where behaviour is *derived*, never *mutating*:

```python
snapshot.workflow_state  # WorkflowState enum with Unknown(raw) fallback
snapshot.is_submitted  # derived from state
snapshot.net_total  # Money, from total_claim_net_amount
snapshot.lines_for(intervention)  # filtered view
```
Mutations are use cases that call the server and return a fresh snapshot. No local state machine
pretends to know what the server will do.

### 5.3 `ClaimSession` (public API sugar, lives in `session.py`)
Binds a `ConsentToken` to the claim use cases so callers don't thread the token through every call:

```python
session = await sha.claims.open_visit(
    patient, ServiceType.OUTPATIENT, [InterventionCode("...")], consent=Otp("123456")
)
await session.add_diagnosis(Icd11Code("1A00"), intervention)
await session.add_line(intervention, unit_price=Money.kes("1500.00"), quantity=1)
await session.attach(Attachment.from_path("discharge.pdf", DocumentType.DISCHARGE_SUMMARY), intervention)
preview = await session.preview()
receipt = await session.submit(invoice_number="INV-2026-000123")
```
`ClaimSession` is a thin coordinator: it coerces strings to value objects, translates their `ValueError`s into
`RequestValidationError`, and delegates. The only orchestration rule it owns ("preview before payer_status if we have no
GUID") is one line. `sha.claims.resume(token)` re-attaches to a claim whose token NaCare persisted.

### 5.4 `RequestValidationPolicy`
Single home for "we can prove the server will reject this": enum membership, ICD-11 pattern,
`quantity > 0`, `unit_price ≥ 0`, attachment size/type, `service_end ≥ service_start`, required
fields per consent strategy. Returns *all* violations. Completeness rules (does the claim have at
least one line?) are **not** duplicated — `preview()` is the server's answer and the SDK surfaces it.

### 5.5 Status vocabularies
`workflow_state`, `claim_auth_status`, authorization `status`, preauth `status` are undocumented
(WORKFLOWS Q4). Each becomes a `StrEnum` populated from UAT recordings **plus** an `Unknown(raw)`
carrier so a new server value degrades to "unknown" instead of crashing a billing run.

---

## 6. Use cases & ports

Each use case: one class, constructor-injected ports, `async def execute(...)`, domain in/out.

| Use case | Port | Endpoint(s) | Idempotent |
|---|---|---|---|
| `VerifyEligibility` | `EligibilityGateway` | `GET /patients/eligibility` (+ benefits, utilization) | yes |
| `CaptureConsent` | `ConsentGateway` | `POST /claims/authorize`, `GET /claims/authorizations` | no (OTP consumed) |
| `OpenVisit` | `VirtualClaimGateway` | `POST /claims/visit` | no (OTP consumed) |
| `AddIntervention/Diagnosis/Line/Attachment` (+ `Remove*`) | `VirtualClaimGateway` | `POST/PATCH /claims/...` | server-side dedupe unknown → no auto-retry |
| `PreviewClaim` | `VirtualClaimGateway` | `POST /claims/preview` | yes (read despite POST) |
| `SubmitClaim` | `VirtualClaimGateway`, `Clock` | `POST /claims/submit` | **no** — see §8 |
| `CloseClaim` | `VirtualClaimGateway` | `POST /claims/close` | effectively yes |
| `DischargeInpatient` | `VirtualClaimGateway` | `POST /claims/otp/discharge`, `POST /claims/discharge` | no |
| `TrackPayerClaim` | `VirtualClaimGateway` | `GET /claims/preview/payer` | yes |
| `RequestPreauthorization` | `PreauthGateway`, `FileGateway` | `POST /preauths` (multipart), `GET /preauths` | no |

Ports are split by consumer role (ISP). A single `HttpGateways` class in `adapters/wire/` may
implement several of them — that is an implementation convenience, not a fat interface.

---

## 7. Public API

```python
from sha_claim import AsyncSHAClient, SHASettings
from sha_claim import (
    ConsentToken,
    PatientId,
    InterventionCode,
    Icd11Code,
    Money,
    ServiceType,
    DocumentType,
    Attachment,
    Otp,
    BiometricGuid,
    WorkflowState,
    Eligibility,
    VirtualClaim,
    SubmissionReceipt,
    Preauthorization,
)
from sha_claim.errors import *

async with (
    AsyncSHAClient.from_env() as sha
):  # SHA_BASE_URL, SHA_AUTH_URL, SHA_CLIENT_ID, SHA_CLIENT_SECRET, SHA_FACILITY_CODE
    elig = await sha.eligibility.check(id_number="37161876", id_type=IdentificationType.NATIONAL_ID)
    patient = elig.patient_id  # CR number
    session = await sha.claims.open_visit(patient, ServiceType.OUTPATIENT, [code], consent=Otp("..."))
    ...
    receipt = await session.submit(invoice_number="INV-1")
    status = await sha.claims.payer_status(receipt.claim_guid, provider_claim_no="INV-1")
```

Resource groups: `sha.eligibility`, `sha.consent`, `sha.claims`, `sha.emergency`. Pre-auth, prescriptions and
emergency billing hang off `ClaimSession` because they are all keyed by the claim's consent token.
Everything is injectable (`AsyncSHAClient(settings, transport=..., clock=...)`) for tests.

Sync client: deferred; if needed, generated via `unasync`, never hand-copied.

---

## 8. Resilience contract

1. **Timeouts** per request: connect 5 s, read 30 s (uploads 120 s), configurable.
2. **Retry** (3 attempts, exp. backoff, full jitter, cap 8 s) only when *both* hold:
   operation is idempotent (all GETs, `/claims/preview`) **and** failure is transient
   (connect/read error, 408/429/502/503/504).
3. **Submit is special.** `SubmitClaim` is attempted once. On a timeout/5xx with an ambiguous
   outcome it raises `SubmissionOutcomeUnknownError(consent_token)`; the caller resolves it with
   `PreviewClaim` (state will be submitted or not) and decides. The SDK never guesses with money.
   Revisit once WORKFLOWS Q5 (server idempotency) is answered.
4. **Auth**: 401 → one token refresh → one replay → `AuthenticationError`.
5. **Correlation id** per logical operation: request header, log field, exception attribute.
6. **Redaction**: bearer tokens, `consent_token`, OTPs, national IDs, phone numbers never reach logs.

---

## 9. Error taxonomy

```
SHAClaimError
├── ConfigurationError               # bad/missing settings (startup)
├── RequestValidationError           # local policy; list[Violation]
├── AuthenticationError              # token endpoint failure / 401 after refresh
├── PermissionDeniedError            # 403 {error, message}
├── BadRequestError                  # 400 {error, message} — server-side validation
├── TransportError                   # network/timeout/5xx after retries; carries correlation_id
│   ├── RateLimitedError             # 429
│   └── SubmissionOutcomeUnknownError     # submit sent, result unknown; carries consent_token
└── UnexpectedResponseError          # schema mismatch — the server changed under us
```
Every wire failure is translated in `adapters/wire/error_translator.py` from the uniform
`{error, message}` envelope. httpx exceptions never escape `infrastructure/`.

---

## 10. Testing strategy

| Layer | Tool | Asserts |
|---|---|---|
| domain | pytest + hypothesis | VO invariants, Money arithmetic, enum `Unknown` fallback, policy completeness |
| use_cases | pytest + in-memory fakes | orchestration, precondition guards, submit-once guarantee |
| adapters | pytest + fixtures | request specs match `docs/api/spec/*.json` paths/fields (drift test); response → domain mapping incl. camel/snake; multipart encoding |
| infrastructure | pytest + respx | retry schedule, single-flight refresh, header injection, redaction |
| live | `pytest -m live` | one outpatient happy path on UAT; nightly, off by default |

Mocks only at httpx/clock. Domain objects are never mocked. Coverage gate 90 %.

---

## 11. Decision log

| # | Decision | Rationale |
|---|---|---|
| D1 | No FHIR anywhere | The API is custom REST; FHIR would be invented complexity |
| D2 | Server-owned claim, SDK holds snapshots | Mirrors the API; a local state machine would drift from the server's |
| D3 | `ConsentToken` treated as a secret | It authorises mutations and submission of a claim |
| D4 | pydantic only in `adapters/` | Dependency rule; domain must be framework-free |
| D5 | Submit attempted once, ambiguity surfaced explicitly | Duplicate claims are a compliance incident, not a retry |
| D6 | Status enums carry `Unknown(raw)` | Vocabularies are undocumented; production must not crash on new values |
| D7 | Emergency / ePrescription / EMT out of v1 | NaCare's first need is outpatient + inpatient + preauth |
| D8 | Async-first; sync via `unasync` if ever | One source of truth |
