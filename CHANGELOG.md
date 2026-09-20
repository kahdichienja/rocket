# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com), versioning: [SemVer](https://semver.org).

## [Unreleased]

## [0.1.7] — 2026-09-20
### Changed
- `PatientId` now enforces the Client Registry shape (`CR` + 13 digits + `-` + check digit) on the request side. DHA accepts any string and creates authorizations against it (seen on UAT with HMIS-internal patient numbers). Response-side values that do not match map to `None` instead of raising.

## [0.1.6] — 2026-09-20
### Fixed
- `consent.list(patient)` now filters by beneficiary locally: DHA ignores `beneficiary_code` and returns the whole facility's authorizations (observed on UAT). Without this, clearing a patient's pending authorizations could have rejected another patient's.
### Added
- `AuthorizationStatus.AUTHORIZED_PENDING_VISIT` (observed).

## [0.1.5] — 2026-09-20
### Added
- Facility identification per DHA (`X-Facility-Id` + `X-Facility-Id-Type`): `facility_scope()` context manager,
  `activate_facility()` / `clear_facility()` for web-framework dependencies, `current_facility()`, and a static
  default via `SHASettings(facility=…)` / `SHA_FACILITY_ID`. Both headers or neither; per-context, so a shared
  client serves concurrent facilities safely.

## [0.1.4] — 2026-09-20
### Added
- `sha.auth.token()` → `BearerToken` (`as_dict()` mirrors `POST /tenants/token` exactly) for callers that must reach the HIE directly.

## [0.1.3] — 2026-09-20
### Added
- `sha.auth.identity()` / `sha.auth.check()` — credential health and the facility/tenant the token represents, without exposing the token.

## [0.1.2] — 2026-09-20

First public release. 49/49 published eClaims endpoints. Live-verified on DHA UAT through visit → diagnosis → line →
preview; `submit` verified up to the doctor-attachment rule (needs an HWR-registered practitioner). Pre-auth nested
request arrays remain unverified (docs/api/WORKFLOWS.md Q3). API is 0.x: expect breaking changes before 1.0.
### Added
- `consent.send_otp()` (`POST /claims/otp`), `consent.list(patient)`, `session.add_doctor()`; `submit()` takes `discharge_reason` + discharge `otp` (all required by UAT, none documented). `discharge()` now takes a tz-aware `discharged_at`.
- Wire models treat `null` as absent. `ClaimWorkflowState` / `AuthorizationStatus` populated from live observations.
- `on_event` hook on `AsyncSHAClient`: one `SDKEvent` per HTTP attempt (operation, status, duration, attempt, trace_id, redacted consent token, error). Emit-only.
- `VirtualClaim.submission_blockers()` — pure pre-submit check over the server's preview snapshot.
- `.github/workflows/live.yml` — scheduled UAT smoke run.
- `docs/GUIDE.md` — consumer guide: every method with parameters, wire call and result fields; recipes; gotchas; generated appendix.
- Project skeleton, quality gates (ruff, mypy strict, import-linter, pytest ≥ 90 % coverage), CI.
- Endpoint reference and workflow documentation generated from the DHA AfyaConnect portal, including the portal's example request/response JSON for every endpoint.
- `Invoice` (with `lines`) on `VirtualClaim`; typed `PayerClaimRecord` (`workflow_state`, `tracking_number`, `proposed_value`, …).
- `AsyncSHAClient` with OAuth2 client-credentials auth (cached, single-flight refresh, 401 replay), idempotent-only retries with jittered backoff, typed error translation (incl. `trace_id`).
- `sha.eligibility.check()` — `GET /patients/eligibility` mapped to an `Eligibility` read model; verified against DHA UAT.
- `sha.eligibility.benefits/sub_benefits/interventions()` — benefit hierarchy with tariffs and preauth flags; `InterventionCoverage.service_type_for_authorization` encodes the CAPITATION rule observed on UAT.
- `sha.consent.authorize/get/reject()` — two-step OTP consent (authorize sends the OTP); verified live incl. reject.
- `sha.claims.open_visit()` — opens the virtual claim with `Otp`, `BiometricGuid` or `MatchId` proof; returns `VirtualClaim` with a redacted `ConsentToken`.
- `ClaimSession` (from `sha.claims.open_visit()` or `sha.claims.resume(token)`): add/retire/restore interventions, add/remove diagnoses, add/remove/edit billing lines, attach/remove documents, `preview`, `submit` (attempted once; ambiguity → `SubmissionOutcomeUnknownError`), `close`, `payer_status`. 15 endpoints, contract-tested against the published spec.
- Pre-authorisation on `ClaimSession`: `request_preauth`, `preauths`, `remove_preauth_diagnosis`, `remove_preauth_doctor`, `cancel_preauth`, `request_doctor_consent`. Nested array encoding follows the API's own field vocabulary and is isolated in one function pending UAT confirmation.
- Inpatient discharge (`send_discharge_otp`, `discharge`), `add_next_of_kin`, `resubmit_lines` on `ClaimSession`.
- ePrescriptions on `ClaimSession`: `prescribe` (`MedicationOrder` items), `prescription`, `dispense` (`DispensedProduct`), `remove_prescription_doctor`. Request bodies asserted against the portal's published item shapes.
- Emergency: `sha.emergency.open_case()` (identified or unidentified casualty) → `ClaimSession`; `sha.emergency.protocols()`; on the session `add_protocol`, `add_emergency_doctor`, `remove_emergency_doctor`, `open_emt_claim`.
- `ClaimGateways` bundle: `ClaimSession` takes one gateway set instead of a growing argument list.
- `switch_intervention` on `ClaimSession`; `sha.eligibility.utilization / pomsf_balances / bed_occupancy`; `sha.files.upload / download_link`. All 49 published endpoints now have a request builder, guarded by a test.
- Error translation unwraps upstream JSON blobs in `error`, `details[]`, and trailing JSON in `message`.
- Domain value objects: identifiers (redacted `ConsentToken`), ICD/intervention codes, `Money`, documented enums, lenient server-status enums.
