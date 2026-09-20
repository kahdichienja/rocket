# HMIS/SHA Integration Requirements — Assessment of `sha-claim`

*Assessed 2026-09-20 against the ten DHA HMIS/SHA integration requirements.*

`sha-claim` is a **stateless SDK**: it turns HMIS intent into correct HIE calls and typed results. It
does not store anything, has no UI and trains nobody. Several requirements are therefore split into
**SDK** (this package), **HMIS** (NaCare, the consumer) and **Gap** (nobody has it yet). Every "Gap"
row has an owner and a concrete action.

Legend: ✅ covered · 🟡 partial · 🔲 HMIS responsibility · ❌ gap

---

## 1. Uniform interpretation and implementation of the SHA benefits matrix and access rules

| | Status | Evidence |
|---|---|---|
| Benefits matrix is fetched live from SHA, never copied locally | ✅ | `sha.eligibility.benefits / sub_benefits / interventions` → `BenefitPackage`, `SubBenefit`, `InterventionCoverage` (tariffs, `needs_preauth`, `needs_doctor_authorization`, `payment_mechanism`, `applicable_schemes`, `access_point`) |
| Access rules that the docs omit are encoded once | ✅ | `InterventionCoverage.service_type_for_authorization` (CAPITATION interventions must be authorised as CAPITATION — observed on UAT, not documented) |
| Coverage decision is a function of SHA data, not local config | ✅ | `Eligibility.is_covered_on(date)` from scheme coverage + policy periods |
| Pre-auth requirement surfaced on the claim itself | ✅ | `ClaimIntervention.preauth_outstanding`, `VirtualClaim.preauth_outstanding` |
| Utilisation limits | 🟡 | `sha.eligibility.utilization()` implemented; endpoint returns an upstream 400 on UAT (Sept 2026) |
| **Enforcement** before submit | ✅ | `VirtualClaim.submission_blockers()` — pure check over the server's preview snapshot (pre-auth outstanding, no lines, zero/negative total, missing diagnosis, missing required documents) |

## 2. Capture of the complete patient journey

| | Status | Evidence |
|---|---|---|
| Every journey step has a typed operation | ✅ | eligibility → consent → visit → interventions/diagnoses/lines/attachments → (preauth, prescriptions, discharge, next-of-kin) → preview → submit → payer status; emergency & EMT variants. 49/49 endpoints |
| Every server response is preserved, including fields not yet modelled | ✅ | `.extra` on every result object |
| Journey **persistence** (visit timeline, snapshots, who did what) | 🔲 HMIS | The SDK returns snapshots; NaCare must store `consent_token.value`, claim GUID, and each `VirtualClaim` snapshot |
| A structured event stream the HMIS can persist as an audit trail | ✅ | `AsyncSHAClient(on_event=…)` → `SDKEvent` per HTTP attempt (operation, status, duration, attempt, `trace_id`, redacted token, error). Emit-only; the SDK stores nothing |

## 3. Consistent claims generation, validation and submission

| | Status | Evidence |
|---|---|---|
| Request-level validation before any network call | ✅ | value objects (`Icd11Code`, `Money`, `InterventionCode`…) and commands (`NewClaimLine`, `PreauthRequest`, `MedicationOrder`…) raise on invalid input; `RequestValidationError` lists every violation |
| Server-side validation surfaced as typed, readable errors | ✅ | uniform `{error, message, trace_id}` envelope → `BadRequestError` etc.; nested JSON unwrapped |
| Preview before submit | ✅ | `session.preview()` returns the server's view of the claim |
| Submit exactly once; no duplicate claims from retries | ✅ | `SubmitClaim` attempt-once; `SubmissionOutcomeUnknownError` forces a `preview` before any retry |
| Request shapes pinned to the published spec | ✅ | `test_spec_drift.py` (49 rows) + `test_portal_examples.py` (schemas vs portal examples) |
| Completeness rules before submit (≥1 line, diagnosis per intervention, required documents present) | ✅ | `submission_blockers()` |

