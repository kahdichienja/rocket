# Eligibility

> Source: https://afyaconnect.dha.go.ke/hie-api/eclaims/eligibility · API: **eClaims and Preauth APIs** v1.0.0 · captured 2026-09-20

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

Endpoints for checking beneficiary eligibility.

## Endpoints

- [`GET /api/v1/patients/benefits`](#get-apiv1patientsbenefits-benefits-coverage) — Benefits Coverage
- [`GET /api/v1/patients/benefits/interventions`](#get-apiv1patientsbenefitsinterventions-interventions-coverage) — Interventions Coverage
- [`GET /api/v1/patients/eligibility`](#get-apiv1patientseligibility-sha-eligibility-check) — SHA Eligibility Check
- [`GET /api/v1/patients/benefits/utilization`](#get-apiv1patientsbenefitsutilization-get-patient-payer-utilization-balances) — Get patient payer utilization balances
- [`GET /api/v1/patients/sub-benefits`](#get-apiv1patientssub-benefits-get-patient-benefits-coverage) — Get patient benefits coverage
- [`GET /api/v1/facilities/{facilityCode}/beds/occupancy`](#get-apiv1facilitiesfacilitycodebedsoccupancy-get-facility-bed-occupancy) — Get facility bed occupancy

---

### `GET /api/v1/patients/benefits` — Benefits Coverage

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/benefits`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eligibility#benefits-coverage

Retrieve the list of benefit packages available for a specific patient.

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `patient_id` | string | **yes** | Patient's client registry ID |
| `fields` | string | no | Fields to include in response (e.g parent_benefit,parent_benefit_code) |
| `is_unique_benefit` | boolean | no | Filter unique benefits only |

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/benefits?patient_id=%3Cpatient_id%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — OK</summary>

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
      "parentBenefit": "parentBenefit",
      "parentBenefitCode": "parentBenefitCode"
    }
  ],
  "startIndex": 0,
  "totalPages": 0
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

### `GET /api/v1/patients/benefits/interventions` — Interventions Coverage

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/benefits/interventions`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eligibility#interventions-coverage

Retrieve the list of medical interventions available under benefit packages for a patient.

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `patient_id` | string | **yes** | Patient's client registry ID |
| `sub_benefit_code` | string | **yes** | Sub benefit whose interventions are to be returned |

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/benefits/interventions?patient_id=%3Cpatient_id%3E&sub_benefit_code=%3Csub_benefit_code%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — OK</summary>

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
      "accessPoint": "accessPoint",
      "active": true,
      "annualLimitValue": 0,
      "annualQuantityLimit": 0,
      "annualQuantityLimitChoice": "annualQuantityLimitChoice",
      "annualQuantityLimitType": "annualQuantityLimitType",
      "applicableDocumentTypes": [
        "string"
      ],
      "applicableFacilityOwnership": "applicableFacilityOwnership",
      "applicableGender": "applicableGender",
      "applicableSchemes": [
        "string"
      ],
      "benefit": 0,
      "benefitCode": "benefitCode",
      "benefitName": "benefitName",
      "code": "code",
      "comment": "comment",
      "complexity": "complexity",
      "coverageLevel": "coverageLevel",
      "diagnosisBlock": [
        "string"
      ],
      "diagnosisList": [
        "string"
      ],
      "fallBackLevel2Tariff": 0,
      "fallBackLevel3Tariff": 0,
      "fallBackLevel4Tariff": 0,
      "fallBackLevel5Tariff": 0,
      "fallBackLevel6Tariff": 0,
      "fallBackOverallTariff": 0,
      "fund": "fund",
      "guid": "guid",
      "id": 0,
      "investigationTariff": 0,
      "investigationTariffHasLimit": true,
      "isIntraMetro": true,
      "level2Tariff": 0,
      "level3Tariff": 0,
      "level4Tariff": 0,
      "level5Tariff": 0,
      "level6Tariff": 0,
      "levelsApplicable": [
        "string"
      ],
      "lowerAgeLimit": 0,
      "managementTariff": 0,
      "managementTariffHasLimit": true,
      "name": "name",
      "needApprovalBeforeClaimSubmission": true,
      "needsDoctorAuthorization": true,
      "needsManualPreauthApproval": true,
      "needsMemberAuthorization": true,
      "needsPreauth": true,
      "numberOfDaysToFallback": 0,
      "numberOfDoctorsRequired": 0,
      "optionalDocumentTypes": [
        "string"
      ],
      "optionalPreauthDocumentTypes": [
        "string"
      ],
      "overallTariff": 0,
      "overallTariffHasLimit": true,
      "parentBenefitCode": "parentBenefitCode",
      "parentBenefitName": "parentBenefitName",
      "paymentMechanism": "paymentMechanism",
      "preauthFinalised": true,
      "protocolUsed": "protocolUsed",
      "requiredPreauthDocumentTypes": [
        "string"
      ],
      "requiresOncologyPreauth": true,
      "requiresOpticalPreauth": true,
      "requiresRadiologyPreauth": true,
      "requiresRenalPreauth": true,
      "requiresSurgicalPreauth": true,
      "status": "status",
      "supportedScheme": "supportedScheme",
      "tariffLimitPerIndividual": 0,
      "tariffPerAdditionalKilometer": 0,
      "upperAgeLimit": 0,
      "usageFrequencyLimit": 0,
      "usageFrequencyType": "usageFrequencyType",
      "kephLevelTarriff": 0
    }
  ],
  "startIndex": 0,
  "totalPages": 0
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

### `GET /api/v1/patients/eligibility` — SHA Eligibility Check

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/eligibility`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eligibility#sha-eligibility-check

This endpoint checks the eligibility of a beneficiary for certain healthcare services.

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `identification_number` | string | **yes** | Patient identification number |
| `identification_type` | string | **yes** | Patient identification type |

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/eligibility?identification_number=%3Cidentification_number%3E&identification_type=%3Cidentification_type%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — OK</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `age` | integer | no |  |
| `dateOfBirth` | string | no |  |
| `fullName` | string | no |  |
| `gender` | string | no |  |
| `memberCrNumber` | string | no |  |
| `requestIdNumber` | string | **yes** |  |
| `requestIdType` | integer | **yes** |  |
| `schemes` | object[] | no |  |
| `statusCode` | string | no |  |
| `statusDesc` | string | no |  |
| `whitelistedForOTP` | boolean | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "age": 0,
  "dateOfBirth": "dateOfBirth",
  "fullName": "fullName",
  "gender": "gender",
  "memberCrNumber": "memberCrNumber",
  "requestIdNumber": "requestIdNumber",
  "requestIdType": 0,
  "schemes": [
    {
      "coverage": {
        "endDate": "endDate",
        "message": "message",
        "possibleSolution": "possibleSolution",
        "reason": "reason",
        "startDate": "startDate",
        "status": "status"
      },
      "memberType": "memberType",
      "policy": {
        "endDate": "endDate",
        "number": "number",
        "startDate": "startDate"
      },
      "principalContributor": {
        "crNumber": "crNumber",
        "employerDetails": {
          "jobGroup": "jobGroup",
          "name": "name"
        },
        "employmentType": "employmentType",
        "idNumber": "idNumber",
        "idType": "idType",
        "name": "name",
        "relationship": "relationship"
      },
      "schemeId": 0,
      "schemeName": "schemeName"
    }
  ],
  "statusCode": "statusCode",
  "statusDesc": "statusDesc",
  "whitelistedForOTP": true
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

### `GET /api/v1/patients/benefits/utilization` — Get patient payer utilization balances

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/benefits/utilization`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eligibility#get-patient-payer-utilization-balances

Retrieves a patient's payer utilization balances showing benefit usage and remaining limits

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `patient_id` | string | **yes** | Patient's CR number |
| `intervention_code` | string | **yes** | Intervention code |

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/benefits/utilization?patient_id=%3Cpatient_id%3E&intervention_code=%3Cintervention_code%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — OK</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `code` | string | no |  |
| `computationalDetail` | object | no |  |
| `crId` | string | no |  |
| `fundUtilizationLimit` | object[] | no |  |
| `householdMaxLimit` | integer | no |  |
| `householdUtilisedLimit` | integer | no |  |
| `individualMaxLimit` | integer | no |  |
| `individualUtilisedLimit` | integer | no |  |
| `limitScope` | string | no |  |
| `nextAvailability` | string | no |  |
| `utilizationDays` | integer | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "code": "code",
  "computationalDetail": {
    "coverageEndDate": "coverageEndDate",
    "coverageStartDate": "coverageStartDate",
    "eligibility": true,
    "householdLimitAvailableCount": 0,
    "individualLimitAvailableCount": 0,
    "intermediatePeriodUsage": {
      "individualMaxDuringPeriod": 0,
      "individualUtilisedDuringPeriod": 0,
      "lastUsageDate": "lastUsageDate",
      "period": "period"
    },
    "limitAvailableAmount": 0,
    "nextAvailableDate": "nextAvailableDate"
  },
  "crId": "crId",
  "fundUtilizationLimit": [
    {
      "availableAmount": 0,
      "fundType": "fundType",
      "maxAmount": 0,
      "utilisedAmount": 0
    }
  ],
  "householdMaxLimit": 0,
  "householdUtilisedLimit": 0,
  "individualMaxLimit": 0,
  "individualUtilisedLimit": 0,
  "limitScope": "limitScope",
  "nextAvailability": "nextAvailability",
  "utilizationDays": 0
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

### `GET /api/v1/patients/sub-benefits` — Get patient benefits coverage

- **Auth:** BearerAuth
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/sub-benefits`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eligibility#get-patient-benefits-coverage

Retrieves a patient's SHA benefits coverage

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `patient_id` | string | **yes** | Patient's client registry ID |

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/patients/sub-benefits?patient_id=%3Cpatient_id%3E' \
  --header 'Authorization: Bearer <token>'
```
</details>

**Responses**

<details><summary><code>200</code> — OK</summary>

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
      "accessPoint": "accessPoint",
      "active": true,
      "allowedInterventions": [
        "string"
      ],
      "applicableLimit": "applicableLimit",
      "code": "code",
      "cover": {
        "category": "category",
        "categoryCode": "categoryCode",
        "effectivePolicyNumber": "effectivePolicyNumber",
        "group": "group",
        "groupCode": "groupCode",
        "groupType": "groupType",
        "isEmployerGroup": true,
        "jobGroup": "jobGroup",
        "policyNumber": "policyNumber",
        "validFrom": "validFrom",
        "validTo": "validTo"
      },
      "fund": "fund",
      "guid": "guid",
      "id": 0,
      "interventionCombination": [
        "string"
      ],
      "name": "name",
      "packageCombination": [
        "string"
      ],
      "parentBenefit": "parentBenefit",
      "parentBenefitCode": "parentBenefitCode",
      "standaloneInterventions": [
        "string"
      ],
      "status": "status"
    }
  ],
  "startIndex": 0,
  "totalPages": 0
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

### `GET /api/v1/facilities/{facilityCode}/beds/occupancy` — Get facility bed occupancy

- **Auth:** none (public)
- **Full URL:** `https://ilm-dev.dha.go.ke/uat-middleware/api/v1/facilities/{facilityCode}/beds/occupancy`
- **Portal:** https://afyaconnect.dha.go.ke/hie-api/eclaims/eligibility#get-facility-bed-occupancy

Returns total capacity and current bed occupancy data for the facility.

**Path parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `facilityCode` | string | **yes** | Facility FR code |

<details><summary>curl</summary>

```bash
curl --request GET \
  --url 'https://ilm-dev.dha.go.ke/uat-middleware/api/v1/facilities/:facilityCode/beds/occupancy'
```
</details>

**Responses**

<details><summary><code>200</code> — Facility occupancy retrieved successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `bed_occupancy_rate` | object | no |  |
| `bp_level` | string | no |  |
| `name` | string | no |  |


**Example** (portal sample; nested objects show the full shape)

```json
{
  "bed_occupancy_rate": {
    "dialysis_visits": 0,
    "hdu_visits": 0,
    "icu_visits": 0,
    "newborn_visits": 0,
    "normal_ip_visits": 0,
    "number_of_baby_cot": 0,
    "number_of_dialysis_bed": 0,
    "number_of_hdu_bed": 0,
    "number_of_icu_bed": 0,
    "number_of_normal_bed": 0,
    "total_ip_visits": 0,
    "total_number_of_bed": 0
  },
  "bp_level": "bp_level",
  "name": "name"
}
```

</details>

<details><summary><code>400</code> — Bad Request - Failed to retrieve occupancy</summary>

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
