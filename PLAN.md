# sha-claim — Delivery Plan

Python SDK for submitting and tracking **Social Health Authority (SHA, Kenya)** claims
through the Digital Health Agency's **AfyaConnect HIE eClaims API**. Built for NaCare HMP,
published to PyPI so other facilities/HMIS vendors can use it.

- Roadmap: this file
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- API reference (all 49 endpoints, generated from the official portal): [docs/api/README.md](docs/api/README.md)
- How the endpoints chain into claim workflows: [docs/api/WORKFLOWS.md](docs/api/WORKFLOWS.md)

**Status 2026-09-20:** docs captured, architecture revised (not FHIR; server-owned virtual claim keyed by `consent_token`).
**Phase 0 done. Vertical slice live:** auth → eligibility → domain, proven against DHA UAT (`make live`). All gates green
(ruff, mypy --strict, import-linter, pytest 96 % coverage). Next: consent + virtual claim (Phase 1–3 for those groups).

---

## Scope

**In scope (v1)**

- OAuth2 client-credentials auth (`POST /tenants/token`): cache, skew, single-flight refresh.
- Eligibility, benefits, intervention coverage, utilization balances.
- Consent capture (OTP / biometrics) and virtual-claim opening (`/claims/visit`).
- Building the server-side claim: interventions, diagnoses, lines, attachments (+ removals).
- Preview, submit, close; inpatient discharge (OTP + discharge); payer-side status.
- Pre-authorization create/get/cancel + doctor-consent request.
- File upload / download URL.
- Typed errors from the uniform `{error, message}` envelope, bounded retries, structured logs, correlation IDs.
- Async-first client; sync facade is a v1.x follow-up.

**Out of scope (v1)**

