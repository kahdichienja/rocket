# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com), versioning: [SemVer](https://semver.org).

## [Unreleased]

## [0.1.16] — 2026-09-24

### Fixed
- `registries.find_patient()` raised instead of returning `None` when the Client Registry holds nobody with
  that document: UAT answers `400 "zero results found in client registry"` rather than 404. A genuine failure
  still raises, so a registry outage is never mistaken for an unknown patient.

## [0.1.15] — 2026-09-24

### Added
- `canonical_scheme()`, `scheme_family()`, `belongs_to_scheme()` — DHA spells a scheme two ways (`POMSF` in
  eligibility, `Public Officers Medical Scheme Fund` on the claim) and decides a visit's scheme itself. These
  fold both spellings and express the one split a caller can decide: `PMF-*` codes are POMSF, `SHA-*` codes are
  any general scheme (DHA picks UHC or SHIF).

## [0.1.14] — 2026-09-24

### Fixed
- **`dispense()` posted to a path that does not exist.** The portal documents `/prescriptions/dispenses`; UAT
  serves `/prescriptions/dispense` (singular) and 404s the plural.
- **`dispense()` sent an identification type UAT refuses.** That endpoint alone rejects `registration_number`
  for the dispenser ("is not a valid choice") and accepts `National ID`, unlike every other practitioner field.

### Docs
- WORKFLOWS §9.13: the ePrescription family on UAT — `POST /prescriptions` is blocked by three undocumented
  vocabularies (`generic_concept_code`, `dose_unit`, `patient_instruction`), `GET /prescriptions` answers 403
  for this client, and `dispense` works but needs a prescription first.

## [0.1.13] — 2026-09-23

### Fixed
- **`PatientId` rejected a valid Client Registry number.** Two formats are live on UAT at once:
  `CR7678914660684-5` and `CR-2026-000256`. The strict form made `Eligibility.patient_id` `None` for any
  member with the second, which also made `member_found` and `is_covered_on()` false — a fully covered member
  looked uncovered and could not be used for anything downstream.

### Added
- `registries` resource — the Client Registry: `find_patient()` (`GET /patients`: identity document in, CR
  number out) and `contacts()` / `can_consent_by_otp()` (`GET /patients/contacts`). An empty contact list is
  exactly why `send_otp` fails with "the contact record … contact id 0 doesn't exist"; now it can be checked
  before the attempt.
- `Eligibility.facility_contracts` — the scheme names the acting facility is contracted for, which SHA sends
  and the SDK was discarding; plus `contracted_schemes_on(day)` (active ∩ contracted) and `can_consent_by_otp`.

## [0.1.12] — 2026-09-23

### Fixed
- **Breaking:** `eligibility.utilization()` returns `tuple[UtilizationBalance, ...]`, not one object. UAT answers
  with a bare list — one record per limit scope — which raised `UnexpectedResponseError` the first time the
  endpoint returned data (it had 400'd upstream until now). A bare object and a `{pageSize, results}` page are
  still accepted.

### Docs
- WORKFLOWS §9.11: `/patients/benefits/utilization` shape; `/facilities/{code}/beds/occupancy` verified live.

## [0.1.11] — 2026-09-22

### Added
- `Authorization.proof` — an authorization returned by `authorize()` can be handed straight to `open_visit()`
  as the `auth_guid` branch of `/claims/visit`; `open_visit` also accepts the `Authorization` itself.
- `ClaimSession.remove_doctor()` — `DELETE /claims/doctors` under its general name (the endpoint is not
  emergency-only); `remove_emergency_doctor()` stays as an alias.

### Fixed
- `open_visit` with a proof that is not an `Otp`, `BiometricGuid` or `MatchId` silently sent a request the
  server always rejects ("one of otp, auth_guid or match_id is required"). It now raises
  `RequestValidationError` before anything is sent.

### Docs
- WORKFLOWS §9.10: an unverified biometric authorization cannot open a visit ("Kindly ensure the biometrics
  visit has been successfully verified"), and `/patients/sub-benefits` is facility-scoped.

## [0.1.10] — 2026-09-21

### Added
- `ClaimSession.set_coverage(principal, policy_number)` — `POST /authorizations/covers` (POMSF schemes; DHA
  billing process page "Set Coverage", absent from the eclaims portal).
- `add_line` / `NewClaimLine` take `service_name`, `service_identifier`, `practitioner` and `attachments`
  (`LineAttachment`) — DHA's "Add New Line" and "Add Combined Billing Details" in one multipart call, with the
  upload timeout when files are present.
- Exports: `CoverageSelection`, `LineAttachment`.

## [0.1.9] — 2026-09-21

### Added
- `ClaimIntervention.is_active` (ACTIVE on the visit; only retired ones can be restored).
- `ClaimSession.switch_intervention` refuses `retain_bill_items=True` without both `bill_from` and `bill_to`
  (DHA requires the previous intervention's billing period) — `RequestValidationError`, nothing sent.

### Docs
- Intervention rules from the DHA process pages on `add_intervention` / `retire_intervention` /
  `restore_intervention` / `switch_intervention` docstrings: combination rules (no IP/OP mixing), retire
  refused with bill items, a linked diagnosis or a per-diem intervention, switch needs the same access point
  and no elective pre-auth on the new code.

## [0.1.8] — 2026-09-21

### Changed
- `EmergencyCase` / `emergency.open_case()` now require `notes` (keyword-only): UAT rejects an emergency case
  with blank notes (`{"notes": ["This field may not be blank."]}`), so the SDK refuses before sending.

### Added
- `InterventionCoverage.is_emergency` — payable from the Emergency, Chronic and Critical Illness Fund
  (`fund` contains `ECCIF`); the only interventions `POST /claims/emergency` accepts.
- Error text now unwraps DRF-style field errors and list-valued upstream messages:
  `{"notes":["This field may not be blank."]}` → `notes: This field may not be blank.`

### Docs
- WORKFLOWS §9.7: emergency facts learned on UAT (notes mandatory, ECCIF interventions, facility accreditation).

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
