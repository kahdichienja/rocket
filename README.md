# sha-claim

Python SDK for **Social Health Authority (SHA, Kenya)** claims through the Digital Health Agency's
**AfyaConnect HIE eClaims API**. Async-first, typed, framework-free — `httpx` and `pydantic`, nothing else.

> **Status: `0.1.17`, pre-production.** All 49 published endpoints implemented. Eligibility, benefits, consent,
> the claim lifecycle, discharge and dispensing are verified live against DHA UAT. Two things are not yours to
> fix: `prescribe()` is blocked by an unpublished `patient_instruction` vocabulary, and the pre-auth nested
> arrays are unverified. Both are tracked in [docs/api/WORKFLOWS.md](docs/api/WORKFLOWS.md). See [PLAN.md](PLAN.md).

**New to SHA or to this SDK? → [Consumer Guide](docs/GUIDE.md)** — every method, its parameters, the HTTP call
it makes, the object it returns, plus end-to-end recipes and the gotchas that cost us days.

## Install

```bash
pip install sha-claim
```

Python 3.11+.

## Configure

Credentials come from DHA onboarding. Settings are validated when you build the client, so a bad
configuration raises `ConfigurationError` immediately rather than mid-claim.

```bash
export SHA_ENVIRONMENT=uat          # uat | production (production also needs SHA_BASE_URL)
export SHA_CLIENT_ID=...
export SHA_CLIENT_SECRET=...
```

The facility is normally embedded in the credential's token, so no call takes a facility argument. A credential
covering several facilities scopes each call instead:

```python
from sha_claim import facility_scope

with facility_scope("FID-47-115307-8"):  # safe under concurrency (ContextVar)
    await sha.eligibility.check(...)
```

`activate_facility(code)` / `clear_facility()` suit a per-request web dependency; `SHA_FACILITY_ID` pins one
facility for the whole process.

## Use

One client, reused. `async with` opens the connection pool; tokens are fetched on first use, cached, and
refreshed single-flight (100 concurrent callers trigger one refresh).

```python
import asyncio
from datetime import date
from sha_claim import AsyncSHAClient, IdentificationType, BadRequestError


async def main() -> None:
    async with AsyncSHAClient.from_env() as sha:
        try:
            e = await sha.eligibility.check("12345678", IdentificationType.NATIONAL_ID)
        except BadRequestError as err:  # server-side validation, carries trace_id
            print(err.trace_id, err)
            return
        if e.is_covered_on(date.today()):
            print(e.full_name, e.patient_id, [s.name for s in e.active_schemes_on(date.today())])


asyncio.run(main())
```

### What's on the client

