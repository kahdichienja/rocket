# Interventions

> Source: https://afyaconnect.dha.go.ke/hie-api/eclaims/interventions · API: **eClaims and Preauth APIs** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

Endpoints for managing interventions and their combinations.

## Endpoints

- [`POST /api/v1/claims/interventions`](#post-apiv1claimsinterventions-add-a-new-intervention-to-claim) — Add a new intervention to claim
- [`POST /api/v1/claims/interventions/restore`](#post-apiv1claimsinterventionsrestore-restore-intervention) — Restore Intervention
- [`POST /api/v1/claims/interventions/retire`](#post-apiv1claimsinterventionsretire-retire-intervention) — Retire Intervention
- [`POST /api/v1/claims/interventions/switch`](#post-apiv1claimsinterventionsswitch-switch-intervention) — Switch intervention

---

### `POST /api/v1/claims/interventions` — Add a new intervention to claim

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/interventions`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/interventions#add-a-new-intervention-to-claim

Adds a new intervention to an existing claim using the consent token from claim creation.

**Request body** — `application/json`, required

Add intervention Request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `facilityID` | string | no |  |
| `facilityIDType` | string | no |  |
| `intervention_code` | string | **yes** |  |

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "facilityID": "facilityID",
  "facilityIDType": "facilityIDType",
  "intervention_code": "intervention_code"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/interventions' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "facilityID": "facilityID",
  "facilityIDType": "facilityIDType",
  "intervention_code": "intervention_code"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Intervention added successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `accrued_per_diem_amount` | number | no |  |
| `accrued_per_diem_days` | integer | no |  |
| `active_for_uhc` | boolean | no |  |
| `applicable_document_types` | string[] | no |  |
| `bill_from` | string | no |  |
| `bill_to` | string | no |  |
| `id` | string | no |  |
| `intervention_code` | string | no |  |
| `intervention_fund` | string | no |  |
| `intervention_name` | string | no |  |
| `intervention_overall_tariff` | number | no |  |
| `intervention_payment_mechanism` | string | no |  |
| `is_switched_intervention` | boolean | no |  |
| `keph_level_tarrif` | number | no |  |
| `needs_preauth` | boolean | no |  |
| `optional_document_type` | string[] | no |  |
| `optional_preauth_document_types` | string[] | no |  |
| `preauth_exist` | boolean | no |  |
| `required_preauth_document_types` | string[] | no |  |
| `requires_oncology_preauth` | boolean | no |  |
| `requires_optical_preauth` | boolean | no |  |
| `requires_radiology_preauth` | boolean | no |  |
| `requires_renal_preauth` | boolean | no |  |
| `requires_surgical_preauth` | boolean | no |  |
| `sub_benefit_code` | string | no |  |
| `supported_scheme` | string | no |  |
| `switched_intervention_id` | integer | no |  |
| `switched_lines_retained` | boolean | no |  |
| `workflow_state` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
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

### `POST /api/v1/claims/interventions/restore` — Restore Intervention

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/interventions/restore`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/interventions#restore-intervention

Restore an intervention to a claim.

**Request body** — `application/json`, required

Restore intervention request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `intervention_code` | string | **yes** |  |

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "intervention_code": "intervention_code"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/interventions/restore' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "intervention_code": "intervention_code"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Intervention restored successfully</summary>

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

### `POST /api/v1/claims/interventions/retire` — Retire Intervention

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/interventions/retire`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/interventions#retire-intervention

Retire an intervention from a claim.

**Request body** — `application/json`, required

Retire intervention Request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `intervention_code` | string | **yes** |  |

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "intervention_code": "intervention_code"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/interventions/retire' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "intervention_code": "intervention_code"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Intervention retired successfully</summary>

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

### `POST /api/v1/claims/interventions/switch` — Switch intervention

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/interventions/switch`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/interventions#switch-intervention

Switches an existing intervention to a new intervention using a valid consent token.

**Request body** — `application/json`, required

Switch intervention request

| Field | Type | Required | Description |
|---|---|---|---|
| `bill_from` | string | no |  |
| `bill_to` | string | no |  |
| `consent_token` | string | **yes** |  |
| `existing_intervention_code` | string | **yes** |  |
| `new_intervention_code` | string | **yes** |  |
| `retain_bill_items` | boolean | **yes** |  |

<details><summary>Example request body</summary>

```json
{
  "bill_from": "bill_from",
  "bill_to": "bill_to",
  "consent_token": "consent_token",
  "existing_intervention_code": "existing_intervention_code",
  "new_intervention_code": "new_intervention_code",
  "retain_bill_items": true
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/interventions/switch' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "bill_from": "bill_from",
  "bill_to": "bill_to",
  "consent_token": "consent_token",
  "existing_intervention_code": "existing_intervention_code",
  "new_intervention_code": "new_intervention_code",
  "retain_bill_items": true
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Intervention switched successfully</summary>

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

<details><summary><code>400</code> — Bad request - invalid payload</summary>

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

<details><summary><code>401</code> — Unauthorized</summary>

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

<details><summary><code>500</code> — Internal server error</summary>

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