- Persistence of claims or consent tokens (the SDK is stateless; NaCare owns storage).
- Emergency / EMT claims, ePrescriptions & dispensing, POMSF balances, bed occupancy (v2 — ports exist, adapters don't).
- Remittance / payment reconciliation (not exposed by this API).
- CLI, web UI, Django/FastAPI integrations (separate packages if ever).

---

## Phases

Each phase ends green: `ruff check . && mypy src && pytest` with coverage ≥ 90 %.
No phase starts coding until its domain vocabulary is confirmed against the official docs.

### Phase 0 — Foundations  `[x]`
- [x] `pyproject.toml` (hatchling, `src/` layout, py ≥ 3.11, `py.typed`)
- [x] Tooling: ruff, mypy `--strict`, pytest + pytest-asyncio + respx, pre-commit, coverage gate
- [x] CI (GitHub Actions): lint → type-check → test matrix (3.11, 3.12, 3.13) → build → `twine check`
- [x] Package skeleton per ARCHITECTURE.md §3 with empty `__init__.py` and the error hierarchy
- [x] `SHASettings` (env-driven, fail-fast validation)
- [x] `CHANGELOG.md`, `LICENSE`, `README.md` quick-start stub
- [x] Remove placeholder `t.txt`

### Phase 1 — Domain  `[ ]`  *(pure Python, zero I/O, zero third-party imports)*
- [x] Identifiers: `ConsentToken` (redacted repr), `PatientId`, `FacilityCode`, `PractitionerRef`, `ClaimGuid`, `LineGuid`, `FileId`
- [x] Codes & enums: `Icd11Code`, `InterventionCode`, `SchemeCode`, `DocumentType`, `RegulationBody`, `ServiceType`,
      `CancelReason`, `DischargeReason`, `IdentificationType`, `NextOfKinIdType` (values from WORKFLOWS §8)
- [x] `Money` (Decimal, KES) with quantisation policy
- [~] Read models: `Eligibility` ✔, `Authorization` ✔ (minimal), `VirtualClaim`, `Preauthorization` — derived behaviour only
- [x] `LenientStrEnum` with unknown-value fallback (`EligibilityStatus`, `CoverageStatus`; more as observed) (`WorkflowState`, `AuthorizationStatus`, `PreauthStatus`)
- [~] Request validation lives in value-object/command `__post_init__` and use cases (decision: no separate policy module until a cross-field rule needs one)
- [x] Property-based tests (hypothesis) for Money; table tests for VOs

### Phase 2 — Ports & Use Cases  `[ ]`
- [~] Ports (`typing.Protocol`, split by consumer): `EligibilityGateway` ✔, `TokenProvider` ✔, `Clock` ✔; `ConsentGateway`, `VirtualClaimGateway`,
      `PreauthGateway`, `FileGateway` pending
- [~] Use cases: `VerifyEligibility` ✔, `CaptureConsent`, `OpenVisit`, `Add/Remove{Intervention,Diagnosis,Line,Attachment}`,
      `PreviewClaim`, `SubmitClaim` (attempt-once + `SubmissionOutcomeUnknownError`), `CloseClaim`, `DischargeInpatient`,
      `TrackPayerClaim`, `RequestPreauthorization`
- [ ] Tests with in-memory fakes for every port — no HTTP, no mocks of domain objects

### Phase 3 — Wire Adapters  `[ ]`
- [~] Pydantic v2 schemas per resource group (eligibility ✔, `ErrorEnvelope` ✔); alias generator for the `camelCase` (authorization/preauth) vs
      `snake_case` (claims) split; `ErrorEnvelope`
- [ ] `requests.py`: domain → request spec (method, path, json | form | multipart). One module (`multipart.py`)
      owns the "JSON-array-in-a-form-field" encoding quirk
- [~] Mappers wire → domain (eligibility ✔); `error_translator.py` ✔ (incl. undocumented `trace_id`)
- [x] **Spec drift test**: every request spec's method+path+required fields asserted against `docs/api/spec/*.json`
- [~] Contract tests against recorded UAT fixtures (eligibility ✔)

### Phase 4 — Infrastructure  `[ ]`
- [x] `HttpxTransport` (async; per-request timeout; `x-request-id` captured; 401 refresh-and-replay)
- [x] `OAuth2ClientCredentials` (`POST /tenants/token`, form-urlencoded) with expiry-aware cache and single-flight refresh
- [x] `RetryPolicy`: exponential backoff + jitter on idempotent calls (GETs, `/claims/preview`) and transient failures only;
      `submit` is attempted once (ARCHITECTURE §8)
- [x] Structured logging at boundaries with redaction (bearer, consent_token, OTP, IDs, phones); optional `on_event` hook
- [x] Contract tests with `respx`; `live` marker for UAT smoke tests (off by default)

### Phase 5 — Composition & Public API  `[ ]`
- [~] `AsyncSHAClient` facade (`eligibility` ✔, `consent`, `claims`, `preauths`, `files`) + `ClaimSession`; composition root
- [ ] `sha_claim.__all__` frozen; docstrings on every public symbol
- [ ] README: install, 20-line happy path, error handling, configuration table
- [ ] End-to-end examples against UAT: `examples/outpatient_claim.py`, `examples/inpatient_discharge.py`, `examples/preauth.py`

### Phase 6 — Release  `[ ]`
- [ ] `0.1.0` to TestPyPI → PyPI via trusted publishing (no long-lived tokens)
- [ ] Integrate into NaCare (`Nacare/backend` or a new `Nacare/claims` module) and
      feed real-world friction back as issues before `1.0.0`

---

## Open Questions

Resolved by the docs (2026-09-20): wire format = custom REST (JSON + multipart), **not FHIR**; auth =
OAuth2 client-credentials, form-urlencoded, `Bearer`; claim status = pull (`GET /claims/preview/payer`);
attachments = multipart inline (`/claims/attachments`) or `/uploads`; UAT base = `https://ilm-dev.dha.go.ke/uat-middleware`;
code systems = ICD (`icd_code`), SHA intervention codes, facility "FR code", practitioner registration number + regulation body.

Still open — detailed in [docs/api/WORKFLOWS.md §9](docs/api/WORKFLOWS.md#9-open-questions-the-portal-does-not-answer):

| # | Question | Blocks |
|---|----------|--------|
| Q1 | ~~How is the visit OTP triggered?~~ → `POST /claims/authorize` is the consent entry point (answered 2026-09-20). **Remaining:** is OTP delivery triggered *by* that call or before it? Confirm on UAT. | one-call vs two-step `CaptureConsent` |
| Q2 | Field name for the biometric authorization GUID on `/claims/visit` | `OpenVisit` request schema |
| Q3 | Inner schema of all `object[]` fields (preauth items/doctors/…, claim lines/invoices) | typed models vs `dict` passthrough in Phase 3 |
| Q4 | Status vocabularies (`workflow_state`, `claim_auth_status`, preauth `status`, …) | enum values (fallback `Unknown` ships regardless) |
| Q5 | Is `POST /claims/submit` idempotent per `consent_token`? | whether submit may ever be retried |
| Q6 | Production base URL, token TTL, rate limits | settings, backoff tuning |
| Q7 | ~~identification_type codes~~ answered: literal `National ID` etc. (WORKFLOWS §9) | — |
| Q8 | Encoding of "JSON array" form fields (`diagnoses`, `attachments`, `interventions`) | `multipart.py` |
| Q9 | Does NaCare need a **sync** client? | whether to ship `SHAClient` (sync) in v1 |
| Q10 | ~~UAT credentials~~ received 2026-09-20; stored in git-ignored `.env` | — |

Next sources: `https://hie-docs.dha.go.ke/` and the Postman collection `https://documenter.getpostman.com/view/39260559/2sB3dSPoWf`.

## Definition of Done (per feature)

1. Domain rule has exactly one home and a unit test.
2. Boundary code has a contract test against a recorded fixture.
3. Public symbol has a docstring and appears in README or API reference.
4. `ruff`, `mypy --strict`, `pytest --cov` all green in CI.
5. CHANGELOG entry written.
