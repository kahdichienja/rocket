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

</details>

<details><summary><code>400</code> — Bad Request - Missing query parameters or invalid request input</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

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

</details>

<details><summary><code>400</code> — Bad Request - Missing query parameters or invalid request input</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

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

</details>

<details><summary><code>400</code> — Bad Request - Missing query parameters or invalid request input</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

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

</details>

<details><summary><code>400</code> — Bad Request - Missing query parameters or invalid request input</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

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

</details>

<details><summary><code>400</code> — Bad Request - Missing query parameters or invalid request input</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no |  |
| `message` | string | no |  |

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

**Responses**

<details><summary><code>200</code> — Facility occupancy retrieved successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `bed_occupancy_rate` | object | no |  |
| `bp_level` | string | no |  |
| `name` | string | no |  |

</details>

<details><summary><code>400</code> — Bad Request - Failed to retrieve occupancy</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `error` | string | no | @Description	HTTP status text from the standard HTTP status codes 	@Example		"Bad Request" |
| `message` | string | no | @Description	Detailed error message explaining what went wrong 	@Example		"token missing required tenant_id claim" |

</details>


---
