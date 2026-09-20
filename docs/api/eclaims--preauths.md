# Preauths

> Source: https://afyaconnect.dha.go.ke/hie-api/eclaims/preauths · API: **eClaims and Preauth APIs** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

Endpoints for preauthorization processes.

## Endpoints

- [`GET /api/v1/preauths`](#get-apiv1preauths-fetches-a-preauthorization) — Fetches a preauthorization
- [`POST /api/v1/preauths`](#post-apiv1preauths-create-a-preauthorization) — Create a preauthorization
- [`DELETE /api/v1/preauths/diagnoses/{icd_code}`](#delete-apiv1preauthsdiagnosesicd_code-remove-diagnosis-from-a-preauth) — Remove diagnosis from a preauth
- [`DELETE /api/v1/preauths/doctors`](#delete-apiv1preauthsdoctors-remove-preauth-doctor) — Remove Preauth Doctor
- [`POST /api/v1/preauths/cancel`](#post-apiv1preauthscancel-cancel-preauth) — Cancel Preauth

---

### `GET /api/v1/preauths` — Fetches a preauthorization

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/preauths#fetches-a-preauthorization

Fetches an existing preauthorization linked to the consent token provided

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | consent token linked to the preauth |

**Responses**

<details><summary><code>200</code> — Preauthorization retrieved successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `accessPoint` | string | no |  |
| `anaesthesiaType` | string | no |  |
| `authorization` | integer | no |  |
| `authorizationDetails` | object | no |  |
| `beneficiaryDetails` | object | no |  |
| `carcinomaStaging` | string | no |  |
| `clinicalIndications` | string | no |  |
| `comorbidity` | string | no |  |
| `conditionCause` | string | no |  |
| `conditionEmploymentRelated` | boolean | no |  |
| `conditionOtherRelated` | boolean | no |  |
| `costPerSession` | string | no |  |
| `countdown` | integer | no |  |
| `createdByName` | string | no |  |
| `description` | string | no |  |
| `doctorApproved` | boolean | no |  |
| `doctorReviewStatus` | string | no |  |
| `finalApprovedAmount` | number | no |  |
| `guid` | string | no |  |
| `id` | integer | no |  |
| `interventionCode` | string | no |  |
| `interventionData` | object | no |  |
| `isElective` | boolean | no |  |
| `isEmergency` | boolean | no |  |
| `isHmisPreauth` | boolean | no |  |
| `isOncology` | boolean | no |  |
| `isOptical` | boolean | no |  |
| `isRadiology` | boolean | no |  |
| `isRenal` | boolean | no |  |
| `isRequestPhase` | boolean | no |  |
| `isResponsePhase` | boolean | no |  |
| `isSurgical` | boolean | no |  |
| `lengthOfStay` | integer | no |  |
| `memberIdentifier` | string | no |  |
| `memberIsVip` | boolean | no |  |
| `memberIsVvip` | boolean | no |  |
| `memberName` | string | no |  |
| `memberScheme` | string | no |  |
| `metastases` | string | no |  |
| `needsDoctorApproval` | boolean | no |  |
| `numberOfPreauthDoctorsRequired` | integer | no |  |
| `otherMetastases` | string | no |  |
| `payerIdentifier` | string | no |  |
| `payerInvoiceNo` | string | no |  |
| `payerName` | string | no |  |
| `preauthAttachments` | object[] | no |  |
| `preauthDiagnoses` | object[] | no |  |
| `preauthDoctors` | object[] | no |  |
| `preauthFlags` | array | no |  |
| `preauthItems` | object[] | no |  |
| `preauthNotes` | object[] | no |  |
| `preauthType` | string | no |  |
| `providerConsent` | boolean | no |  |
| `providerCurrency` | string | no |  |
| `providerDetails` | object | no |  |
| `providerName` | string | no |  |
| `providerNotificationEmail` | string | no |  |
| `reasonForAcuteDialysis` | string | no |  |
| `reasonForSelectingOther` | string | no |  |
| `requestExtraData` | object | no |  |
| `responseExtraData` | string | no |  |
| `serviceEnd` | string | no |  |
| `serviceStart` | string | no |  |
| `sessionExpectedDate` | string | no |  |
| `sessionType` | string | no |  |
| `sessionsFrequency` | string | no |  |
| `sessionsRequired` | integer | no |  |
| `status` | string | no |  |
| `submissionDateIn_EAT` | string | no |  |
| `token` | string | no |  |
| `totalEstimatedAmountForPreauth` | number | no |  |
| `totalInterimApprovedAmountForPreauth` | number | no |  |
| `updatedByName` | string | no |  |

</details>

<details><summary><code>400</code> — Invalid request</summary>

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

<details><summary><code>500</code> — Internal server error</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>


---

### `POST /api/v1/preauths` — Create a preauthorization

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/preauths#create-a-preauthorization

Creates a new preauthorization using multipart form data with file uploads

**Request body** — `multipart/form-data`, optional

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | Consent token for authorization. This is the `authorization_code` received from the `Create Virtual Claim` endpoint. |
| `intervention_code` | string | **yes** | Intervention code for the service offered |
| `service_start` | string | **yes** | ISO timestamp for when the service started |
| `service_end` | string | **yes** | ISO timestamp for when the service ended |
| `items` | object[] | **yes** | List of billed items |
| `diagnoses` | object[] | **yes** | List of diagnoses |
| `doctors` | object[] | **yes** | List of doctors |
| `attachments` | object[] | **yes** | List of attachments |
| `provider_notification_email` | string (email) | **yes** | Email to notify the provider of any updates on the preauthorization request |

**Responses**

<details><summary><code>200</code> — Preauthorization created successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `accessPoint` | string | no |  |
| `anaesthesiaType` | string | no |  |
| `authorization` | integer | no |  |
| `authorizationDetails` | object | no |  |
| `beneficiaryDetails` | object | no |  |
| `carcinomaStaging` | string | no |  |
| `clinicalIndications` | string | no |  |
| `comorbidity` | string | no |  |
| `conditionCause` | string | no |  |
| `conditionEmploymentRelated` | boolean | no |  |
| `conditionOtherRelated` | boolean | no |  |
| `costPerSession` | string | no |  |
| `countdown` | integer | no |  |
| `createdByName` | string | no |  |
| `description` | string | no |  |
| `doctorApproved` | boolean | no |  |
| `doctorReviewStatus` | string | no |  |
| `finalApprovedAmount` | number | no |  |
| `guid` | string | no |  |
| `id` | integer | no |  |
| `interventionCode` | string | no |  |
| `interventionData` | object | no |  |
| `isElective` | boolean | no |  |
| `isEmergency` | boolean | no |  |
| `isHmisPreauth` | boolean | no |  |
| `isOncology` | boolean | no |  |
| `isOptical` | boolean | no |  |
| `isRadiology` | boolean | no |  |
| `isRenal` | boolean | no |  |
| `isRequestPhase` | boolean | no |  |
| `isResponsePhase` | boolean | no |  |
| `isSurgical` | boolean | no |  |
| `lengthOfStay` | integer | no |  |
| `memberIdentifier` | string | no |  |
| `memberIsVip` | boolean | no |  |
| `memberIsVvip` | boolean | no |  |
| `memberName` | string | no |  |
| `memberScheme` | string | no |  |
| `metastases` | string | no |  |
| `needsDoctorApproval` | boolean | no |  |
| `numberOfPreauthDoctorsRequired` | integer | no |  |
| `otherMetastases` | string | no |  |
| `payerIdentifier` | string | no |  |
| `payerInvoiceNo` | string | no |  |
| `payerName` | string | no |  |
| `preauthAttachments` | object[] | no |  |
| `preauthDiagnoses` | object[] | no |  |
| `preauthDoctors` | object[] | no |  |
| `preauthFlags` | array | no |  |
| `preauthItems` | object[] | no |  |
| `preauthNotes` | object[] | no |  |
| `preauthType` | string | no |  |
| `providerConsent` | boolean | no |  |
| `providerCurrency` | string | no |  |
| `providerDetails` | object | no |  |
| `providerName` | string | no |  |
| `providerNotificationEmail` | string | no |  |
| `reasonForAcuteDialysis` | string | no |  |
| `reasonForSelectingOther` | string | no |  |
| `requestExtraData` | object | no |  |
| `responseExtraData` | string | no |  |
| `serviceEnd` | string | no |  |
| `serviceStart` | string | no |  |
| `sessionExpectedDate` | string | no |  |
| `sessionType` | string | no |  |
| `sessionsFrequency` | string | no |  |
| `sessionsRequired` | integer | no |  |
| `status` | string | no |  |
| `submissionDateIn_EAT` | string | no |  |
| `token` | string | no |  |
| `totalEstimatedAmountForPreauth` | number | no |  |
| `totalInterimApprovedAmountForPreauth` | number | no |  |
| `updatedByName` | string | no |  |

</details>

<details><summary><code>400</code> — Invalid request</summary>

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

<details><summary><code>500</code> — Internal server error</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>


---

### `DELETE /api/v1/preauths/diagnoses/{icd_code}` — Remove diagnosis from a preauth

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths/diagnoses/{icd_code}`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/preauths#remove-diagnosis-from-a-preauth

Remove a diagnosis from an existing preauthorization.

**Request body** — `application/json`, required

Remove preauth diagnosis request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `icd_code` | string | **yes** |  |
| `intervention_code` | string | **yes** |  |

**Responses**

<details><summary><code>200</code> — Preauthorization canceled successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `accessPoint` | string | no |  |
| `anaesthesiaType` | string | no |  |
| `authorization` | integer | no |  |
| `authorizationDetails` | object | no |  |
| `beneficiaryDetails` | object | no |  |
| `carcinomaStaging` | string | no |  |
| `clinicalIndications` | string | no |  |
| `comorbidity` | string | no |  |
| `conditionCause` | string | no |  |
| `conditionEmploymentRelated` | boolean | no |  |
| `conditionOtherRelated` | boolean | no |  |
| `costPerSession` | string | no |  |
| `countdown` | integer | no |  |
| `createdByName` | string | no |  |
| `description` | string | no |  |
| `doctorApproved` | boolean | no |  |
| `doctorReviewStatus` | string | no |  |
| `finalApprovedAmount` | number | no |  |
| `guid` | string | no |  |
| `id` | integer | no |  |
| `interventionCode` | string | no |  |
| `interventionData` | object | no |  |
| `isElective` | boolean | no |  |
| `isEmergency` | boolean | no |  |
| `isHmisPreauth` | boolean | no |  |
| `isOncology` | boolean | no |  |
| `isOptical` | boolean | no |  |
| `isRadiology` | boolean | no |  |
| `isRenal` | boolean | no |  |
| `isRequestPhase` | boolean | no |  |
| `isResponsePhase` | boolean | no |  |
| `isSurgical` | boolean | no |  |
| `lengthOfStay` | integer | no |  |
| `memberIdentifier` | string | no |  |
| `memberIsVip` | boolean | no |  |
| `memberIsVvip` | boolean | no |  |
| `memberName` | string | no |  |
| `memberScheme` | string | no |  |
| `metastases` | string | no |  |
| `needsDoctorApproval` | boolean | no |  |
| `numberOfPreauthDoctorsRequired` | integer | no |  |
| `otherMetastases` | string | no |  |
| `payerIdentifier` | string | no |  |
| `payerInvoiceNo` | string | no |  |
| `payerName` | string | no |  |
| `preauthAttachments` | object[] | no |  |
| `preauthDiagnoses` | object[] | no |  |
| `preauthDoctors` | object[] | no |  |
| `preauthFlags` | array | no |  |
| `preauthItems` | object[] | no |  |
| `preauthNotes` | object[] | no |  |
| `preauthType` | string | no |  |
| `providerConsent` | boolean | no |  |
| `providerCurrency` | string | no |  |
| `providerDetails` | object | no |  |
| `providerName` | string | no |  |
| `providerNotificationEmail` | string | no |  |
| `reasonForAcuteDialysis` | string | no |  |
| `reasonForSelectingOther` | string | no |  |
| `requestExtraData` | object | no |  |
| `responseExtraData` | string | no |  |
| `serviceEnd` | string | no |  |
| `serviceStart` | string | no |  |
| `sessionExpectedDate` | string | no |  |
| `sessionType` | string | no |  |
| `sessionsFrequency` | string | no |  |
| `sessionsRequired` | integer | no |  |
| `status` | string | no |  |
| `submissionDateIn_EAT` | string | no |  |
| `token` | string | no |  |
| `totalEstimatedAmountForPreauth` | number | no |  |
| `totalInterimApprovedAmountForPreauth` | number | no |  |
| `updatedByName` | string | no |  |

</details>

<details><summary><code>400</code> — Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>

<details><summary><code>401</code> — Unauthorized</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>

<details><summary><code>403</code> — Forbidden</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>

<details><summary><code>500</code> — Internal server error</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>


---

### `DELETE /api/v1/preauths/doctors` — Remove Preauth Doctor

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths/doctors`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/preauths#remove-preauth-doctor

Remove a doctor associated with an existing preauthorization. Can only be done before the preauthorization is submitted.

**Request body** — `application/json`, required

Remove preauth doctor

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `intervention_code` | string | **yes** |  |
| `practitioner_registration_number` | string | **yes** |  |

**Responses**

<details><summary><code>200</code> — Preauth Doctor removed successfully</summary>

_none_

</details>

<details><summary><code>400</code> — Invalid request</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>

<details><summary><code>401</code> — Unauthorized</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>

<details><summary><code>403</code> — Forbidden</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>

<details><summary><code>500</code> — Internal server error</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>


---

### `POST /api/v1/preauths/cancel` — Cancel Preauth

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths/cancel`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/preauths#cancel-preauth

Cancel an existing preauthorization using the consent token and intervention code.

**Request body** — `application/json`, required

Cancel preauthorization request

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** |  |
| `intervention_code` | string | **yes** |  |

**Responses**

<details><summary><code>200</code> — Preauthorization canceled successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `accessPoint` | string | no |  |
| `anaesthesiaType` | string | no |  |
| `authorization` | integer | no |  |
| `authorizationDetails` | object | no |  |
| `beneficiaryDetails` | object | no |  |
| `carcinomaStaging` | string | no |  |
| `clinicalIndications` | string | no |  |
| `comorbidity` | string | no |  |
| `conditionCause` | string | no |  |
| `conditionEmploymentRelated` | boolean | no |  |
| `conditionOtherRelated` | boolean | no |  |
| `costPerSession` | string | no |  |
| `countdown` | integer | no |  |
| `createdByName` | string | no |  |
| `description` | string | no |  |
| `doctorApproved` | boolean | no |  |
| `doctorReviewStatus` | string | no |  |
| `finalApprovedAmount` | number | no |  |
| `guid` | string | no |  |
| `id` | integer | no |  |
| `interventionCode` | string | no |  |
| `interventionData` | object | no |  |
| `isElective` | boolean | no |  |
| `isEmergency` | boolean | no |  |
| `isHmisPreauth` | boolean | no |  |
| `isOncology` | boolean | no |  |
| `isOptical` | boolean | no |  |
| `isRadiology` | boolean | no |  |
| `isRenal` | boolean | no |  |
| `isRequestPhase` | boolean | no |  |
| `isResponsePhase` | boolean | no |  |
| `isSurgical` | boolean | no |  |
| `lengthOfStay` | integer | no |  |
| `memberIdentifier` | string | no |  |
| `memberIsVip` | boolean | no |  |
| `memberIsVvip` | boolean | no |  |
| `memberName` | string | no |  |
| `memberScheme` | string | no |  |
| `metastases` | string | no |  |
| `needsDoctorApproval` | boolean | no |  |
| `numberOfPreauthDoctorsRequired` | integer | no |  |
| `otherMetastases` | string | no |  |
| `payerIdentifier` | string | no |  |
| `payerInvoiceNo` | string | no |  |
| `payerName` | string | no |  |
| `preauthAttachments` | object[] | no |  |
| `preauthDiagnoses` | object[] | no |  |
| `preauthDoctors` | object[] | no |  |
| `preauthFlags` | array | no |  |
| `preauthItems` | object[] | no |  |
| `preauthNotes` | object[] | no |  |
| `preauthType` | string | no |  |
| `providerConsent` | boolean | no |  |
| `providerCurrency` | string | no |  |
| `providerDetails` | object | no |  |
| `providerName` | string | no |  |
| `providerNotificationEmail` | string | no |  |
| `reasonForAcuteDialysis` | string | no |  |
| `reasonForSelectingOther` | string | no |  |
| `requestExtraData` | object | no |  |
| `responseExtraData` | string | no |  |
| `serviceEnd` | string | no |  |
| `serviceStart` | string | no |  |
| `sessionExpectedDate` | string | no |  |
| `sessionType` | string | no |  |
| `sessionsFrequency` | string | no |  |
| `sessionsRequired` | integer | no |  |
| `status` | string | no |  |
| `submissionDateIn_EAT` | string | no |  |
| `token` | string | no |  |
| `totalEstimatedAmountForPreauth` | number | no |  |
| `totalInterimApprovedAmountForPreauth` | number | no |  |
| `updatedByName` | string | no |  |

</details>

<details><summary><code>400</code> — Invalid request</summary>

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

<details><summary><code>500</code> — Internal server error</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

</details>


---
