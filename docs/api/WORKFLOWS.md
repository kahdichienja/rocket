# AfyaConnect eClaims — End-to-End Workflows

Derived from the endpoint reference in this folder. Field-level detail lives in the per-tag files;
this document explains **how the endpoints chain together**, which is what the SDK's use cases model.

## 0. Mental model

- The HIE middleware (`https://ilm-dev.dha.go.ke/uat-middleware`, UAT) fronts an ILM/Slade360-style
  claims engine (`payer_slade_code`, `provider_slade_code`, `edi_claim_guid` leak through).
- **The claim lives on the server.** A facility does not build a claim locally and POST it once; it
  *opens a virtual claim* and then mutates it with a series of calls, then submits.
- Every mutation is keyed by the **`consent_token`** — the `authorization_code` returned when the
  virtual claim is created. It is the claim's handle, the patient's proof of consent, and the
  authorization scope in one string. Lose it and you cannot touch the claim.
- Auth is **OAuth2 client-credentials** → `Bearer` token on every call (except `GET /facilities/{code}/beds/occupancy`, which is public).
- Errors are uniformly `{ "error": "<HTTP status text>", "message": "<detail>" }` for 400/401/403/500.
- Wire naming is inconsistent: claims payloads are `snake_case`; authorization and preauth responses
  are `camelCase`. The SDK must normalise this at the adapter boundary.

## 1. Authentication

```
POST {auth}/tenants/token      (application/x-www-form-urlencoded)
     client_id, client_secret
 →   { access_token, expires_in, token_type }
```
Cache until `expires_in` minus a safety skew; refresh single-flight; on 401 refresh once and replay.

## 2. Outpatient claim (the common path)

```
1. GET  /patients/eligibility?identification_number&identification_type
        → statusCode/statusDesc, memberCrNumber, schemes[], whitelistedForOTP
        (memberCrNumber is the `patient_id` used everywhere after this)

2. GET  /patients/benefits?patient_id                       (optional: which packages)
   GET  /patients/benefits/interventions?patient_id&sub_benefit_code
   GET  /patients/benefits/utilization?patient_id&intervention_code   (remaining limits)

3. Consent — entry point is POST /claims/authorize for BOTH strategies:
   POST /claims/authorize {patient_id, service_type∈{OUTPATIENT,INPATIENT}, interventions[], otp}
        → { guid, token, status, isComplete, needsPreauth, shaVerificationRequest, shaVerificationRequestId, ... }
   a) OTP:        the OTP reaches the beneficiary's registered phone as part of this authorization
                  (`shaVerificationRequest*` in the response is the SHA-side verification record).
                  Whether the OTP is delivered *before* this call (facility-triggered elsewhere) or *by* this
                  call (two-step: create → beneficiary receives OTP → verify on /claims/visit) must be
                  confirmed on UAT — see Q1.
   b) Biometrics: same endpoint via a registered hardware agent (eKYC / fingerprint); the returned `guid`
                  is what /claims/visit takes instead of an OTP.
   Reject a pending biometric authorization: POST /claims/authorizations/{consent_token}/reject
   Re-read one:                              GET  /claims/authorizations?token&guid

4. POST /claims/visit {patient_id, service_type=OUTPATIENT, intervention_codes[], otp | authorization guid}
        → virtual claim; keep `authorization_code` (= consent_token), `claim_id`, `id`, `workflow_state`

5. Build the claim (all keyed by consent_token):
   POST  /claims/interventions          add intervention          (also /retire, /restore, /switch)
   POST  /claims/diagnoses              {icd_code, intervention_code}
   POST  /authorizations/covers         {principal_cr_id, consent_token, policy_number}   POMSF only, before lines (process docs)
   POST  /claims/lines   (multipart)    {intervention_code, unit_price, quantity, scheme_code?, charge_date?, diagnoses?,
                                         service_name?, service_identifier?, practitioner_*?, attachments? (+ binary parts)}
                                        = "Add New Line" / "Add Combined Billing Details" on the process docs
   POST  /claims/attachments (multipart){file_blob, document_type∈enum, intervention_code}
   (PATCH variants remove diagnoses / lines / attachments)

6. POST /claims/preview {consent_token}          → full claim as the server sees it; verify totals

7. POST /claims/submit {consent_token, invoice_number?, reason_for_unknown_patient?}
        → claim record incl. workflow_state, total_claim_amount, total_claim_net_amount, edi_claim_guid
        NO FURTHER CHANGES after this.

8. Track:  GET /claims/preview/payer?guid&provider_claim_no → {pageSize, results[]}  (payer-side status)
   Fix:    PATCH /claims/lines/edit {line_id, quantity, unit_price, scheme_code} after payer review,
           then POST /claims/lines/resubmit {consent_token}

Abort at any point before 7:  POST /claims/close {consent_token, cancel_reason_type∈enum, cancel_reason_text}
```

