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

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths?consent_token=%3Cconsent_token%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "accessPoint": "accessPoint",
  "anaesthesiaType": "anaesthesiaType",
  "authorization": 0,
  "authorizationDetails": {
    "authCode": "authCode",
    "authorizationReason": "authorizationReason",
    "authorizationType": [
      "string"
    ],
    "authorizingDeviceOs": "authorizingDeviceOs",
    "beneficiary": 0,
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryName": "beneficiaryName",
    "beneficiaryNumber": "beneficiaryNumber",
    "beneficiaryScheme": "beneficiaryScheme",
    "benefitType": "benefitType",
    "biometricMatchLogId": "biometricMatchLogId",
    "children": [
      {
        "authorizingDeviceOs": "authorizingDeviceOs",
        "beneficiaryCode": "beneficiaryCode",
        "beneficiaryName": "beneficiaryName",
        "beneficiaryNumber": "beneficiaryNumber",
        "biometricMatchLogId": "biometricMatchLogId",
        "ekycToken": "ekycToken",
        "guid": "guid",
        "interventions": [
          {}
        ],
        "isBiometricsDischargeAuthorization": true,
        "isElective": true,
        "isOpen": true,
        "parentAuthorization": 0,
        "parentType": "parentType",
        "preauthTypes": {},
        "sessionType": "sessionType",
        "shaGuid": "shaGuid",
        "shaVerificationRequestId": "shaVerificationRequestId",
        "status": "status",
        "token": "token",
        "workStationId": "workStationId"
      }
    ],
    "createdByName": "createdByName",
    "dateAuthorized": "dateAuthorized",
    "ekycToken": "ekycToken",
    "electivePreauth": {
      "doctorReviewStatus": "doctorReviewStatus",
      "isElective": true,
      "memberName": "memberName",
      "preauthType": "preauthType",
      "serviceEnd": "serviceEnd",
      "serviceStart": "serviceStart",
      "status": "status"
    },
    "eligibility": "eligibility",
    "eligibilityDetails": {
      "cover": {
        "group": "group",
        "groupCode": "groupCode",
        "jobGroup": "jobGroup",
        "validFrom": "validFrom",
        "validTo": "validTo"
      },
      "member": {
        "age": 0,
        "beneficiaryCode": "beneficiaryCode",
        "gender": "gender",
        "group": "group",
        "idNo": "idNo",
        "idNoType": "idNoType",
        "isAlive": true,
        "isMinor": true,
        "isPrincipal": true,
        "names": "names",
        "principalMember": "principalMember",
        "principalRelationship": "principalRelationship"
      }
    },
    "endDate": "endDate",
    "endedVia": [
      "string"
    ],
    "expiry": "expiry",
    "guardian": "guardian",
    "guid": "guid",
    "id": 0,
    "interventions": [
      {
        "activeForUhc": true,
        "allowedInterventions": [
          {}
        ],
        "applicableSchemes": [
          "string"
        ],
        "authInterventionId": 0,
        "code": "code",
        "dispenseMedication": true,
        "fallBackKephLevelTariff": 0,
        "fund": "fund",
        "id": 0,
        "interventionCombinations": [
          {}
        ],
        "kephLevelTarrif": 0,
        "name": "name",
        "needsPreauth": true,
        "numberOfDaysToFallback": 0,
        "overallTariff": 0,
        "packageCombinations": [
          {}
        ],
        "paymentMechanism": "paymentMechanism",
        "preauthFinalised": true,
        "prescriptionMedication": true,
        "requiresSurgicalPreauth": true,
        "standaloneInterventions": [
          {}
        ],
        "subBenefitCode": "subBenefitCode",
        "supportedScheme": "supportedScheme"
      }
    ],
    "isBiometricsDischargeAuthorization": true,
    "isComplete": true,
    "isElective": true,
    "isOpen": true,
    "label": "label",
    "needsPreauth": true,
    "notes": "notes",
    "overallPreauthFinalised": true,
    "parentAuthorization": 0,
    "parentPreauth": {
      "authorizingDeviceOs": "authorizingDeviceOs",
      "beneficiaryCode": "beneficiaryCode",
      "beneficiaryName": "beneficiaryName",
      "beneficiaryNumber": "beneficiaryNumber",
      "biometricMatchLogId": "biometricMatchLogId",
      "ekycToken": "ekycToken",
      "guid": "guid",
      "interventions": [
        {}
      ],
      "isBiometricsDischargeAuthorization": true,
      "isElective": true,
      "isOpen": true,
      "parentAuthorization": 0,
      "parentType": "parentType",
      "preauthTypes": {},
      "sessionType": "sessionType",
      "shaGuid": "shaGuid",
      "shaVerificationRequestId": "shaVerificationRequestId",
      "status": "status",
      "token": "token",
      "workStationId": "workStationId"
    },
    "parentType": "parentType",
    "payerName": "payerName",
    "payerSladeCode": 0,
    "preauthIds": [
      0
    ],
    "preauthTypes": {},
    "provider": 0,
    "providerFid": "providerFid",
    "providerName": "providerName",
    "requestedBy": "requestedBy",
    "sessionType": "sessionType",
    "shaGuid": "shaGuid",
    "shaVerificationRequest": {
      "EmbedExpiry": 0,
      "embededToken": "embededToken",
      "requestId": "requestId",
      "requestUrl": "requestUrl"
    },
    "shaVerificationRequestId": "shaVerificationRequestId",
    "status": "status",
    "token": "token",
    "workStationId": "workStationId"
  },
  "beneficiaryDetails": {
    "DoB": "DoB",
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryId": 0,
    "categoryCode": "categoryCode",
    "categoryName": "categoryName",
    "firstName": "firstName",
    "gender": "gender",
    "guid": "guid",
    "identifiers": [
      {
        "identifier": "identifier",
        "identifierType": "identifierType"
      }
    ],
    "lastName": "lastName",
    "otherNames": "otherNames",
    "schemeCode": "UHC",
    "schemeName": "schemeName"
  },
  "carcinomaStaging": "carcinomaStaging",
  "clinicalIndications": "clinicalIndications",
  "comorbidity": "comorbidity",
  "conditionCause": "conditionCause",
  "conditionEmploymentRelated": true,
  "conditionOtherRelated": true,
  "costPerSession": "costPerSession",
  "countdown": 0,
  "createdByName": "createdByName",
  "description": "description",
  "doctorApproved": true,
  "doctorReviewStatus": "doctorReviewStatus",
  "finalApprovedAmount": 0,
  "guid": "guid",
  "id": 0,
  "interventionCode": "interventionCode",
  "interventionData": {
    "code": "code",
    "fallBackKephLevelTariff": 0,
    "guid": "guid",
    "id": 0,
    "kephLevelTarrif": 0,
    "name": "name",
    "numberOfDaysToFallback": 0,
    "overallTariff": 0,
    "paymentMechanism": "paymentMechanism",
    "status": "status"
  },
  "isElective": true,
  "isEmergency": true,
  "isHmisPreauth": true,
  "isOncology": true,
  "isOptical": true,
  "isRadiology": true,
  "isRenal": true,
  "isRequestPhase": true,
  "isResponsePhase": true,
  "isSurgical": true,
  "lengthOfStay": 0,
  "memberIdentifier": "memberIdentifier",
  "memberIsVip": true,
  "memberIsVvip": true,
  "memberName": "memberName",
  "memberScheme": "memberScheme",
  "metastases": "metastases",
  "needsDoctorApproval": true,
  "numberOfPreauthDoctorsRequired": 0,
  "otherMetastases": "otherMetastases",
  "payerIdentifier": "payerIdentifier",
  "payerInvoiceNo": "payerInvoiceNo",
  "payerName": "payerName",
  "preauthAttachments": [
    {
      "attachment": 0,
      "attachmentType": "DISCHARGE_SUMMARY",
      "author": "author",
      "authorEmail": "authorEmail",
      "authorName": "authorName",
      "contentType": "contentType",
      "description": "description",
      "guid": "guid",
      "id": 0,
      "interventionCode": "interventionCode",
      "organisationName": "organisationName",
      "source": "source",
      "title": "title",
      "uploadedFile": "uploadedFile"
    }
  ],
  "preauthDiagnoses": [
    {
      "authorizationIntervention": "authorizationIntervention",
      "description": "description",
      "guid": "guid",
      "id": 0,
      "interventionCode": "interventionCode",
      "interventionName": "interventionName",
      "name": "name",
      "preauthDiagnosisType": "preauthDiagnosisType",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "siteCode": "siteCode",
      "siteCodeType": "siteCodeType",
      "status": "status"
    }
  ],
  "preauthDoctors": [
    {
      "doctorProfile": {
        "active": true,
        "contacts": [
          {}
        ],
        "country": "country",
        "currencyCode": "currencyCode",
        "guid": "guid",
        "id": 0,
        "identifiers": [
          {}
        ],
        "name": "name",
        "nationalIdentifier": "nationalIdentifier",
        "practitionerCadre": "practitionerCadre",
        "practitionerDisciplineName": "practitionerDisciplineName",
        "practitionerGender": "practitionerGender",
        "practitionerIdNumber": "practitionerIdNumber",
        "practitionerIdType": "practitionerIdType",
        "practitionerInHealthWorkerRegistry": true,
        "practitionerLicenceNumber": "practitionerLicenceNumber",
        "practitionerLicenceStart": "practitionerLicenceStart",
        "practitionerLicenceType": "practitionerLicenceType",
        "practitionerLicenceValidity": "practitionerLicenceValidity",
        "practitionerLicenseBody": "practitionerLicenseBody",
        "practitionerLicenseStatus": "practitionerLicenseStatus",
        "practitionerPostalAddress": "practitionerPostalAddress",
        "practitionerQualifications": "practitionerQualifications",
        "practitionerRegistrationNumber": "practitionerRegistrationNumber",
        "practitionerRegistryId": "practitionerRegistryId",
        "practitionerSpecialty": "practitionerSpecialty",
        "practitionerSubSpecialty": "practitionerSubSpecialty",
        "practitionerType": "practitionerType",
        "sladeCode": 0,
        "specialty": [
          "string"
        ],
        "suspended": true,
        "suspensionReason": "suspensionReason"
      },
      "doctorReviewStatus": "doctorReviewStatus",
      "doctorType": "doctorType",
      "guid": "guid",
      "hospitalDoctorName": "hospitalDoctorName",
      "id": 0,
      "isHospitalDoctor": true,
      "name": "name",
      "notes": "notes",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "sladeCode": 0,
      "status": "status"
    }
  ],
  "preauthFlags": [
    {}
  ],
  "preauthItems": [
    {
      "approvedAmount": 0,
      "approvedBy": "approvedBy",
      "approvedByName": "approvedByName",
      "approvedQuantity": "approvedQuantity",
      "approvedUnitPrice": 0,
      "category": "category",
      "chargeDate": "chargeDate",
      "cmCode": "cmCode",
      "description": "description",
      "estimatedAmount": 0,
      "guid": "guid",
      "id": 0,
      "intervention": "intervention",
      "interventionCode": "interventionCode",
      "interventionName": "interventionName",
      "name": "name",
      "payerInvoiceLineNo": "payerInvoiceLineNo",
      "providerCurrency": "providerCurrency",
      "quantity": "quantity",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "schemeCode": "UHC",
      "schemeName": "schemeName",
      "status": "status",
      "unitPrice": 0
    }
  ],
  "preauthNotes": [
    {
      "author": "author",
      "authorEmail": "authorEmail",
      "authorName": "authorName",
      "guid": "guid",
      "id": 0,
      "note": "note",
      "organisationName": "organisationName",
      "source": "source"
    }
  ],
  "preauthType": "preauthType",
  "providerConsent": true,
  "providerCurrency": "providerCurrency",
  "providerDetails": {
    "active": true,
    "bpLevel": "bpLevel",
    "businessPartnerId": 0,
    "guid": "guid",
    "identifiers": [
      {
        "identifier": "identifier",
        "identifierType": "identifierType"
      }
    ],
    "name": "name",
    "nationalIdentifier": "nationalIdentifier",
    "sladeCode": 0
  },
  "providerName": "providerName",
  "providerNotificationEmail": "providerNotificationEmail",
  "reasonForAcuteDialysis": "reasonForAcuteDialysis",
  "reasonForSelectingOther": "reasonForSelectingOther",
  "requestExtraData": {
    "anaesthesiaType": "anaesthesiaType",
    "carcinomaStaging": "STAGE_1",
    "chiefComplaint": "chiefComplaint",
    "clinicalIndications": "clinicalIndications",
    "coinsuranceDetails": "coinsuranceDetails",
    "comorbidity": "comorbidity",
    "conditionEmploymentRelated": true,
    "conditionOtherRelated": true,
    "consultationDescription": "consultationDescription",
    "costPerSession": 0,
    "eyeExaminationAmount": 0,
    "eyeExaminationDescription": "eyeExaminationDescription",
    "frameAmount": 0,
    "frameDescription": "frameDescription",
    "hasCoinsurance": true,
    "hpi": "hpi",
    "investigations": "investigations",
    "lensAmount": 0,
    "lensDescription": "lensDescription",
    "lensPrescription": "lensPrescription",
    "metastases": [
      "LUNG"
    ],
    "physicalExamination": "physicalExamination",
    "progressReport": "progressReport",
    "reasonForService": "reasonForService",
    "replacement": "replacement",
    "sessionExpectedDate": "sessionExpectedDate",
    "sessionsFrequency": "sessionsFrequency",
    "sessionsRequired": 0,
    "subType": "subType",
    "treatmentSetting": [
      "DAY_WARD"
    ],
    "vitalSigns": "vitalSigns"
  },
  "responseExtraData": "responseExtraData",
  "serviceEnd": "serviceEnd",
  "serviceStart": "serviceStart",
  "sessionExpectedDate": "sessionExpectedDate",
  "sessionType": "sessionType",
  "sessionsFrequency": "sessionsFrequency",
  "sessionsRequired": 0,
  "status": "status",
  "submissionDateIn_EAT": "submissionDateIn_EAT",
  "token": "token",
  "totalEstimatedAmountForPreauth": 0,
  "totalInterimApprovedAmountForPreauth": 0,
  "updatedByName": "updatedByName"
}
```

</details>

<details><summary><code>400</code> — Invalid request</summary>

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

<details><summary><code>500</code> — Internal server error</summary>

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "intervention_code": "intervention_code",
  "service_start": "service_start",
  "service_end": "service_end",
  "items": [
    {}
  ],
  "diagnoses": [
    {}
  ],
  "doctors": [
    {}
  ],
  "attachments": [
    {}
  ],
  "provider_notification_email": "user@example.com"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: multipart/form-data' \
  --form consent_token=consent_token \
  --form intervention_code=intervention_code \
  --form service_start=service_start \
  --form service_end=service_end \
  --form items=[object Object] \
  --form diagnoses=[object Object] \
  --form doctors=[object Object] \
  --form attachments=[object Object] \
  --form provider_notification_email=user@example.com
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "accessPoint": "accessPoint",
  "anaesthesiaType": "anaesthesiaType",
  "authorization": 0,
  "authorizationDetails": {
    "authCode": "authCode",
    "authorizationReason": "authorizationReason",
    "authorizationType": [
      "string"
    ],
    "authorizingDeviceOs": "authorizingDeviceOs",
    "beneficiary": 0,
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryName": "beneficiaryName",
    "beneficiaryNumber": "beneficiaryNumber",
    "beneficiaryScheme": "beneficiaryScheme",
    "benefitType": "benefitType",
    "biometricMatchLogId": "biometricMatchLogId",
    "children": [
      {
        "authorizingDeviceOs": "authorizingDeviceOs",
        "beneficiaryCode": "beneficiaryCode",
        "beneficiaryName": "beneficiaryName",
        "beneficiaryNumber": "beneficiaryNumber",
        "biometricMatchLogId": "biometricMatchLogId",
        "ekycToken": "ekycToken",
        "guid": "guid",
        "interventions": [
          {}
        ],
        "isBiometricsDischargeAuthorization": true,
        "isElective": true,
        "isOpen": true,
        "parentAuthorization": 0,
        "parentType": "parentType",
        "preauthTypes": {},
        "sessionType": "sessionType",
        "shaGuid": "shaGuid",
        "shaVerificationRequestId": "shaVerificationRequestId",
        "status": "status",
        "token": "token",
        "workStationId": "workStationId"
      }
    ],
    "createdByName": "createdByName",
    "dateAuthorized": "dateAuthorized",
    "ekycToken": "ekycToken",
    "electivePreauth": {
      "doctorReviewStatus": "doctorReviewStatus",
      "isElective": true,
      "memberName": "memberName",
      "preauthType": "preauthType",
      "serviceEnd": "serviceEnd",
      "serviceStart": "serviceStart",
      "status": "status"
    },
    "eligibility": "eligibility",
    "eligibilityDetails": {
      "cover": {
        "group": "group",
        "groupCode": "groupCode",
        "jobGroup": "jobGroup",
        "validFrom": "validFrom",
        "validTo": "validTo"
      },
      "member": {
        "age": 0,
        "beneficiaryCode": "beneficiaryCode",
        "gender": "gender",
        "group": "group",
        "idNo": "idNo",
        "idNoType": "idNoType",
        "isAlive": true,
        "isMinor": true,
        "isPrincipal": true,
        "names": "names",
        "principalMember": "principalMember",
        "principalRelationship": "principalRelationship"
      }
    },
    "endDate": "endDate",
    "endedVia": [
      "string"
    ],
    "expiry": "expiry",
    "guardian": "guardian",
    "guid": "guid",
    "id": 0,
    "interventions": [
      {
        "activeForUhc": true,
        "allowedInterventions": [
          {}
        ],
        "applicableSchemes": [
          "string"
        ],
        "authInterventionId": 0,
        "code": "code",
        "dispenseMedication": true,
        "fallBackKephLevelTariff": 0,
        "fund": "fund",
        "id": 0,
        "interventionCombinations": [
          {}
        ],
        "kephLevelTarrif": 0,
        "name": "name",
        "needsPreauth": true,
        "numberOfDaysToFallback": 0,
        "overallTariff": 0,
        "packageCombinations": [
          {}
        ],
        "paymentMechanism": "paymentMechanism",
        "preauthFinalised": true,
        "prescriptionMedication": true,
        "requiresSurgicalPreauth": true,
        "standaloneInterventions": [
          {}
        ],
        "subBenefitCode": "subBenefitCode",
        "supportedScheme": "supportedScheme"
      }
    ],
    "isBiometricsDischargeAuthorization": true,
    "isComplete": true,
    "isElective": true,
    "isOpen": true,
    "label": "label",
    "needsPreauth": true,
    "notes": "notes",
    "overallPreauthFinalised": true,
    "parentAuthorization": 0,
    "parentPreauth": {
      "authorizingDeviceOs": "authorizingDeviceOs",
      "beneficiaryCode": "beneficiaryCode",
      "beneficiaryName": "beneficiaryName",
      "beneficiaryNumber": "beneficiaryNumber",
      "biometricMatchLogId": "biometricMatchLogId",
      "ekycToken": "ekycToken",
      "guid": "guid",
      "interventions": [
        {}
      ],
      "isBiometricsDischargeAuthorization": true,
      "isElective": true,
      "isOpen": true,
      "parentAuthorization": 0,
      "parentType": "parentType",
      "preauthTypes": {},
      "sessionType": "sessionType",
      "shaGuid": "shaGuid",
      "shaVerificationRequestId": "shaVerificationRequestId",
      "status": "status",
      "token": "token",
      "workStationId": "workStationId"
    },
    "parentType": "parentType",
    "payerName": "payerName",
    "payerSladeCode": 0,
    "preauthIds": [
      0
    ],
    "preauthTypes": {},
    "provider": 0,
    "providerFid": "providerFid",
    "providerName": "providerName",
    "requestedBy": "requestedBy",
    "sessionType": "sessionType",
    "shaGuid": "shaGuid",
    "shaVerificationRequest": {
      "EmbedExpiry": 0,
      "embededToken": "embededToken",
      "requestId": "requestId",
      "requestUrl": "requestUrl"
    },
    "shaVerificationRequestId": "shaVerificationRequestId",
    "status": "status",
    "token": "token",
    "workStationId": "workStationId"
  },
  "beneficiaryDetails": {
    "DoB": "DoB",
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryId": 0,
    "categoryCode": "categoryCode",
    "categoryName": "categoryName",
    "firstName": "firstName",
    "gender": "gender",
    "guid": "guid",
    "identifiers": [
      {
        "identifier": "identifier",
        "identifierType": "identifierType"
      }
    ],
    "lastName": "lastName",
    "otherNames": "otherNames",
    "schemeCode": "UHC",
    "schemeName": "schemeName"
  },
  "carcinomaStaging": "carcinomaStaging",
  "clinicalIndications": "clinicalIndications",
  "comorbidity": "comorbidity",
  "conditionCause": "conditionCause",
  "conditionEmploymentRelated": true,
  "conditionOtherRelated": true,
  "costPerSession": "costPerSession",
  "countdown": 0,
  "createdByName": "createdByName",
  "description": "description",
  "doctorApproved": true,
  "doctorReviewStatus": "doctorReviewStatus",
  "finalApprovedAmount": 0,
  "guid": "guid",
  "id": 0,
  "interventionCode": "interventionCode",
  "interventionData": {
    "code": "code",
    "fallBackKephLevelTariff": 0,
    "guid": "guid",
    "id": 0,
    "kephLevelTarrif": 0,
    "name": "name",
    "numberOfDaysToFallback": 0,
    "overallTariff": 0,
    "paymentMechanism": "paymentMechanism",
    "status": "status"
  },
  "isElective": true,
  "isEmergency": true,
  "isHmisPreauth": true,
  "isOncology": true,
  "isOptical": true,
  "isRadiology": true,
  "isRenal": true,
  "isRequestPhase": true,
  "isResponsePhase": true,
  "isSurgical": true,
  "lengthOfStay": 0,
  "memberIdentifier": "memberIdentifier",
  "memberIsVip": true,
  "memberIsVvip": true,
  "memberName": "memberName",
  "memberScheme": "memberScheme",
  "metastases": "metastases",
  "needsDoctorApproval": true,
  "numberOfPreauthDoctorsRequired": 0,
  "otherMetastases": "otherMetastases",
  "payerIdentifier": "payerIdentifier",
  "payerInvoiceNo": "payerInvoiceNo",
  "payerName": "payerName",
  "preauthAttachments": [
    {
      "attachment": 0,
      "attachmentType": "DISCHARGE_SUMMARY",
      "author": "author",
      "authorEmail": "authorEmail",
      "authorName": "authorName",
      "contentType": "contentType",
      "description": "description",
      "guid": "guid",
      "id": 0,
      "interventionCode": "interventionCode",
      "organisationName": "organisationName",
      "source": "source",
      "title": "title",
      "uploadedFile": "uploadedFile"
    }
  ],
  "preauthDiagnoses": [
    {
      "authorizationIntervention": "authorizationIntervention",
      "description": "description",
      "guid": "guid",
      "id": 0,
      "interventionCode": "interventionCode",
      "interventionName": "interventionName",
      "name": "name",
      "preauthDiagnosisType": "preauthDiagnosisType",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "siteCode": "siteCode",
      "siteCodeType": "siteCodeType",
      "status": "status"
    }
  ],
  "preauthDoctors": [
    {
      "doctorProfile": {
        "active": true,
        "contacts": [
          {}
        ],
        "country": "country",
        "currencyCode": "currencyCode",
        "guid": "guid",
        "id": 0,
        "identifiers": [
          {}
        ],
        "name": "name",
        "nationalIdentifier": "nationalIdentifier",
        "practitionerCadre": "practitionerCadre",
        "practitionerDisciplineName": "practitionerDisciplineName",
        "practitionerGender": "practitionerGender",
        "practitionerIdNumber": "practitionerIdNumber",
        "practitionerIdType": "practitionerIdType",
        "practitionerInHealthWorkerRegistry": true,
        "practitionerLicenceNumber": "practitionerLicenceNumber",
        "practitionerLicenceStart": "practitionerLicenceStart",
        "practitionerLicenceType": "practitionerLicenceType",
        "practitionerLicenceValidity": "practitionerLicenceValidity",
        "practitionerLicenseBody": "practitionerLicenseBody",
        "practitionerLicenseStatus": "practitionerLicenseStatus",
        "practitionerPostalAddress": "practitionerPostalAddress",
        "practitionerQualifications": "practitionerQualifications",
        "practitionerRegistrationNumber": "practitionerRegistrationNumber",
        "practitionerRegistryId": "practitionerRegistryId",
        "practitionerSpecialty": "practitionerSpecialty",
        "practitionerSubSpecialty": "practitionerSubSpecialty",
        "practitionerType": "practitionerType",
        "sladeCode": 0,
        "specialty": [
          "string"
        ],
        "suspended": true,
        "suspensionReason": "suspensionReason"
      },
      "doctorReviewStatus": "doctorReviewStatus",
      "doctorType": "doctorType",
      "guid": "guid",
      "hospitalDoctorName": "hospitalDoctorName",
      "id": 0,
      "isHospitalDoctor": true,
      "name": "name",
      "notes": "notes",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "sladeCode": 0,
      "status": "status"
    }
  ],
  "preauthFlags": [
    {}
  ],
  "preauthItems": [
    {
      "approvedAmount": 0,
      "approvedBy": "approvedBy",
      "approvedByName": "approvedByName",
      "approvedQuantity": "approvedQuantity",
      "approvedUnitPrice": 0,
      "category": "category",
      "chargeDate": "chargeDate",
      "cmCode": "cmCode",
      "description": "description",
      "estimatedAmount": 0,
      "guid": "guid",
      "id": 0,
      "intervention": "intervention",
      "interventionCode": "interventionCode",
      "interventionName": "interventionName",
      "name": "name",
      "payerInvoiceLineNo": "payerInvoiceLineNo",
      "providerCurrency": "providerCurrency",
      "quantity": "quantity",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "schemeCode": "UHC",
      "schemeName": "schemeName",
      "status": "status",
      "unitPrice": 0
    }
  ],
  "preauthNotes": [
    {
      "author": "author",
      "authorEmail": "authorEmail",
      "authorName": "authorName",
      "guid": "guid",
      "id": 0,
      "note": "note",
      "organisationName": "organisationName",
      "source": "source"
    }
  ],
  "preauthType": "preauthType",
  "providerConsent": true,
  "providerCurrency": "providerCurrency",
  "providerDetails": {
    "active": true,
    "bpLevel": "bpLevel",
    "businessPartnerId": 0,
    "guid": "guid",
    "identifiers": [
      {
        "identifier": "identifier",
        "identifierType": "identifierType"
      }
    ],
    "name": "name",
    "nationalIdentifier": "nationalIdentifier",
    "sladeCode": 0
  },
  "providerName": "providerName",
  "providerNotificationEmail": "providerNotificationEmail",
  "reasonForAcuteDialysis": "reasonForAcuteDialysis",
  "reasonForSelectingOther": "reasonForSelectingOther",
  "requestExtraData": {
    "anaesthesiaType": "anaesthesiaType",
    "carcinomaStaging": "STAGE_1",
    "chiefComplaint": "chiefComplaint",
    "clinicalIndications": "clinicalIndications",
    "coinsuranceDetails": "coinsuranceDetails",
    "comorbidity": "comorbidity",
    "conditionEmploymentRelated": true,
    "conditionOtherRelated": true,
    "consultationDescription": "consultationDescription",
    "costPerSession": 0,
    "eyeExaminationAmount": 0,
    "eyeExaminationDescription": "eyeExaminationDescription",
    "frameAmount": 0,
    "frameDescription": "frameDescription",
    "hasCoinsurance": true,
    "hpi": "hpi",
    "investigations": "investigations",
    "lensAmount": 0,
    "lensDescription": "lensDescription",
    "lensPrescription": "lensPrescription",
    "metastases": [
      "LUNG"
    ],
    "physicalExamination": "physicalExamination",
    "progressReport": "progressReport",
    "reasonForService": "reasonForService",
    "replacement": "replacement",
    "sessionExpectedDate": "sessionExpectedDate",
    "sessionsFrequency": "sessionsFrequency",
    "sessionsRequired": 0,
    "subType": "subType",
    "treatmentSetting": [
      "DAY_WARD"
    ],
    "vitalSigns": "vitalSigns"
  },
  "responseExtraData": "responseExtraData",
  "serviceEnd": "serviceEnd",
  "serviceStart": "serviceStart",
  "sessionExpectedDate": "sessionExpectedDate",
  "sessionType": "sessionType",
  "sessionsFrequency": "sessionsFrequency",
  "sessionsRequired": 0,
  "status": "status",
  "submissionDateIn_EAT": "submissionDateIn_EAT",
  "token": "token",
  "totalEstimatedAmountForPreauth": 0,
  "totalInterimApprovedAmountForPreauth": 0,
  "updatedByName": "updatedByName"
}
```

