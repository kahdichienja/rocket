# Start Visit Consent

> Source: https://afyaconnect.dha.go.ke/hie-api/eclaims/start-visit-consent · API: **eClaims and Preauth APIs** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

Endpoints for managing visit consent and OTP verification.

## Endpoints

- [`POST /api/v1/claims/visit`](#post-apiv1claimsvisit-create-new-virtual-claim) — Create new virtual claim

---

### `POST /api/v1/claims/visit` — Create new virtual claim

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/visit`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/start-visit-consent#create-new-virtual-claim

Creates a new virtual claim for a beneficiary after verifying their consent. Use the OTP strategy when consent was captured via a one-time password, or the biometrics strategy when consent was captured via eKYC or fingerprint — in which case the authorization GUID from POST /api/v1/claims/authorize is passed instead of an OTP.

**Request body** — `application/json`, required

Visit request payload. Choose one strategy: OTP (one-time password consent) or Biometrics (authorization GUID from a preceding biometric authorization).

| Field | Type | Required | Description |
|---|---|---|---|
| `intervention_codes` | string[] | **yes** | Intervention code(s) for the service scheduled to be offered. |
| `patient_id` | string | **yes** | Client Registry identifier of the beneficiary associated with the patient. |
| `service_type` | string | **yes** | Type of service being initiated. Allowed: `CAPITATION`, `OUTPATIENT`, `INPATIENT`, `EMERGENCY` |
| `otp` | string | **yes** | One-time password sent to the beneficiary's registered contact. |

**Responses**

<details><summary><code>200</code> — Visit started successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `admitted_on` | string | no |  |
| `appointment_number` | string | no |  |
| `attributes` | string | no |  |
| `authorization_code` | string | no |  |
| `authorization_guid` | string | no |  |
| `beneficiary_guid` | string | no |  |
| `beneficiary_id` | integer | no |  |
| `beneficiary_is_fuzzy_matched` | boolean | no |  |
| `cancel_reason_text` | string | no |  |
| `cancel_reason_type` | string | no |  |
| `claim_attachments_count` | integer | no |  |
| `claim_auth_status` | string | no |  |
| `claim_diagnoses` | object[] | no |  |
| `claim_id` | integer | no |  |
| `created_by_name` | string | no |  |
| `currency` | string | no |  |
| `diagnoses_count` | integer | no |  |
| `discharge_cancel_date` | string | no |  |
| `discharge_cancel_remarks` | string | no |  |
| `discharge_reason` | string | no |  |
| `discharged_on` | string | no |  |
| `edi_claim_guid` | string | no |  |
| `emergency_visit_expiry` | string | no |  |
| `estimate_ip_days` | integer | no |  |
| `expected_discharge_date` | string | no |  |
| `has_reviewed_claim` | boolean | no |  |
| `id` | string | no |  |
| `initial_intervention` | string | no |  |
| `interventions` | object[] | no |  |
| `invoice_attachments_count` | integer | no |  |
| `invoice_id` | string | no |  |
| `invoice_number` | string | no |  |
| `invoices` | object[] | no |  |
| `is_charge_master_mapped` | boolean | no |  |
| `is_negative` | boolean | no |  |
| `is_resubmitted` | boolean | no |  |
| `is_zero` | boolean | no |  |
| `last_retry` | string | no |  |
| `location_code` | string | no |  |
| `location_name` | string | no |  |
| `member_name` | string | no |  |
| `member_number` | string | no |  |
| `member_number_has_token` | boolean | no |  |
| `mode_of_arrival` | string | no |  |
| `nhif_number` | string | no |  |
| `notes` | string | no |  |
| `number_of_invoices` | integer | no |  |
| `patient_name` | string | no |  |
| `patient_number` | string | no |  |
| `payer_code` | string | no |  |
| `payer_name` | string | no |  |
| `payer_slade_code` | string | no |  |
| `policy_number` | string | no |  |
| `policy_valid_from` | string | no |  |
| `policy_valid_to` | string | no |  |
| `provider_name` | string | no |  |
| `provider_slade_code` | string | no |  |
| `reason_for_unknown_patient` | string | no |  |
| `reference_number` | string | no |  |
| `resubmission_workflow_state` | string | no |  |
| `retry_count` | integer | no |  |
| `scheme_code` | string | no |  |
| `scheme_name` | string | no |  |
| `service_type` | string | no |  |
| `total_claim_amount` | number | no |  |
| `total_claim_copay` | number | no |  |
| `total_claim_discount` | number | no |  |
| `total_claim_net_amount` | number | no |  |
| `total_claim_splits` | number | no |  |
| `updated_by_name` | string | no |  |
| `visit_end` | string | no |  |
| `visit_number` | string | no |  |
| `visit_start` | string | no |  |
| `workflow_state` | string | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Missing required fields</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>


---