## 3. Inpatient claim

Same as §2 with `service_type=INPATIENT`, plus a discharge gate before submit:

```
POST /claims/otp/discharge {consent_token, patient_id}           → OTP sent to beneficiary / next of kin
POST /claims/discharge {consent_token, discharge_date, discharge_reason∈enum, invoice_number, otp}
POST /claims/submit ...
```
If the beneficiary cannot consent: `POST /patients/next-of-kin/contacts {consent_token, next_of_kin_*}` first.

## 4. Pre-authorization (when `needsPreauth` is true / the benefit requires it)

```
POST /preauths  (multipart/form-data)
     consent_token, intervention_code, service_start, service_end,
     items[], diagnoses[], doctors[], attachments[], provider_notification_email
 →   { guid, token, status, doctorReviewStatus, needsDoctorApproval, numberOfPreauthDoctorsRequired,
       totalEstimatedAmountForPreauth, finalApprovedAmount, preauthItems[], ... }

Doctor approval (when needsDoctorApproval):
POST /claims/doctor-consent {intervention_code, request_type=PREAUTH_DOCTOR_APPROVAL_REQUEST,
                             practitioner_registration_number | identification_*, regulation_body∈{KMPDC,COC,NCK}}

Amend before submission:
DELETE /preauths/diagnoses/{icd_code}   DELETE /preauths/doctors   POST /preauths/cancel
Poll:   GET /preauths?consent_token
```
Inner schema of `items[]`, `diagnoses[]`, `doctors[]`, `attachments[]` is **not exposed** by the portal (flattened) — Q3.
The SDK's working assumption (`requests.create_preauth`): JSON strings in form fields, `items` as
`{item_code, item_name, quantity, unit_price}`, `diagnoses` as `{icd_code}`, `doctors` as the practitioner fields used by
`/claims/doctor-consent`, `attachments` as `{field, document_type, title}` where `field` names a multipart file part
(the convention `/claims/emt` documents). Unverified until a live preauth call succeeds.

## 5. Emergency

```
POST /claims/emergency {identification_type, identification_number, regulation_body, reference_number,
                        brought_by∈enum, mode_of_arrival∈enum, interventions[], beneficiary_cr_id?, otp?, notes?}
GET  /claims/emergency/protocols?active&intervention_code
POST /claims/emergency/protocols (multipart) {consent_token, protocol_code, intervention_code, unit_price, quantity, diagnoses?, attachments?}
POST /claims/doctors {consent_token, identification_*, regulation_body}   (DELETE to remove)
POST /claims/emt (multipart) — ambulance/EMT provider claim
… then §2 steps 6–8.
```
Doctor sign-off: `POST /claims/doctor-consent` with `request_type=EMERGENCY_CLAIM_DOCTOR_APPROVAL_REQUEST`.

## 6. ePrescriptions & dispensing

```
POST /prescriptions {consent_token, intervention_code, items[], identification_*, regulation_body}
GET  /prescriptions?consent_token
POST /prescriptions/dispenses {consent_token, intervention_code, actual_products[], doctors[]}
DELETE /prescriptions/doctors {consent_token, intervention_code, practitioner_registration_number}
```

