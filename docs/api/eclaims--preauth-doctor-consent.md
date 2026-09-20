# Preauth Doctor Consent

> Source: https://afyaconnect.dha.go.ke/hie-api/eclaims/preauth-doctor-consent · API: **eClaims and Preauth APIs** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

Endpoints for doctor consent in preauthorization.

## Endpoints

- [`POST /api/v1/claims/doctor-consent`](#post-apiv1claimsdoctor-consent-request-doctor-consent) — Request Doctor Consent

---

### `POST /api/v1/claims/doctor-consent` — Request Doctor Consent

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/doctor-consent`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/preauth-doctor-consent#request-doctor-consent

Sends a request for a doctor's consent related to a preauthorization.

**Request body** — `application/json`, required

Doctor consent request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | no |  |
| `created` | string | no |  |
| `emergency_claim_id` | string | no |  |
| `identification_number` | string | no |  |
| `identification_type` | string | no | Allowed: `registration_number`, `National ID`, `Alien ID`, `Refugee ID` |
| `intervention_code` | string | **yes** |  |
| `practitioner_registration_number` | string | no |  |
| `regulation_body` | string | no | Allowed: `KMPDC`, `COC`, `NCK` |
| `request_type` | string | **yes** | Allowed: `PREAUTH_DOCTOR_APPROVAL_REQUEST`, `EMERGENCY_CLAIM_DOCTOR_APPROVAL_REQUEST`, `PRESCRIPTION_REQUEST` |
| `service_type` | string | no |  |

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "created": "created",
  "emergency_claim_id": "emergency_claim_id",
  "identification_number": "identification_number",
  "identification_type": "registration_number",
  "intervention_code": "intervention_code",
  "practitioner_registration_number": "practitioner_registration_number",
  "regulation_body": "KMPDC",
  "request_type": "PREAUTH_DOCTOR_APPROVAL_REQUEST",
  "service_type": "service_type"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/doctor-consent' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "created": "created",
  "emergency_claim_id": "emergency_claim_id",
  "identification_number": "identification_number",
  "identification_type": "registration_number",
  "intervention_code": "intervention_code",
  "practitioner_registration_number": "practitioner_registration_number",
  "regulation_body": "KMPDC",
  "request_type": "PREAUTH_DOCTOR_APPROVAL_REQUEST",
  "service_type": "service_type"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Doctor consent request initiated successfully</summary>

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