</details>

<details><summary><code>400</code> — Invalid request</summary>

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

<details><summary><code>500</code> — Internal server error</summary>

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
curl --request DELETE \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths/diagnoses/:icd_code' \
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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "accessPoint": "accessPoint",
  "anaesthesiaType": "anaesthesiaType",
  "authorization": 0,
  "authorizationDetails": {
    "authCode": "authCode",
    "authorizationReason": "authorizationReason",
    "authorizationType": [
      "string"
    ],
    "authorizingDeviceOs": "authorizingDeviceOs",
    "beneficiary": 0,
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryName": "beneficiaryName",
    "beneficiaryNumber": "beneficiaryNumber",
    "beneficiaryScheme": "beneficiaryScheme",
    "benefitType": "benefitType",
    "biometricMatchLogId": "biometricMatchLogId",
    "children": [
      {
        "authorizingDeviceOs": "authorizingDeviceOs",
        "beneficiaryCode": "beneficiaryCode",
        "beneficiaryName": "beneficiaryName",
        "beneficiaryNumber": "beneficiaryNumber",
        "biometricMatchLogId": "biometricMatchLogId",
        "ekycToken": "ekycToken",
        "guid": "guid",
        "interventions": [
          {}
        ],
        "isBiometricsDischargeAuthorization": true,
        "isElective": true,
        "isOpen": true,
        "parentAuthorization": 0,
        "parentType": "parentType",
        "preauthTypes": {},
        "sessionType": "sessionType",
        "shaGuid": "shaGuid",
        "shaVerificationRequestId": "shaVerificationRequestId",
        "status": "status",
        "token": "token",
        "workStationId": "workStationId"
      }
    ],
    "createdByName": "createdByName",
    "dateAuthorized": "dateAuthorized",
    "ekycToken": "ekycToken",
    "electivePreauth": {
      "doctorReviewStatus": "doctorReviewStatus",
      "isElective": true,
      "memberName": "memberName",
      "preauthType": "preauthType",
      "serviceEnd": "serviceEnd",
      "serviceStart": "serviceStart",
      "status": "status"
    },
    "eligibility": "eligibility",
    "eligibilityDetails": {
      "cover": {
        "group": "group",
        "groupCode": "groupCode",
        "jobGroup": "jobGroup",
        "validFrom": "validFrom",
        "validTo": "validTo"
      },
      "member": {
        "age": 0,
        "beneficiaryCode": "beneficiaryCode",
        "gender": "gender",
        "group": "group",
        "idNo": "idNo",
        "idNoType": "idNoType",
        "isAlive": true,
        "isMinor": true,
        "isPrincipal": true,
        "names": "names",
        "principalMember": "principalMember",
        "principalRelationship": "principalRelationship"
      }
    },
    "endDate": "endDate",
    "endedVia": [
      "string"
    ],
    "expiry": "expiry",
    "guardian": "guardian",
    "guid": "guid",
    "id": 0,
    "interventions": [
      {
        "activeForUhc": true,
        "allowedInterventions": [
          {}
        ],
        "applicableSchemes": [
          "string"
        ],
        "authInterventionId": 0,
        "code": "code",
        "dispenseMedication": true,
        "fallBackKephLevelTariff": 0,
        "fund": "fund",
        "id": 0,
        "interventionCombinations": [
          {}
        ],
        "kephLevelTarrif": 0,
        "name": "name",
        "needsPreauth": true,
        "numberOfDaysToFallback": 0,
        "overallTariff": 0,
        "packageCombinations": [
          {}
        ],
        "paymentMechanism": "paymentMechanism",
        "preauthFinalised": true,
        "prescriptionMedication": true,
        "requiresSurgicalPreauth": true,
        "standaloneInterventions": [
          {}
        ],
        "subBenefitCode": "subBenefitCode",
        "supportedScheme": "supportedScheme"
      }
    ],
    "isBiometricsDischargeAuthorization": true,
    "isComplete": true,
    "isElective": true,
    "isOpen": true,
    "label": "label",
    "needsPreauth": true,
    "notes": "notes",
    "overallPreauthFinalised": true,
    "parentAuthorization": 0,
    "parentPreauth": {
      "authorizingDeviceOs": "authorizingDeviceOs",
      "beneficiaryCode": "beneficiaryCode",
      "beneficiaryName": "beneficiaryName",
      "beneficiaryNumber": "beneficiaryNumber",
      "biometricMatchLogId": "biometricMatchLogId",
      "ekycToken": "ekycToken",
      "guid": "guid",
      "interventions": [
        {}
      ],
      "isBiometricsDischargeAuthorization": true,
      "isElective": true,
      "isOpen": true,
      "parentAuthorization": 0,
      "parentType": "parentType",
      "preauthTypes": {},
      "sessionType": "sessionType",
      "shaGuid": "shaGuid",
      "shaVerificationRequestId": "shaVerificationRequestId",
      "status": "status",
      "token": "token",
      "workStationId": "workStationId"
    },
    "parentType": "parentType",
    "payerName": "payerName",
    "payerSladeCode": 0,
    "preauthIds": [
      0
    ],
    "preauthTypes": {},
    "provider": 0,
    "providerFid": "providerFid",
    "providerName": "providerName",
    "requestedBy": "requestedBy",
    "sessionType": "sessionType",
    "shaGuid": "shaGuid",
    "shaVerificationRequest": {
      "EmbedExpiry": 0,
      "embededToken": "embededToken",
      "requestId": "requestId",
      "requestUrl": "requestUrl"
    },
    "shaVerificationRequestId": "shaVerificationRequestId",
    "status": "status",
    "token": "token",
    "workStationId": "workStationId"
  },
  "beneficiaryDetails": {
    "DoB": "DoB",
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryId": 0,
    "categoryCode": "categoryCode",
    "categoryName": "categoryName",
    "firstName": "firstName",
    "gender": "gender",
    "guid": "guid",
    "identifiers": [
      {
        "identifier": "identifier",
        "identifierType": "identifierType"
      }
    ],
    "lastName": "lastName",
    "otherNames": "otherNames",
    "schemeCode": "UHC",
    "schemeName": "schemeName"
  },
  "carcinomaStaging": "carcinomaStaging",
  "clinicalIndications": "clinicalIndications",
  "comorbidity": "comorbidity",
  "conditionCause": "conditionCause",
  "conditionEmploymentRelated": true,
  "conditionOtherRelated": true,
  "costPerSession": "costPerSession",
  "countdown": 0,
  "createdByName": "createdByName",
  "description": "description",
  "doctorApproved": true,
  "doctorReviewStatus": "doctorReviewStatus",
  "finalApprovedAmount": 0,
  "guid": "guid",
  "id": 0,
  "interventionCode": "interventionCode",
  "interventionData": {
    "code": "code",
    "fallBackKephLevelTariff": 0,
    "guid": "guid",
    "id": 0,
    "kephLevelTarrif": 0,
    "name": "name",
    "numberOfDaysToFallback": 0,
    "overallTariff": 0,
    "paymentMechanism": "paymentMechanism",
    "status": "status"
  },
  "isElective": true,
  "isEmergency": true,
  "isHmisPreauth": true,
  "isOncology": true,
  "isOptical": true,
  "isRadiology": true,
  "isRenal": true,
  "isRequestPhase": true,
  "isResponsePhase": true,
  "isSurgical": true,
  "lengthOfStay": 0,
  "memberIdentifier": "memberIdentifier",
  "memberIsVip": true,
  "memberIsVvip": true,
  "memberName": "memberName",
  "memberScheme": "memberScheme",
  "metastases": "metastases",
  "needsDoctorApproval": true,
  "numberOfPreauthDoctorsRequired": 0,
  "otherMetastases": "otherMetastases",
  "payerIdentifier": "payerIdentifier",
  "payerInvoiceNo": "payerInvoiceNo",
  "payerName": "payerName",
  "preauthAttachments": [
    {
      "attachment": 0,
      "attachmentType": "DISCHARGE_SUMMARY",
      "author": "author",
      "authorEmail": "authorEmail",
      "authorName": "authorName",
      "contentType": "contentType",
      "description": "description",
      "guid": "guid",
      "id": 0,
      "interventionCode": "interventionCode",
      "organisationName": "organisationName",
      "source": "source",
      "title": "title",
      "uploadedFile": "uploadedFile"
    }
  ],
  "preauthDiagnoses": [
    {
      "authorizationIntervention": "authorizationIntervention",
      "description": "description",
      "guid": "guid",
      "id": 0,
      "interventionCode": "interventionCode",
      "interventionName": "interventionName",
      "name": "name",
      "preauthDiagnosisType": "preauthDiagnosisType",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "siteCode": "siteCode",
      "siteCodeType": "siteCodeType",
      "status": "status"
    }
  ],
  "preauthDoctors": [
    {
      "doctorProfile": {
        "active": true,
        "contacts": [
          {}
        ],
        "country": "country",
        "currencyCode": "currencyCode",
        "guid": "guid",
        "id": 0,
        "identifiers": [
          {}
        ],
        "name": "name",
        "nationalIdentifier": "nationalIdentifier",
        "practitionerCadre": "practitionerCadre",
        "practitionerDisciplineName": "practitionerDisciplineName",
        "practitionerGender": "practitionerGender",
        "practitionerIdNumber": "practitionerIdNumber",
        "practitionerIdType": "practitionerIdType",
        "practitionerInHealthWorkerRegistry": true,
        "practitionerLicenceNumber": "practitionerLicenceNumber",
        "practitionerLicenceStart": "practitionerLicenceStart",
        "practitionerLicenceType": "practitionerLicenceType",
        "practitionerLicenceValidity": "practitionerLicenceValidity",
        "practitionerLicenseBody": "practitionerLicenseBody",
        "practitionerLicenseStatus": "practitionerLicenseStatus",
        "practitionerPostalAddress": "practitionerPostalAddress",
        "practitionerQualifications": "practitionerQualifications",
        "practitionerRegistrationNumber": "practitionerRegistrationNumber",
        "practitionerRegistryId": "practitionerRegistryId",
        "practitionerSpecialty": "practitionerSpecialty",
        "practitionerSubSpecialty": "practitionerSubSpecialty",
        "practitionerType": "practitionerType",
        "sladeCode": 0,
        "specialty": [
          "string"
        ],
        "suspended": true,
        "suspensionReason": "suspensionReason"
      },
      "doctorReviewStatus": "doctorReviewStatus",
      "doctorType": "doctorType",
      "guid": "guid",
      "hospitalDoctorName": "hospitalDoctorName",
      "id": 0,
      "isHospitalDoctor": true,
      "name": "name",
      "notes": "notes",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "sladeCode": 0,
      "status": "status"
    }
  ],
  "preauthFlags": [
    {}
  ],
  "preauthItems": [
    {
      "approvedAmount": 0,
      "approvedBy": "approvedBy",
      "approvedByName": "approvedByName",
      "approvedQuantity": "approvedQuantity",
      "approvedUnitPrice": 0,
      "category": "category",
      "chargeDate": "chargeDate",
      "cmCode": "cmCode",
      "description": "description",
      "estimatedAmount": 0,
      "guid": "guid",
      "id": 0,
      "intervention": "intervention",
      "interventionCode": "interventionCode",
      "interventionName": "interventionName",
      "name": "name",
      "payerInvoiceLineNo": "payerInvoiceLineNo",
      "providerCurrency": "providerCurrency",
      "quantity": "quantity",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "schemeCode": "UHC",
      "schemeName": "schemeName",
      "status": "status",
      "unitPrice": 0
    }
  ],
  "preauthNotes": [
    {
      "author": "author",
      "authorEmail": "authorEmail",
      "authorName": "authorName",
      "guid": "guid",
      "id": 0,
      "note": "note",
      "organisationName": "organisationName",
      "source": "source"
    }
  ],
  "preauthType": "preauthType",
  "providerConsent": true,
  "providerCurrency": "providerCurrency",
  "providerDetails": {
    "active": true,
    "bpLevel": "bpLevel",
    "businessPartnerId": 0,
    "guid": "guid",
    "identifiers": [
      {
        "identifier": "identifier",
        "identifierType": "identifierType"
      }
    ],
    "name": "name",
    "nationalIdentifier": "nationalIdentifier",
    "sladeCode": 0
  },
  "providerName": "providerName",
  "providerNotificationEmail": "providerNotificationEmail",
  "reasonForAcuteDialysis": "reasonForAcuteDialysis",
  "reasonForSelectingOther": "reasonForSelectingOther",
  "requestExtraData": {
    "anaesthesiaType": "anaesthesiaType",
    "carcinomaStaging": "STAGE_1",
    "chiefComplaint": "chiefComplaint",
    "clinicalIndications": "clinicalIndications",
    "coinsuranceDetails": "coinsuranceDetails",
    "comorbidity": "comorbidity",
    "conditionEmploymentRelated": true,
    "conditionOtherRelated": true,
    "consultationDescription": "consultationDescription",
    "costPerSession": 0,
    "eyeExaminationAmount": 0,
    "eyeExaminationDescription": "eyeExaminationDescription",
    "frameAmount": 0,
    "frameDescription": "frameDescription",
    "hasCoinsurance": true,
    "hpi": "hpi",
    "investigations": "investigations",
    "lensAmount": 0,
    "lensDescription": "lensDescription",
    "lensPrescription": "lensPrescription",
    "metastases": [
      "LUNG"
    ],
    "physicalExamination": "physicalExamination",
    "progressReport": "progressReport",
    "reasonForService": "reasonForService",
    "replacement": "replacement",
    "sessionExpectedDate": "sessionExpectedDate",
    "sessionsFrequency": "sessionsFrequency",
    "sessionsRequired": 0,
    "subType": "subType",
    "treatmentSetting": [
      "DAY_WARD"
    ],
    "vitalSigns": "vitalSigns"
  },
  "responseExtraData": "responseExtraData",
  "serviceEnd": "serviceEnd",
  "serviceStart": "serviceStart",
  "sessionExpectedDate": "sessionExpectedDate",
  "sessionType": "sessionType",
  "sessionsFrequency": "sessionsFrequency",
  "sessionsRequired": 0,
  "status": "status",
  "submissionDateIn_EAT": "submissionDateIn_EAT",
  "token": "token",
  "totalEstimatedAmountForPreauth": 0,
  "totalInterimApprovedAmountForPreauth": 0,
  "updatedByName": "updatedByName"
}
```

</details>

<details><summary><code>400</code> — Invalid request</summary>

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

<details><summary><code>401</code> — Unauthorized</summary>

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

<details><summary><code>403</code> — Forbidden</summary>

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

<details><summary><code>500</code> — Internal server error</summary>

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

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "intervention_code": "intervention_code",
  "practitioner_registration_number": "practitioner_registration_number"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request DELETE \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths/doctors' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "intervention_code": "intervention_code",
  "practitioner_registration_number": "practitioner_registration_number"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Preauth Doctor removed successfully</summary>

_none_


**Example** (portal sample; nested objects show the full shape)

```json
{}
```

</details>

<details><summary><code>400</code> — Invalid request</summary>

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

<details><summary><code>401</code> — Unauthorized</summary>

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

<details><summary><code>403</code> — Forbidden</summary>

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

<details><summary><code>500</code> — Internal server error</summary>

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
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/preauths/cancel' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "intervention_code": "intervention_code"
}'
```
</details>

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