## 7. Files

`POST /uploads` (multipart `file`) → storage path/id; `GET /uploads/{file_id}` → pre-signed URL.
Claim attachments can also be sent inline via `POST /claims/attachments`.

## 8. Enumerations worth owning as domain types

| Concept | Values |
|---|---|
| `service_type` (visit) | `CAPITATION`, `OUTPATIENT`, `INPATIENT`, `EMERGENCY` |
| `service_type` (authorize) | `OUTPATIENT`, `INPATIENT` |
| `document_type` | 31 values — see [eclaims--billing.md](eclaims--billing.md) |
| `cancel_reason_type` | `WRONG_PATIENT`, `NO_SERVICE_GIVEN`, `WRONG_BENEFIT`, `EXPIRED_VISIT`, `EXHAUSTED_BENEFIT`, `TIME_BARRED`, `OTHER_REASONS` |
| `discharge_reason` | `RECOVERED`, `REFERRED`, `DECEASED`, `ABSCONDED`, `OTHER` |
| `identification_type` (practitioner) | `registration_number`, `National ID`, `Alien ID`, `Refugee ID` |
| `regulation_body` | `KMPDC`, `COC`, `NCK` |
| `request_type` (doctor consent) | `PREAUTH_DOCTOR_APPROVAL_REQUEST`, `EMERGENCY_CLAIM_DOCTOR_APPROVAL_REQUEST`, `PRESCRIPTION_REQUEST` |
| `brought_by` | `RELATIVE`, `UNKNOWN`, `SAMARITAN`, `PARAMEDICS` |
| `mode_of_arrival` | `AMBULANCE`, `WALK-IN`, `OTHER` |
| `next_of_kin_id_number_type` | `National ID`, `ClientRegistry ID`, `Birth Notification`, `Birth Certificate`, `Alien ID`, `Refugee ID`, `Mandate Number`, `Temporary ID` |

## 9. Observed on UAT (2026-09-20) — facts the portal omits

- Token: Keycloak (`iss: https://accounts-uat.dha.go.ke/realms/hie`), `expires_in: 3600`. The JWT carries
  `facility_id` (`FID-47-105963-0`) and `facility_id_type: fr-code` — **the facility is implied by the credential**,
  so the SDK has no `SHA_FACILITY_CODE` setting.
- Gateway is APISIX; every response has `x-request-id`. Error envelope is `{error, message, trace_id}` — `trace_id`
  is undocumented but always present; the SDK attaches it to every raised error.
- `identification_type` for eligibility is the literal `National ID` (echoed back as `requestIdType: 2`). Q7 answered.
- `GET /facilities/{code}/beds/occupancy` **requires** a bearer token despite the spec saying otherwise.
- `GET /preauths?consent_token=…` returns a paginated list `{pageSize, results[]}`, not a single object.
- `identification_number=00000000` returns a synthetic member (`statusCode: "10"`, scheme `UHC`, coverage `status: "1"`,
  `memberCrNumber: CR7678914660684-5`) — usable as a stable fixture (`tests/fixtures/*.json`, sanitised).
- **Consent is a two-step handshake (Q1 closed).** `POST /claims/authorize` *without* `otp` returns `200` with a
  `status: "PENDING"`, `label: "UNAUTHORIZED"`, `isOpen: true` authorization (`guid`, `token`, `authCode`) and sends
  the OTP to the beneficiary's registered phone. `POST /claims/visit` then verifies with **one of `otp`, `auth_guid`
  or `match_id`** (Q2 closed) — the server says so verbatim when none is given. `visit` with an OTP but no pending
  authorization fails with `OTP was not found for contact: +2547…`.
- `service_type` on `/claims/authorize` accepts **`CAPITATION`** (docs list only OUTPATIENT/INPATIENT). Interventions with
  `paymentMechanism: CAPITATION` are *refused* under `OUTPATIENT`
  (`Kindly note the intervention Consultation(SHA-12-001) is not supported for service type OUTPATIENT`).
  The SDK encodes this as `InterventionCoverage.service_type_for_authorization`.