| Resource | What it answers | Guide |
|---|---|---|
| `sha.eligibility` | Is this person covered, for which benefits and interventions? Balances, bed occupancy. | [§6](docs/GUIDE.md#6-shaeligibility) |
| `sha.consent` | Send the OTP; inspect or reject an authorization. | [§7](docs/GUIDE.md#7-shaconsent) |
| `sha.claims` | Open a claim (→ `ClaimSession`), or resume one from a saved token. | [§8](docs/GUIDE.md#8-shaclaims) |
| `sha.emergency` | Open an emergency case without prior consent; treatment protocols. | [§10](docs/GUIDE.md#10-shaemergency) |
| `sha.files` | Standalone upload / download link. | [§11](docs/GUIDE.md#11-shafiles) |
| `sha.registries` | Look a patient up in the Client Registry. | [Guide](docs/GUIDE.md) |

A `ClaimSession` carries the consent token for you and covers interventions, diagnoses, billing lines,
attachments, pre-authorisation, ePrescriptions, discharge, submit and close — [§9](docs/GUIDE.md#9-claimsession).

### A claim, end to end

```python
from sha_claim import (
    AsyncSHAClient,
    DischargeReason,
    Money,
    Otp,
    PractitionerRef,
    RegulationBody,
    ServiceType,
    DocumentType,
    Attachment,
    SubmissionOutcomeUnknownError,
)

async with AsyncSHAClient.from_env() as sha:
    patient = (await sha.eligibility.check("12345678", IdentificationType.NATIONAL_ID)).patient_id
    coverage = await sha.eligibility.interventions(patient, "SHA-12-SC-01")
    consultation = next(c for c in coverage if c.name == "Consultation")

    # 1. consent: this is the call that sends the OTP to the beneficiary's registered phone
    auth = await sha.consent.authorize(
        patient, consultation.service_type_for_authorization, [consultation.code]
    )

    # 2. open the server-side virtual claim with the OTP the patient read out
    session = await sha.claims.open_visit(
        patient, consultation.service_type_for_authorization, [consultation.code], Otp("123456")
    )

    # 3. build it — every call is keyed by the session's consent_token
    await session.add_diagnosis("1A00", consultation.code)
    await session.add_line(consultation.code, Money.kes("1500"), quantity=1, diagnoses=["1A00"])
    await session.attach(Attachment.from_path("invoice.pdf", DocumentType.INVOICE), consultation.code)
    await session.add_doctor(PractitionerRef.registered("A1234", RegulationBody.KMPDC))

    # 4. check what the server thinks before you commit
    preview = await session.preview()
    if blockers := preview.submission_blockers():
        return [str(b) for b in blockers]  # NO_DIAGNOSIS, PREAUTH_OUTSTANDING, ZERO_TOTAL, …

    # 5. submit exactly once (UAT requires a discharge reason and OTP even for outpatient)
    await session.send_discharge_otp(patient)
    try:
        claim = await session.submit(
            preview.invoice_number, discharge_reason=DischargeReason.RECOVERED, otp=Otp("654321")
        )
    except SubmissionOutcomeUnknownError:
        claim = await session.preview()  # the server knows whether it went through; ask it

    # later, from any process that persisted the token:
    status = await sha.claims.resume(claim.consent_token).payer_status("INV-2026-000123")
```

### Critical care: SHA pays by the day

ICU, HDU, NICU and the burns unit (`SHA-03-*`) are `PaymentMechanism.PER_DIEM` — a bed rebate SHA accrues
itself. Undocumented in the portal spec, modelled here:

```python
bed = next(i for i in claim.interventions if i.is_per_diem)
allowance = bed.per_diem_allowance  # SHA's accrual, else KEPH-level rate × days, else None
```

`None` means SHA published neither — **unknown, not zero.** Don't coerce it: a zero on an ICU stay reads as
"SHA pays nothing" and bills the patient for the bed. Each line read back from `preview()` also carries SHA's
own split — `rebate_amount`, `sponsor_net`, `patient_net`, `benefit_exceeded`.

### Errors

Every exception subclasses `sha_claim.SHAClaimError`. `RequestValidationError` means nothing was sent (with
`.violations`); everything else carries the server's `.trace_id` — **quote it when you raise a ticket with DHA.**
`SubmissionOutcomeUnknownError` is the one that matters: submit left, the answer didn't come back, and the SDK
refuses to guess. Call `preview()`. Full table in [§4](docs/GUIDE.md#4-errors).

### Observability

The SDK **stores nothing** — no database, no polling, no background tasks. Pass `on_event=` and you get one
`SDKEvent` per HTTP attempt (`operation`, `status`, `duration_ms`, `attempt`, `trace_id`, redacted
`consent_token`); audit logging and metrics live in your callback. A hook that raises is logged and ignored, so
it can never break a claim.

```python
async with AsyncSHAClient.from_env(on_event=audit) as sha:
    ...
```

## Design in one paragraph

The server owns the claim: you open a *virtual claim*, receive a `consent_token`, mutate the claim
call by call, then submit. The SDK mirrors that faithfully — it holds **snapshots**, not a local
state machine — and only rejects locally what the server will certainly reject. Reads are retried
with backoff; `submit` is attempted exactly once. Layers follow Clean Architecture and are enforced
by `import-linter`. Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); API reference generated
from the official portal: [docs/api/](docs/api/README.md); what UAT actually does, as opposed to what it
documents: [docs/api/WORKFLOWS.md](docs/api/WORKFLOWS.md).

Treat the `consent_token` like a password — it lets anyone bill against that patient's visit. Persist
`token.value`, never `str(token)`, which is redacted on purpose.

## Develop

```bash
make install      # venv + editable install with dev extras
make check        # ruff, mypy --strict, import-linter, pytest (≥ 90 % coverage)
make live         # RUN_LIVE=1: smoke tests against DHA UAT (needs .env)
```

Docs: [GUIDE](docs/GUIDE.md) · [ARCHITECTURE](docs/ARCHITECTURE.md) · [WORKFLOWS](docs/api/WORKFLOWS.md) ·
[NACARE_INTEGRATION](docs/NACARE_INTEGRATION.md) · [CERTIFICATION](docs/CERTIFICATION.md) ·
[RELEASING](docs/RELEASING.md) · [CHANGELOG](CHANGELOG.md)

## License

Apache-2.0
