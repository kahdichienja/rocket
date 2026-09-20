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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "file_blob": "<binary>",
  "document_type": "BIO_DETAILS",
  "intervention_code": "intervention_code"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/attachments' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: multipart/form-data' \
  --form consent_token=consent_token \
  --form file_blob=<binary> \
  --form document_type=BIO_DETAILS \
  --form intervention_code=intervention_code
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "attachment": "attachment",
  "attachment_type": "attachment_type",
  "claim": "claim",
  "data": "data",
  "debug_data": "debug_data",
  "description": "description",
  "id": "id",
  "intervention_code": "intervention_code",
  "last_retry": "last_retry",
  "retry_count": 0,
  "title": "title"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>Example request body</summary>

```json
{
  "attachment_id": "attachment_id",
  "consent_token": "consent_token",
  "intervention_code": "intervention_code"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request PATCH \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/attachments' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "attachment_id": "attachment_id",
  "consent_token": "consent_token",
  "intervention_code": "intervention_code"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Claim attachment removed successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "data": {},
  "message": "message"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "facilityID": "facilityID",
  "facilityIDType": "facilityIDType",
  "icd_code": "icd_code",
  "intervention_code": "intervention_code"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/diagnoses' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "facilityID": "facilityID",
  "facilityIDType": "facilityIDType",
  "icd_code": "icd_code",
  "intervention_code": "intervention_code"
}'
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "claim": "claim",
  "claim_diagnosis_id": 0,
  "diagnosis": "diagnosis",
  "diagnosis_code": "diagnosis_code",
  "diagnosis_name": "diagnosis_name",
  "edi_claim_diagnosis_guid": "edi_claim_diagnosis_guid",
  "edi_claim_diagnosis_replicated": "edi_claim_diagnosis_replicated",
  "intervention_code": "intervention_code",
  "is_flagged_diagnosis": true,
  "is_inpatient": true,
  "original_visit_date": "original_visit_date",
  "patient_number": "patient_number",
  "recorded_on": "recorded_on",
  "site_code": "site_code",
  "site_code_type": "site_code_type",
  "visit_number": "visit_number"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Missing required fields</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "icd_code": "icd_code",
  "intervention_code": "intervention_code"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request PATCH \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/diagnoses' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "icd_code": "icd_code",
  "intervention_code": "intervention_code"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Claim diagnosis removed successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "data": {},
  "message": "message"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "intervention_code": "intervention_code",
  "unit_price": 0,
  "quantity": 0,
  "scheme_code": "scheme_code",
  "charge_date": "charge_date",
  "diagnoses": "diagnoses",
  "attachments": "attachments"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/lines' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: multipart/form-data' \
  --form consent_token=consent_token \
  --form intervention_code=intervention_code \
  --form unit_price=0 \
  --form quantity=0 \
  --form scheme_code=scheme_code \
  --form charge_date=charge_date \
  --form diagnoses=diagnoses \
  --form attachments=attachments
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "attributes": "attributes",
  "bill_from": "bill_from",
  "bill_to": "bill_to",
  "charge_date": "charge_date",
  "discount": 0,
  "discount_reason": "discount_reason",
  "doctor_code": "doctor_code",
  "doctor_name": "doctor_name",
  "id": "id",
  "intervention_code": "intervention_code",
  "invoice": "invoice",
  "is_active": true,
  "is_cancellation": true,
  "is_return": true,
  "item_code": "item_code",
  "item_name": "item_name",
  "line_copay": 0,
  "line_net_amount": 0,
  "line_number": "line_number",
  "line_total_amount": 0,
  "linked_invoice_line": "linked_invoice_line",
  "map_request": "map_request",
  "map_request_description": "map_request_description",
  "mapped_slade_code": "mapped_slade_code",
  "nhif_rebate_amount": 0,
  "patient_discount_amount": 0,
  "patient_net_price": 0,
  "pmf_line_status": "pmf_line_status",
  "quantity": 0,
  "scheme_code": "scheme_code",
  "scheme_name": "scheme_name",
  "sponsor_net_price": 0,
  "uhc_exceeded": true,
  "unit": "unit",
  "unit_price": 0
}
```