- Error envelope can also carry `details: [..]`, and `error` may be a JSON-encoded string from the upstream engine
  (`{"error":"{\"error\":\"Kindly note…\"}"}`); `message` may end in a JSON blob (`{"Edi Error":{"detail":…}}`).
  `ErrorEnvelope.detail()` unwraps all three.
- `GET /claims/authorizations` returns a **list** (`[ {...} ]`), not an object.
- Benefit reads are paginated: `{count, pageSize, currentPage, totalPages, results[]}`. `/patients/benefits` gives
  `{parentBenefit, parentBenefitCode}`; `/patients/sub-benefits` gives `{code, name, accessPoint, parentBenefitCode}`;
  `/patients/benefits/interventions` gives rich rows (`code, name, paymentMechanism, needsPreauth, needsDoctorAuthorization,
  overallTariff, level2..6Tariff, applicableSchemes, fund, requires*Preauth`).
- `GET /patients/benefits/utilization` returns 400 `invalid character 'P' looking for beginning of value` on UAT for the
  synthetic patient — an upstream parsing bug, not a request error.
- `POST /claims/authorizations/{token}/reject` → `200 {"message":"The authorization has been closed."}`.
- `GET /patients/benefits/interventions` with an unknown/wrong `sub_benefit_code` (e.g. a policy number) returns `[]`, not 400.
  A real member has ~30 sub-benefits / ~850 interventions and DHA serves each sub-benefit's list in ~1–4 s serially
  (≈20 s for all): load sub-benefits first, interventions on demand. `applicableSchemes` on interventions uses a different
  vocabulary (`UHC`, `PMF`) from eligibility `schemes[].schemeName` (`UHC`, `SHIF`) — do not join on it.
