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

**Responses**

<details><summary><code>200</code> — Dispense created successfully</summary>

| Field | Type | Required | Description |
|---|---|---|---|
| `dispenseDosages` | object[] | no |  |
| `dispensingDoctors` | object[] | no |  |
| `id` | integer | no |  |
| `prescription` | object | no |  |
| `status` | string | no |  |

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

**Responses**

<details><summary><code>200</code> — Doctor prescription successfully removed</summary>

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
