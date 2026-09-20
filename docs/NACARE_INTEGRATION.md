# Using `sha-claim` inside NaCare (`Nacare/backend`)

*Plan, 2026-09-20. Additive only: no existing DHA file is removed or modified until the product team retires it.*

## 0. What is already there

`Nacare/backend` has a hand-rolled DHA integration:

| Existing | Lines | Role |
|---|---|---|
| `app/gateways/dha_gateway.py` | 328 | `IDHAHIEGateway` ABC, ~55 methods returning `Dict[str, Any]` |
| `app/infrastructure/dha_http_adapter.py` | 1013 | httpx calls, own token cache, own error mapping, `X-Facility-Id` headers, audit → `hie_logs` |
| `app/use_cases/dha_claims/*` | 8 files | thin pass-throughs to the gateway (dicts in, dicts out) |
| `app/routes/claims.py`, `app/routes/hie.py` | 1124 + 261 | FastAPI routes at `/api/v1/claims/dha/...` |
| `app/domain/entities/claim_session.py`, `value_objects/dha_consent.py`, `policies/dha_billing_policy.py`, `value_objects/pmf_tariff.py` | | a local claim state machine + rules that duplicate server knowledge |

It works, and it also encodes things the SDK now owns better: typed results instead of dicts, spec-drift
tests, submit-once, error unwrapping, redaction, the CAPITATION rule. The plan is a **strangler**: build
the SDK-backed path beside the old one under a new URL prefix, move the frontend over screen by screen,
and let the old path fall silent. Nothing is deleted in this plan.

Three facts from the probe that shape the plan:

