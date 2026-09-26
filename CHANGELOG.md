# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com), versioning: [SemVer](https://semver.org).

## [Unreleased]

## [0.1.22] — 2026-09-26

### Added
- **Elective pre-authorisations are recognised**, on the preauth (`is_elective`) and on the authorization
  (`is_elective`, `elective_preauth`, and SHA's own `server_needs_preauth`), with a new `ElectivePreauth`
  carrying the earlier approval's status, type and service window.

  This is recognition, not a new capability, because **the API offers no way to raise one**. Across the 48
  endpoints DHA publishes there is no elective endpoint and no elective field on any request body; Postman
  has neither. `POST /preauths` requires a `consent_token`, which only `POST /claims/visit` issues, which
  only an authorised consent produces — so a pre-auth cannot exist before the patient has arrived. What
  makes one elective is that its service is dated later, and when the member returns, SHA reports the
  approval on the **new authorization** rather than anywhere a facility could look it up. That is the whole
  of the mechanism, and `elective_preauth` is where it now lands.

- `ElectivePreauth.is_approved` — substring-matched against SHA's several spellings of approval, and
  **anything unrecognised is not approved**. An elective approval is the one most likely to be assumed: it
  was granted days ago by someone who may be off today, and a theatre list built on a pre-auth SHA never
  granted is refused after the operation.

- `Preauthorization.countdown_label()` — reports SHA's `countdown` as a number and names it as SHA's.

### Notes
- **`countdown` has no published unit.** DHA sends a bare integer, the guides give it no description, and no
  Postman request produces one; the plain readings — days, hours, sessions — differ by orders of magnitude.
  Earlier planning for this work assumed seven days. That was an assumption, and an operating list would
  have been scheduled against it, so nothing here presents it as a deadline until UAT settles it.

### Fixed
- `Authorization.needs_preauth` now takes SHA's own top-level flag **or** any authorized intervention
  asking for one, instead of only the latter. An authorization can arrive with no interventions listed while
  SHA still wants a pre-auth; reading that as "none needed" bills a line SHA refuses.

## [0.1.21] — 2026-09-26

### Fixed
- **`POST /preauths` multipart was wrong in four places, and attachments were silently lost.** The builder
  was written against a portal reference that does not publish the inner schema of `items`, `diagnoses`,
  `doctors` or `attachments`, and carried an `UNVERIFIED` note saying so. Corrected against the published
  Postman collection:
  - an attachment entry names its own form part through **`file_field_name`**, and that part must exist —
    `attachments_0_file_blob`, not `attachment_0`. A file SHA cannot resolve is dropped without complaint,
    so every pre-auth was reviewed with no supporting documents.
  - the title field is **`document_title`**, not `title`;
  - each diagnosis repeats the **`consent_token`** beside its `icd_code`;
  - an item carries **`unit_price`** only;
  - a doctor carries the **`intervention_code`** they are attached to.

### Added
- **Intervention coverage now carries what SHA states about a pre-auth**, instead of dropping it into the
  untyped `extra` bag: `required_preauth_document_types`, `required_claim_documents`, `is_multisession`, and
  the five `requires*Preauth` flags behind a `preauth_kind` property. All of it arrives on the coverage
  lookup, **before a visit exists** — so a desk can be told which documents to gather while the service is
  still being chosen, and the specialised form is SHA's own answer rather than one inferred from the code
  family.
- **The five specialised pre-auth forms**, as a `details` object on `PreauthRequest`: `SurgicalDetails`,
  `RenalDetails`, `OncologyDetails`, `OpticalDetails`, `ImagingDetails`, with `NoDetails` for a normal one.
  One endpoint serves all six; only the clinical detail changes.
- `domain/preauth_vocabulary.py` — the closed choices in one file.

### Notes
- **DHA publishes these enums twice and the two copies disagree**: the prose guides say `General
  Anaesthesia`, `Stage 1`, `Once a month`, `Framed`; the Postman collection sends `GENERAL`, `STAGE_1`,
  `ONCE_A_MONTH`, `FRAMES_LENSES`. The guides also say `number_of_sessions` where Postman sends
  `number_of_sessions_required`. This release takes Postman's spelling — a runnable artifact beats prose —
  and records the alternative in `DOCS_SPELLINGS` so a UAT answer is a one-line correction.
- Optional booleans (`is_co_insured`, and the employment/accident questions on a surgical form) are omitted
  when unanswered rather than sent as `false`: on those two, a `false` nobody typed is a claim about
  liability.

## [0.1.20] — 2026-09-26

### Added
- **POMSF balances (`GET /patients/pomsf-balances`), parsed rather than raw:**
  - Added `PomsfBalance`, `PomsfPolicy`, `PomsfBenefit` and `PomsfFamilyMember` domain models.
  - Added `policy_year_for(day)` — POMSF policy years follow Kenya's financial year, which turns on 1 July.
    Asking for the wrong year returns another year's balance, which reads as a real answer.
  - `eligibility.pomsf_balances(...)` now returns a `PomsfBalance | None` and defaults `policy_year` to the
    year covering today. The previous raw payload is still available as `pomsf_balances_raw(...)`.

### Notes
- DHA publishes the `benefit` array of a member policy as a bare `[{}]`, so the amounts inside it are read
  by trying several plausible key spellings. Where none is present the SDK reports **`None`, never zero** —
  `PomsfBenefit.is_known`, `PomsfPolicy.remaining` and `PomsfBalance.remaining` all preserve that
  distinction, and `is_exhausted` is false for an unknown amount. A desk decides whether to open a visit on
  this figure, and a fabricated zero would turn away a covered patient.

### Changed
- **Breaking (internal):** `eligibility.pomsf_balances(...)` returns `PomsfBalance | None` instead of a raw
  mapping. `policy_year` is now optional.

## [0.1.19] — 2026-09-26

### Added
- **Biometric consent & eKYC integration (`POST /claims/authorize`):**
  - Added `BiometricContext` and `VerificationRequest` domain models (`request_url`, `embed_expiry`, `embeded_token`, `request_id`).
  - Added `consent.authorize_biometric(...)` on `AsyncSHAClient` supporting `agent_id`, `work_station_id`, `authorizing_device_os`, `ekyc_provider_id`, `provider`, and `factors: ["SHA"]`.
  - Added `Eligibility.consent_route()` method returning `ConsentRoute` (`OTP` | `BIOMETRIC`) based on payer flags (`facility_biometrics_enforced` and `whitelisted_for_otp`).
  - Wire authorization request mapping supporting optional biometric capture fields while preserving exact backwards compatibility with OTP authorizations.

## [0.1.18] — 2026-09-25

Documentation only — no code changes, so nothing to upgrade for.

### Docs
- **The consumer guide is now the README.** It was a pointer to `docs/GUIDE.md`; the guide now *is* the
  README, so the one document a consumer needs is the first thing they see on GitHub and on PyPI.
  `docs/GUIDE.md` remains as a stub with section links, and the `Documentation` project URL follows.
- Documented two resources that had never been written up: **`sha.auth`** (`identity()`, `check()`,
  `token()` — "which facility am I", without parsing a JWT) and **`sha.registries`** (§6.4 — the Client
  Registry, and `can_consent_by_otp()`, which answers before a failed authorize whether SHA can reach
  the member at all).
- WORKFLOWS §3.1: the `PER DIEM` mechanism, the four interventions carrying it, and why
  `intervention_overall_tariff` is `0.00` on all of them in UAT (a missing facility KEPH level, not the
  blanket zero-balance problem).
- WORKFLOWS §6.1: `patient_instruction` remains unanswerable from any published source — 36 candidates
  rejected, including every member of DHA's own `PRESCRIPTION-CONDITION-KENYA` value set, all 40
  administrative routes, free text and integer choices. The live portal page carries enumerations for 14
  other fields and none for this one. Recorded with the elimination table so it is not re-guessed.
- Corrected two errors in the guide: the `discharge()` recipe passed a `discharge_date` parameter that
  does not exist (it is `discharged_at`, defaulting to now), and `dispense()` was documented against the
  portal's `/prescriptions/dispenses`, which 404s — UAT serves the singular, as the SDK has sent since
  0.1.14.


## [0.1.17] — 2026-09-24

### Added
- **`PaymentMechanism.PER_DIEM` — SHA's bed rebate.** Critical care (`SHA-03-*`: ICU, HDU, NICU, burns) is
  paid by the day, not the item, and SHA accrues the stay itself. The mechanism is named nowhere in the
  portal spec and the fields that carry the accrual have empty descriptions, so this is modelled from
  observed UAT behaviour.
- `ClaimIntervention.is_per_diem`, `.accrued_per_diem_days`, `.accrued_per_diem`, `.keph_level_tariff`
  (SHA spells the wire field `kephLevelTarrif`), and `.per_diem_allowance` — what SHA will pay for the
  stay so far. It prefers SHA's own accrual, falls back to `keph_level_tariff × accrued_per_diem_days`,
  and returns **`None`, never zero**, when it knows neither: every per-diem intervention on UAT returns a
  `0.00` tariff because no rate is published for the facility's KEPH level, and a zero there would read as
  "SHA pays nothing" and push a covered stay onto the patient.
- `ClaimLine.rebate_amount`, `.sponsor_net`, `.patient_net`, `.benefit_exceeded` — how SHA splits a line
  between sponsor and patient. Computed by SHA and returned only; populated on lines read back from
  `preview()`, not on the line `add_line()` returns. The wire still calls the first `nhifRebateAmount`.

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
