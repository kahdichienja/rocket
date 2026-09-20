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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "identification_number": "identification_number",
  "identification_type": "registration_number",
  "regulation_body": "KMPDC"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/doctors' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "identification_number": "identification_number",
  "identification_type": "registration_number",
  "regulation_body": "KMPDC"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Doctor successfully added to claim</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `data` | object | no | @Description	Response data payload containing operation details 	@Example		{"status": "success"} |
| `message` | string | no | @Description	Success message describing the operation result 	@Example		"Visit has been successfully started" |
| `data` | object | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "data": {},
  "message": "message"
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

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

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

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request DELETE \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/doctors' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token"
}'
```
</details>

**Responses**

<details><summary><code>204</code> — No Content</summary>

_none_

</details>

<details><summary><code>400</code> — Bad Request - Request failed validation</summary>

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

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

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

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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

<details><summary>Example request body</summary>

```json
{
  "beneficiary_cr_id": "beneficiary_cr_id",
  "brought_by": "RELATIVE",
  "identification_number": "identification_number",
  "identification_type": "registration_number",
  "interventions": [
    "string"
  ],
  "mode_of_arrival": "AMBULANCE",
  "notes": "notes",
  "otp": "otp",
  "reference_number": "reference_number",
  "regulation_body": "KMPDC"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/emergency' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "beneficiary_cr_id": "beneficiary_cr_id",
  "brought_by": "RELATIVE",
  "identification_number": "identification_number",
  "identification_type": "registration_number",
  "interventions": [
    "string"
  ],
  "mode_of_arrival": "AMBULANCE",
  "notes": "notes",
  "otp": "otp",
  "reference_number": "reference_number",
  "regulation_body": "KMPDC"
}'
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "admitted_on": "admitted_on",
  "appointment_number": "appointment_number",
  "attributes": "attributes",
  "authorization_code": "authorization_code",
  "authorization_guid": "authorization_guid",
  "beneficiary_guid": "beneficiary_guid",
  "beneficiary_id": 0,
  "beneficiary_is_fuzzy_matched": true,
  "cancel_reason_text": "cancel_reason_text",
  "cancel_reason_type": "cancel_reason_type",
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
  "claim_id": 0,
  "created_by_name": "created_by_name",
  "currency": "currency",
  "diagnoses_count": 0,
  "discharge_cancel_date": "discharge_cancel_date",
  "discharge_cancel_remarks": "discharge_cancel_remarks",
  "discharge_reason": "discharge_reason",
  "discharged_on": "discharged_on",
  "edi_claim_guid": "edi_claim_guid",
  "emergency_visit_expiry": "emergency_visit_expiry",
  "estimate_ip_days": 0,
  "expected_discharge_date": "expected_discharge_date",
  "has_reviewed_claim": true,
  "id": "id",
  "initial_intervention": "initial_intervention",
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
  "invoice_id": "invoice_id",
  "invoice_number": "invoice_number",
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
  "is_charge_master_mapped": true,
  "is_negative": true,
  "is_resubmitted": true,
  "is_zero": true,
  "last_retry": "last_retry",
  "location_code": "location_code",
  "location_name": "location_name",
  "member_name": "member_name",
  "member_number": "member_number",
  "member_number_has_token": true,
  "mode_of_arrival": "mode_of_arrival",
  "nhif_number": "nhif_number",
  "notes": "notes",
  "number_of_invoices": 0,
  "patient_name": "patient_name",
  "patient_number": "patient_number",
  "payer_code": "payer_code",
  "payer_name": "payer_name",
  "payer_slade_code": "payer_slade_code",
  "policy_number": "policy_number",
  "policy_valid_from": "policy_valid_from",
  "policy_valid_to": "policy_valid_to",
  "provider_name": "provider_name",
  "provider_slade_code": "provider_slade_code",
  "reason_for_unknown_patient": "reason_for_unknown_patient",
  "reference_number": "reference_number",
  "resubmission_workflow_state": "resubmission_workflow_state",
  "retry_count": 0,
  "scheme_code": "scheme_code",
  "scheme_name": "scheme_name",
  "service_type": "service_type",
  "total_claim_amount": 0,
  "total_claim_copay": 0,
  "total_claim_discount": 0,
  "total_claim_net_amount": 0,
  "total_claim_splits": 0,
  "updated_by_name": "updated_by_name",
  "visit_end": "visit_end",
  "visit_number": "visit_number",
  "visit_start": "visit_start",
  "workflow_state": "workflow_state"
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

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/emergency/protocols?active=%3Cactive%3E&intervention_code=%3Cintervention_code%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "count": 0,
  "currentPage": 0,
  "endIndex": 0,
  "next": "next",
  "pageSize": 0,
  "previous": "previous",
  "results": [
    {
      "applicableTariff": "applicableTariff",
      "guid": "guid",
      "id": 0,
      "intervention": [
        {}
      ],
      "name": "name",
      "protocolClassificationType": "protocolClassificationType",
      "protocolCode": "protocolCode",
      "protocolType": "protocolType",
      "status": "status"
    }
  ],
  "startIndex": 0,
  "totalPages": 0
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

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

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

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "protocol_code": "protocol_code",
  "intervention_code": "intervention_code",
  "unit_price": 0,
  "quantity": 0,
  "diagnoses": "diagnoses",
  "attachments": "attachments"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/emergency/protocols' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: multipart/form-data' \
  --form consent_token=consent_token \
  --form protocol_code=protocol_code \
  --form intervention_code=intervention_code \
  --form unit_price=0 \
  --form quantity=0 \
  --form diagnoses=diagnoses \
  --form attachments=attachments