- `patient_id` is not validated by DHA: authorizations exist on UAT with `beneficiaryCode` values like `CR-2026-000018`
  (an HMIS's internal number). The SDK enforces the CR shape before sending.
- **`GET /claims/authorizations` ignores `beneficiary_code`** (`?beneficiary_code=DOES-NOT-EXIST` returns the same 25 rows as no
  filter): it lists the *facility's* authorizations. The SDK filters by `beneficiaryCode` client-side. Also observed status
  `AUTHORIZED_PENDING_VISIT`.

### Live claim lifecycle, UAT 2026-09-20 (evening) — the rules nobody documented

Run through the SDK against the synthetic member; every step below is verified except the last, which
needs an HWR-registered practitioner.

1. **The OTP path is `POST /claims/otp` → `POST /claims/visit`.** `/claims/otp` is not on the eclaims portal
   pages but is live; on UAT its response *contains the OTP* (`"Your OTP is 349835"`). `authorize` is the
   biometric path only; a **PENDING authorization blocks the OTP path** ("Kindly ensure the biometrics visit
   has been successfully verified"). `GET /claims/authorizations?beneficiary_code=` (no token/guid) lists a
   beneficiary's authorizations so a dangling PENDING one can be found and rejected.
2. `open_visit` for a patient with an open visit **returns that visit** (same guid, same consent token) —
   effectively idempotent. `authorize` likewise returns the open AUTHORIZED record instead of a new PENDING one.
3. Real vocabularies: authorization `status` ∈ {PENDING, AUTHORIZED, SUBMITTED_CLAIM, CLOSED}, `label` ∈
   {UNAUTHORIZED, OTP, SHA}; claim `workflow_state` ∈ {DRAFT, SUBMITTED}; `claim_auth_status` = AUTHORIZED;
   intervention `workflow_state` = ACTIVE; invoice `workflow_state` = VALID, `dispatch_status` = DISPATCHED.
   The server assigns `invoice_number` (`INV/13545/75385`) at visit creation.
4. `null` appears where the docs promise `[]`/`""` (e.g. `required_preauth_document_types: null`).
5. **`POST /claims/submit` needs, for every service type (CAPITATION included):** `discharge_reason`
   (undocumented field), `otp` from `POST /claims/otp/discharge` (undocumented field — "Please provide a
   beneficiary discharge authorization method: OTP or biometrics"), and **a doctor on the claim** via
   `POST /claims/doctors` ("there is no doctor attached to the claim"). `POST /claims/discharge` itself is
   **INPATIENT-only** ("only claims of service type INPATIENT … use appropriate route for CAPITATION") and
   wants an RFC 3339 datetime, not a date.
7. **Emergency (`POST /claims/emergency`, UAT 2026-09-21):** `notes` is mandatory (blank → `{"notes":["This
   field may not be blank."]}`), despite the portal marking it optional. Interventions must be payable from the
   emergency fund (`fund: "ECCIF Only"`, sub-benefit `SHA-01-SC-01 Emergency`); a capitation one is refused
   ("Consultation(SHA-12-001) is not supported for service type EMERGENCY"). The **facility must be accredited**
   for emergency care — the UAT facility is not ("Kindly note the facility MATHARE NORTH HOSPITAL is not allowed to
   provide emergency services"), and with a beneficiary attached the upstream engine answers 500. So the emergency
   path is contract-tested against the portal examples but not live-verified.
8. **Interventions on an open visit (UAT 2026-09-21, all four live-verified):** add / retire / restore / switch
   each return the updated intervention list on the next `preview`. A retired intervention has
   `workflow_state: "INACTIVE"` (the process pages never name the state); `switch` leaves the old one INACTIVE and
   the new one ACTIVE. UAT **did not** refuse retiring an intervention that had bill items (Consultation with six
   lines), contrary to the retire page — and **deleted those lines** (invoice KES 3,000 → 0); `restore` brought the
   intervention back but not the lines. Do not rely on DHA to protect billed lines: check `VirtualClaim.lines`
   before retiring, or `switch` with `retain_bill_items=True`. `switch` with `retain_bill_items=false` needs no dates.
9. **UAT facility contracts change without notice (2026-09-21, later in the day):** `POST /claims/visit` for
   MATHARE NORTH HOSPITAL (FID-47-115307-8) started answering "Kindly note the facility … is not allowed to
   provide service for intervention Consultation(SHA-12-001) of sub benefit Outpatient Care" for every
   capitation intervention that had opened fine the day before. Nothing in the request changed. Treat the
   sandbox facility's contract as volatile; the SDK surfaces it as a `BadRequestError` and NaCare words it as
   `FACILITY_NOT_CONTRACTED`.
10. **Consent needs a real channel (UAT 2026-09-22).** `authorize()` returns a PENDING authorization with a
   guid even for a beneficiary with no phone on record, but `/claims/visit` with that guid is refused —
   "Kindly ensure the biometrics visit has been successfully verified": the guid only works once a device has
   verified the fingerprint. So a member with no phone and no biometric capture cannot open a visit at all.
   Also: **`GET /patients/sub-benefits` is facility-scoped** — the same member returns 30 sub-benefits at one
   facility and 0 at another, which is the cheapest way to see what a facility is contracted for before
   attempting a visit.
11. **Reference endpoints (UAT 2026-09-22/23, facility FID-47-108521-3 KENYATTA NATIONAL HOSPITAL).**
   `GET /patients/benefits/utilization` returns a **bare list**, one record per limit scope (`limitScope`),
   not the single object the portal documents — it had been answering 400 upstream until this facility, so the
   shape surfaced only now. `GET /facilities/{code}/beds/occupancy` is live and real (1889 normal beds, 93 ICU);
   `total_number_of_bed` can be 0 while the per-type counts are populated. `GET /patients/pomsf-balances`
   answers "Not Found" for a non-POMSF member.
12. **Client Registry (UAT 2026-09-23).** `GET /patients?identification_number&identification_type` returns the
   member record with `id` = the CR number, and `GET /patients/contacts?patient_id` returns
   `{count, results[{contactValue (masked), contactType: "PHO", isConfirmed, active, isMainContact}]}`.
   **`count: 0` is exactly the cause of "the contact record for beneficiary … contact id 0 doesn't exist"** —
   check it before sending an OTP. Eligibility says the same thing in `whitelistedForOTP`, and also carries
   `facilityContracts` (the schemes the acting facility may bill) and `facilityBiometricsEnforced`.
   **Two CR formats are live at once**: `CR7678914660684-5` and `CR-2026-000256`.
13. **ePrescriptions on UAT (2026-09-24).** The family is only partly usable:
   - `POST /prescriptions` is reachable but blocked by three **undocumented controlled vocabularies**:
     `generic_concept_code`, `dose_unit` and `patient_instruction`. Words (`TABLET`, `MG`, `ORAL`), numeric ids
     and an empty string are all refused with `"X" is not a valid choice`, and none appear in the portal spec.
     `patient_instruction` is *required* — `""` is refused — so a prescription cannot be filed at all until DHA
     publishes the dictionaries.
   - `GET /prescriptions` answers **403 insufficient permissions** for this client (same entitlement gap as
     `POST /authorizations/covers`).
   - **`POST /prescriptions/dispense` is singular**; the documented `/prescriptions/dispenses` 404s. It
     validates and reaches the engine, which then asks for a prescription to exist first
     ("Prescription matching query does not exist"). It also refuses `registration_number` for the dispenser
     and wants `National ID` — the only place in the API where a practitioner is identified that way.
   - The dispensing intervention is one per visit, not one per drug: `PMF-12-004` (Public Officers) /
     `SHA-12-004` — "Prescription, drug administration and dispensing".
6. `POST /claims/doctors` validates the practitioner against the Health Worker Registry (upstream
   `edi-api.provider-uat.sha.go.ke`); a made-up registration number is rejected.

## 10. Open questions the portal does not answer

| # | Question | Why it matters |
|---|---|---|
| Q1 | **Closed (UAT 2026-09-20):** two-step. `authorize` without `otp` → PENDING authorization + OTP sent; `visit` verifies. See §9. | — |
| Q2 | **Closed:** `visit` takes one of `otp`, `auth_guid`, `match_id`. | — |
| Q3 | **Response side answered** by the portal examples (`spec/examples.json`, 2026-09-20): `invoices[].lines[]`, `claim_diagnoses[]`, `interventions[]`, `preauthItems[]`, `preauthDoctors[].doctorProfile`, payer `results[]` are all modelled now. **Request side still open** for preauth `items/diagnoses/doctors/attachments` (the example shows `[{}]`). Prescription `items[]` and dispense `actual_products[]/doctors[]` *are* published and the SDK's bodies are asserted against them. | preauth request encoding |
| Q4 | ~~Vocabularies~~ **partly observed** (§9): authorization status/label, claim `DRAFT`/`SUBMITTED`, `claim_auth_status`, invoice states. Preauth `status`/`doctorReviewStatus` and `resubmission_workflow_state` still unobserved. | lenient enums carry unknown values |
| Q5 | Is `POST /claims/submit` idempotent for the same `consent_token`? What happens on a retried submit after a timeout? | Retry policy for the one call that moves money |
| Q6 | Production base URL and rate limits. ~~Token TTL~~ observed 3600 s. | Settings + backoff tuning |
| Q7 | ~~identification_type codes~~ **Answered:** literal strings (`National ID` → `requestIdType: 2`); see §9. Alien/Refugee codes still unobserved. | — |
| Q8 | Multipart fields typed `string` but described as "JSON array" (`diagnoses`, `attachments`, `interventions` on lines/protocols/emt) — exact encoding (JSON string vs repeated fields vs comma-separated). | Serialiser correctness; `/emergency/protocols` says comma-separated while `/claims/lines` says JSON |

Sources to check next: the DHA docs site (`https://hie-docs.dha.go.ke/`) and the public Postman
collection (`https://documenter.getpostman.com/view/39260559/2sB3dSPoWf`), both referenced from the portal bundle.