1. **`POST /claims/otp` exists** (the old adapter uses it; the eclaims portal doesn't list it) and on
   **UAT it returns the OTP in the response body**. This unblocks live end-to-end testing (Q11) and is
   the first thing to add to the SDK.
2. Client-registry endpoints (`GET /patients`, `GET /patients/contacts`, `GET /professionals`,
   `GET /facilities/search`) exist on UAT under the same base URL but are not on the eclaims pages.
   NaCare uses them for lookups. → SDK `registries` resource, after (1).
3. The old adapter sends `X-Facility-Id` / `X-Facility-Id-Type: fr-code` on every call. UAT accepts
   calls **with or without** them; the token already carries `facility_id`. Keep as an optional SDK
   setting for multi-facility tenants, default off.

## 1. Layout — agreed: a `sha/` sub-package per layer

```
app/
├── domain/sha/
│   └── claim_journey.py        # NaCare's *stateful* record of a visit (see §3). The only new domain code.
├── gateways/sha/
│   ├── journey_repository.py   # port: persist/load ClaimJourney
│   └── event_sink.py           # port: persist SDKEvent (audit)
├── use_cases/sha/
│   ├── check_eligibility.py
│   ├── start_visit.py          # authorize → (OTP) → open_visit → persist journey
│   ├── build_claim.py          # add_line / add_diagnosis / attach …  → refresh snapshot
│   ├── finalise_claim.py       # preview → blockers → submit (once) → persist
│   ├── track_claim.py          # payer_status / preauths → persist state change
│   └── …emergency, preauth, prescriptions
├── infrastructure/sha/
│   ├── client.py               # ONE AsyncSHAClient for the app lifetime (FastAPI lifespan) + settings mapping
│   ├── event_sink.py           # SDKEvent → existing `hie_logs` table (reuses crud.create_hie_log)
│   ├── journey_repository.py   # SQLAlchemy impl; consent_token encrypted at rest
│   └── errors.py               # SHAClaimError → HTTPException mapping (one place)
├── routes/sha/
│   ├── eligibility.py          # /api/v1/sha/eligibility/…
│   ├── consent.py              # /api/v1/sha/consent/…
│   ├── claims.py               # /api/v1/sha/claims/…
│   ├── emergency.py            # /api/v1/sha/emergency/…
│   └── schemas.py              # response models (thin: dataclasses → pydantic)
└── models.py                   # + SHAClaimJourney, (hie_logs already exists)
```

**One deliberate exception to "use cases depend only on ports":** NaCare use cases import
`sha_claim` types (`AsyncSHAClient`, `ClaimSession`, `VirtualClaim`, …) directly. Re-declaring an
`ISHAGateway` in front of the SDK would re-wrap 49 typed operations in dicts and throw away exactly
what the SDK provides. The SDK *is* the port: it exposes `Protocol`s, every collaborator is injectable,
and tests use `respx` or a fake `ClaimGateways`. Treat it like SQLAlchemy — a boundary library, not
business logic. The old `IDHAHIEGateway` stays untouched for the old routes.

## 2. Routes — agreed: `/api/v1/sha/**`

Old routes stay at `/api/v1/claims/dha/**`. New ones:

| Route | Use case | SDK call |
|---|---|---|
| `GET  /api/v1/sha/eligibility?id_number&id_type` | `CheckEligibility` | `sha.eligibility.check` |
| `GET  /api/v1/sha/eligibility/{cr}/interventions?sub_benefit` | | `sha.eligibility.interventions` |
| `POST /api/v1/sha/consent/authorize` | `StartVisit.authorize` | `sha.consent.authorize` → journey `AUTHORIZING` |
| `POST /api/v1/sha/consent/otp` | | `sha.consent.send_otp` *(after SDK adds it)* |
| `POST /api/v1/sha/claims` `{journey_id, otp}` | `StartVisit.open` | `sha.claims.open_visit` → journey `OPEN`, token stored encrypted |
| `POST /api/v1/sha/claims/{journey_id}/diagnoses` | `BuildClaim` | `session.add_diagnosis` |
| `POST /api/v1/sha/claims/{journey_id}/lines` | | `session.add_line` |
| `POST /api/v1/sha/claims/{journey_id}/attachments` (multipart) | | `session.attach` |
| `GET  /api/v1/sha/claims/{journey_id}/preview` | `FinaliseClaim.preview` | `session.preview` + `submission_blockers()` in the response |
| `POST /api/v1/sha/claims/{journey_id}/submit` | `FinaliseClaim.submit` | `session.submit` → journey `SUBMITTED` (or `SUBMIT_UNKNOWN` → preview) |
| `POST /api/v1/sha/claims/{journey_id}/close` | | `session.close` → `CLOSED` |
| `GET  /api/v1/sha/claims/{journey_id}/payer-status` | `TrackClaim` | `session.payer_status` |
| `POST /api/v1/sha/claims/{journey_id}/preauths` … | | `session.request_preauth` … |
| `POST /api/v1/sha/emergency` | | `sha.emergency.open_case` |

Routes are keyed by **NaCare's `journey_id`, never by `consent_token`**. The token is a credential;
it lives encrypted in the DB and is loaded by the use case via `sha.claims.resume(token)`. It should
never appear in a URL, a log line, or a browser.

## 3. Persistence — `ClaimJourney` (this is where NaCare's state lives; the SDK has none)

```python
@dataclass
class ClaimJourney:
    journey_id: UUID
    patient_cr: str  # PatientId.value
    encounter_id: str  # NaCare's own encounter / FHIR Encounter id
    service_type: str
    state: JourneyState  # AUTHORIZING → OPEN → SUBMITTED | CLOSED | SUBMIT_UNKNOWN
    consent_token_enc: bytes | None  # encrypted; decrypt only inside the repository
    authorization_guid: str | None
    claim_guid: str | None
    invoice_number: str | None
    last_snapshot: dict | None  # dataclasses.asdict(VirtualClaim) from the last preview/submit
    last_payer_state: str | None
    created_at / updated_at
```

The existing `domain/entities/claim_session.py` has a richer local model (line items, diagnoses,
totals). Don't extend it for the SDK path: the SDK path takes those from the server snapshot
(`VirtualClaim`) so they can't drift from what SHA will pay. `ClaimJourney` stores *identity and
state*, not a second copy of the claim.

Audit: `infrastructure/sha/event_sink.py` writes every `SDKEvent` to the existing `hie_logs` table,
so the audit trail is continuous with the old adapter's `_log_audit`.

## 4. Wiring

```python
# infrastructure/sha/client.py
from sha_claim import AsyncSHAClient, SHASettings, Environment


def build_settings() -> SHASettings:  # no env renames: map DHA_* → SHASettings
    return SHASettings(
        client_id=settings.dha_client_id,
        client_secret=settings.dha_client_secret,
        base_url=settings.dha_base_url.removesuffix("/api/v1"),
        environment=Environment.UAT if "ilm-dev" in settings.dha_base_url else Environment.PRODUCTION,
    )


# main.py lifespan
@asynccontextmanager
async def lifespan(app):
    app.state.sha = AsyncSHAClient(build_settings(), on_event=HIELogEventSink(SessionLocal).write)
    yield
    await app.state.sha.aclose()


# routes/sha/deps.py
def get_sha(request: Request) -> AsyncSHAClient:
    return request.app.state.sha
```

One client per process (it owns a connection pool and the token cache). Not one per request — the
old adapter did that and re-fetched tokens.

## 5. Error mapping (one function, `infrastructure/sha/errors.py`)

| SDK error | HTTP | Body |
|---|---|---|
| `RequestValidationError` | 422 | `violations[]` |
| `BadRequestError` | 400 | `message`, `trace_id` |
| `PermissionDeniedError` | 403 | `trace_id` |
| `NotFoundError` | 404 | |
| `AuthenticationError` | 502 | "SHA credentials rejected" + `trace_id` (never the token) |
| `RateLimitedError` | 429 | `Retry-After` |
| `TransportError` | 503 | `trace_id` |
| `SubmissionOutcomeUnknownError` | 409 | "submission outcome unknown — journey marked SUBMIT_UNKNOWN; call preview" |
| `UnexpectedResponseError` | 502 | |

## 6. Install

Until `sha-claim` is on PyPI, add to `requirements.txt`:
```
sha-claim @ git+ssh://git@<host>/<org>/sha_claim.git@<tag>
```
or for local development `pip install -e ../../sha_claim`. Pin a tag; the SDK is `0.x`.

## 7. Delivery order

| Step | Scope | Live-verifiable now? |
|---|---|---|
| A | SDK: add `consent.send_otp()` (`POST /claims/otp`), optional facility header; run the **full claim lifecycle live on UAT** | ✅ (OTP returned on UAT) |
| B | NaCare: `infrastructure/sha/client.py`, event sink → `hie_logs`, error mapping, `/api/v1/sha/eligibility/*` | ✅ |
| C | NaCare: `ClaimJourney` model + migration, consent + open-visit routes | ✅ |
| D | NaCare: build / preview(+blockers) / submit / close / payer-status | ✅ after A |
| E | NaCare: preauth, prescriptions, emergency routes | preauth request encoding still Q3 |
| F | Frontend: point screens at `/api/v1/sha/**`; old `/claims/dha/**` stays until product retires it | |
| G | SDK: `registries` resource (`/patients`, `/patients/contacts`, `/professionals`, `/facilities/search`) to replace the old adapter's lookups | needs their param contracts (probe) |

## 8. What the old code does that the new path must not lose

- Audit rows in `hie_logs` per call → covered by `on_event` sink.
- `DHA_DEFAULT_FACILITY_FR_CODE` header → optional SDK setting (step A).
- `/claims/otp` send-OTP → step A.
- Registry lookups (`search_patient`, `search_practitioner`, `search_facility`) → step G; until then the
  old routes remain the way to do them.
- `dha_claims_base_url` (`qa-mis.apeiro-digital.com`) is declared but **never used** by the adapter
  (only assigned). Nothing to carry over.
