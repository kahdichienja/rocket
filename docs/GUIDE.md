# sha-claim — Consumer Guide

*For a developer who has never touched SHA, the DHA API or this SDK.* Read §1–§4 once; the rest is
reference you come back to.

**Contents**

1. [What you are talking to](#1-what-you-are-talking-to)
2. [Install and configure](#2-install-and-configure)
3. [The client](#3-the-client)
4. [Errors](#4-errors)
5. [The types you pass around](#5-the-types-you-pass-around)
6. [`sha.eligibility` — who is covered, for what](#6-shaeligibility)
7. [`sha.consent` — patient consent (OTP)](#7-shaconsent)
8. [`sha.claims` — opening and resuming a claim](#8-shaclaims)
9. [`ClaimSession` — everything you do to one claim](#9-claimsession)
10. [`sha.emergency` — emergency cases](#10-shaemergency)
11. [`sha.files` — standalone uploads](#11-shafiles)
12. [End-to-end recipes](#12-end-to-end-recipes)
13. [Testing code that uses the SDK](#13-testing-code-that-uses-the-sdk)
14. [Gotchas](#14-gotchas)
15. [Appendix — every result object, field by field](#15-appendix--result-objects)

---

## 1. What you are talking to

**SHA** (Social Health Authority) is Kenya's public health insurer. Facilities get paid by submitting
**claims** to SHA through the Digital Health Agency's **AfyaConnect HIE eClaims API**. This SDK is a
typed Python wrapper around that API.

Four ideas explain almost everything:

| Idea | What it means for you |
|---|---|
| **The claim lives on the server.** | You don't build a claim locally and post it. You *open* one on the server, then add things to it call by call, then *submit* it. |
| **`consent_token` is the handle.** | Opening a claim returns a token. Every later call about that claim needs it. The SDK hides this inside a `ClaimSession` object. Treat the token like a password: it lets anyone bill against that patient's visit. |
| **Consent is a two-step OTP dance.** | `authorize` sends the patient an SMS code; `open_visit` consumes it. Without the code, no claim. |
| **Interventions are the unit of everything.** | An intervention code (e.g. `SHA-12-001` Consultation) is what you authorise, bill against, attach documents to, and pre-authorise. |

Two environments exist: **UAT** (`https://ilm-dev.dha.go.ke/uat-middleware`, test data) and
**production** (URL supplied by DHA at onboarding). Your credentials decide which facility you are:
the facility code is embedded in the access token, so you never pass it.

---

## 2. Install and configure

```bash
pip install sha-claim
```

Requires Python 3.11+. Runtime dependencies: `httpx`, `pydantic` — nothing else.

Configuration is read from environment variables:

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `SHA_CLIENT_ID` | yes | — | OAuth2 client id from DHA onboarding |
| `SHA_CLIENT_SECRET` | yes | — | OAuth2 client secret |
| `SHA_ENVIRONMENT` | no | `uat` | `uat` or `production` |
| `SHA_BASE_URL` | production only | UAT URL | Override the base URL (no trailing `/api/v1`) |
| `SHA_CONNECT_TIMEOUT` | no | `5` | seconds |
| `SHA_READ_TIMEOUT` | no | `30` | seconds |
| `SHA_UPLOAD_TIMEOUT` | no | `120` | seconds, for multipart uploads |
| `SHA_FACILITY_ID` | no | — | static `X-Facility-Id` for single-facility deployments (see *Facility scoping* in §3) |
| `SHA_FACILITY_ID_TYPE` | no | `fr-code` | `X-Facility-Id-Type` |

Missing or invalid settings raise `ConfigurationError` **when you create the client**, not later.

If you prefer code over env vars:

```python
from sha_claim import SHASettings, Environment, Timeouts

settings = SHASettings(
    client_id="…",
    client_secret="…",
    base_url="https://ilm-dev.dha.go.ke/uat-middleware",
    environment=Environment.UAT,
    timeouts=Timeouts(connect=5, read=30, upload=120),
)
```

---

## 3. The client

Everything starts from `AsyncSHAClient`. It is **async**: every call is `await`ed and you run it
inside an event loop (`asyncio.run(...)`, or your FastAPI/Django-async handler).

```python
import asyncio
from sha_claim import AsyncSHAClient, IdentificationType


async def main() -> None:
    async with AsyncSHAClient.from_env() as sha:  # reads SHA_* env vars
        e = await sha.eligibility.check("12345678", IdentificationType.NATIONAL_ID)
        print(e.full_name, e.member_found)


asyncio.run(main())
```

`async with … as sha:` opens the HTTP connection pool and closes it at the end. Reuse one client
for many calls; don't create one per request. Tokens are fetched on first use, cached, and refreshed
automatically (single-flight: 100 concurrent callers trigger one refresh).

The client exposes five **resources**:

| Attribute | What it's for | Section |
|---|---|---|
| `sha.eligibility` | Is this person covered? For which benefits/interventions? Balances. | §6 |
| `sha.consent` | Send the OTP; inspect/reject an authorization | §7 |
| `sha.claims` | Open a claim (→ `ClaimSession`) or resume one from a saved token | §8 |
| `sha.emergency` | Open an emergency case (→ `ClaimSession`); list treatment protocols | §10 |
| `sha.files` | Upload a file / get a download URL | §11 |

Constructor options, all optional (used mainly in tests):

```python
AsyncSHAClient(settings, transport=…, tokens=…, clock=…, retry=RetryPolicy(max_attempts=3), http=httpx.AsyncClient())
```

**Observability.** Pass `on_event=` a callable and the SDK calls it once per HTTP attempt with an
`SDKEvent` — `operation`, `status`, `duration_ms`, `attempt`, `trace_id`, redacted `consent_token`,
`error`. The SDK **stores nothing**; your callback is where audit logging, metrics and alerting live.
A hook that raises is logged and ignored — it can never break a claim call.

```python
def audit(e: SDKEvent) -> None:
    db.insert(
        "sha_events",
        operation=e.operation,
        status=e.status,
        trace_id=e.trace_id,
        duration_ms=e.duration_ms,
        token=e.consent_token,
        at=e.occurred_at,
    )
    if not e.ok:
        metrics.increment("sha.errors", tags={"op": e.operation, "status": e.status})


async with AsyncSHAClient.from_env(on_event=audit) as sha:
    ...
```

**Facility scoping.** DHA scopes claims/preauth/patient calls to one facility
([docs](https://hie-docs.dha.go.ke/docs/authentication/process/facility-identification)). A facility-specific
credential needs nothing: its token carries `facility_id`. A multi-facility integration sends
`X-Facility-Id` + `X-Facility-Id-Type` on every request; the SDK does that for you:

```python
with facility_scope("FID-47-115307-8"):            # everything inside is scoped; safe under concurrency
    await sha.eligibility.check(...)
# or, in a per-request web dependency: activate_facility(code) … clear_facility()
# or, one facility for the whole process: SHA_FACILITY_ID=FID-… / SHASettings(facility=...)
```
Headers override the token claim. The SDK never sends one header without the other.

**Retries.** Reads (`GET`, and `preview`) are retried up to 3 times with jittered backoff on
network errors and 408/429/502/503/504. Writes are **never** retried automatically. A `401` triggers
one token refresh and one replay.

---

## 4. Errors

Every exception the SDK raises is a subclass of `sha_claim.SHAClaimError`. Catch that if you don't
care which; catch specific ones when you do.

| Exception | When | Useful attributes |
|---|---|---|
| `ConfigurationError` | bad/missing settings | — |
| `RequestValidationError` | the SDK refused to send because the request is certainly wrong (empty list, negative price, bad ICD format…) | `.violations` → list of `Violation(field, message)` |
| `BadRequestError` | server said 400 — usually a business rule ("intervention X not supported for OUTPATIENT") | `.status`, `.error`, `.trace_id` |
| `AuthenticationError` | token could not be obtained, or 401 even after a refresh | `.trace_id` |
| `PermissionDeniedError` | 403 | `.trace_id` |
| `NotFoundError` | 404 | `.trace_id` |
| `ServerError` | any other 4xx | `.status`, `.trace_id` |
| `RateLimitedError` | 429 | `.retry_after` (seconds, may be `None`) |
| `TransportError` | network failure / timeout / 5xx after retries | `.trace_id` |
| `SubmissionOutcomeUnknownError` | `submit` was sent but we never got an answer — **see §9 lifecycle** | `.trace_id` |
| `UnexpectedResponseError` | the server answered with a shape we don't understand | — |

`trace_id` is the server's own correlation id. **Quote it when you raise a ticket with DHA.**

```python
from sha_claim import BadRequestError, RequestValidationError, SHAClaimError

try:
    auth = await sha.consent.authorize(patient, ServiceType.OUTPATIENT, ["SHA-12-001"])
except RequestValidationError as e:  # nothing was sent
    for v in e.violations:
        print(v.field, v.message)
except BadRequestError as e:  # server refused
    log.warning("SHA rejected: %s (trace %s)", e, e.trace_id)
except SHAClaimError:  # anything else from the SDK
    raise
```

Server messages are unwrapped for you: the API sometimes nests JSON inside strings
(`{"error":"{\"error\":\"Kindly note…\"}"}`); `str(exc)` gives you the human sentence.

---

## 5. The types you pass around

The SDK uses small typed values instead of bare strings so mistakes fail early and loudly.
**Almost every method also accepts a plain `str`** and converts it for you — the types below are
what you get *back*, and what you use when you want the validation up front.

### Identifiers

| Type | What it is | Notes |
|---|---|---|
| `PatientId` | the beneficiary's **CR number** (e.g. `CR7678914660684-5`) | comes from `eligibility.check(...).patient_id`; this is `patient_id` everywhere in the API |
| `ConsentToken` | the claim handle returned by `open_visit` | `repr`/`str` are **redacted** (`CR76…G6`); use `.value` when you must persist it |
| `ClaimGuid`, `LineGuid`, `AttachmentId`, `FileId`, `InvoiceNumber`, `FacilityCode` | server ids / your invoice number | non-empty, whitespace-trimmed |

All raise `ValueError` if empty.

### Codes

| Type | Format | Example |
|---|---|---|
| `InterventionCode` | SHA intervention, upper-cased for you | `InterventionCode("sha-12-001")` → `SHA-12-001` |
| `Icd11Code` | ICD-11 / ICD-10 stem, upper-cased, validated | `"1A00"`, `"BA00.1"`, `"J18.9"` ok; `"malaria"` → `ValueError` |
| `SchemeCode`, `ProtocolCode` | as given by SHA | `"UHC"`, `"EP-1"` |

### Money

```python
from sha_claim import Money

Money.kes("1500")  # KES 1,500.00
Money.kes("1500.505")  # → 1500.51 (half-up to cents)
Money.kes(1500) * 2  # KES 3,000.00
Money(1500.0)  # TypeError — floats are refused on purpose; pass str/int/Decimal
```

### Consent proof

`Otp("123456")` (digits only, redacted in repr), `BiometricGuid("…")`, `MatchId("…")`.
`open_visit` accepts any of the three as `proof`.

### Practitioners

```python
from sha_claim import PractitionerRef, RegulationBody, IdentificationType

PractitionerRef.registered("A1234", RegulationBody.KMPDC)  # by registration number (usual)
PractitionerRef("12345678", IdentificationType.NATIONAL_ID, RegulationBody.NCK)  # by national ID
```
`RegulationBody`: `KMPDC` (doctors), `COC` (clinical officers), `NCK` (nurses).

### Attachments

```python
from sha_claim import Attachment, DocumentType

Attachment.from_path("discharge.pdf", DocumentType.DISCHARGE_SUMMARY)  # reads the file, guesses content type
Attachment("inv.pdf", pdf_bytes, DocumentType.INVOICE, "application/pdf")
```
Empty content or > 10 MB → `ValueError`. `DocumentType` has 31 values (`INVOICE`, `LAB_RESULTS`,
`DISCHARGE_SUMMARY`, `PREAUTH_FORM`, `PRESCRIPTION`, `CT_SCAN`, … see appendix).

### Enums you will pass

| Enum | Values |
|---|---|
| `ServiceType` | `CAPITATION`, `OUTPATIENT`, `INPATIENT`, `EMERGENCY` |
| `IdentificationType` | `NATIONAL_ID` ("National ID"), `ALIEN_ID`, `REFUGEE_ID`, `REGISTRATION_NUMBER` (practitioners only) |
| `CancelReason` | `WRONG_PATIENT`, `NO_SERVICE_GIVEN`, `WRONG_BENEFIT`, `EXPIRED_VISIT`, `EXHAUSTED_BENEFIT`, `TIME_BARRED`, `OTHER_REASONS` |
| `DischargeReason` | `RECOVERED`, `REFERRED`, `DECEASED`, `ABSCONDED`, `OTHER` |
| `NextOfKinIdType` | `NATIONAL_ID`, `CLIENT_REGISTRY_ID`, `BIRTH_NOTIFICATION`, `BIRTH_CERTIFICATE`, `ALIEN_ID`, `REFUGEE_ID`, `MANDATE_NUMBER`, `TEMPORARY_ID` |
| `BroughtBy` | `RELATIVE`, `UNKNOWN`, `SAMARITAN`, `PARAMEDICS` |
| `ModeOfArrival` | `AMBULANCE`, `WALK_IN`, `OTHER` |
| `DoctorConsentRequestType` | `PREAUTH_DOCTOR_APPROVAL`, `EMERGENCY_CLAIM_DOCTOR_APPROVAL`, `PRESCRIPTION` |

### Enums you will read (lenient)

`PaymentMechanism`, `AuthorizationStatus`, `EligibilityStatus`, `CoverageStatus` come *from the
server*. Their vocabularies aren't fully documented, so an unknown value does **not** crash: you get a
member whose `.is_known` is `False` and whose value is the raw string. Compare with `==`.

### `extra`

Every result object has an `extra` dict holding server fields the SDK hasn't modelled yet. It's a
read-only escape hatch — log it, don't build logic on it.

---

## 6. `sha.eligibility`

All reads. Safe to call any time; retried automatically on transient failures.

### `check(identification_number, identification_type) → Eligibility`

**Start here for every patient.** Turns an ID document into the CR number you need everywhere else,
and tells you whether they're covered.

| Param | Type | Notes |
|---|---|---|
| `identification_number` | `str` | e.g. national ID number |
| `identification_type` | `IdentificationType` | `NATIONAL_ID`, `ALIEN_ID`, `REFUGEE_ID` (not `REGISTRATION_NUMBER` — that's for doctors) |

Sends `GET /patients/eligibility?identification_number=…&identification_type=National ID`.

Returns **`Eligibility`**:

| Field | Type | Meaning |
|---|---|---|
| `patient_id` | `PatientId \| None` | **the CR number** — keep it |
| `full_name` | `str` | |
| `status` / `status_description` | `EligibilityStatus \| None` / `str` | `"10"` = member found; UAT returns `"00"` "Member Not found!" for unknown IDs |
| `schemes` | `tuple[Scheme, …]` | e.g. UHC; each has `coverage.status`, `policy_period` |
| `date_of_birth`, `gender`, `age`, `is_alive` | | may be empty on UAT |
| `whitelisted_for_otp`, `facility_biometrics_enforced` | `bool` | |
| `member_found` *(property)* | `bool` | status is "member found" **and** a CR number came back |
| `is_covered_on(day)` | `bool` | member found and at least one scheme is active on that date |
| `active_schemes_on(day)` | `tuple[Scheme, …]` | |

```python
e = await sha.eligibility.check("00000000", IdentificationType.NATIONAL_ID)  # UAT synthetic member
if not e.is_covered_on(date.today()):
    raise Exception(f"not covered: {e.status_description}")
patient = e.patient_id
```

### `benefits(patient) → tuple[BenefitPackage, …]`

Top-level packages the patient can use. `GET /patients/benefits?patient_id=…`.
Each `BenefitPackage`: `code` (`SHA-12`), `name` (`Outpatient Services`).

### `sub_benefits(patient) → tuple[SubBenefit, …]`

`GET /patients/sub-benefits?patient_id=…`. Each `SubBenefit`: `code` (`SHA-12-SC-01`), `name`,
`parent_code` (`SHA-12`), `access_point` (`OP`, `IP`, `OP and IP`).

### `interventions(patient, sub_benefit_code) → tuple[InterventionCoverage, …]`

**The billable things** under a sub-benefit, with tariffs and rules.
`GET /patients/benefits/interventions?patient_id=…&sub_benefit_code=…`.

| Field | Meaning |
|---|---|
| `code` | `InterventionCode` — what you authorise and bill |
| `name` | `Consultation`, `Cesarean Section`, … |
| `payment_mechanism` | `CAPITATION`, `CASE BASED`, `FEE FOR SERVICE` (lenient) |
| `needs_preauth` | must file a pre-auth (§9) before billing |
| `needs_doctor_authorization` | needs a doctor's sign-off |
| `access_point` | `OP` / `IP` |
| `overall_tariff` | `Money \| None` — `0` for capitation |
| `applicable_schemes` | e.g. `("UHC",)` |
| `service_type_for_authorization` *(property)* | **use this** as `service_type` when authorising — see gotcha in §14 |

```python
coverage = await sha.eligibility.interventions(patient, "SHA-12-SC-01")
consultation = next(c for c in coverage if c.name == "Consultation")
consultation.service_type_for_authorization  # ServiceType.CAPITATION on UAT
```

### `utilization(patient, intervention) → UtilizationBalance`

Remaining limits for one intervention. `GET /patients/benefits/utilization`. Fields:
`individual_max`, `individual_utilised`, `household_max`, `household_utilised`, `available_amount`,
`eligible`, `funds` (per-fund limits), `individual_remaining` *(property)*.
*On UAT this endpoint returned an upstream 400 in Sept 2026; expect `BadRequestError`.*

### `pomsf_balances(patient, policy_year, *, principal_member_number=None) → dict`

Public Officers Medical Scheme Fund (civil servants). Returned **raw** as a dict — the payload is
large and NaCare has no POMSF members yet.

### `bed_occupancy(facility) → BedOccupancy`

`GET /facilities/{code}/beds/occupancy`. Fields: `facility_name`, `level`, `total_beds`,
`total_inpatient_visits`, `normal_beds`, `icu_beds`, `hdu_beds`, `dialysis_beds`, `baby_cots`,
`occupancy_rate` *(property, `None` if no beds)*. Needs auth on UAT despite the docs.

---

## 7. `sha.consent`

> **Which consent path?** Two exist and they don't mix:
> - **OTP (usual):** `send_otp` → patient reads the code → `claims.open_visit(..., Otp(code))`. Do **not** call `authorize` first.
> - **Biometrics (device):** `authorize` → the patient verifies on the biometric device → `open_visit(..., BiometricGuid(auth.guid))`.
>
> A `PENDING` authorization left behind by the biometric path **blocks** the OTP path. Use `list` + `reject` to clear it.

### `send_otp(patient, interventions) → str`

`POST /claims/otp` `{patient_id, intervention_codes}`. Sends the visit OTP to the beneficiary's registered
phone; returns the server message. (On UAT the message contains the OTP itself — sandbox only.)

### `list(patient) → tuple[Authorization, …]`

`GET /claims/authorizations?beneficiary_code=…`. Every authorization the beneficiary has at your facility,
newest first, with `status` ∈ `PENDING | AUTHORIZED | SUBMITTED_CLAIM | CLOSED`. Undocumented but live.

### `authorize(patient, service_type, interventions, otp=None) → Authorization`

**Biometric path.** Creates a *pending* authorization to be verified on a biometric device. If the patient
already has an open visit, UAT returns that `AUTHORIZED` record instead.

| Param | Type | Notes |
|---|---|---|
| `patient` | `PatientId \| str` | CR number |
| `service_type` | `ServiceType` | use `InterventionCoverage.service_type_for_authorization` |
| `interventions` | list of `InterventionCode \| str` | at least one; duplicates removed |
| `otp` | `Otp \| None` | leave `None` — the server generates and sends it |

Sends `POST /claims/authorize` with `{"patient_id", "service_type", "interventions": [...]}` (+ `"otp"` if given).

Returns **`Authorization`**: `guid`, `token`, `auth_code`, `status` (`PENDING`), `label`
(`UNAUTHORIZED` until verified), `is_open`, `benefit_type`, `beneficiary`, `beneficiary_name`,
`provider_fid`, `interventions` (each with `needs_preauth`), `expiry`, `is_pending` *(prop)*,
`needs_preauth` *(prop, any intervention)*, `as_biometric_proof()` → `BiometricGuid(guid)`.

Raises `RequestValidationError` if `interventions` is empty; `BadRequestError` e.g.
*"intervention Consultation(SHA-12-001) is not supported for service type OUTPATIENT"*.

### `get(token, guid, patient=None) → Authorization | None`

Re-read an authorization. `GET /claims/authorizations?token=…&guid=…[&beneficiary_code=…]`.
`None` if the server has nothing.

### `reject(token) → None`

Close a pending authorization you won't use. `POST /claims/authorizations/{token}/reject`.

---

## 8. `sha.claims`

### `open_visit(patient, service_type, interventions, proof) → ClaimSession`

**Step 2.** Verifies the OTP and opens the server-side virtual claim.

| Param | Type | Notes |
|---|---|---|
| `patient` | `PatientId \| str` | |
| `service_type` | `ServiceType` | same as you used in `authorize` |
| `interventions` | list of codes | |
| `proof` | `Otp` \| `BiometricGuid` \| `MatchId` | the code the patient read out, or a verified biometric GUID |

Sends `POST /claims/visit` with `{"patient_id", "service_type", "intervention_codes": [...]}` plus
exactly one of `"otp"` / `"auth_guid"` / `"match_id"`.

Returns a **`ClaimSession`** (§9). `session.consent_token` is the handle; `session.claim` is the
`VirtualClaim` snapshot the server returned.

Typical failures: `BadRequestError` *"OTP was not found for contact: +2547…"* (no pending
authorization / wrong code), *"Kindly ensure the biometrics visit has been successfully verified"*.

### `resume(consent_token) → ClaimSession`

Re-attach to a claim you opened earlier (e.g. token persisted in your DB). **No network call.**
`session.claim` is `None` until you `preview()`.

```python
session = sha.claims.resume(saved_token)
claim = await session.preview()
```

---

## 9. `ClaimSession`

One object = one server-side claim. Every method sends the session's `consent_token` for you.
Methods that return a `VirtualClaim` also refresh `session.claim`.

### 9.1 Interventions

| Method | Sends | Returns |
|---|---|---|
| `add_intervention(code)` | `POST /claims/interventions` `{consent_token, intervention_code}` | `ClaimIntervention` — `needs_preauth`, `preauth_exists`, `preauth_outstanding` *(prop)*, `applicable_document_types`, `required_preauth_document_types`, tariff |
| `retire_intervention(code)` | `POST /claims/interventions/retire` | `None` |
| `restore_intervention(code)` | `POST /claims/interventions/restore` | `None` |
| `switch_intervention(existing, new, *, retain_bill_items=True, bill_from=None, bill_to=None)` | `POST /claims/interventions/switch` | `None` |

### 9.2 Diagnoses

| Method | Sends | Returns |
|---|---|---|
| `add_diagnosis(icd, intervention)` | `POST /claims/diagnoses` `{consent_token, icd_code, intervention_code}` | `ClaimDiagnosis` — `code`, `name`, `intervention_code`, `record_id`, `is_flagged`, `recorded_on` |
| `remove_diagnosis(icd, intervention)` | `PATCH /claims/diagnoses` | `None` |

`icd` is validated locally (`Icd11Code`), so a typo fails before any network call.

### 9.3 Billing lines

#### `add_line(intervention, unit_price, quantity=1, *, scheme_code=None, charge_date=None, diagnoses=()) → ClaimLine`

| Param | Type | Notes |
|---|---|---|
| `intervention` | code | which intervention this line bills |
| `unit_price` | `Money` | **required, `Money` not a number** |
| `quantity` | `int \| Decimal` | > 0 |
| `scheme_code` | `SchemeCode \| str \| None` | e.g. `"UHC"` |
| `charge_date` | `date \| None` | |
| `diagnoses` | ICD codes | linked to this line |

Sends `POST /claims/lines` as **multipart/form-data**: `consent_token, intervention_code,
unit_price ("1500.00"), quantity, [scheme_code], [charge_date], [diagnoses = JSON array]`.

Returns **`ClaimLine`**: `guid` (needed to remove/edit), `intervention_code`, `item_code`, `item_name`,
`quantity` (Decimal), `unit_price`, `total_amount`, `net_amount`, `copay`, `scheme_code`,
`charge_date`, `is_active`, `doctor_name`.

`RequestValidationError` if quantity ≤ 0 or price negative.

| Method | Sends | Returns |
|---|---|---|
| `remove_line(line_guid)` | `PATCH /claims/lines` `{consent_token, line_guid}` | `None` |
| `edit_line(line_guid, *, quantity=None, unit_price=None, scheme_code=None)` | `PATCH /claims/lines/edit` `{line_id, …changed fields}` — for after payer review | `ClaimLine` |
| `resubmit_lines()` | `POST /claims/lines/resubmit` `{consent_token}` — after `edit_line` | `LineResubmission` — `line`, `status`, `message`, `resubmitted_at` |

### 9.4 Attachments

| Method | Sends | Returns |
|---|---|---|
| `attach(attachment, intervention)` | `POST /claims/attachments` multipart: `consent_token, document_type, intervention_code, file_blob` (uses the upload timeout) | `ClaimAttachment` — `attachment_id`, `title`, `attachment_type`, `intervention_code` |
| `remove_attachment(attachment_id, intervention)` | `PATCH /claims/attachments` | `None` |

```python
await session.attach(Attachment.from_path("invoice.pdf", DocumentType.INVOICE), "SHA-12-001")
```

### 9.5 Lifecycle

#### `preview() → VirtualClaim`
`POST /claims/preview` `{consent_token}`. **The claim as the server sees it.** Safe to call any time
(it's retried like a read). Use it to check totals before submitting, and to resolve an ambiguous submit.

#### `VirtualClaim.submission_blockers() → tuple[Blocker, …]`
Pure check over the snapshot `preview()` returned — nothing is stored or fetched. Each `Blocker`
has `code`, `message`, `intervention`. Codes: `NO_BILLING_LINES`, `ZERO_TOTAL`, `NEGATIVE_TOTAL`,
`PREAUTH_OUTSTANDING`, `NO_DIAGNOSIS`, `MISSING_DOCUMENTS`, `NO_ACTIVE_INTERVENTIONS`. It is
conservative (it only interprets what the server said), so an empty tuple means *no known blocker*,
not a guarantee. Use it to disable the Submit button and tell the biller why.

```python
claim = await session.preview()
if blockers := claim.submission_blockers():
    for b in blockers:
        print(b)  # PREAUTH_OUTSTANDING [SHA-08-006]: intervention needs a pre-authorisation…
else:
    await session.submit("INV-1")
```

#### `add_doctor(practitioner) → str`
`POST /claims/doctors`. Attaches the attending practitioner; the registration is checked against the
Health Worker Registry. **Required before `submit`** (UAT: *"there is no doctor attached to the claim"*).

#### `submit(invoice_number=None, *, discharge_reason=None, otp=None, reason_for_unknown_patient=None) → VirtualClaim`
`POST /claims/submit` `{consent_token, invoice_number, discharge_reason, otp, [reason_for_unknown_patient]}`.
**Final.** No changes after this.

What UAT actually requires (none of it documented): a `discharge_reason`, the OTP from
`send_discharge_otp()` — yes, for outpatient/CAPITATION too — and a doctor on the claim. The server-assigned
`invoice_number` is on the preview (`preview.invoice_number`). So the real sequence is:

```python
await session.add_doctor(PractitionerRef.registered("A1234", RegulationBody.KMPDC))
preview = await session.preview()
await session.send_discharge_otp(patient)  # OTP to the patient / next of kin
claim = await session.submit(preview.invoice_number, discharge_reason=DischargeReason.RECOVERED, otp=code)
```

The SDK sends submit **exactly once**. If the network drops or the server times out *after* the
request left, you get `SubmissionOutcomeUnknownError` — the SDK does not guess. Do this:

```python
try:
    claim = await session.submit("INV-2026-000123")
except SubmissionOutcomeUnknownError as e:
    log.warning("submit outcome unknown, trace %s", e.trace_id)
    claim = await session.preview()  # the server knows; ask it
    if claim.workflow_state not in SUBMITTED_STATES:  # your own mapping once you've seen real values
        claim = await session.submit("INV-2026-000123")
```

#### `close(reason, text) → VirtualClaim`
`POST /claims/close` `{consent_token, cancel_reason_type, cancel_reason_text}`. Abandon a claim that
will never be submitted. `reason` is a `CancelReason`; `text` must be non-empty.

#### `payer_status(provider_claim_no) → tuple[PayerClaimRecord, …]`
`GET /claims/preview/payer?guid=…&provider_claim_no=…` — how the **payer's** system sees the
submitted claim. Needs the claim GUID; if the session has no snapshot yet it calls `preview()` first.
Each `PayerClaimRecord`: `guid`, `provider_claim_no`, `tracking_number`, `workflow_state`,
`workflow_display_name`, `status` *(prop)*, `claim_type`, `is_inpatient`, `proposed_value`,
`proposed_value_less_copays`, `total_copay`, `member_name`, `scheme_name`, `created`.

### 9.6 Inpatient: discharge and next of kin

Every claim needs a discharge OTP and reason before submit. **Inpatient** claims additionally call `discharge`; **outpatient / CAPITATION** pass `discharge_reason` + `otp` straight to `submit` (UAT rejects `/claims/discharge` for them).

| Method | Sends | Returns |
|---|---|---|
| `add_next_of_kin(*, full_name, id_number, id_type, contact_value)` | `POST /patients/next-of-kin/contacts` — register who receives OTPs when the patient can't | `NextOfKinContact` — `guid`, `is_verified`, `is_confirmed`, `is_main_contact` |
| `send_discharge_otp(patient)` | `POST /claims/otp/discharge` `{consent_token, patient_id}` | `str` message |
| `discharge(*, reason, invoice_number, otp, discharged_at=None)` | `POST /claims/discharge` — **INPATIENT only** (UAT rejects it for other service types; outpatient/CAPITATION pass the discharge fields to `submit` instead). `discharged_at` defaults to now, must be tz-aware | `VirtualClaim` |

`id_type` is a `NextOfKinIdType`; `reason` a `DischargeReason`; `otp` may be `Otp` or `str`.

### 9.7 Pre-authorisation

Needed when an intervention has `needs_preauth` (check `InterventionCoverage` or
`ClaimIntervention.preauth_outstanding`).

#### `request_preauth(intervention, *, service_start, service_end, items, diagnoses, doctors, notification_email, attachments=()) → Preauthorization`

| Param | Type | Notes |
|---|---|---|
| `intervention` | code | |
| `service_start`, `service_end` | `datetime` (tz-aware) | end ≥ start |
| `items` | `list[PreauthItem]` | ≥ 1; `PreauthItem(code, description, quantity, unit_price: Money)` |
| `diagnoses` | ICD codes | ≥ 1 |
| `doctors` | `list[PractitionerRef]` | |
| `notification_email` | `str` | valid email; DHA sends updates here |
| `attachments` | `list[Attachment]` | e.g. `PREAUTH_FORM` |

Sends `POST /preauths` as multipart; `items/diagnoses/doctors/attachments` are JSON strings in form
fields and attachment bytes are extra file parts. ⚠ The portal does not publish the inner schema of
those four arrays; the SDK's encoding follows the API's own vocabulary and is **unverified on UAT**
(see `docs/api/WORKFLOWS.md` Q3). If DHA rejects it, the fix is in one function.

Returns **`Preauthorization`**: `guid`, `token`, `status`, `doctor_review_status`,
`needs_doctor_approval`, `doctor_approved`, `doctors_required`, `is_request_phase`,
`is_response_phase`, `total_estimated`, `interim_approved`, `final_approved`, `service_start/end`,
`countdown`, `awaiting_doctor` *(prop)*, `decided` *(prop)*.

| Method | Sends | Returns |
|---|---|---|
| `preauths()` | `GET /preauths?consent_token=…` | `tuple[Preauthorization, …]` |
| `remove_preauth_diagnosis(icd, intervention)` | `DELETE /preauths/diagnoses/{icd}` | `Preauthorization` |
| `remove_preauth_doctor(intervention, registration_number)` | `DELETE /preauths/doctors` — only before submission | `None` |
| `cancel_preauth(intervention)` | `POST /preauths/cancel` | `Preauthorization` |
| `request_doctor_consent(intervention, practitioner, *, request_type=PREAUTH_DOCTOR_APPROVAL, service_type=None, emergency_claim_id=None)` | `POST /claims/doctor-consent` | `str` message |

### 9.8 ePrescriptions

#### `prescribe(intervention, items, *, prescriber=None) → Prescription`

`items` is a list of **`MedicationOrder`**:

| Field | Type | Notes |
|---|---|---|
| `generic_concept_code` | `str` | the medication's code |
| `dose_quantity` | `int \| Decimal` | > 0 |
| `dose_unit` | `str` | `TABLET`, `ML`, … |
| `frequency` | `int` | times per `period_unit`, > 0 |
| `period_unit` | `str` | `DAY`, … |
| `duration` | `int` | > 0 |
| `duration_unit` | `str` | `DAY`, `WEEK`, … |
| `start_date` | `date` | |
| `end_date` | `date \| None` | ≥ start |
| `patient_instruction`, `additional_instruction` | `str` | optional |
| `needs_refill`, `refill_count` | `bool`, `int` | refill_count > 0 when needs_refill |

Sends `POST /prescriptions` JSON `{consent_token, intervention_code, items: [...], [identification_number,
identification_type, regulation_body]}`. Field names match the portal's published example exactly.

Returns **`Prescription`**: `guid`, `code`, `status`, `doctor_review_status`, `intervention_code`,
`dosage` (tuple of `Dosage`: `medication`, `dose_quantity`, `dose_unit`, `frequency`, `period_unit`,
`duration`, `route`, `start_date`, `end_date`, `price`, `status`).

| Method | Sends | Returns |
|---|---|---|
| `prescription()` | `GET /prescriptions?consent_token=…` | `Prescription \| None` |
| `dispense(intervention, products, dispensers)` | `POST /prescriptions/dispenses` `{consent_token, intervention_code, actual_products: [{actual_product_code, total_quantity, medication_price}], doctors: [{identification_number, identification_type}]}` | `Dispense` — `record_id`, `status`, `dosages` |
| `remove_prescription_doctor(intervention, registration_number)` | `DELETE /prescriptions/doctors` | `None` |

`products` is a list of `DispensedProduct(product_code, quantity, price: Money)`; `dispensers` a list
of `PractitionerRef`. Both must be non-empty.

### 9.9 Emergency (on a session opened via `sha.emergency.open_case`)

| Method | Sends | Returns |
|---|---|---|
| `add_protocol(protocol, intervention, unit_price, quantity=1, *, diagnoses=())` | `POST /claims/emergency/protocols` multipart (`diagnoses` **comma-separated** here) | `ClaimLine` |
| `add_emergency_doctor(doctor)` | `POST /claims/doctors` `{consent_token, identification_number, identification_type, regulation_body}` | `str` message |
| `remove_emergency_doctor()` | `DELETE /claims/doctors` `{consent_token}` | `None` |
| `open_emt_claim(EmtClaim(...))` | `POST /claims/emt` multipart — the ambulance provider's claim | `VirtualClaim` |

`EmtClaim(protocol_code, case_number, practitioner_registration_number, provider_registration_number,
beneficiary, otp, diagnoses, interventions, attachments=())`.

---

## 10. `sha.emergency`

### `open_case(attending, reference_number, brought_by, mode_of_arrival, interventions, *, patient=None, otp=None, notes="") → ClaimSession`

Opens an emergency claim **without prior OTP consent**. `patient=None` for an unidentified casualty.

| Param | Type |
|---|---|
| `attending` | `PractitionerRef` (identification + regulation body) |
| `reference_number` | your ER reference |
| `brought_by` | `BroughtBy` |
| `mode_of_arrival` | `ModeOfArrival` |
| `interventions` | codes, ≥ 1 |
| `patient` | `PatientId \| str \| None` |
| `otp` | `Otp \| None` (if the patient can consent) |

Sends `POST /claims/emergency`. Returns a `ClaimSession` — use `add_protocol`, `add_emergency_doctor`,
then the normal `preview` / `submit`.

### `protocols(intervention, *, active=True) → tuple[EmergencyProtocol, …]`

`GET /claims/emergency/protocols?intervention_code=…&active=true`. Each `EmergencyProtocol`: `code`
(`ProtocolCode`), `name`, `protocol_type`, `classification`, `status`, `tariff` (`Money | None`).

---

## 11. `sha.files`

Claim documents normally go through `session.attach(...)`. These are for standalone storage.

| Method | Sends | Returns |
|---|---|---|
| `upload(filename, content: bytes, content_type="application/octet-stream")` | `POST /uploads` multipart `file` | `StoredFile` — `file_id`, `path` (the documented response is `{}`; fields appear if the server sends them) |
| `download_link(file_id)` | `GET /uploads/{file_id}` | `DownloadLink` — `url`, `message` |

---

## 12. End-to-end recipes

### 12.1 Outpatient consultation (the common case)

```python
import asyncio
from datetime import date
from sha_claim import (
    AsyncSHAClient,
    Attachment,
    DocumentType,
    IdentificationType,
    Money,
    Otp,
    SubmissionOutcomeUnknownError,
)


async def outpatient(id_number: str, read_otp_from_patient) -> str:
    async with AsyncSHAClient.from_env() as sha:
        # 1. Who is this, and are they covered?
        e = await sha.eligibility.check(id_number, IdentificationType.NATIONAL_ID)
        if not e.is_covered_on(date.today()):
            raise RuntimeError(f"Not covered: {e.status_description}")
        patient = e.patient_id

        # 2. What can we bill? Pick the intervention and let it tell us the service type.
        coverage = await sha.eligibility.interventions(patient, "SHA-12-SC-01")
        consultation = next(c for c in coverage if c.name == "Consultation")
        service_type = consultation.service_type_for_authorization

        # 3. Consent: this sends the SMS.
        await sha.consent.authorize(patient, service_type, [consultation.code])
        otp = Otp(read_otp_from_patient())  # your UI asks the patient for the code

        # 4. Open the claim.
        session = await sha.claims.open_visit(patient, service_type, [consultation.code], otp)
        token_to_persist = session.consent_token.value  # save this if the visit spans requests

        # 5. Build it.
        await session.add_diagnosis("1A00", consultation.code)
        await session.add_line(consultation.code, Money.kes("1500"), quantity=1, diagnoses=["1A00"])
        await session.attach(Attachment.from_path("invoice.pdf", DocumentType.INVOICE), consultation.code)

        # 6. Check, then submit once.
        preview = await session.preview()
        print("server total:", preview.total_amount)
        try:
            claim = await session.submit("INV-2026-000123")
        except SubmissionOutcomeUnknownError:
            claim = await session.preview()
        return claim.consent_token.value


asyncio.run(outpatient("00000000", lambda: input("OTP: ")))
```

### 12.2 Inpatient with discharge

```python
session = await sha.claims.open_visit(patient, ServiceType.INPATIENT, ["SHA-08-005"], otp)
await session.add_diagnosis("JB0Z", "SHA-08-005")
await session.add_line("SHA-08-005", Money.kes("10000"))
# patient can't consent to discharge herself → register next of kin first
await session.add_next_of_kin(
    full_name="Jane Doe", id_number="12345678", id_type=NextOfKinIdType.NATIONAL_ID, contact_value="+2547…"
)
await session.send_discharge_otp(patient)
await session.discharge(
    discharge_date=date.today(), reason=DischargeReason.RECOVERED, invoice_number="INV-1", otp=read_otp()
)
await session.submit("INV-1")
```

### 12.3 Something that needs pre-authorisation

```python
session = await sha.claims.open_visit(patient, ServiceType.INPATIENT, ["SHA-08-006"], otp)  # Cesarean
pa = await session.request_preauth(
    "SHA-08-006",
    service_start=start,
    service_end=end,
    items=[PreauthItem("CS", "Cesarean section", 1, Money.kes("30000"))],
    diagnoses=["JB0Z"],
    doctors=[PractitionerRef.registered("A1234", RegulationBody.KMPDC)],
    notification_email="claims@yourfacility.example",
    attachments=[Attachment.from_path("preauth.pdf", DocumentType.PREAUTH_FORM)],
)
if pa.awaiting_doctor:
    await session.request_doctor_consent(
        "SHA-08-006", PractitionerRef.registered("A1234", RegulationBody.KMPDC)
    )
# poll later:
for p in await session.preauths():
    print(p.status, p.final_approved)
```

### 12.4 Emergency

```python
doctor = PractitionerRef.registered("A1234", RegulationBody.KMPDC)
protocols = await sha.emergency.protocols("SHA-19-001")
session = await sha.emergency.open_case(
    doctor, "ER-0917", BroughtBy.PARAMEDICS, ModeOfArrival.AMBULANCE, ["SHA-19-001"], patient=None
)  # unidentified casualty
await session.add_emergency_doctor(doctor)
await session.add_protocol(protocols[0].code, "SHA-19-001", protocols[0].tariff, diagnoses=["NF0A"])
await session.submit(reason_for_unknown_patient="unconscious, no ID")
```

### 12.5 Resume a claim tomorrow

```python
session = sha.claims.resume(token_from_your_db)
claim = await session.preview()
status = await session.payer_status(claim.invoice_number.value)
```

---

## 13. Testing code that uses the SDK

You have three levels, cheapest first.

**Fake the SDK's port.** `ClaimSession` and the resources depend on `Protocol`s; hand them fakes.
See `tests/unit/test_session_and_submit.py` for complete fakes you can copy.

**Fake the HTTP layer.** Give the real client a mocked `httpx` server with `respx`:

```python
import httpx, respx
from sha_claim import AsyncSHAClient, SHASettings

settings = SHASettings(client_id="x", client_secret="y", base_url="https://uat.example/uat-middleware")


@respx.mock
async def test_my_code():
    respx.post(f"{settings.api_root}/tenants/token").mock(
        return_value=httpx.Response(200, json={"access_token": "T", "expires_in": 3600})
    )
    respx.get(f"{settings.api_root}/patients/eligibility").mock(return_value=httpx.Response(200, json={...}))
    async with AsyncSHAClient(settings) as sha:
        ...
```
Realistic payloads for every endpoint are in `docs/api/spec/examples.json` (the portal's samples) and
`tests/fixtures/` (recorded from UAT, sanitised).

**Hit UAT.** Set `RUN_LIVE=1` and real credentials in `.env`; see `tests/live/`.

---

## 14. Gotchas

1. **CAPITATION interventions must be authorised as `ServiceType.CAPITATION`, not `OUTPATIENT`** —
   the server rejects the latter even though the docs don't list CAPITATION for that endpoint. Use
   `InterventionCoverage.service_type_for_authorization` and you never think about it.
2. **`authorize` without an OTP is what sends the SMS.** Don't ask the patient for a code before you've
   called it. `open_visit` with an OTP but no pending authorization fails with *"OTP was not found"*.
3. **`submit` is attempted once.** On `SubmissionOutcomeUnknownError`, `preview()` — never blindly retry.
4. **Persist `consent_token.value`, not the object's `str()`** — `str()` is redacted on purpose.
5. **`Money` refuses floats.** `Money.kes("1500.50")` or `Money.kes(1500)`.
6. **Diagnosis codes are validated locally.** `"malaria"` raises before any request.
7. **Server status strings (`workflow_state`, `claim_auth_status`, preauth `status`) are raw `str`** —
   DHA hasn't documented the vocabulary. Log what you see; the SDK will promote them to enums as
   values are confirmed.
8. **Lenient enums**: `PaymentMechanism("SOMETHING NEW")` doesn't raise; check `.is_known` if you
   care.
9. **Every result has `.extra`** with unmodelled server fields. Read-only.
10. **Reads retry, writes don't.** If you wrap a write in your own retry, you own the duplicate.
11. **The facility is in your credentials.** There's no facility parameter anywhere.
12. **Pre-auth nested arrays are unverified on UAT** (Q3). Everything else in this guide is either
    live-verified or asserted against the portal's published examples.

---
## 15. Appendix — result objects

Generated from the code. All are frozen dataclasses: read fields, don't mutate. `extra` holds unmodelled server fields.

### 15.1 Objects the SDK returns

#### `Eligibility`

Eligibility(patient_id: 'PatientId | None', full_name: 'str', status: 'EligibilityStatus | None', status_description: 'str', schemes: 'tuple[Scheme, ...]', date_of_birth: 'date | None' = None, gender: 'str' = '', age: 'int | None' = None, is_alive: 'bool | None' = None, whitelisted_for_otp: 'bool' = False, facility_biometrics_enforced: 'bool' = False, extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `patient_id` | `PatientId | None` | yes |
| `full_name` | `str` | yes |
| `status` | `EligibilityStatus | None` | yes |
| `status_description` | `str` | yes |
| `schemes` | `tuple[Scheme, ...]` | yes |
| `date_of_birth` | `date | None` | no |
| `gender` | `str` | no |
| `age` | `int | None` | no |
| `is_alive` | `bool | None` | no |
| `whitelisted_for_otp` | `bool` | no |
| `facility_biometrics_enforced` | `bool` | no |
| `extra` | `dict` | no |

Properties: `member_found`

#### `Scheme`

Scheme(name: 'str', scheme_id: 'int | None', member_type: 'str', policy_number: 'str', policy_period: 'DateRange', coverage: 'Coverage')

| Field | Type | Required |
|---|---|---|
| `name` | `str` | yes |
| `scheme_id` | `int | None` | yes |
| `member_type` | `str` | yes |
| `policy_number` | `str` | yes |
| `policy_period` | `DateRange` | yes |
| `coverage` | `Coverage` | yes |

#### `Coverage`

Coverage(status: 'CoverageStatus | None', message: 'str', reason: 'str', period: 'DateRange')

| Field | Type | Required |
|---|---|---|
| `status` | `CoverageStatus | None` | yes |
| `message` | `str` | yes |
| `reason` | `str` | yes |
| `period` | `DateRange` | yes |

#### `DateRange`

DateRange(start: 'date | None', end: 'date | None')

| Field | Type | Required |
|---|---|---|
| `start` | `date | None` | yes |
| `end` | `date | None` | yes |

#### `BenefitPackage`

BenefitPackage(code: 'str', name: 'str')

| Field | Type | Required |
|---|---|---|
| `code` | `str` | yes |
| `name` | `str` | yes |

#### `SubBenefit`

SubBenefit(code: 'str', name: 'str', parent_code: 'str', access_point: 'str')

| Field | Type | Required |
|---|---|---|
| `code` | `str` | yes |
| `name` | `str` | yes |
| `parent_code` | `str` | yes |
| `access_point` | `str` | yes |

#### `InterventionCoverage`

InterventionCoverage(code: 'InterventionCode', name: 'str', payment_mechanism: 'PaymentMechanism | None', needs_preauth: 'bool', needs_doctor_authorization: 'bool', access_point: 'str', overall_tariff: 'Money | None', applicable_schemes: 'tuple[str, ...]', fund: 'str' = '', sub_benefit_code: 'str' = '', extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `code` | `InterventionCode` | yes |
| `name` | `str` | yes |
| `payment_mechanism` | `PaymentMechanism | None` | yes |
| `needs_preauth` | `bool` | yes |
| `needs_doctor_authorization` | `bool` | yes |
| `access_point` | `str` | yes |
| `overall_tariff` | `Money | None` | yes |
| `applicable_schemes` | `tuple[str, ...]` | yes |
| `fund` | `str` | no |
| `sub_benefit_code` | `str` | no |
| `extra` | `dict` | no |

Properties: `service_type_for_authorization`

#### `UtilizationBalance`

`GET /patients/benefits/utilization` — how much of a benefit the member (and household) has left.

| Field | Type | Required |
|---|---|---|
| `intervention_code` | `InterventionCode | None` | yes |
| `patient_id` | `str` | yes |
| `limit_scope` | `str` | yes |
| `individual_max` | `Money | None` | yes |
| `individual_utilised` | `Money | None` | yes |
| `household_max` | `Money | None` | yes |
| `household_utilised` | `Money | None` | yes |
| `available_amount` | `Money | None` | yes |
| `eligible` | `bool | None` | yes |
| `next_availability` | `str` | no |
| `funds` | `tuple[FundLimit, ...]` | no |
| `extra` | `dict` | no |

Properties: `individual_remaining`

#### `FundLimit`

FundLimit(fund_type: 'str', max_amount: 'Money | None', utilised_amount: 'Money | None', available_amount: 'Money | None')

| Field | Type | Required |
|---|---|---|
| `fund_type` | `str` | yes |
| `max_amount` | `Money | None` | yes |
| `utilised_amount` | `Money | None` | yes |
| `available_amount` | `Money | None` | yes |

#### `BedOccupancy`

BedOccupancy(facility_name: 'str', level: 'str', total_beds: 'int', total_inpatient_visits: 'int', normal_beds: 'int' = 0, icu_beds: 'int' = 0, hdu_beds: 'int' = 0, dialysis_beds: 'int' = 0, baby_cots: 'int' = 0, extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `facility_name` | `str` | yes |
| `level` | `str` | yes |
| `total_beds` | `int` | yes |
| `total_inpatient_visits` | `int` | yes |
| `normal_beds` | `int` | no |
| `icu_beds` | `int` | no |
| `hdu_beds` | `int` | no |
| `dialysis_beds` | `int` | no |
| `baby_cots` | `int` | no |
| `extra` | `dict` | no |

Properties: `occupancy_rate`

#### `Authorization`

Snapshot of `POST /claims/authorize` / `GET /claims/authorizations`.

| Field | Type | Required |
|---|---|---|
| `guid` | `str` | yes |
| `token` | `str` | yes |
| `auth_code` | `str` | yes |
| `status` | `AuthorizationStatus | None` | yes |
| `label` | `str` | yes |
| `is_open` | `bool` | yes |
| `benefit_type` | `str` | yes |
| `beneficiary` | `PatientId | None` | yes |
| `beneficiary_name` | `str` | yes |
| `provider_fid` | `str` | yes |
| `interventions` | `tuple[AuthorizedIntervention, ...]` | yes |
| `expiry` | `datetime | None` | no |
| `overall_preauth_finalised` | `bool` | no |
| `record_id` | `int | None` | no |
| `extra` | `dict` | no |

Properties: `is_pending`, `needs_preauth`

#### `AuthorizedIntervention`

AuthorizedIntervention(code: 'InterventionCode', name: 'str', needs_preauth: 'bool', payment_mechanism: 'PaymentMechanism | None', sub_benefit_code: 'str' = '')

| Field | Type | Required |
|---|---|---|
| `code` | `InterventionCode` | yes |
| `name` | `str` | yes |
| `needs_preauth` | `bool` | yes |
| `payment_mechanism` | `PaymentMechanism | None` | yes |
| `sub_benefit_code` | `str` | no |

#### `VirtualClaim`

VirtualClaim(consent_token: 'ConsentToken', guid: 'ClaimGuid | None', claim_id: 'int | None', workflow_state: 'str', claim_auth_status: 'str', service_type: 'ServiceType | None', patient_name: 'str', member_number: 'str', payer_name: 'str', scheme_name: 'str', currency: 'str', total_amount: 'Money | None', net_amount: 'Money | None', total_copay: 'Money | None' = None, total_discount: 'Money | None' = None, invoice_number: 'InvoiceNumber | None' = None, visit_number: 'str' = '', visit_start: 'datetime | None' = None, visit_end: 'datetime | None' = None, interventions: 'tuple[ClaimIntervention, ...]' = (), diagnoses: 'tuple[ClaimDiagnosis, ...]' = (), attachments: 'tuple[ClaimAttachment, ...]' = (), invoices: 'tuple[Invoice, ...]' = (), is_negative: 'bool' = False, is_zero: 'bool' = False, extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `consent_token` | `ConsentToken` | yes |
| `guid` | `ClaimGuid | None` | yes |
| `claim_id` | `int | None` | yes |
| `workflow_state` | `str` | yes |
| `claim_auth_status` | `str` | yes |
| `service_type` | `ServiceType | None` | yes |
| `patient_name` | `str` | yes |
| `member_number` | `str` | yes |
| `payer_name` | `str` | yes |
| `scheme_name` | `str` | yes |
| `currency` | `str` | yes |
| `total_amount` | `Money | None` | yes |
| `net_amount` | `Money | None` | yes |
| `total_copay` | `Money | None` | no |
| `total_discount` | `Money | None` | no |
| `invoice_number` | `InvoiceNumber | None` | no |
| `visit_number` | `str` | no |
| `visit_start` | `datetime | None` | no |
| `visit_end` | `datetime | None` | no |
| `interventions` | `tuple[ClaimIntervention, ...]` | no |
| `diagnoses` | `tuple[ClaimDiagnosis, ...]` | no |
| `attachments` | `tuple[ClaimAttachment, ...]` | no |
| `invoices` | `tuple[Invoice, ...]` | no |
| `is_negative` | `bool` | no |
| `is_zero` | `bool` | no |
| `extra` | `dict` | no |

Properties: `preauth_outstanding`, `lines`

#### `ClaimIntervention`

ClaimIntervention(code: 'InterventionCode', name: 'str', payment_mechanism: 'PaymentMechanism | None', needs_preauth: 'bool', preauth_exists: 'bool', workflow_state: 'str', sub_benefit_code: 'str' = '', fund: 'str' = '', overall_tariff: 'Money | None' = None, applicable_document_types: 'tuple[str, ...]' = (), required_preauth_document_types: 'tuple[str, ...]' = (), bill_from: 'datetime | None' = None, bill_to: 'datetime | None' = None, extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `code` | `InterventionCode` | yes |
| `name` | `str` | yes |
| `payment_mechanism` | `PaymentMechanism | None` | yes |
| `needs_preauth` | `bool` | yes |
| `preauth_exists` | `bool` | yes |
| `workflow_state` | `str` | yes |
| `sub_benefit_code` | `str` | no |
| `fund` | `str` | no |
| `overall_tariff` | `Money | None` | no |
| `applicable_document_types` | `tuple[str, ...]` | no |
| `required_preauth_document_types` | `tuple[str, ...]` | no |
| `bill_from` | `datetime | None` | no |
| `bill_to` | `datetime | None` | no |
| `extra` | `dict` | no |

Properties: `preauth_outstanding`

#### `ClaimDiagnosis`

ClaimDiagnosis(code: 'Icd11Code | None', name: 'str', intervention_code: 'InterventionCode | None', record_id: 'int | None' = None, is_flagged: 'bool' = False, recorded_on: 'datetime | None' = None, extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `code` | `Icd11Code | None` | yes |
| `name` | `str` | yes |
| `intervention_code` | `InterventionCode | None` | yes |
| `record_id` | `int | None` | no |
| `is_flagged` | `bool` | no |
| `recorded_on` | `datetime | None` | no |
| `extra` | `dict` | no |

#### `ClaimLine`

ClaimLine(guid: 'LineGuid | None', intervention_code: 'InterventionCode | None', item_code: 'str', item_name: 'str', quantity: 'Decimal', unit_price: 'Money | None', total_amount: 'Money | None', net_amount: 'Money | None', copay: 'Money | None' = None, scheme_code: 'str' = '', charge_date: 'date | None' = None, is_active: 'bool' = True, doctor_name: 'str' = '', extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `guid` | `LineGuid | None` | yes |
| `intervention_code` | `InterventionCode | None` | yes |
| `item_code` | `str` | yes |
| `item_name` | `str` | yes |
| `quantity` | `Decimal` | yes |
| `unit_price` | `Money | None` | yes |
| `total_amount` | `Money | None` | yes |
| `net_amount` | `Money | None` | yes |
| `copay` | `Money | None` | no |
| `scheme_code` | `str` | no |
| `charge_date` | `date | None` | no |
| `is_active` | `bool` | no |
| `doctor_name` | `str` | no |
| `extra` | `dict` | no |

#### `Invoice`

An invoice inside a virtual claim (lines are grouped by invoice on the server side).

| Field | Type | Required |
|---|---|---|
| `invoice_id` | `str` | yes |
| `invoice_number` | `InvoiceNumber | None` | yes |
| `invoice_type` | `str` | yes |
| `workflow_state` | `str` | yes |
| `dispatch_status` | `str` | yes |
| `total_amount` | `Money | None` | yes |
| `net_amount` | `Money | None` | yes |
| `copay` | `Money | None` | no |
| `discount` | `Money | None` | no |
| `lines` | `tuple[ClaimLine, ...]` | no |
| `invoice_date` | `date | None` | no |
| `extra` | `dict` | no |

#### `ClaimAttachment`

ClaimAttachment(attachment_id: 'AttachmentId | None', title: 'str', attachment_type: 'str', intervention_code: 'InterventionCode | None', description: 'str' = '', extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `attachment_id` | `AttachmentId | None` | yes |
| `title` | `str` | yes |
| `attachment_type` | `str` | yes |
| `intervention_code` | `InterventionCode | None` | yes |
| `description` | `str` | no |
| `extra` | `dict` | no |

#### `PayerClaimRecord`

A row from `GET /claims/preview/payer` — the claim as the payer's system sees it (camelCase on the wire).

| Field | Type | Required |
|---|---|---|
| `guid` | `str` | yes |
| `provider_claim_no` | `str` | yes |
| `tracking_number` | `str` | yes |
| `workflow_state` | `str` | yes |
| `workflow_display_name` | `str` | yes |
| `claim_type` | `str` | yes |
| `is_inpatient` | `bool` | yes |
| `proposed_value` | `Money | None` | yes |
| `proposed_value_less_copays` | `Money | None` | yes |
| `total_copay` | `Money | None` | yes |
| `member_name` | `str` | no |
| `member_number` | `str` | no |
| `scheme_name` | `str` | no |
| `created` | `datetime | None` | no |
| `extra` | `dict` | no |

Properties: `status`

#### `NextOfKinContact`

NextOfKinContact(guid: 'str', full_name: 'str', id_number: 'str', contact_value: 'str', contact_type: 'str', is_verified: 'bool', is_confirmed: 'bool', is_main_contact: 'bool', owner_type: 'str' = '', extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `guid` | `str` | yes |
| `full_name` | `str` | yes |
| `id_number` | `str` | yes |
| `contact_value` | `str` | yes |
| `contact_type` | `str` | yes |
| `is_verified` | `bool` | yes |
| `is_confirmed` | `bool` | yes |
| `is_main_contact` | `bool` | yes |
| `owner_type` | `str` | no |
| `extra` | `dict` | no |

#### `LineResubmission`

LineResubmission(line: 'LineGuid | None', status: 'str', message: 'str', resubmitted_at: 'datetime | None' = None)

| Field | Type | Required |
|---|---|---|
| `line` | `LineGuid | None` | yes |
| `status` | `str` | yes |
| `message` | `str` | yes |
| `resubmitted_at` | `datetime | None` | no |

#### `Preauthorization`

Snapshot of a pre-authorisation record (camelCase on the wire).

| Field | Type | Required |
|---|---|---|
| `guid` | `str` | yes |
| `token` | `str` | yes |
| `intervention_code` | `InterventionCode | None` | yes |
| `status` | `str` | yes |
| `doctor_review_status` | `str` | yes |
| `needs_doctor_approval` | `bool` | yes |
| `doctor_approved` | `bool` | yes |
| `doctors_required` | `int` | yes |
| `is_request_phase` | `bool` | yes |
| `is_response_phase` | `bool` | yes |
| `total_estimated` | `Money | None` | yes |
| `interim_approved` | `Money | None` | yes |
| `final_approved` | `Money | None` | yes |
| `service_start` | `datetime | None` | no |
| `service_end` | `datetime | None` | no |
| `provider_notification_email` | `str` | no |
| `member_name` | `str` | no |
| `description` | `str` | no |
| `countdown` | `int | None` | no |
| `record_id` | `int | None` | no |
| `extra` | `dict` | no |

Properties: `awaiting_doctor`, `decided`

#### `Prescription`

Prescription(guid: 'str', code: 'str', status: 'str', doctor_review_status: 'str', intervention_code: 'InterventionCode | None', dosage: 'tuple[Dosage, ...]', record_id: 'int | None' = None, extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `guid` | `str` | yes |
| `code` | `str` | yes |
| `status` | `str` | yes |
| `doctor_review_status` | `str` | yes |
| `intervention_code` | `InterventionCode | None` | yes |
| `dosage` | `tuple[Dosage, ...]` | yes |
| `record_id` | `int | None` | no |
| `extra` | `dict` | no |

#### `Dosage`

A dosage line as the server stores it.

| Field | Type | Required |
|---|---|---|
| `medication` | `str` | yes |
| `medication_identifier` | `str` | yes |
| `dose_quantity` | `Decimal | None` | yes |
| `dose_unit` | `str` | yes |
| `frequency` | `int | None` | yes |
| `period_unit` | `str` | yes |
| `duration` | `str` | yes |
| `duration_unit` | `str` | yes |
| `route` | `str` | no |
| `start_date` | `date | None` | no |
| `end_date` | `date | None` | no |
| `price` | `Money | None` | no |
| `status` | `str` | no |
| `extra` | `dict` | no |

#### `Dispense`

Dispense(record_id: 'int | None', status: 'str', dosages: 'tuple[Dosage, ...]', extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `record_id` | `int | None` | yes |
| `status` | `str` | yes |
| `dosages` | `tuple[Dosage, ...]` | yes |
| `extra` | `dict` | no |

#### `EmergencyProtocol`

EmergencyProtocol(code: 'ProtocolCode', name: 'str', protocol_type: 'str', classification: 'str', status: 'str', tariff: 'Money | None', guid: 'str' = '', extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `code` | `ProtocolCode` | yes |
| `name` | `str` | yes |
| `protocol_type` | `str` | yes |
| `classification` | `str` | yes |
| `status` | `str` | yes |
| `tariff` | `Money | None` | yes |
| `guid` | `str` | no |
| `extra` | `dict` | no |

#### `StoredFile`

Result of `POST /uploads`. The documented response is `{}`; the id/path surface when the server sends them.

| Field | Type | Required |
|---|---|---|
| `file_id` | `FileId | None` | yes |
| `path` | `str` | no |
| `extra` | `dict` | no |

#### `DownloadLink`

DownloadLink(url: 'str', message: 'str' = '', extra: 'Mapping[str, Any]' = <factory>)

| Field | Type | Required |
|---|---|---|
| `url` | `str` | yes |
| `message` | `str` | no |
| `extra` | `dict` | no |

### 15.2 Objects you construct (commands)

`Required = yes` means you must pass it. Each validates in its constructor and raises `ValueError`; when passed through a `ClaimSession` method the same problem surfaces as `RequestValidationError`.

#### `NewClaimLine`

Command for `POST /claims/lines`.

| Field | Type | Required |
|---|---|---|
| `intervention_code` | `InterventionCode` | yes |
| `unit_price` | `Money` | yes |
| `quantity` | `Decimal | int` | yes |
| `scheme_code` | `SchemeCode | None` | no |
| `charge_date` | `date | None` | no |
| `diagnoses` | `tuple[Icd11Code, ...]` | no |

Properties: `total`

#### `LineEdit`

Command for `PATCH /claims/lines/edit` (after payer review).

| Field | Type | Required |
|---|---|---|
| `line` | `LineGuid` | yes |
| `quantity` | `int | None` | no |
| `unit_price` | `Money | None` | no |
| `scheme_code` | `SchemeCode | None` | no |

#### `Discharge`

Command for `POST /claims/discharge` (inpatient). The OTP comes from `send_discharge_otp`.

| Field | Type | Required |
|---|---|---|
| `discharge_date` | `date` | yes |
| `reason` | `DischargeReason` | yes |
| `invoice_number` | `InvoiceNumber` | yes |
| `otp` | `Otp` | yes |

#### `NextOfKin`

Command for `POST /patients/next-of-kin/contacts` — who consents when the beneficiary cannot.

| Field | Type | Required |
|---|---|---|
| `full_name` | `str` | yes |
| `id_number` | `str` | yes |
| `id_type` | `NextOfKinIdType` | yes |
| `contact_value` | `str` | yes |

#### `PreauthRequest`

Command for `POST /preauths`. Validates what the server would certainly reject.

| Field | Type | Required |
|---|---|---|
| `intervention_code` | `InterventionCode` | yes |
| `service_start` | `datetime` | yes |
| `service_end` | `datetime` | yes |
| `items` | `tuple[PreauthItem, ...]` | yes |
| `diagnoses` | `tuple[Icd11Code, ...]` | yes |
| `doctors` | `tuple[PractitionerRef, ...]` | yes |
| `provider_notification_email` | `str` | yes |
| `attachments` | `tuple[Attachment, ...]` | no |

Properties: `estimated_total`

#### `PreauthItem`

A billed item on the pre-auth request.

| Field | Type | Required |
|---|---|---|
| `code` | `str` | yes |
| `description` | `str` | yes |
| `quantity` | `Decimal | int` | yes |
| `unit_price` | `Money` | yes |

Properties: `total`

#### `DoctorConsentRequest`

Command for `POST /claims/doctor-consent`.

| Field | Type | Required |
|---|---|---|
| `intervention_code` | `InterventionCode` | yes |
| `request_type` | `DoctorConsentRequestType` | yes |
| `practitioner` | `PractitionerRef` | yes |
| `service_type` | `ServiceType | None` | no |
| `emergency_claim_id` | `str | None` | no |

#### `MedicationOrder`

One prescribed medication (an `items[]` entry of `POST /prescriptions`).

| Field | Type | Required |
|---|---|---|
| `generic_concept_code` | `str` | yes |
| `dose_quantity` | `Decimal | int` | yes |
| `dose_unit` | `str` | yes |
| `frequency` | `int` | yes |
| `period_unit` | `str` | yes |
| `duration` | `int` | yes |
| `duration_unit` | `str` | yes |
| `start_date` | `date` | yes |
| `end_date` | `date | None` | no |
| `patient_instruction` | `str` | no |
| `additional_instruction` | `str` | no |
| `needs_refill` | `bool` | no |
| `refill_count` | `int` | no |

#### `PrescriptionRequest`

PrescriptionRequest(intervention_code: 'InterventionCode', items: 'tuple[MedicationOrder, ...]', prescriber: 'PractitionerRef | None' = None)

| Field | Type | Required |
|---|---|---|
| `intervention_code` | `InterventionCode` | yes |
| `items` | `tuple[MedicationOrder, ...]` | yes |
| `prescriber` | `PractitionerRef | None` | no |

#### `DispensedProduct`

An `actual_products[]` entry of `POST /prescriptions/dispenses`.

| Field | Type | Required |
|---|---|---|
| `product_code` | `str` | yes |
| `quantity` | `Decimal | int` | yes |
| `price` | `Money` | yes |

#### `DispenseRequest`

DispenseRequest(intervention_code: 'InterventionCode', products: 'tuple[DispensedProduct, ...]', dispensers: 'tuple[PractitionerRef, ...]')

| Field | Type | Required |
|---|---|---|
| `intervention_code` | `InterventionCode` | yes |
| `products` | `tuple[DispensedProduct, ...]` | yes |
| `dispensers` | `tuple[PractitionerRef, ...]` | yes |

#### `EmergencyCase`

Command for `POST /claims/emergency`. `beneficiary` is None for an unidentified patient.

| Field | Type | Required |
|---|---|---|
| `attending` | `PractitionerRef` | yes |
| `reference_number` | `str` | yes |
| `brought_by` | `BroughtBy` | yes |
| `mode_of_arrival` | `ModeOfArrival` | yes |
| `interventions` | `tuple[InterventionCode, ...]` | yes |
| `beneficiary` | `PatientId | None` | no |
| `otp` | `Otp | None` | no |
| `notes` | `str` | no |

#### `ProtocolLine`

Command for `POST /claims/emergency/protocols` — bills a treatment protocol on an emergency claim.

| Field | Type | Required |
|---|---|---|
| `protocol_code` | `ProtocolCode` | yes |
| `intervention_code` | `InterventionCode` | yes |
| `unit_price` | `Money` | yes |
| `quantity` | `int` | no |
| `diagnoses` | `tuple[Icd11Code, ...]` | no |

#### `EmtClaim`

Command for `POST /claims/emt` — the ambulance / EMT provider's claim for an emergency case.

| Field | Type | Required |
|---|---|---|
| `protocol_code` | `ProtocolCode` | yes |
| `case_number` | `str` | yes |
| `practitioner_registration_number` | `str` | yes |
| `provider_registration_number` | `str` | yes |
| `beneficiary` | `PatientId` | yes |
| `otp` | `Otp` | yes |
| `diagnoses` | `tuple[Icd11Code, ...]` | yes |
| `interventions` | `tuple[InterventionCode, ...]` | yes |
| `attachments` | `tuple[Attachment, ...]` | no |

#### `Attachment`

Attachment(filename: 'str', content: 'bytes', document_type: 'DocumentType', content_type: 'str' = 'application/octet-stream')

| Field | Type | Required |
|---|---|---|
| `filename` | `str` | yes |
| `content` | `bytes` | yes |
| `document_type` | `DocumentType` | yes |
| `content_type` | `str` | no |

Properties: `size`

#### `PractitionerRef`

Identifies a doctor by registration number (preferred) or a national identity document.

| Field | Type | Required |
|---|---|---|
| `identification_number` | `str` | yes |
| `identification_type` | `IdentificationType` | yes |
| `regulation_body` | `RegulationBody` | yes |

### 15.3 Enum values

- **`AuthorizationStatus`** (lenient — unknown values allowed): `PENDING` = `PENDING`
- **`BroughtBy`** (strict): `RELATIVE` = `RELATIVE`, `UNKNOWN` = `UNKNOWN`, `SAMARITAN` = `SAMARITAN`, `PARAMEDICS` = `PARAMEDICS`
- **`CancelReason`** (strict): `WRONG_PATIENT` = `WRONG_PATIENT`, `NO_SERVICE_GIVEN` = `NO_SERVICE_GIVEN`, `WRONG_BENEFIT` = `WRONG_BENEFIT`, `EXPIRED_VISIT` = `EXPIRED_VISIT`, `EXHAUSTED_BENEFIT` = `EXHAUSTED_BENEFIT`, `TIME_BARRED` = `TIME_BARRED`, `OTHER_REASONS` = `OTHER_REASONS`
- **`CoverageStatus`** (lenient — unknown values allowed): `COVERED` = `1`
- **`DischargeReason`** (strict): `RECOVERED` = `RECOVERED`, `REFERRED` = `REFERRED`, `DECEASED` = `DECEASED`, `ABSCONDED` = `ABSCONDED`, `OTHER` = `OTHER`
- **`DoctorConsentRequestType`** (strict): `PREAUTH_DOCTOR_APPROVAL` = `PREAUTH_DOCTOR_APPROVAL_REQUEST`, `EMERGENCY_CLAIM_DOCTOR_APPROVAL` = `EMERGENCY_CLAIM_DOCTOR_APPROVAL_REQUEST`, `PRESCRIPTION` = `PRESCRIPTION_REQUEST`
- **`EligibilityStatus`** (lenient — unknown values allowed): `MEMBER_FOUND` = `10`
- **`IdentificationType`** (strict): `NATIONAL_ID` = `National ID`, `ALIEN_ID` = `Alien ID`, `REFUGEE_ID` = `Refugee ID`, `REGISTRATION_NUMBER` = `registration_number`
- **`ModeOfArrival`** (strict): `AMBULANCE` = `AMBULANCE`, `WALK_IN` = `WALK-IN`, `OTHER` = `OTHER`
- **`NextOfKinIdType`** (strict): `NATIONAL_ID` = `National ID`, `CLIENT_REGISTRY_ID` = `ClientRegistry ID`, `BIRTH_NOTIFICATION` = `Birth Notification`, `BIRTH_CERTIFICATE` = `Birth Certificate`, `ALIEN_ID` = `Alien ID`, `REFUGEE_ID` = `Refugee ID`, `MANDATE_NUMBER` = `Mandate Number`, `TEMPORARY_ID` = `Temporary ID`
- **`PaymentMechanism`** (lenient — unknown values allowed): `CAPITATION` = `CAPITATION`, `CASE_BASED` = `CASE BASED`, `FEE_FOR_SERVICE` = `FEE FOR SERVICE`
- **`ServiceType`** (strict): `CAPITATION` = `CAPITATION`, `OUTPATIENT` = `OUTPATIENT`, `INPATIENT` = `INPATIENT`, `EMERGENCY` = `EMERGENCY`
- **`DocumentType`** (strict): `BIO_DETAILS` = `BIO_DETAILS`, `BIRTH_NOTIFICATION` = `BIRTH_NOTIFICATION`, `CARE_PLAN` = `CARE_PLAN`, `CASE_NOTE` = `CASE_NOTE`, `CASE_SUMMARY` = `CASE_SUMMARY`, `CERTIFIED_BURIAL_PERMIT` = `CERTIFIED_BURIAL_PERMIT`, `CERTIFIED_COPY_OF_DECEASED_ID` = `CERTIFIED_COPY_OF_DECEASED_ID`, `CLAIM_FORM` = `CLAIM_FORM`, `COVER_LETTER_FROM_EMPLOYER` = `COVER_LETTER_FROM_EMPLOYER`, `CRITICAL_CARE_UNIT_CASE` = `CRITICAL_CARE_UNIT_CASE`, `CT_SCAN` = `CT_SCAN`, `DEATH_NOTICE` = `DEATH_NOTICE`, `DIALYSIS_CHART` = `DIALYSIS_CHART`, `DISCHARGE_SUMMARY` = `DISCHARGE_SUMMARY`, `ENTRY_EXIT_VISA_STAMP` = `ENTRY_EXIT_VISA_STAMP`, `FINAL_BILL` = `FINAL_BILL`, `IMAGING_ORDER` = `IMAGING_ORDER`, `IMAGING_REPORT` = `IMAGING_REPORT`, `INVOICE` = `INVOICE`, `LAB_ORDER` = `LAB_ORDER`, `LAB_RESULTS` = `LAB_RESULTS`, `MAGNETIC_RESONANCE_IMAGING` = `MAGNETIC_RESONANCE_IMAGING`, `MEDICAL_REPORT` = `MEDICAL_REPORT`, `OTHER` = `OTHER`, `POST_SERVICE_IMAGING_REPORT` = `POST_SERVICE_IMAGING_REPORT`, `PRE_SERVICE_IMAGING_REPORT` = `PRE_SERVICE_IMAGING_REPORT`, `PREAUTH_FORM` = `PREAUTH_FORM`, `PRESCRIPTION` = `PRESCRIPTION`, `REQUEST_FORM_BY_RELEVANT_CONSULTANT` = `REQUEST_FORM_BY_RELEVANT_CONSULTANT`, `RHESUS_FACTOR` = `RHESUS_FACTOR`, `THEATRE_NOTES` = `THEATRE_NOTES`
- **`RegulationBody`** (strict): `KMPDC` = `KMPDC`, `COC` = `COC`, `NCK` = `NCK`
