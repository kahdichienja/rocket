# Authorizations

> Source: https://afyaconnect.dha.go.ke/hie-api/eclaims/authorizations · API: **eClaims and Preauth APIs** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

Endpoint for creating authorizations using biometrics or OTP.

## Endpoints

- [`GET /api/v1/claims/authorizations`](#get-apiv1claimsauthorizations-retrieve-an-existing-authorization) — Retrieve an existing authorization
- [`POST /api/v1/claims/authorize`](#post-apiv1claimsauthorize-create-a-new-authorization-otp-or-biometrics) — Create a new authorization (OTP or biometrics)
- [`POST /api/v1/claims/authorizations/{consent_token}/reject`](#post-apiv1claimsauthorizationsconsent_tokenreject-rejects-existing-pending-biometrics-authorization) — Rejects existing pending biometrics authorization.

---

### `GET /api/v1/claims/authorizations` — Retrieve an existing authorization

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/authorizations`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/authorizations#retrieve-an-existing-authorization

Retrieves an existing authorization for a patient using the provided token, beneficiary code, and GUID.

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `token` | string | **yes** | Authorization token linked to the patient's consent. |
| `beneficiary_code` | string | no | The beneficiary's identifier code. |
| `guid` | string | **yes** | Unique identifier (GUID) of the authorization record. |

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/authorizations?token=%3Ctoken%3E&guid=%3Cguid%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — Authorization retrieved successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `authCode` | string | no |  |
| `authorizationReason` | string | no |  |
| `authorizationType` | string[] | no |  |
| `authorizingDeviceOs` | string | no |  |
| `beneficiary` | integer | no |  |
| `beneficiaryCode` | string | no |  |
| `beneficiaryJoinDate` | string | no |  |
| `beneficiaryName` | string | no |  |
| `beneficiaryNumber` | string | no |  |
| `beneficiaryScheme` | string | no |  |
| `benefitType` | string | no |  |
| `biometricMatchLogId` | string | no |  |
| `createdByName` | string | no |  |
| `created_by` | string | no |  |
| `dateAuthorized` | string | no |  |
| `ekycToken` | string | no |  |
| `endDate` | string | no |  |
| `endedVia` | string | no |  |
| `expiry` | string | no |  |
| `guardian` | integer | no |  |
| `guid` | string | no |  |
| `id` | integer | no |  |
| `isBiometricsDischargeAuthorization` | boolean | no |  |
| `isComplete` | boolean | no |  |
| `isElective` | boolean | no |  |
| `isEmergency` | boolean | no |  |
| `isOpen` | boolean | no |  |
| `label` | string | no |  |
| `needsPreauth` | boolean | no |  |
| `notes` | string | no |  |
| `overallPreauthFinalised` | boolean | no |  |
| `parentAuthorization` | integer | no |  |
| `parentType` | string | no |  |
| `payerName` | string | no |  |
| `payerSladeCode` | integer | no |  |
| `provider` | integer | no |  |
| `providerFid` | string | no |  |
| `providerName` | string | no |  |
| `requestedBy` | string | no |  |
| `sessionType` | string | no |  |
| `shaGuid` | string | no |  |
| `shaVerificationRequest` | object | no |  |
| `shaVerificationRequestId` | string | no |  |
| `status` | string | no |  |
| `token` | string | no |  |
| `updated_by` | string | no |  |
| `workStationId` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "authCode": "authCode",
  "authorizationReason": "authorizationReason",
  "authorizationType": [
    "string"
  ],
  "authorizingDeviceOs": "authorizingDeviceOs",
  "beneficiary": 0,
  "beneficiaryCode": "beneficiaryCode",
  "beneficiaryJoinDate": "beneficiaryJoinDate",
  "beneficiaryName": "beneficiaryName",
  "beneficiaryNumber": "beneficiaryNumber",
  "beneficiaryScheme": "beneficiaryScheme",
  "benefitType": "benefitType",
  "biometricMatchLogId": "biometricMatchLogId",
  "createdByName": "createdByName",
  "created_by": "created_by",
  "dateAuthorized": "dateAuthorized",
  "ekycToken": "ekycToken",
  "endDate": "endDate",
  "endedVia": "endedVia",
  "expiry": "expiry",
  "guardian": 0,
  "guid": "guid",
  "id": 0,
  "isBiometricsDischargeAuthorization": true,
  "isComplete": true,
  "isElective": true,
  "isEmergency": true,
  "isOpen": true,
  "label": "label",
  "needsPreauth": true,
  "notes": "notes",
  "overallPreauthFinalised": true,
  "parentAuthorization": 0,
  "parentType": "parentType",
  "payerName": "payerName",
  "payerSladeCode": 0,
  "provider": 0,
  "providerFid": "providerFid",
  "providerName": "providerName",
  "requestedBy": "requestedBy",
  "sessionType": "sessionType",
  "shaGuid": "shaGuid",
  "shaVerificationRequest": {
    "embedExpiry": 0,
    "embededToken": "embededToken",
    "requestId": "requestId",
    "requestUrl": "requestUrl"
  },
  "shaVerificationRequestId": "shaVerificationRequestId",
  "status": "status",
  "token": "token",
  "updated_by": "updated_by",
  "workStationId": "workStationId"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Invalid request or authorization retrieval failed</summary>

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

<details><summary><code>500</code> — Internal Server Error</summary>

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

### `POST /api/v1/claims/authorize` — Create a new authorization (OTP or biometrics)

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/authorize`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/authorizations#create-a-new-authorization-otp-or-biometrics

Creates a new authorization by capturing patient consent via OTP or biometrics. Use the OTP strategy for standard outpatient and inpatient consent; use the biometrics strategy (eKYC or fingerprint) when the facility has a registered hardware agent. The same endpoint is used across claims creation and consent workflows.

**Request body** — `application/json`, required

Authorization request payload. Choose one strategy: OTP (phone-based one-time password) or Biometrics (eKYC/fingerprint via hardware agent).

| Field | Type | Required | Description |
|---|---|---|---|
| `patient_id` | string | **yes** | The patient's Client Registry identifier. |
| `service_type` | string | **yes** | Type of service being authorized. Allowed: `OUTPATIENT`, `INPATIENT` |
| `otp` | string | **yes** | One-time password delivered to the patient's registered phone number. |
| `interventions` | string[] | **yes** | List of intervention codes for the services being requested in this visit. |

<details><summary>Example request body</summary>

```json
{
  "patient_id": "patient_id",
  "service_type": "OUTPATIENT",
  "otp": "otp",
  "interventions": [
    "string"
  ]
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/authorize' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "patient_id": "patient_id",
  "service_type": "OUTPATIENT",
  "otp": "otp",
  "interventions": [
    "string"
  ]
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Authorization created successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `authCode` | string | no |  |
| `authorizationReason` | string | no |  |
| `authorizationType` | string[] | no |  |
| `authorizingDeviceOs` | string | no |  |
| `beneficiary` | integer | no |  |
| `beneficiaryCode` | string | no |  |
| `beneficiaryJoinDate` | string | no |  |
| `beneficiaryName` | string | no |  |
| `beneficiaryNumber` | string | no |  |
| `beneficiaryScheme` | string | no |  |
| `benefitType` | string | no |  |
| `biometricMatchLogId` | string | no |  |
| `createdByName` | string | no |  |
| `created_by` | string | no |  |
| `dateAuthorized` | string | no |  |
| `ekycToken` | string | no |  |
| `endDate` | string | no |  |
| `endedVia` | string | no |  |
| `expiry` | string | no |  |
| `guardian` | integer | no |  |
| `guid` | string | no |  |
| `id` | integer | no |  |
| `isBiometricsDischargeAuthorization` | boolean | no |  |
| `isComplete` | boolean | no |  |
| `isElective` | boolean | no |  |
| `isEmergency` | boolean | no |  |
| `isOpen` | boolean | no |  |
| `label` | string | no |  |
| `needsPreauth` | boolean | no |  |
| `notes` | string | no |  |
| `overallPreauthFinalised` | boolean | no |  |
| `parentAuthorization` | integer | no |  |
| `parentType` | string | no |  |
| `payerName` | string | no |  |
| `payerSladeCode` | integer | no |  |
| `provider` | integer | no |  |
| `providerFid` | string | no |  |
| `providerName` | string | no |  |
| `requestedBy` | string | no |  |
| `sessionType` | string | no |  |
| `shaGuid` | string | no |  |
| `shaVerificationRequest` | object | no |  |
| `shaVerificationRequestId` | string | no |  |
| `status` | string | no |  |
| `token` | string | no |  |
| `updated_by` | string | no |  |
| `workStationId` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "authCode": "authCode",
  "authorizationReason": "authorizationReason",
  "authorizationType": [
    "string"
  ],
  "authorizingDeviceOs": "authorizingDeviceOs",
  "beneficiary": 0,
  "beneficiaryCode": "beneficiaryCode",
  "beneficiaryJoinDate": "beneficiaryJoinDate",
  "beneficiaryName": "beneficiaryName",
  "beneficiaryNumber": "beneficiaryNumber",
  "beneficiaryScheme": "beneficiaryScheme",
  "benefitType": "benefitType",
  "biometricMatchLogId": "biometricMatchLogId",
  "createdByName": "createdByName",
  "created_by": "created_by",
  "dateAuthorized": "dateAuthorized",
  "ekycToken": "ekycToken",
  "endDate": "endDate",
  "endedVia": "endedVia",
  "expiry": "expiry",
  "guardian": 0,
  "guid": "guid",
  "id": 0,
  "isBiometricsDischargeAuthorization": true,
  "isComplete": true,
  "isElective": true,
  "isEmergency": true,
  "isOpen": true,
  "label": "label",
  "needsPreauth": true,
  "notes": "notes",
  "overallPreauthFinalised": true,
  "parentAuthorization": 0,
  "parentType": "parentType",
  "payerName": "payerName",
  "payerSladeCode": 0,
  "provider": 0,
  "providerFid": "providerFid",
  "providerName": "providerName",
  "requestedBy": "requestedBy",
  "sessionType": "sessionType",
  "shaGuid": "shaGuid",
  "shaVerificationRequest": {
    "embedExpiry": 0,
    "embededToken": "embededToken",
    "requestId": "requestId",
    "requestUrl": "requestUrl"
  },
  "shaVerificationRequestId": "shaVerificationRequestId",
  "status": "status",
  "token": "token",
  "updated_by": "updated_by",
  "workStationId": "workStationId"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Missing or invalid fields</summary>

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

### `POST /api/v1/claims/authorizations/{consent_token}/reject` — Rejects existing pending biometrics authorization.

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/authorizations/{consent_token}/reject`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/authorizations#rejects-existing-pending-biometrics-authorization

Rejects existing pending biometrics authorization.

**Path parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | Consent Token |

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/claims/authorizations/:consent_token/reject' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — Authorization rejected</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
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