**Example** (portal sample; nested objects show the full shape)

```json
{
  "accessPoint": "accessPoint",
  "anaesthesiaType": "anaesthesiaType",
  "authorization": 0,
  "authorizationDetails": {
    "authCode": "authCode",
    "authorizationReason": "authorizationReason",
    "authorizationType": [
      "string"
    ],
    "authorizingDeviceOs": "authorizingDeviceOs",
    "beneficiary": 0,
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryName": "beneficiaryName",
    "beneficiaryNumber": "beneficiaryNumber",
    "beneficiaryScheme": "beneficiaryScheme",
    "benefitType": "benefitType",
    "biometricMatchLogId": "biometricMatchLogId",
    "children": [
      {
        "authorizingDeviceOs": "authorizingDeviceOs",
        "beneficiaryCode": "beneficiaryCode",
        "beneficiaryName": "beneficiaryName",
        "beneficiaryNumber": "beneficiaryNumber",
        "biometricMatchLogId": "biometricMatchLogId",
        "ekycToken": "ekycToken",
        "guid": "guid",
        "interventions": [
          {}
        ],
        "isBiometricsDischargeAuthorization": true,
        "isElective": true,
        "isOpen": true,
        "parentAuthorization": 0,
        "parentType": "parentType",
        "preauthTypes": {},
        "sessionType": "sessionType",
        "shaGuid": "shaGuid",
        "shaVerificationRequestId": "shaVerificationRequestId",
        "status": "status",
        "token": "token",
        "workStationId": "workStationId"
      }
    ],
    "createdByName": "createdByName",
    "dateAuthorized": "dateAuthorized",
    "ekycToken": "ekycToken",
    "electivePreauth": {
      "doctorReviewStatus": "doctorReviewStatus",
      "isElective": true,
      "memberName": "memberName",
      "preauthType": "preauthType",
      "serviceEnd": "serviceEnd",
      "serviceStart": "serviceStart",
      "status": "status"
    },
    "eligibility": "eligibility",
    "eligibilityDetails": {
      "cover": {
        "group": "group",
        "groupCode": "groupCode",
        "jobGroup": "jobGroup",
        "validFrom": "validFrom",
        "validTo": "validTo"
      },
      "member": {
        "age": 0,
        "beneficiaryCode": "beneficiaryCode",
        "gender": "gender",
        "group": "group",
        "idNo": "idNo",
        "idNoType": "idNoType",
        "isAlive": true,
        "isMinor": true,
        "isPrincipal": true,
        "names": "names",
        "principalMember": "principalMember",
        "principalRelationship": "principalRelationship"
      }
    },
    "endDate": "endDate",
    "endedVia": [
      "string"
    ],
    "expiry": "expiry",
    "guardian": "guardian",
    "guid": "guid",
    "id": 0,
    "interventions": [
      {
        "activeForUhc": true,
        "allowedInterventions": [
          {}
        ],
        "applicableSchemes": [
          "string"
        ],
        "authInterventionId": 0,
        "code": "code",
        "dispenseMedication": true,
        "fallBackKephLevelTariff": 0,
        "fund": "fund",
        "id": 0,
        "interventionCombinations": [
          {}
        ],
        "kephLevelTarrif": 0,
        "name": "name",
        "needsPreauth": true,
        "numberOfDaysToFallback": 0,
        "overallTariff": 0,
        "packageCombinations": [
          {}
        ],
        "paymentMechanism": "paymentMechanism",
        "preauthFinalised": true,
        "prescriptionMedication": true,
        "requiresSurgicalPreauth": true,
        "standaloneInterventions": [
          {}
        ],
        "subBenefitCode": "subBenefitCode",
        "supportedScheme": "supportedScheme"
      }
    ],
    "isBiometricsDischargeAuthorization": true,
    "isComplete": true,
    "isElective": true,
    "isOpen": true,
    "label": "label",
    "needsPreauth": true,
    "notes": "notes",
    "overallPreauthFinalised": true,
    "parentAuthorization": 0,
    "parentPreauth": {
      "authorizingDeviceOs": "authorizingDeviceOs",
      "beneficiaryCode": "beneficiaryCode",
      "beneficiaryName": "beneficiaryName",
      "beneficiaryNumber": "beneficiaryNumber",
      "biometricMatchLogId": "biometricMatchLogId",
      "ekycToken": "ekycToken",
      "guid": "guid",
      "interventions": [
        {}
      ],
      "isBiometricsDischargeAuthorization": true,
      "isElective": true,
      "isOpen": true,
      "parentAuthorization": 0,
      "parentType": "parentType",
      "preauthTypes": {},
      "sessionType": "sessionType",
      "shaGuid": "shaGuid",
      "shaVerificationRequestId": "shaVerificationRequestId",
      "status": "status",
      "token": "token",
      "workStationId": "workStationId"
    },
    "parentType": "parentType",
    "payerName": "payerName",
    "payerSladeCode": 0,
    "preauthIds": [
      0
    ],
    "preauthTypes": {},
    "provider": 0,
    "providerFid": "providerFid",
    "providerName": "providerName",
    "requestedBy": "requestedBy",
    "sessionType": "sessionType",
    "shaGuid": "shaGuid",
    "shaVerificationRequest": {
      "EmbedExpiry": 0,
      "embededToken": "embededToken",
      "requestId": "requestId",
      "requestUrl": "requestUrl"
    },
    "shaVerificationRequestId": "shaVerificationRequestId",
    "status": "status",
    "token": "token",
    "workStationId": "workStationId"
  },
  "beneficiaryDetails": {
    "DoB": "DoB",
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryId": 0,
    "categoryCode": "categoryCode",
    "categoryName": "categoryName",
    "firstName": "firstName",
    "gender": "gender",
    "guid": "guid",
    "identifiers": [
      {
        "identifier": "identifier",
        "identifierType": "identifierType"
      }
    ],
    "lastName": "lastName",
    "otherNames": "otherNames",
    "schemeCode": "UHC",
    "schemeName": "schemeName"
  },
  "carcinomaStaging": "carcinomaStaging",
  "clinicalIndications": "clinicalIndications",
  "comorbidity": "comorbidity",
  "conditionCause": "conditionCause",
  "conditionEmploymentRelated": true,
  "conditionOtherRelated": true,
  "costPerSession": "costPerSession",
  "countdown": 0,
  "createdByName": "createdByName",
  "description": "description",
  "doctorApproved": true,
  "doctorReviewStatus": "doctorReviewStatus",
  "finalApprovedAmount": 0,
  "guid": "guid",
  "id": 0,
  "interventionCode": "interventionCode",
  "interventionData": {
    "code": "code",
    "fallBackKephLevelTariff": 0,
    "guid": "guid",
    "id": 0,
    "kephLevelTarrif": 0,
    "name": "name",
    "numberOfDaysToFallback": 0,
    "overallTariff": 0,
    "paymentMechanism": "paymentMechanism",
    "status": "status"
  },
  "isElective": true,
  "isEmergency": true,
  "isHmisPreauth": true,
  "isOncology": true,
  "isOptical": true,
  "isRadiology": true,
  "isRenal": true,
  "isRequestPhase": true,
  "isResponsePhase": true,
  "isSurgical": true,
  "lengthOfStay": 0,
  "memberIdentifier": "memberIdentifier",
  "memberIsVip": true,
  "memberIsVvip": true,
  "memberName": "memberName",
  "memberScheme": "memberScheme",
  "metastases": "metastases",
  "needsDoctorApproval": true,
  "numberOfPreauthDoctorsRequired": 0,
  "otherMetastases": "otherMetastases",
  "payerIdentifier": "payerIdentifier",
  "payerInvoiceNo": "payerInvoiceNo",
  "payerName": "payerName",
  "preauthAttachments": [
    {
      "attachment": 0,
      "attachmentType": "DISCHARGE_SUMMARY",
      "author": "author",
      "authorEmail": "authorEmail",
      "authorName": "authorName",
      "contentType": "contentType",
      "description": "description",
      "guid": "guid",
      "id": 0,
      "interventionCode": "interventionCode",
      "organisationName": "organisationName",
      "source": "source",
      "title": "title",
      "uploadedFile": "uploadedFile"
    }
  ],
  "preauthDiagnoses": [
    {
      "authorizationIntervention": "authorizationIntervention",
      "description": "description",
      "guid": "guid",
      "id": 0,
      "interventionCode": "interventionCode",
      "interventionName": "interventionName",
      "name": "name",
      "preauthDiagnosisType": "preauthDiagnosisType",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "siteCode": "siteCode",
      "siteCodeType": "siteCodeType",
      "status": "status"
    }
  ],
  "preauthDoctors": [
    {
      "doctorProfile": {
        "active": true,
        "contacts": [
          {}
        ],
        "country": "country",
        "currencyCode": "currencyCode",
        "guid": "guid",
        "id": 0,
        "identifiers": [
          {}
        ],
        "name": "name",
        "nationalIdentifier": "nationalIdentifier",
        "practitionerCadre": "practitionerCadre",
        "practitionerDisciplineName": "practitionerDisciplineName",
        "practitionerGender": "practitionerGender",
        "practitionerIdNumber": "practitionerIdNumber",
        "practitionerIdType": "practitionerIdType",
        "practitionerInHealthWorkerRegistry": true,
        "practitionerLicenceNumber": "practitionerLicenceNumber",
        "practitionerLicenceStart": "practitionerLicenceStart",
        "practitionerLicenceType": "practitionerLicenceType",
        "practitionerLicenceValidity": "practitionerLicenceValidity",
        "practitionerLicenseBody": "practitionerLicenseBody",
        "practitionerLicenseStatus": "practitionerLicenseStatus",
        "practitionerPostalAddress": "practitionerPostalAddress",
        "practitionerQualifications": "practitionerQualifications",
        "practitionerRegistrationNumber": "practitionerRegistrationNumber",
        "practitionerRegistryId": "practitionerRegistryId",
        "practitionerSpecialty": "practitionerSpecialty",
        "practitionerSubSpecialty": "practitionerSubSpecialty",
        "practitionerType": "practitionerType",
        "sladeCode": 0,
        "specialty": [
          "string"
        ],
        "suspended": true,
        "suspensionReason": "suspensionReason"
      },
      "doctorReviewStatus": "doctorReviewStatus",
      "doctorType": "doctorType",
      "guid": "guid",
      "hospitalDoctorName": "hospitalDoctorName",
      "id": 0,
      "isHospitalDoctor": true,
      "name": "name",
      "notes": "notes",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "sladeCode": 0,
      "status": "status"
    }
  ],
  "preauthFlags": [
    {}
  ],
  "preauthItems": [
    {
      "approvedAmount": 0,
      "approvedBy": "approvedBy",
      "approvedByName": "approvedByName",
      "approvedQuantity": "approvedQuantity",
      "approvedUnitPrice": 0,
      "category": "category",
      "chargeDate": "chargeDate",
      "cmCode": "cmCode",
      "description": "description",
      "estimatedAmount": 0,
      "guid": "guid",
      "id": 0,
      "intervention": "intervention",
      "interventionCode": "interventionCode",
      "interventionName": "interventionName",
      "name": "name",
      "payerInvoiceLineNo": "payerInvoiceLineNo",
      "providerCurrency": "providerCurrency",
      "quantity": "quantity",
      "requestedBy": "requestedBy",
      "requestedByName": "requestedByName",
      "requestedOn": "requestedOn",
      "respondedBy": "respondedBy",
      "respondedByName": "respondedByName",
      "respondedOn": "respondedOn",
      "responseNote": "responseNote",
      "schemeCode": "UHC",
      "schemeName": "schemeName",
      "status": "status",
      "unitPrice": 0
    }
  ],
  "preauthNotes": [
    {
      "author": "author",
      "authorEmail": "authorEmail",
      "authorName": "authorName",
      "guid": "guid",
      "id": 0,
      "note": "note",
      "organisationName": "organisationName",
      "source": "source"
    }
  ],
  "preauthType": "preauthType",
  "providerConsent": true,
  "providerCurrency": "providerCurrency",
  "providerDetails": {
    "active": true,
    "bpLevel": "bpLevel",
    "businessPartnerId": 0,
    "guid": "guid",
    "identifiers": [
      {
        "identifier": "identifier",
        "identifierType": "identifierType"
      }
    ],
    "name": "name",
    "nationalIdentifier": "nationalIdentifier",
    "sladeCode": 0
  },
  "providerName": "providerName",
  "providerNotificationEmail": "providerNotificationEmail",
  "reasonForAcuteDialysis": "reasonForAcuteDialysis",
  "reasonForSelectingOther": "reasonForSelectingOther",
  "requestExtraData": {
    "anaesthesiaType": "anaesthesiaType",
    "carcinomaStaging": "STAGE_1",
    "chiefComplaint": "chiefComplaint",
    "clinicalIndications": "clinicalIndications",
    "coinsuranceDetails": "coinsuranceDetails",
    "comorbidity": "comorbidity",
    "conditionEmploymentRelated": true,
    "conditionOtherRelated": true,
    "consultationDescription": "consultationDescription",
    "costPerSession": 0,
    "eyeExaminationAmount": 0,
    "eyeExaminationDescription": "eyeExaminationDescription",
    "frameAmount": 0,
    "frameDescription": "frameDescription",
    "hasCoinsurance": true,
    "hpi": "hpi",
    "investigations": "investigations",
    "lensAmount": 0,
    "lensDescription": "lensDescription",
    "lensPrescription": "lensPrescription",
    "metastases": [
      "LUNG"
    ],
    "physicalExamination": "physicalExamination",
    "progressReport": "progressReport",
    "reasonForService": "reasonForService",
    "replacement": "replacement",
    "sessionExpectedDate": "sessionExpectedDate",
    "sessionsFrequency": "sessionsFrequency",
    "sessionsRequired": 0,
    "subType": "subType",
    "treatmentSetting": [
      "DAY_WARD"
    ],
    "vitalSigns": "vitalSigns"
  },
  "responseExtraData": "responseExtraData",
  "serviceEnd": "serviceEnd",
  "serviceStart": "serviceStart",
  "sessionExpectedDate": "sessionExpectedDate",
  "sessionType": "sessionType",
  "sessionsFrequency": "sessionsFrequency",
  "sessionsRequired": 0,
  "status": "status",
  "submissionDateIn_EAT": "submissionDateIn_EAT",
  "token": "token",
  "totalEstimatedAmountForPreauth": 0,
  "totalInterimApprovedAmountForPreauth": 0,
  "updatedByName": "updatedByName"
}
```

</details>

<details><summary><code>400</code> — Invalid request</summary>

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

<details><summary><code>500</code> — Internal server error</summary>

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
