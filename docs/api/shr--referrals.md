# Shared Health Record — Referrals, Observations, Security Labels & the Facility Registry

> Source: https://hie-docs.dha.go.ke/sharedhealthrecord/shr-records and
> https://hie-docs.dha.go.ke/registries/facility-registry · captured 2026-09-29

> Base URL (UAT): `https://ilm-dev.dha.go.ke/uat-middleware`

The SHR endpoints that a **referral** turns on, plus the Facility Registry search that lets a referral name
its destination. Consent, patient records and bundle submission are covered by the SHR consent flow
documented in `src/sha_claim/domain/shr.py`.

## Endpoints

- [`GET /api/v1/shr/ServiceRequest`](#get-apiv1shrservicerequest--query-referrals-fhir) — Query referrals (FHIR)
- [`GET /api/v1/shr/Observation`](#get-apiv1shrobservation--query-patient-observations-fhir) — Query patient observations (FHIR)
- [`GET /api/v1/shr/security-labels`](#get-apiv1shrsecurity-labels--the-security-label-catalogue) — The security label catalogue
- [`GET /api/v1/facilities/search`](#get-apiv1facilitiessearch--get-facilitys-record) — Get facility's record

---

### `GET /api/v1/shr/ServiceRequest` — Query referrals (FHIR)

- **Auth:** BearerAuth
- **Consent token:** **none** — see below
- **SDK:** `sha.shr.referrals(performer=..., requester=...)`

**The one SHR read that is not scoped by a patient's consent.** DHA's own wording:

> Unlike the observation query, this endpoint is not scoped by a per-visit consent token — it is a query
> over referrals directed at an organisation, not a read of one patient's record.

This is what makes a referral **inbox** possible. Every other SHR read answers *"what is in this person's
record"* and needs the patient's say-so; this answers *"which referrals point at this facility"*, which is a
question about our own workload. A receiving desk can therefore see that a patient is coming **before** the
patient — and their OTP — has arrived.

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `performer:Organization` | string | no | FR code of the facility the referral is addressed to — **our inbox** |
| `requester:Organization` | string | no | FR code of the facility that raised it — **our outbox** |
| `status` | string | no | FHIR `ServiceRequest.status`: `draft`, `active`, `on-hold`, `revoked`, `completed`, `entered-in-error`, `unknown` |
| `count` | integer | no | Results per page |
| `page_token` | string | no | From the previous bundle's `next` link |

The `:Organization` suffix is a FHIR **reference-type modifier** and part of the parameter name.
`ShrReferralQuery.as_params` owns that spelling so no caller has to remember the colon.

DHA marks both direction parameters optional; the SDK requires one of them. A query with neither is a
search over every referral DHA holds, which no caller means to run.

**Raising a referral** — there is no `POST` here. Referrals are written to the SHR as `ServiceRequest`
entries inside a bundle submitted to `POST /api/v1/shr/bundles`, which **does** carry `X-Consent-Token`.
So the two directions have asymmetric consent requirements, and that asymmetry is the main thing to
understand about this module:

| | Consent needed? |
|---|---|
| Reading referrals addressed to us | **No** |
| Raising a referral (bundle submission) | **Yes** — per-visit `X-Consent-Token` |

**Response (200)** — a FHIR `searchset` bundle, passed through unchanged:

```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 1,
  "entry": [{
    "resource": {
      "resourceType": "ServiceRequest",
      "id": "48752cdf5cb3c748-ktn2",
      "status": "active",
      "performer": [{"reference": "Organization/FID-17-116073-1", "display": "KATHONZWENI HEALTH CENTRE"}]
    }
  }],
  "link": [{"relation": "next", "url": "https://shr.sha.go.ke?page_token=Bnm8Qm7w4Sngv-4W_GpOfrNn"}]
}
```

FHIR is deliberately not modelled in this SDK — the bundle is returned as a `Mapping` and handed to the
caller, which already speaks FHIR.

---

### `GET /api/v1/shr/Observation` — Query patient observations (FHIR)

- **Auth:** BearerAuth
- **SDK:** `sha.shr.observations(token, subject, practitioner_uid)`

**Two headers, not one.**

| Header | Required | Description |
|---|---|---|
| `X-Consent-Token` | **yes** | The per-visit consent token |
| `X-PUID` | **yes** | Practitioner Unique Identifier |

`X-PUID` is required on this endpoint and **on no other in this SDK**. Elsewhere the reading clinician
travels as the `practitioner_id` *query parameter* (`GET /shr/patient-records`). Same fact, different
place, and DHA rejects the request if it is in the wrong one.

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `subject` | string | **yes** | CR identifier of the patient |
| `page_token` | string | no | From the previous bundle's `next` link |

Largely redundant with `GET /shr/patient-records?resources=Observation`. It exists because DHA publishes it
and because paging a single resource type is cheaper than paging the whole record.

---

### `GET /api/v1/shr/security-labels` — The security label catalogue

- **Auth:** BearerAuth
- **Query parameters:** none
- **SDK:** `sha.shr.security_labels()`

The full catalogue of labels that appear in an SHR resource's `meta.security`. Static reference data —
fetch once and keep.

**Distinct from `GET /shr/resource-labels`**, which answers *which labels apply to a given resource type*
and requires a `resource_name` or `code`. This one answers *what the codes mean*.

Two vocabularies, which must not be conflated — confidentiality is **how guarded** a resource is,
sensitivity is **what kind of thing** it is about. A resource can be `N` and still carry `HIV`.

| Kind | System | Codes |
|---|---|---|
| Confidentiality | `http://terminology.hl7.org/CodeSystem/v3-Confidentiality` | `N` (normal), `R` (restricted) |
| Sensitivity | `http://terminology.hl7.org/CodeSystem/v3-ActCode` | `HIV`, `PSY`, `SUD`, `STD`, `SEX`, `PRG`, `GDIS`, `CRITINN`, `FININF` |

Why fetch it at all: `SUD`, `GDIS` and `CRITINN` mean nothing to a desk. A referral screen that prints the
bare code has told the clinician nothing while *looking* as though it has. `PSY` and `HIV` are the cases
that matter — a label a receiving clerk cannot read is a label they cannot honour.

The SDK models this response (unlike the FHIR passthroughs) because it is reference data a screen has to
reason about. `ShrSecurityLabel.kind` is **derived** from the system URI rather than trusted from DHA's
free-text `category`, with the code list as fallback; an unrecognised code is reported as `UNKNOWN` rather
than filed under a guess.

---

### `GET /api/v1/facilities/search` — Get facility's record

- **Auth:** BearerAuth
- **SDK:** `sha.facilities.search(name=...)` / `sha.facilities.find_by_fr_code(code)`

The Facility Registry. Everywhere else in this SDK a facility is *implied* — the credential carries it, or
`activate_facility` names it. This is for the other case: naming a facility that is **not** us. A referral
has to say where the patient is going, and the SHR addresses referrals by FR code
(`Organization/FID-17-116073-1`), so a desk that only knows a hospital's name needs this to get a code.

**Query parameters**

| Field | Type | Required | Description |
|---|---|---|---|
| `identifier` | string | no | Facility identification number, e.g. `FID-47-108521-3` |
| `identifier-type` | string | no | One of `fr-code`, `mfl`, `license-number`, `registration-number`, `fid` |
| `name` | string | no | Facility's name — the only free-text search in this SDK |

**`identifier-type` is hyphenated.** Every other parameter in this API is snake_case. Sending
`identifier_type` is not rejected: DHA ignores it, applies its own default, and may answer about a
different facility.

**Two response shapes.** A lookup by identifier answers with a **bare object**; a search by name with a
**list** (or a `data`/`results` wrapper). Validating the envelope as though it were a record yields one
facility with **no FR code** — a picker entry a referral cannot address. `HttpFacilityRegistryGateway._records`
handles all of them.

**Response fields** (camelCase, unlike the snake_case SHR payloads):
`frCode`, `name`, `uuid`, `facilityType`, `kephLevel`, `owner`, `isHub`, `facilityPhoneNumber`,
`facilityAdministratorName`, `facilityAdministratorEmail`, `address` (county, constituency, latitude,
longitude), `bedOccupancy` (normalBeds, icuBeds, dialysisBeds, …), `SHAOperationStatus`,
`shaContractStatus`, `shaContractedServices`.

Note `SHAOperationStatus` — pydantic's `to_camel` produces `shaOperationStatus`, so this needs an explicit
alias. Getting it wrong is **silent**: the field stays at its default and a suspended facility reads as
operational, which is the one error that could send a patient to a hospital that cannot take them.

**A code is not the same as a facility that can receive the patient.** The registry answers for hospitals
that are suspended and for hospitals that never contracted with SHA. `FacilityRecord.is_referable` is the
one-line reading — operational **and** SHA-contracted. Both failures are worth showing rather than hiding:
a suspended facility cannot treat the patient, an uncontracted one can treat them and then bill them
privately, and some referrals are clinically necessary regardless.

`is_operational` is matched **negatively** and leniently: anything saying suspended, closed or inactive is
not operational, and a status nobody recognises is treated as operational rather than hidden. Wrongly
hiding a hospital that could have taken the patient is the worse failure, and the status is shown beside
the name either way.

`offers(service)` returns `False` when the registry listed no services at all — which means *unknown*, not
*not offered*, so it must not be used to hide a facility.

---

## Not in the published spec

`docs/api/spec/eclaims.json` predates the SHR and carries none of these paths, so
`tests/contract/adapters/test_spec_drift.py` does not cover them — the same position the existing SHR
requests are already in. The contract is pinned instead by `tests/contract/adapters/test_shr.py` and
`test_facility_registry.py` against the published Postman collection and these docs.