</details>

<details><summary><code>400</code> — Bad Request - Missing required fields or invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "line_guid": "line_guid"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request PATCH \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/lines' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "line_guid": "line_guid"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Claim line removed successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "data": {},
  "message": "message"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>Example request body</summary>

```json
{
  "line_id": "line_id",
  "quantity": 0,
  "scheme_code": "scheme_code",
  "unit_price": "unit_price"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request PATCH \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/lines/edit' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "line_id": "line_id",
  "quantity": 0,
  "scheme_code": "scheme_code",
  "unit_price": "unit_price"
}'
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "attributes": "attributes",
  "bill_from": "bill_from",
  "bill_to": "bill_to",
  "charge_date": "charge_date",
  "discount": 0,
  "discount_reason": "discount_reason",
  "doctor_code": "doctor_code",
  "doctor_name": "doctor_name",
  "id": "id",
  "intervention_code": "intervention_code",
  "invoice": "invoice",
  "is_active": true,
  "is_cancellation": true,
  "is_return": true,
  "item_code": "item_code",
  "item_name": "item_name",
  "line_copay": 0,
  "line_net_amount": 0,
  "line_number": "line_number",
  "line_total_amount": 0,
  "linked_invoice_line": "linked_invoice_line",
  "map_request": "map_request",
  "map_request_description": "map_request_description",
  "mapped_slade_code": "mapped_slade_code",
  "nhif_rebate_amount": 0,
  "patient_discount_amount": 0,
  "patient_net_price": 0,
  "pmf_line_status": "pmf_line_status",
  "quantity": 0,
  "scheme_code": "scheme_code",
  "scheme_name": "scheme_name",
  "sponsor_net_price": 0,
  "uhc_exceeded": true,
  "unit": "unit",
  "unit_price": 0
}
```

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/lines/resubmit' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Claim line resubmitted successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `line_id` | string | no |  |
| `message` | string | no |  |
| `resubmitted_at` | string | no |  |
| `status` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "line_id": "line_id",
  "message": "message",
  "resubmitted_at": "resubmitted_at",
  "status": "status"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/preview' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token"
}'
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "authorization_code": "authorization_code",
  "claim_attachments": [
    {
      "attachment": "attachment",
      "attachment_type": "attachment_type",
      "claim": "claim",
      "data": "data",
      "debug_data": "debug_data",
      "description": "description",
      "id": "id",
      "intervention_code": "intervention_code",
      "last_retry": "last_retry",
      "retry_count": 0,
      "title": "title"
    }
  ],
  "claim_attachments_count": 0,
  "claim_auth_status": "claim_auth_status",
  "claim_diagnoses": [
    {
      "claim": "claim",
      "claim_diagnosis_id": 0,
      "diagnosis": "diagnosis",
      "diagnosis_code": "diagnosis_code",
      "diagnosis_name": "diagnosis_name",
      "edi_claim_diagnosis_guid": "edi_claim_diagnosis_guid",
      "edi_claim_diagnosis_replicated": "edi_claim_diagnosis_replicated",
      "intervention_code": "intervention_code",
      "is_flagged_diagnosis": true,
      "is_inpatient": true,
      "original_visit_date": "original_visit_date",
      "patient_number": "patient_number",
      "recorded_on": "recorded_on",
      "site_code": "site_code",
      "site_code_type": "site_code_type",
      "visit_number": "visit_number"
    }
  ],
  "created_by_name": "created_by_name",
  "diagnoses_count": 0,
  "id": "id",
  "interventions": [
    {
      "accrued_per_diem_amount": 0,
      "accrued_per_diem_days": 0,
      "active_for_uhc": true,
      "applicable_document_types": [
        "string"
      ],
      "bill_from": "bill_from",
      "bill_to": "bill_to",
      "id": "id",
      "intervention_code": "intervention_code",
      "intervention_fund": "intervention_fund",
      "intervention_name": "intervention_name",
      "intervention_overall_tariff": 0,
      "intervention_payment_mechanism": "intervention_payment_mechanism",
      "is_switched_intervention": true,
      "keph_level_tarrif": 0,
      "needs_preauth": true,
      "optional_document_type": [
        "string"
      ],
      "optional_preauth_document_types": [
        "string"
      ],
      "preauth_exist": true,
      "required_preauth_document_types": [
        "string"
      ],
      "requires_oncology_preauth": true,
      "requires_optical_preauth": true,
      "requires_radiology_preauth": true,
      "requires_renal_preauth": true,
      "requires_surgical_preauth": true,
      "sub_benefit_code": "sub_benefit_code",
      "supported_scheme": "supported_scheme",
      "switched_intervention_id": 0,
      "switched_lines_retained": true,
      "workflow_state": "workflow_state"
    }
  ],
  "invoice_attachments_count": 0,
  "invoices": [
    {
      "created_by_name": "created_by_name",
      "department": "department",
      "discount_amount": 0,
      "dispatch_batch_number": "dispatch_batch_number",
      "dispatch_status": "dispatch_status",
      "doctors": [
        {}
      ],
      "edi_invoice_guid": "edi_invoice_guid",
      "edi_invoice_id": 0,
      "id": "id",
      "invoice_date": "invoice_date",
      "invoice_flags": [
        {}
      ],
      "invoice_number": "invoice_number",
      "invoice_type": "invoice_type",
      "lines": [
        {}
      ],
      "linked_invoice": "linked_invoice",
      "linked_invoice_line": "linked_invoice_line",
      "member_name": "member_name",
      "patient_name": "patient_name",
      "patient_number": "patient_number",
      "provider_invoice_ref": "provider_invoice_ref",
      "provider_name": "provider_name",
      "scheme_code": "scheme_code",
      "scheme_name": "scheme_name",
      "scu_branch_id": "scu_branch_id",
      "scu_dispatch_timestamp": "scu_dispatch_timestamp",
      "scu_receipt_signature": "scu_receipt_signature",
      "service_type": "service_type",
      "total_inv_amount": 0,
      "total_inv_copay": 0,
      "total_inv_discount": 0,
      "total_inv_net_amount": 0,
      "visit_end": "visit_end",
      "visit_start": "visit_start",
      "workflow_state": "workflow_state"
    }
  ],
  "is_negative": true,
  "is_zero": true,
  "member_number": "member_number",
  "number_of_invoices": 0,
  "patient_name": "patient_name",
  "patient_number": "patient_number",
  "provider_name": "provider_name",
  "scheme_code": "scheme_code",
  "scheme_name": "scheme_name",
  "service_type": "service_type",
  "total_claim_amount": 0,
  "total_claim_copay": 0,
  "total_claim_discount": 0,
  "total_claim_net_amount": 0,
  "total_claim_splits": 0,
  "visit_end": "visit_end",
  "visit_start": "visit_start",
  "workflow_state": "workflow_state"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/preview/payer?guid=%3Cguid%3E&provider_claim_no=%3Cprovider_claim_no%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — Payer claim preview retrieved successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `pageSize` | integer | no |  |
