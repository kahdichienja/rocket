# Billing

> Source: https://afyaconnect.dha.go.ke/hie-api/eclaims/billing · API: **eClaims and Preauth APIs** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

Endpoints for billing and invoice management.

## Endpoints

- [`POST /api/v1/claims/attachments`](#post-apiv1claimsattachments-add-virtual-claim-attachment) — Add virtual Claim Attachment
- [`PATCH /api/v1/claims/attachments`](#patch-apiv1claimsattachments-remove-virtual-claim-attachment) — Remove Virtual Claim Attachment
- [`POST /api/v1/claims/diagnoses`](#post-apiv1claimsdiagnoses-add-a-diagnosis-to-an-existing-virtual-claim) — Add a diagnosis to an existing virtual claim.
- [`PATCH /api/v1/claims/diagnoses`](#patch-apiv1claimsdiagnoses-remove-virtual-claim-diagnosis) — Remove Virtual Claim Diagnosis
- [`POST /api/v1/claims/lines`](#post-apiv1claimslines-add-billing-line-item-to-virtual-claim) — Add billing line item to virtual claim.
- [`PATCH /api/v1/claims/lines`](#patch-apiv1claimslines-remove-virtual-claim-line) — Remove Virtual Claim Line
- [`PATCH /api/v1/claims/lines/edit`](#patch-apiv1claimslinesedit-edit-virtual-claim-line) — Edit Virtual Claim Line
- [`POST /api/v1/claims/lines/resubmit`](#post-apiv1claimslinesresubmit-resubmit-a-claim-line) — Resubmit a claim line
- [`POST /api/v1/claims/preview`](#post-apiv1claimspreview-preview-claim) — Preview Claim
- [`GET /api/v1/claims/preview/payer`](#get-apiv1claimspreviewpayer-preview-payer-claim) — Preview Payer Claim
- [`GET /api/v1/patients/pomsf-balances`](#get-apiv1patientspomsf-balances-get-pomsf-balances-for-a-patient) — Get POMSF balances for a patient
- [`POST /api/v1/uploads`](#post-apiv1uploads-upload-a-file) — Upload a file
- [`GET /api/v1/uploads/{file_id}`](#get-apiv1uploadsfile_id-get-file-download-url) — Get file download URL

---

### `POST /api/v1/claims/attachments` — Add virtual Claim Attachment

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/attachments`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#add-virtual-claim-attachment

This endpoint allows addition of an attachment associated with a claim

**Request body** — `multipart/form-data`, required

Add claim attachment request input

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | Consent token |
| `file_blob` | string (binary) | **yes** | Attachment file |
| `document_type` | string | **yes** | Document type Allowed: `BIO_DETAILS`, `BIRTH_NOTIFICATION`, `CARE_PLAN`, `CASE_NOTE`, `CASE_SUMMARY`, `CERTIFIED_BURIAL_PERMIT`, `CERTIFIED_COPY_OF_DECEASED_ID`, `CLAIM_FORM`, `COVER_LETTER_FROM_EMPLOYER`, `CRITICAL_CARE_UNIT_CASE`, `CT_SCAN`, `DEATH_NOTICE`, `DIALYSIS_CHART`, `DISCHARGE_SUMMARY`, `ENTRY_EXIT_VISA_STAMP`, `FINAL_BILL`, `IMAGING_ORDER`, `IMAGING_REPORT`, `INVOICE`, `LAB_ORDER`, `LAB_RESULTS`, `MAGNETIC_RESONANCE_IMAGING`, `MEDICAL_REPORT`, `OTHER`, `POST_SERVICE_IMAGING_REPORT`, `PRE_SERVICE_IMAGING_REPORT`, `PREAUTH_FORM`, `PRESCRIPTION`, `REQUEST_FORM_BY_RELEVANT_CONSULTANT`, `RHESUS_FACTOR`, `THEATRE_NOTES` |
| `intervention_code` | string | **yes** | Intervention code |

**Responses**

<details><summary><code>200</code> — Claim attachment added successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `attachment` | string | no |  |
| `attachment_type` | string | no |  |
| `claim` | string | no |  |
| `data` | string | no |  |
| `debug_data` | string | no |  |
| `description` | string | no |  |
| `id` | string | no |  |
| `intervention_code` | string | no |  |
| `last_retry` | string | no |  |
| `retry_count` | integer | no |  |
| `title` | string | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

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

### `PATCH /api/v1/claims/attachments` — Remove Virtual Claim Attachment

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/attachments`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#remove-virtual-claim-attachment

Removes a specific attachment from a virtual claim.

**Request body** — `application/json`, required

Remove claim attachment request input

| Field | Type | Required | Description |
|---|---|---|---|
| `attachment_id` | string | **yes** |  |
| `consent_token` | string | **yes** |  |
| `intervention_code` | string | **yes** |  |

**Responses**

<details><summary><code>200</code> — Claim attachment removed successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

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

### `POST /api/v1/claims/diagnoses` — Add a diagnosis to an existing virtual claim.

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/diagnoses`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#add-a-diagnosis-to-an-existing-virtual-claim

Links a diagnosis to a specific intervention within a virtual claim. Uses ICD codes to capture the patient’s condition for billing and reporting purposes.

**Request body** — `application/json`, required

Add diagnosis request input

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `facilityID` | string | no |  |
| `facilityIDType` | string | no |  |
| `icd_code` | string | **yes** |  |
| `intervention_code` | string | **yes** |  |

**Responses**

<details><summary><code>200</code> — diagnosis added successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `claim` | string | no |  |
| `claim_diagnosis_id` | integer | no |  |
| `diagnosis` | string | no |  |
| `diagnosis_code` | string | no |  |
| `diagnosis_name` | string | no |  |
| `edi_claim_diagnosis_guid` | string | no |  |
| `edi_claim_diagnosis_replicated` | string | no |  |
| `intervention_code` | string | no |  |
| `is_flagged_diagnosis` | boolean | no |  |
| `is_inpatient` | boolean | no |  |
| `original_visit_date` | string | no |  |
| `patient_number` | string | no |  |
| `recorded_on` | string | no |  |
| `site_code` | string | no |  |
| `site_code_type` | string | no |  |
| `visit_number` | string | no |  |

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

### `PATCH /api/v1/claims/diagnoses` — Remove Virtual Claim Diagnosis

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/diagnoses`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#remove-virtual-claim-diagnosis

Removes a diagnosis linked to a virtual claim for a specific beneficiary.

**Request body** — `application/json`, required

Remove claim diagnosis request input

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `icd_code` | string | **yes** |  |
| `intervention_code` | string | **yes** |  |

**Responses**

<details><summary><code>200</code> — Claim diagnosis removed successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

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

### `POST /api/v1/claims/lines` — Add billing line item to virtual claim.

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/lines`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#add-billing-line-item-to-virtual-claim

Adds a line item to an existing virtual claim’s invoice. Requires intervention details, pricing, and quantity to record the service or item billed.

**Request body** — `multipart/form-data`, required

Add claim line item request input

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | Consent token |
| `intervention_code` | string | **yes** | Intervention code |
| `unit_price` | number | **yes** | Unit price |
| `quantity` | number | **yes** | Quantity |
| `scheme_code` | string | no | Scheme code |
| `charge_date` | string | no | Charge date |
| `diagnoses` | string | no | JSON array of ICD diagnosis codes |
| `attachments` | string | no | Attachments metadata as JSON |

**Responses**

<details><summary><code>200</code> — Claim line item added successfully</summary>

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

<details><summary><code>400</code> — Bad Request - Missing required fields or invalid request</summary>

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

### `PATCH /api/v1/claims/lines` — Remove Virtual Claim Line

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/lines`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#remove-virtual-claim-line

Removes a specific claim line from a virtual claim using its GUID.

**Request body** — `application/json`, required

Remove claim line request input

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `line_guid` | string | **yes** |  |

**Responses**

<details><summary><code>200</code> — Claim line removed successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

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

### `PATCH /api/v1/claims/lines/edit` — Edit Virtual Claim Line

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/lines/edit`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#edit-virtual-claim-line

Edit a virtual claim line item before resubmitting the invoice. This endpoint allows modification of  unit price and quantity of a specific line item in a virtual claim after payer review.

**Request body** — `application/json`, required

Edit claim line request input

| Field | Type | Required | Description |
|---|---|---|---|
| `line_id` | string | **yes** |  |
| `quantity` | integer | no |  |
| `scheme_code` | string | no |  |
| `unit_price` | string | no |  |

**Responses**

<details><summary><code>200</code> — Claim line edited successfully</summary>

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

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

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

### `POST /api/v1/claims/lines/resubmit` — Resubmit a claim line

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/lines/resubmit`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#resubmit-a-claim-line

Resubmit a previously failed or rejected claim line for processing

**Request body** — `application/json`, required

Resubmit claim line request input

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |

**Responses**

<details><summary><code>200</code> — Claim line resubmitted successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `line_id` | string | no |  |
| `message` | string | no |  |
| `resubmitted_at` | string | no |  |
| `status` | string | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

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

### `POST /api/v1/claims/preview` — Preview Claim

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/preview`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#preview-claim

Previews a claim using the provided consent token before final submission. This allows the provider to verify claim details.

**Request body** — `application/json`, required

Preview claim request input

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |

**Responses**

<details><summary><code>200</code> — Claim preview retrieved successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `authorization_code` | string | no |  |
| `claim_attachments` | object[] | no |  |
| `claim_attachments_count` | integer | no |  |
| `claim_auth_status` | string | no |  |
| `claim_diagnoses` | object[] | no |  |
| `created_by_name` | string | no |  |
| `diagnoses_count` | integer | no |  |
| `id` | string | no |  |
| `interventions` | object[] | no |  |
| `invoice_attachments_count` | integer | no |  |
| `invoices` | object[] | no |  |
| `is_negative` | boolean | no |  |
| `is_zero` | boolean | no |  |
| `member_number` | string | no |  |
| `number_of_invoices` | integer | no |  |
| `patient_name` | string | no |  |
| `patient_number` | string | no |  |
| `provider_name` | string | no |  |
| `scheme_code` | string | no |  |
| `scheme_name` | string | no |  |
| `service_type` | string | no |  |
| `total_claim_amount` | number | no |  |
| `total_claim_copay` | number | no |  |
| `total_claim_discount` | number | no |  |
| `total_claim_net_amount` | number | no |  |
| `total_claim_splits` | number | no |  |
| `visit_end` | string | no |  |
| `visit_start` | string | no |  |
| `workflow_state` | string | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

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

### `GET /api/v1/claims/preview/payer` — Preview Payer Claim

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/preview/payer`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#preview-payer-claim

This endpoint allows the user to preview the claim that has been sennt to the payer. It provides a way to check the claim status as seen from payer.

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `guid` | string | **yes** | Claim GUID |
| `provider_claim_no` | string | **yes** | Provider claim number |

**Responses**

<details><summary><code>200</code> — Payer claim preview retrieved successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `pageSize` | integer | no |  |
| `results` | object[] | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

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

### `GET /api/v1/patients/pomsf-balances` — Get POMSF balances for a patient

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/pomsf-balances`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#get-pomsf-balances-for-a-patient

Retrieves Public Officers Medical Scheme Fund balances for a civil servant patient

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `patient_id` | string | **yes** | Patient's POMSF member number (CR number) |
| `policy_year` | string | **yes** | The policy year for which you want to fetch the balances |
| `principal_member_number` | string | no | Patient principal POMSF member number (CR number) |

**Responses**

<details><summary><code>200</code> — OK</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `dateOfBirth` | string | no |  |
| `email` | string | no |  |
| `familyMembers` | object[] | no |  |
| `firstName` | string | no |  |
| `gender` | string | no |  |
| `householdId` | string | no |  |
| `id` | string | no |  |
| `lastName` | string | no |  |
| `memberNumber` | string | no |  |
| `memberPolicies` | object[] | no |  |
| `middleName` | string | no |  |
| `nationalId` | string | no |  |
| `parentNumber` | string | no |  |
| `phone` | string | no |  |
| `phoneCode` | string | no |  |
| `policyCount` | integer | no |  |
| `registeredOn` | string | no |  |
| `relationshipType` | string | no |  |
| `schemeCount` | integer | no |  |
| `shaNumber` | string | no |  |
| `title` | string | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Missing query parameters or invalid request input</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>


---

### `POST /api/v1/uploads` — Upload a file

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/uploads`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#upload-a-file

Uploads a file and returns its storage path

**Request body** — `multipart/form-data`, required

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | string (binary) | **yes** | File to upload |

**Responses**

<details><summary><code>200</code> — File stored successfully</summary>

_none_

</details>

<details><summary><code>400</code> — Bad Request - Failed to parse or read file</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>

<details><summary><code>500</code> — Internal Server Error - Failed to store file</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>


---

### `GET /api/v1/uploads/{file_id}` — Get file download URL

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/uploads/{file_id}`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/billing#get-file-download-url

Generates a pre-signed download URL for a previously uploaded file.

**Path parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `file_id` | string | **yes** | File ID returned when the file was uploaded |

**Responses**

<details><summary><code>200</code> — Pre-signed URL generated successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |

</details>

<details><summary><code>400</code> — Bad request - file_id is required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>403</code> — Forbidden - tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>

<details><summary><code>500</code> — Internal server error - failed to generate download URL</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>


---
