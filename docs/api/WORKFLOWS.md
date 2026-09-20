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
   POST  /claims/lines   (multipart)    {intervention_code, unit_price, quantity, scheme_code?, charge_date?, diagnoses?, attachments?}
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

## 10. Open questions the portal does not answer

| # | Question | Why it matters |
|---|---|---|
| Q1 | **Closed (UAT 2026-09-20):** two-step. `authorize` without `otp` → PENDING authorization + OTP sent; `visit` verifies. See §9. | — |
| Q2 | **Closed:** `visit` takes one of `otp`, `auth_guid`, `match_id`. | — |
| Q3 | **Response side answered** by the portal examples (`spec/examples.json`, 2026-09-20): `invoices[].lines[]`, `claim_diagnoses[]`, `interventions[]`, `preauthItems[]`, `preauthDoctors[].doctorProfile`, payer `results[]` are all modelled now. **Request side still open** for preauth `items/diagnoses/doctors/attachments` (the example shows `[{}]`). Prescription `items[]` and dispense `actual_products[]/doctors[]` *are* published and the SDK's bodies are asserted against them. | preauth request encoding |
| Q4 | Vocabulary of `workflow_state`, `claim_auth_status`, `resubmission_workflow_state`, authorization `status`, preauth `status`/`doctorReviewStatus`, eligibility `statusCode`. | Status enums; must include `Unknown(raw)` fallback |
| Q5 | Is `POST /claims/submit` idempotent for the same `consent_token`? What happens on a retried submit after a timeout? | Retry policy for the one call that moves money |
| Q6 | Production base URL and rate limits. ~~Token TTL~~ observed 3600 s. | Settings + backoff tuning |
| Q7 | ~~identification_type codes~~ **Answered:** literal strings (`National ID` → `requestIdType: 2`); see §9. Alien/Refugee codes still unobserved. | — |
| Q8 | Multipart fields typed `string` but described as "JSON array" (`diagnoses`, `attachments`, `interventions` on lines/protocols/emt) — exact encoding (JSON string vs repeated fields vs comma-separated). | Serialiser correctness; `/emergency/protocols` says comma-separated while `/claims/lines` says JSON |

Sources to check next: the DHA docs site (`https://hie-docs.dha.go.ke/`) and the public Postman
collection (`https://documenter.getpostman.com/view/39260559/2sB3dSPoWf`), both referenced from the portal bundle.
