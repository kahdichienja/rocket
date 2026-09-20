# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com), versioning: [SemVer](https://semver.org).

## [Unreleased]
### Added
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
