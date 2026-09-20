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

<details><summary>Example request body</summary>

```json
{
  "intervention_codes": [
    "string"
  ],
  "patient_id": "patient_id",
  "service_type": "CAPITATION",
  "otp": "otp"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/visit' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "intervention_codes": [
    "string"
  ],
  "patient_id": "patient_id",
  "service_type": "CAPITATION",
  "otp": "otp"
}'
```
</details>

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