## 4. Interoperability and effective integration with the HIE

| | Status | Evidence |
|---|---|---|
| Full API surface | ✅ | 49/49 published endpoints; guard test fails if DHA adds one |
| Auth | ✅ | OAuth2 client-credentials, cached, single-flight refresh, 401 replay — live-verified |
| Resilience | ✅ | per-request timeouts, jittered retries on reads only, transient-status detection |
| Correlation | ✅ | server `trace_id` / `x-request-id` attached to every error and log line |
| Wire quirks handled | ✅ | camelCase/snake_case mix, multipart-without-file, JSON-in-form-field vs comma-separated diagnoses, list-vs-object responses |
| **Live verification of the claim lifecycle** | ❌ Gap → DHA/NaCare | 9 endpoints live-verified; 40 contract-tested only. Blocked on a UAT beneficiary whose OTP NaCare can receive (WORKFLOWS Q11) |

## 5. Identify and address gaps before certification

| | Status | Evidence |
|---|---|---|
| Documented discrepancies between DHA docs and UAT behaviour | ✅ | `docs/api/WORKFLOWS.md` §9 (10 findings: OTP is optional on authorize, CAPITATION service type, `trace_id`, bed-occupancy needs auth, list-shaped responses, utilization bug…) |
| Open-question register with owners | ✅ | `PLAN.md` Open Questions (Q3 preauth nested schema, Q4 status vocabularies, Q5 submit idempotency, Q6 production URL/limits, Q11 test beneficiary) |
| Unverified assumptions marked in code | ✅ | `requests.create_preauth` docstring; guide §9.7 |
| Gap resolution path | 🟡 | Needs DHA engagement for Q3/Q4/Q5/Q6/Q11 — see "Asks of DHA" below |

## 6. User capacity and error reduction

| | Status | Evidence |
|---|---|---|
| Developer documentation | ✅ | `docs/GUIDE.md` (every method: params, wire call, result), `docs/ARCHITECTURE.md`, `docs/api/*` reference with examples, Postman collection |
| Errors are actionable | ✅ | human message + `trace_id`; local violations name the field |
| API designed to prevent misuse | ✅ | redacted `ConsentToken`/`Otp`, `Money` refuses floats, strict request enums, `service_type_for_authorization` |
| End-user (clinician/biller) training and UI guidance | 🔲 HMIS | Out of SDK scope |

## 7. Minimum technical, functional and operational requirements

| | Status | Evidence |
|---|---|---|
| Typed, tested, layered | ✅ | mypy `--strict`, import-linter contracts, 245 tests / 95 % coverage, CI on 3.11–3.13 |
| Config from environment, fail-fast, secrets never in code | ✅ | `SHASettings.from_env()`; `.env` git-ignored; token & PII redaction in logs |
| Timeouts / retries / idempotency semantics defined per call | ✅ | `docs/ARCHITECTURE.md` §8 |
| Packaging | ✅ | wheel + sdist build, `twine check`, clean-venv install, `py.typed`, 2 runtime deps |
| Operational metrics (RED signals per operation) | ✅ / 🔲 | `on_event` provides rate/errors/duration per operation; NaCare exports them |
| Nightly live smoke against UAT in CI | ✅ (needs secrets) | `.github/workflows/live.yml` — weekday cron + manual; add `SHA_CLIENT_ID/SECRET` as repository secrets |
| Production base URL / rate limits | ❌ Gap → DHA | Q6 |

## 8. End-to-end visibility for case management, monitoring, fraud risk, surveillance

| | Status | Evidence |
|---|---|---|
| Read-back of every artefact | ✅ | `consent.get`, `session.preview`, `session.preauths`, `session.prescription`, `session.payer_status` |
| Payer-side view of a submitted claim | ✅ | `PayerClaimRecord` (`workflow_state`, `tracking_number`, `proposed_value`…) |
| Fraud-relevant controls in the SDK | ✅ | consent token treated as a credential; OTP never logged; submit-once; no local tariff table to tamper with |
| Dashboards, alerts, case-management workflow | 🔲 HMIS | Built on persisted snapshots + the event stream |
| Event stream to feed them | ✅ | `on_event` hook |

