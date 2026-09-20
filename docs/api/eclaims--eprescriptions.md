# ePrescriptions

> Source: https://afyaconnect.dha.go.ke/hie-api/eclaims/eprescriptions · API: **eClaims and Preauth APIs** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

Endpoints for managing prescriptions.

## Endpoints

- [`GET /api/v1/prescriptions`](#get-apiv1prescriptions-preview-prescription) — Preview prescription
- [`POST /api/v1/prescriptions`](#post-apiv1prescriptions-create-prescription) — Create prescription
- [`POST /api/v1/prescriptions/dispenses`](#post-apiv1prescriptionsdispenses-create-dispense) — Create dispense
- [`DELETE /api/v1/prescriptions/doctors`](#delete-apiv1prescriptionsdoctors-remove-prescription-doctor) — Remove prescription doctor

---

### `GET /api/v1/prescriptions` — Preview prescription

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/prescriptions`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eprescriptions#preview-prescription

Fetches a preview of a prescription using a consent token

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | Consent token |

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/prescriptions?consent_token=%3Cconsent_token%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — Prescription preview fetched successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `authorization` | object | no |  |
| `beneficiary` | object | no |  |
| `code` | string | no |  |
| `doctorReviewStatus` | string | no |  |
| `dosage` | object[] | no |  |
| `guid` | string | no |  |
| `id` | integer | no |  |
| `intervention` | object | no |  |
| `replicated` | string | no |  |
| `status` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "authorization": {
    "authCode": "authCode",
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryName": "beneficiaryName",
    "beneficiaryNumber": "beneficiaryNumber",
    "expiry": "expiry",
    "guid": "guid",
    "id": 0,
    "payerName": "payerName",
    "providerName": "providerName",
    "replicated": "replicated",
    "status": "status",
    "token": "token"
  },
  "beneficiary": {
    "age": 0,
    "beneficiaryCode": "beneficiaryCode",
    "contacts": [
      {
        "active": true,
        "contactType": "contactType",
        "contactValue": "contactValue",
        "id": 0,
        "isMainContact": true,
        "ownerType": "ownerType"
      }
    ],
    "dob": "dob",
    "gender": "gender",
    "guid": "guid",
    "id": 0,
    "identifiers": [
      {
        "id": 0,
        "identifier": "identifier",
        "identifierType": "identifierType",
        "isMainIdentifier": true
      }
    ],
    "isPrincipal": true,
    "mainIdentifier": "mainIdentifier",
    "names": "names"
  },
  "code": "code",
  "doctorReviewStatus": "doctorReviewStatus",
  "dosage": [
    {
      "doseQuantity": "doseQuantity",
      "doseUnit": "doseUnit",
      "duration": "duration",
      "durationUnit": "durationUnit",
      "endDate": "endDate",
      "frequency": 0,
      "guid": "guid",
      "id": 0,
      "medication": "medication",
      "medicationIdentifier": "medicationIdentifier",
      "medicationPrice": 0,
      "patientInstruction": "patientInstruction",
      "periodUnit": "periodUnit",
      "practitionerId": "practitionerId",
      "prescription": 0,
      "replicated": "replicated",
      "route": "route",
      "routeCode": "routeCode",
      "startDate": "startDate"
    }
  ],
  "guid": "guid",
  "id": 0,
  "intervention": {
    "accessPoint": "accessPoint",
    "active": true,
    "activeForUhc": true,
    "applicableFacilityOwnership": "applicableFacilityOwnership",
    "applicableGender": "applicableGender",
    "applicableSchemes": [
      "string"
    ],
    "benefit": 0,
    "benefitCode": "benefitCode",
    "benefitName": "benefitName",
    "code": "code",
    "coverageLevel": "coverageLevel",
    "fund": "fund",
    "guid": "guid",
    "id": 0,
    "levelsApplicable": [
      "string"
    ],
    "name": "name",
    "packageCombinations": [
      "string"
    ],
    "parentBenefitCode": "parentBenefitCode",
    "parentBenefitName": "parentBenefitName",
    "paymentMechanism": "paymentMechanism",
    "replicated": "replicated",
    "status": "status",
    "supportedScheme": "supportedScheme"
  },
  "replicated": "replicated",
  "status": "status"
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

### `POST /api/v1/prescriptions` — Create prescription

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/prescriptions`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eprescriptions#create-prescription

Creates a new prescription for a patient

**Request body** — `application/json`, required

Create prescription payload

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | Consent token |
| `identification_number` | string | no | Doctor's ID number |
| `identification_type` | string | no | Identification type e.g. 'registration_number', 'National ID', 'Alien ID', 'Refugee ID' |
| `intervention_code` | string | **yes** | Intervention code |
| `items` | object[] | **yes** | List of prescribed medication items |
| `regulation_body` | string | no | Regulation body e.g. 'KMPDC', 'COC', 'NCK' |

<details><summary>Example request body</summary>

```json
{
  "consent_token": "consent_token",
  "identification_number": "identification_number",
  "identification_type": "identification_type",
  "intervention_code": "intervention_code",
  "items": [
    {
      "additional_instruction": "additional_instruction",
      "dose_quantity": 0,
      "dose_unit": "dose_unit",
      "duration": 0,
      "duration_unit": "duration_unit",
      "end_date": "end_date",
      "frequency": 0,
      "generic_concept_code": "generic_concept_code",
      "needs_refill": true,
      "patient_instruction": "patient_instruction",
      "period_unit": "period_unit",
      "refill_count": 0,
      "start_date": "start_date"
    }
  ],
  "regulation_body": "regulation_body"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/prescriptions' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "consent_token": "consent_token",
  "identification_number": "identification_number",
  "identification_type": "identification_type",
  "intervention_code": "intervention_code",
  "items": [
    {
      "additional_instruction": "additional_instruction",
      "dose_quantity": 0,
      "dose_unit": "dose_unit",
      "duration": 0,
      "duration_unit": "duration_unit",
      "end_date": "end_date",
      "frequency": 0,
      "generic_concept_code": "generic_concept_code",
      "needs_refill": true,
      "patient_instruction": "patient_instruction",
      "period_unit": "period_unit",
      "refill_count": 0,
      "start_date": "start_date"
    }
  ],
  "regulation_body": "regulation_body"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Prescription created successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `authorization` | object | no |  |
| `beneficiary` | object | no |  |
| `code` | string | no |  |
| `doctorReviewStatus` | string | no |  |
| `dosage` | object[] | no |  |
| `guid` | string | no |  |
| `id` | integer | no |  |
| `intervention` | object | no |  |
| `replicated` | string | no |  |
| `status` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "authorization": {
    "authCode": "authCode",
    "beneficiaryCode": "beneficiaryCode",
    "beneficiaryName": "beneficiaryName",
    "beneficiaryNumber": "beneficiaryNumber",
    "expiry": "expiry",
    "guid": "guid",
    "id": 0,
    "payerName": "payerName",
    "providerName": "providerName",
    "replicated": "replicated",
    "status": "status",
    "token": "token"
  },
  "beneficiary": {
    "age": 0,
    "beneficiaryCode": "beneficiaryCode",
    "contacts": [
      {
        "active": true,
        "contactType": "contactType",
        "contactValue": "contactValue",
        "id": 0,
        "isMainContact": true,
        "ownerType": "ownerType"
      }
    ],
    "dob": "dob",
    "gender": "gender",
    "guid": "guid",
    "id": 0,
    "identifiers": [
      {
        "id": 0,
        "identifier": "identifier",
        "identifierType": "identifierType",
        "isMainIdentifier": true
      }
    ],
    "isPrincipal": true,
    "mainIdentifier": "mainIdentifier",
    "names": "names"
  },
  "code": "code",
  "doctorReviewStatus": "doctorReviewStatus",
  "dosage": [
    {
      "doseQuantity": "doseQuantity",
      "doseUnit": "doseUnit",
      "duration": "duration",
      "durationUnit": "durationUnit",
      "endDate": "endDate",
      "frequency": 0,
      "guid": "guid",
      "id": 0,
      "medication": "medication",
      "medicationIdentifier": "medicationIdentifier",
      "medicationPrice": 0,
      "patientInstruction": "patientInstruction",
      "periodUnit": "periodUnit",
      "practitionerId": "practitionerId",
      "prescription": 0,
      "replicated": "replicated",
      "route": "route",
      "routeCode": "routeCode",
      "startDate": "startDate"
    }
  ],
  "guid": "guid",
  "id": 0,
  "intervention": {
    "accessPoint": "accessPoint",
    "active": true,
    "activeForUhc": true,
    "applicableFacilityOwnership": "applicableFacilityOwnership",
    "applicableGender": "applicableGender",
    "applicableSchemes": [
      "string"
    ],
    "benefit": 0,
    "benefitCode": "benefitCode",
    "benefitName": "benefitName",
    "code": "code",
    "coverageLevel": "coverageLevel",
    "fund": "fund",
    "guid": "guid",
    "id": 0,
    "levelsApplicable": [
      "string"
    ],
    "name": "name",
    "packageCombinations": [
      "string"
    ],
    "parentBenefitCode": "parentBenefitCode",
    "parentBenefitName": "parentBenefitName",
    "paymentMechanism": "paymentMechanism",
    "replicated": "replicated",
    "status": "status",
    "supportedScheme": "supportedScheme"
  },
  "replicated": "replicated",
  "status": "status"
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

### `POST /api/v1/prescriptions/dispenses` — Create dispense

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/prescriptions/dispenses`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eprescriptions#create-dispense

Creates a dispense for a prescription using the provided dispense details

**Request body** — `application/json`, required

Create dispense payload

| Field | Type | Required | Description |
|---|---|---|---|
| `actual_products` | object[] | **yes** | List of actual products dispensed |
| `consent_token` | string | **yes** | Consent token |
| `doctors` | object[] | **yes** | Information from the healthcare professional dispensing the drug |
| `intervention_code` | string | **yes** | Intervention code |

<details><summary>Example request body</summary>

```json
{
  "actual_products": [
    {
      "actual_product_code": "actual_product_code",
      "medication_price": 0,
      "total_quantity": 0
    }
  ],
  "consent_token": "consent_token",
  "doctors": [
    {
      "identification_number": "identification_number",
      "identification_type": "identification_type"
    }
  ],
  "intervention_code": "intervention_code"
}
```

</details>

<details><summary>curl</summary>

```bash
curl --request POST \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/prescriptions/dispenses' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "actual_products": [
    {
      "actual_product_code": "actual_product_code",
      "medication_price": 0,
      "total_quantity": 0
    }
  ],
  "consent_token": "consent_token",
  "doctors": [
    {
      "identification_number": "identification_number",
      "identification_type": "identification_type"
    }
  ],
  "intervention_code": "intervention_code"
}'
```
</details>

**Responses**

<details><summary><code>200</code> — Dispense created successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `dispenseDosages` | object[] | no |  |
| `dispensingDoctors` | object[] | no |  |
| `id` | integer | no |  |
| `prescription` | object | no |  |
| `status` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "dispenseDosages": [
    {
      "dispense": 0,
      "doseQuantity": 0,
      "doseUnit": "doseUnit",
      "duration": "duration",
      "durationUnit": "durationUnit",
      "endDate": "endDate",
      "frequency": 0,
      "genericDosageInstruction": 0,
      "guid": "guid",
      "id": 0,
      "medication": "medication",
      "medicationIdentifier": "medicationIdentifier",
      "medicationPrice": "medicationPrice",
      "medicationRequestId": "medicationRequestId",
      "periodUnit": "periodUnit",
      "practitionerId": "practitionerId",
      "route": "route",
      "routeCode": "routeCode",
      "startDate": "startDate",
      "status": "status",
      "totalQuantity": "totalQuantity"
    }
  ],
  "dispensingDoctors": [
    {
      "dispense": 0,
      "id": 0
    }
  ],
  "id": 0,
  "prescription": {
    "authorization": {
      "authCode": "authCode",
      "beneficiaryCode": "beneficiaryCode",
      "beneficiaryName": "beneficiaryName",
      "beneficiaryNumber": "beneficiaryNumber",
      "expiry": "expiry",
      "guid": "guid",
      "id": 0,
      "payerName": "payerName",
      "providerName": "providerName",
      "replicated": "replicated",
      "status": "status",
      "token": "token"
    },
    "beneficiary": {
      "age": 0,
      "beneficiaryCode": "beneficiaryCode",
      "contacts": [
        {}
      ],
      "dob": "dob",
      "gender": "gender",
      "guid": "guid",
      "id": 0,
      "identifiers": [
        {}
      ],
      "isPrincipal": true,
      "mainIdentifier": "mainIdentifier",
      "names": "names"
    },
    "code": "code",
    "doctorReviewStatus": "doctorReviewStatus",
    "dosage": [
      {
        "doseQuantity": "doseQuantity",
        "doseUnit": "doseUnit",
        "duration": "duration",
        "durationUnit": "durationUnit",
        "endDate": "endDate",
        "frequency": 0,
        "guid": "guid",
        "id": 0,
        "medication": "medication",
        "medicationIdentifier": "medicationIdentifier",
        "medicationPrice": 0,
        "patientInstruction": "patientInstruction",
        "periodUnit": "periodUnit",
        "practitionerId": "practitionerId",
        "prescription": 0,
        "replicated": "replicated",
        "route": "route",
        "routeCode": "routeCode",
        "startDate": "startDate"
      }
    ],
    "guid": "guid",
    "id": 0,
    "intervention": {
      "accessPoint": "accessPoint",
      "active": true,
      "activeForUhc": true,
      "applicableFacilityOwnership": "applicableFacilityOwnership",
      "applicableGender": "applicableGender",
      "applicableSchemes": [
        "string"
      ],
      "benefit": 0,
      "benefitCode": "benefitCode",
      "benefitName": "benefitName",
      "code": "code",
      "coverageLevel": "coverageLevel",
      "fund": "fund",
      "guid": "guid",
      "id": 0,
      "levelsApplicable": [
        "string"
      ],
      "name": "name",
      "packageCombinations": [
        "string"
      ],
      "parentBenefitCode": "parentBenefitCode",
      "parentBenefitName": "parentBenefitName",
      "paymentMechanism": "paymentMechanism",
      "replicated": "replicated",
      "status": "status",
      "supportedScheme": "supportedScheme"
    },
    "replicated": "replicated",
    "status": "status"
  },
  "status": "status"
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

### `DELETE /api/v1/prescriptions/doctors` — Remove prescription doctor

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/prescriptions/doctors`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eprescriptions#remove-prescription-doctor

Removes a doctor associated with a prescription using the provided details

**Request body** — `application/json`, required

Remove prescription doctor payload

| Field | Type | Required | Description |
|---|---|---|---|
| `consent_token` | string | **yes** | Consent token |
| `intervention_code` | string | **yes** | Intervention code |
| `practitioner_registration_number` | string | **yes** | Registration number of the practitioner to remove |

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
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/prescriptions/doctors' \
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

<details><summary><code>200</code> — Doctor prescription successfully removed</summary>

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