| `results` | object[] | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "pageSize": 0,
  "results": [
    {
      "actualDeductableCopay": 0,
      "authToken": "authToken",
      "authorization": {
        "authCode": "authCode",
        "authorizationReason": "authorizationReason",
        "authorizationType": [
          "string"
        ],
        "beneficiaryCode": "beneficiaryCode",
        "beneficiaryJoinDate": "beneficiaryJoinDate",
        "beneficiaryName": "beneficiaryName",
        "beneficiaryNumber": "beneficiaryNumber",
        "beneficiaryScheme": "beneficiaryScheme",
        "benefitType": "benefitType",
        "created": "created",
        "createdByName": "createdByName",
        "currentAvailableBalance": 0,
        "expiry": "expiry",
        "guid": "guid",
        "id": 0,
        "interventions": [
          {}
        ],
        "isComplete": true,
        "isElective": true,
        "isOpen": true,
        "label": "label",
        "needsPreauth": true,
        "notes": "notes",
        "overallPreauthFinalised": true,
        "owner": 0,
        "parentAuthorization": 0,
        "parentPreauth": {
          "accessPoint": "accessPoint",
          "anaesthesiaType": "anaesthesiaType",
          "authorization": null,
          "authorizationDetails": null,
          "beneficiaryDetails": null,
          "carcinomaStaging": "carcinomaStaging",
          "clinicalIndications": "clinicalIndications",
          "comorbidity": "comorbidity",
          "conditionCause": "conditionCause",
          "conditionEmploymentRelated": null,
          "conditionOtherRelated": null,
          "costPerSession": "costPerSession",
          "countdown": null,
          "createdByName": "createdByName",
          "description": "description",
          "doctorApproved": null,
          "doctorReviewStatus": "doctorReviewStatus",
          "finalApprovedAmount": null,
          "guid": "guid",
          "id": null,
          "interventionCode": "interventionCode",
          "interventionData": null,
          "isElective": null,
          "isEmergency": null,
          "isHmisPreauth": null,
          "isOncology": null,
          "isOptical": null,
          "isRadiology": null,
          "isRenal": null,
          "isRequestPhase": null,
          "isResponsePhase": null,
          "isSurgical": null,
          "lengthOfStay": null,
          "memberIdentifier": "memberIdentifier",
          "memberIsVip": null,
          "memberIsVvip": null,
          "memberName": "memberName",
          "memberScheme": "memberScheme",
          "metastases": "metastases",
          "needsDoctorApproval": null,
          "numberOfPreauthDoctorsRequired": null,
          "otherMetastases": "otherMetastases",
          "payerIdentifier": "payerIdentifier",
          "payerInvoiceNo": "payerInvoiceNo",
          "payerName": "payerName",
          "preauthAttachments": null,
          "preauthDiagnoses": null,
          "preauthDoctors": null,
          "preauthFlags": null,
          "preauthItems": null,
          "preauthNotes": null,
          "preauthType": "preauthType",
          "providerConsent": null,
          "providerCurrency": "providerCurrency",
          "providerDetails": null,
          "providerName": "providerName",
          "providerNotificationEmail": "providerNotificationEmail",
          "reasonForAcuteDialysis": "reasonForAcuteDialysis",
          "reasonForSelectingOther": "reasonForSelectingOther",
          "requestExtraData": null,
          "responseExtraData": "responseExtraData",
          "serviceEnd": "serviceEnd",
          "serviceStart": "serviceStart",
          "sessionExpectedDate": "sessionExpectedDate",
          "sessionType": "sessionType",
          "sessionsFrequency": "sessionsFrequency",
          "sessionsRequired": null,
          "status": "status",
          "submissionDateIn_EAT": "submissionDateIn_EAT",
          "token": "token",
          "totalEstimatedAmountForPreauth": null,
          "totalInterimApprovedAmountForPreauth": null,
          "updatedByName": "updatedByName"
        },
        "parentType": "parentType",
        "policyEffectiveDate": "policyEffectiveDate",
        "preauthIds": [
          0
        ],
        "providerName": "providerName",
        "requestedBy": "requestedBy",
        "sessionType": "sessionType",
        "status": "status",
        "token": "token",
        "totalAuthorizedAmount": 0
      },
      "billFrom": "billFrom",
      "billTo": "billTo",
      "claimAttachments": [
        {}
      ],
      "claimFlags": [
        {}
      ],
      "claimLines": [
        {}
      ],
      "claimNotes": [
        {}
      ],
      "claimTransitions": [
        {}
      ],
      "claimType": "claimType",
      "created": "created",
      "diagnoses": [
        {}
      ],
      "encounter": 0,
      "guid": "guid",
      "id": 0,
      "isCreditNote": true,
      "isInpatient": true,
      "memberName": "memberName",
      "memberNumber": "memberNumber",
      "owner": 0,
      "proposedValue": 0,
      "proposedValueLessCopays": 0,
      "providerClaimNo": "providerClaimNo",
      "providerName": "providerName",
      "schemeName": "schemeName",
      "totalCopayValue": 0,
      "trackingNumber": "trackingNumber",
      "workflowDisplayName": "workflowDisplayName",
      "workflowState": "workflowState"
    }
  ]
}
```

</details>

<details><summary><code>400</code> — Bad Request - Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Service error occurred</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/pomsf-balances?patient_id=%3Cpatient_id%3E&policy_year=%3Cpolicy_year%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "dateOfBirth": "dateOfBirth",
  "email": "email",
  "familyMembers": [
    {
      "dateOfBirth": "dateOfBirth",
      "email": "email",
      "firstName": "firstName",
      "gender": "gender",
      "householdId": "householdId",
      "isActive": true,
      "lastName": "lastName",
      "memberNumber": "memberNumber",
      "middleName": "middleName",
      "nationalId": "nationalId",
      "parentNumber": "parentNumber",
      "phone": "phone",
      "phoneCode": "phoneCode",
      "relationshipType": "relationshipType",
      "schemeCount": 0,
      "shaNumber": "shaNumber",
      "title": "title"
    }
  ],
  "firstName": "firstName",
  "gender": "gender",
  "householdId": "householdId",
  "id": "id",
  "lastName": "lastName",
  "memberNumber": "memberNumber",
  "memberPolicies": [
    {
      "benefit": [
        {}
      ],
      "dependentCount": [
        "string"
      ],
      "joinDate": "joinDate",
      "leaveDate": "leaveDate",
      "memberOriginalJoinDate": "memberOriginalJoinDate",
      "parentMemberNumber": "parentMemberNumber",
      "policy": {
        "PolicyYear": "PolicyYear",
        "activeDate": "activeDate",
        "companyName": "companyName",
        "description": "description",
        "endDate": "endDate",
        "hasHospitalCodes": true,
        "hasICD10Code": true,
        "hasImagingServices": true,
        "hasIncludeandExclude": true,
        "hasLabtests": true,
        "hasMedicalprocedures": true,
        "hasMedicines": true,
        "hasOpticalServices": true,
        "iCD10Type": "iCD10Type",
        "medicalproceduresType": "medicalproceduresType",
        "name": "name",
        "policyCode": "policyCode",
        "policyGroup": "policyGroup",
        "policyId": "policyId",
        "schemeCode": "schemeCode",
        "schemeName": "schemeName",
        "status": "status",
        "terminationDate": "terminationDate",
        "totalBenefit": 0,
        "type": "type"
      },
      "policyJoinDate": "policyJoinDate",
      "spouseCount": [
        "string"
      ],
      "status": "status"
    }
  ],
  "middleName": "middleName",
  "nationalId": "nationalId",
  "parentNumber": "parentNumber",
  "phone": "phone",
  "phoneCode": "phoneCode",
  "policyCount": 0,
  "registeredOn": "registeredOn",
  "relationshipType": "relationshipType",
  "schemeCount": 0,
  "shaNumber": "shaNumber",
  "title": "title"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Missing query parameters or invalid request input</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>Example request body</summary>

```json
{
  "file": "<binary>"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/uploads' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: multipart/form-data' \
  --form file=<binary>
```
</details>

**Responses**

<details><summary><code>200</code> — File stored successfully</summary>

_none_


**Example** (portal sample; nested objects show the full shape)

```json
{}
```

</details>

<details><summary><code>400</code> — Bad Request - Failed to parse or read file</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - Tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal Server Error - Failed to store file</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

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

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/uploads/:file_id' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — Pre-signed URL generated successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "data": {},
  "message": "message"
}
```

</details>

<details><summary><code>400</code> — Bad request - file_id is required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>403</code> — Forbidden - tenant context required</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>

<details><summary><code>500</code> — Internal server error - failed to generate download URL</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "error": "error",
  "message": "message"
}
```

</details>


---