```
</details>

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

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

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

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "protocol_code": "protocol_code",
  "case_number": "case_number",
  "practitioner_reg_number": "practitioner_reg_number",
  "beneficiary_cr_id": "beneficiary_cr_id",
  "otp": "otp",
  "provider_registration_number": "provider_registration_number",
  "diagnoses": "diagnoses",
  "interventions": "interventions",
  "attachments": "attachments"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/emt' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: multipart/form-data' \
  --form consent_token=consent_token \
  --form protocol_code=protocol_code \
  --form case_number=case_number \
  --form practitioner_reg_number=practitioner_reg_number \
  --form beneficiary_cr_id=beneficiary_cr_id \
  --form otp=otp \
  --form provider_registration_number=provider_registration_number \
  --form diagnoses=diagnoses \
  --form interventions=interventions \
  --form attachments=attachments
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "admitted_on": "admitted_on",
  "appointment_number": "appointment_number",
  "attributes": "attributes",
  "authorization_code": "authorization_code",
  "authorization_guid": "authorization_guid",
  "beneficiary_guid": "beneficiary_guid",
  "beneficiary_id": 0,
  "beneficiary_is_fuzzy_matched": true,
  "cancel_reason_text": "cancel_reason_text",
  "cancel_reason_type": "cancel_reason_type",
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
  "claim_id": 0,
  "created_by_name": "created_by_name",
  "currency": "currency",
  "diagnoses_count": 0,
  "discharge_cancel_date": "discharge_cancel_date",
  "discharge_cancel_remarks": "discharge_cancel_remarks",
  "discharge_reason": "discharge_reason",
  "discharged_on": "discharged_on",
  "edi_claim_guid": "edi_claim_guid",
  "emergency_visit_expiry": "emergency_visit_expiry",
  "estimate_ip_days": 0,
  "expected_discharge_date": "expected_discharge_date",
  "has_reviewed_claim": true,
  "id": "id",
  "initial_intervention": "initial_intervention",
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
  "invoice_id": "invoice_id",
  "invoice_number": "invoice_number",
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
  "is_charge_master_mapped": true,
  "is_negative": true,
  "is_resubmitted": true,
  "is_zero": true,
  "last_retry": "last_retry",
  "location_code": "location_code",
  "location_name": "location_name",
  "member_name": "member_name",
  "member_number": "member_number",
  "member_number_has_token": true,
  "mode_of_arrival": "mode_of_arrival",
  "nhif_number": "nhif_number",
  "notes": "notes",
  "number_of_invoices": 0,
  "patient_name": "patient_name",
  "patient_number": "patient_number",
  "payer_code": "payer_code",
  "payer_name": "payer_name",
  "payer_slade_code": "payer_slade_code",
  "policy_number": "policy_number",
  "policy_valid_from": "policy_valid_from",
  "policy_valid_to": "policy_valid_to",
  "provider_name": "provider_name",
  "provider_slade_code": "provider_slade_code",
  "reason_for_unknown_patient": "reason_for_unknown_patient",
  "reference_number": "reference_number",
  "resubmission_workflow_state": "resubmission_workflow_state",
  "retry_count": 0,
  "scheme_code": "scheme_code",
  "scheme_name": "scheme_name",
  "service_type": "service_type",
  "total_claim_amount": 0,
  "total_claim_copay": 0,
  "total_claim_discount": 0,
  "total_claim_net_amount": 0,
  "total_claim_splits": 0,
  "updated_by_name": "updated_by_name",
  "visit_end": "visit_end",
  "visit_number": "visit_number",
  "visit_start": "visit_start",
  "workflow_state": "workflow_state"
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

<details><summary><code>401</code> — Unauthorized - Invalid identity</summary>

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

<details><summary><code>403</code> — Forbidden - Not enough permissions</summary>

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