## 9. Tracking authorizations, pre-auths, submitted/unsubmitted claims, notifications

| Artefact | Status | How |
|---|---|---|
| Authorizations | ✅ | `consent.authorize` returns `guid/token`; `consent.get` re-reads; `consent.reject` closes |
| Pre-authorizations | ✅ | `session.request_preauth` → `preauths()` list with `status`, `doctor_review_status`, amounts |
| Unsubmitted claims | ✅ | `sha.claims.resume(token).preview()` — `workflow_state` shows the open claim |
| Submitted claims | ✅ | `submit` result + `payer_status()` |
| Claim **notifications** | 🟡 | The HIE API has **no push/webhook**; pre-auth updates go to `provider_notification_email`. Tracking is poll-based (`payer_status`, `preauths`) — HMIS schedules the polling |
| Cross-referencing key | ✅ | `consent_token` ↔ `ClaimGuid` ↔ `InvoiceNumber` all typed and available on `VirtualClaim` |

## 10. Timely identification and resolution of system/workflow gaps

| | Status | Evidence |
|---|---|---|
| Contract drift detected automatically | ✅ | spec-drift + portal-example tests; 49/49 guard |
| Forward-compatible parsing | ✅ | lenient status enums, `extra` for unknown fields, tolerant date/number parsing |
| Every failure carries the server's `trace_id` | ✅ | for DHA support tickets |
| Change log | ✅ | `CHANGELOG.md` |
| Nightly live regression | ✅ (needs secrets) | `live.yml` |

---

## Summary

| Req | SDK | HMIS | Gap |
|---|---|---|---|
| 1 Benefits matrix | ✅ | — | — |
| 2 Patient journey | ✅ | persistence (via `on_event` + snapshots) | — |
| 3 Validation & submission | ✅ | — | — |
| 4 HIE interoperability | ✅ | — | live run of claim lifecycle (Q11) |
| 5 Gap identification | ✅ | — | DHA answers to Q3–Q6, Q11 |
| 6 User capacity | ✅ docs | training/UI | — |
| 7 Tech/ops minimums | ✅ | metrics export, CI secrets | prod URL (DHA) |
| 8 Visibility | ✅ reads + events | dashboards | — |
| 9 Tracking | ✅ | polling schedule | none in API for push |
| 10 Gap resolution | ✅ | add CI secrets | — |

### SDK work items

All three closed 2026-09-20: `on_event` hook, `VirtualClaim.submission_blockers()`, `live.yml`. The SDK remains
stateless by design — persistence, polling schedules and dashboards are the consumer's.

### NaCare work items

- Persist `consent_token.value`, claim GUID, invoice number and each snapshot per visit; persist `SDKEvent`s from `on_event` as the audit trail.
- Add `SHA_CLIENT_ID` / `SHA_CLIENT_SECRET` as GitHub repository secrets so `live.yml` runs.
- Schedule polling of `payer_status()` and `preauths()`; surface `workflow_state` changes to billers.
- Export RED metrics from the event stream; alert on `TransportError`/`AuthenticationError` rates.
- Biller UI: show `submission_blockers()` before enabling Submit; show `trace_id` on every failure.
- Training material for the OTP consent flow and pre-auth workflow.

### Asks of DHA

| Q | Ask |
|---|---|
| Q11 | A UAT beneficiary bound to a phone NaCare controls, or a static sandbox OTP |
| Q3 | Inner schema of `POST /preauths` `items / diagnoses / doctors / attachments` |
| Q4 | Vocabulary of `workflow_state`, `claim_auth_status`, authorization `status`, preauth `status` |
| Q5 | Is `POST /claims/submit` idempotent per `consent_token`? |
| Q6 | Production base URL, token TTL, rate limits |
| — | Confirm CAPITATION on `/claims/authorize` is intended (undocumented) |
