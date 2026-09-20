# Emergency

> Source: https://afyaconnect.dha.go.ke/hie-api/eclaims/emergency · API: **eClaims and Preauth APIs** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

Endpoints for emergency case claims and protocols.

## Endpoints

- [`POST /api/v1/claims/doctors`](#post-apiv1claimsdoctors-add-emergency-case-claim-doctor) — Add Emergency Case Claim Doctor
- [`DELETE /api/v1/claims/doctors`](#delete-apiv1claimsdoctors-remove-doctor-from-claim) — Remove doctor from claim
- [`POST /api/v1/claims/emergency`](#post-apiv1claimsemergency-create-emergency-case-claim) — Create Emergency Case Claim
- [`GET /api/v1/claims/emergency/protocols`](#get-apiv1claimsemergencyprotocols-get-emergency-protocols) — Get Emergency Protocols
- [`POST /api/v1/claims/emergency/protocols`](#post-apiv1claimsemergencyprotocols-add-emergency-case-protocol) — Add Emergency Case Protocol
- [`POST /api/v1/claims/emt`](#post-apiv1claimsemt-creates-an-emt-claim) — Creates an EMT claim

---

### `POST /api/v1/claims/doctors` — Add Emergency Case Claim Doctor

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/doctors`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/emergency#add-emergency-case-claim-doctor

Adds a doctor to an existing emergency case claim using their registration or identification details.

**Request body** — `application/json`, required

Emergency claim doctor request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `identification_number` | string | **yes** |  |
| `identification_type` | string | **yes** | Allowed: `registration_number`, `National ID`, `Alien ID`, `Refugee ID` |
| `regulation_body` | string | **yes** | Allowed: `KMPDC`, `COC`, `NCK` |

**Responses**

<details><summary><code>200</code> — Doctor successfully added to claim</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |
| `data` | object | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Missing required fields</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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

### `DELETE /api/v1/claims/doctors` — Remove doctor from claim

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/doctors`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/emergency#remove-doctor-from-claim

Removes a doctor from an authorized claim

**Request body** — `application/json`, required

Emergency claim doctor request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |

**Responses**

<details><summary><code>204</code> — No Content</summary>

_none_

</details>

<details><summary><code>400</code> — Bad Request - Request failed validation</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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

### `POST /api/v1/claims/emergency` — Create Emergency Case Claim

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/emergency`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/emergency#create-emergency-case-claim

This endpoint allows facilities to create a new virtual emergency case claim. Depending on the patient type, the request can be for either an identified or unidentified patient.

**Request body** — `application/json`, required

Emergency visit Request

| Field | Type | Required | Description |
|---|---|---|---|
| `beneficiary_cr_id` | string | no |  |
| `brought_by` | string | **yes** | Allowed: `RELATIVE`, `UNKNOWN`, `SAMARITAN`, `PARAMEDICS` |
| `identification_number` | string | **yes** |  |
| `identification_type` | string | **yes** | Allowed: `registration_number`, `National ID`, `Alien ID`, `Refugee ID` |
| `interventions` | string[] | **yes** |  |
| `mode_of_arrival` | string | **yes** | Allowed: `AMBULANCE`, `WALK-IN`, `OTHER` |
| `notes` | string | no |  |
| `otp` | string | no |  |
| `reference_number` | string | **yes** |  |
| `regulation_body` | string | **yes** | Allowed: `KMPDC`, `COC`, `NCK` |

**Responses**

<details><summary><code>200</code> — Emergency claim created successfully</summary>

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

### `GET /api/v1/claims/emergency/protocols` — Get Emergency Protocols

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/emergency/protocols`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/emergency#get-emergency-protocols

Retrieve a list of emergency protocols from the ILM Adapter API. These define the applicable clinical or management procedures for emergency cases filtered by status, intervention code, and facility details.

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `active` | string | **yes** | Filter intervention if it is still active |
| `intervention_code` | string | **yes** | Intervention applicable to a protocol |

**Responses**

<details><summary><code>200</code> — Emergency protocol retrieved successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `count` | integer | no |  |
| `currentPage` | integer | no |  |
| `endIndex` | integer | no |  |
| `next` | string | no |  |
| `pageSize` | integer | no |  |
| `previous` | string | no |  |
| `results` | object[] | no |  |
| `startIndex` | integer | no |  |
| `totalPages` | integer | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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

### `POST /api/v1/claims/emergency/protocols` — Add Emergency Case Protocol

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/emergency/protocols`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/emergency#add-emergency-case-protocol

This endpoint allows adding a treatment protocol to an existing emergency case claim.

**Request body** — `multipart/form-data`, required

Emergency protocol Request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | Consent token |
| `protocol_code` | string | **yes** | Protocol code |
| `intervention_code` | string | **yes** | Intervention code |
| `unit_price` | number | **yes** | Unit price |
| `quantity` | integer | **yes** | Quantity |
| `diagnoses` | string | no | Comma-separated ICD diagnosis codes |
| `attachments` | string | no | Attachments metadata as JSON |

**Responses**

<details><summary><code>200</code> — Emergency protocol added successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `attributes` | string | no |  |
| `bill_from` | string | no |  |
| `bill_to` | string | no |  |
| `charge_date` | string | no |  |
| `discount` | number | no |  |
| `discount_reason` | string | no |  |
| `doctor_code` | string | no |  |
| `doctor_name` | string | no |  |
| `id` | string | no |  |
| `intervention_code` | string | no |  |
| `invoice` | string | no |  |
| `is_active` | boolean | no |  |
| `is_cancellation` | boolean | no |  |
| `is_return` | boolean | no |  |
| `item_code` | string | no |  |
| `item_name` | string | no |  |
| `line_copay` | number | no |  |
| `line_net_amount` | number | no |  |
| `line_number` | string | no |  |
| `line_total_amount` | number | no |  |
| `linked_invoice_line` | string | no |  |
| `map_request` | string | no |  |
| `map_request_description` | string | no |  |
| `mapped_slade_code` | string | no |  |
| `nhif_rebate_amount` | number | no |  |
| `patient_discount_amount` | number | no |  |
| `patient_net_price` | number | no |  |
| `pmf_line_status` | string | no |  |
| `quantity` | number | no |  |
| `scheme_code` | string | no |  |
| `scheme_name` | string | no |  |
| `sponsor_net_price` | number | no |  |
| `uhc_exceeded` | boolean | no |  |
| `unit` | string | no |  |
| `unit_price` | number | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Missing required fields</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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

### `POST /api/v1/claims/emt` — Creates an EMT claim

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/emt`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/emergency#creates-an-emt-claim

Creates an EMT claim

**Request body** — `multipart/form-data`, required

EMT visit Request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | Consent token |
| `protocol_code` | string | **yes** | Protocol code |
| `case_number` | string | **yes** | Emergency case number |
| `practitioner_reg_number` | string | **yes** | Practitioner registration number |
| `beneficiary_cr_id` | string | **yes** | Patient (beneficiary) CR identifier |
| `otp` | string | **yes** | One-time password for patient verification |
| `provider_registration_number` | string | **yes** | Ambulance / EMT provider registration number |
| `diagnoses` | string | **yes** | JSON array of ICD diagnosis codes |
| `interventions` | string | **yes** | JSON array of intervention codes |
| `attachments` | string | no | JSON metadata; entries reference uploaded form file fields |

**Responses**

<details><summary><code>200</code> — EMT claim created successfully</summary>

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

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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
