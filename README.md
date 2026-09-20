# sha-claim

Python SDK for **Social Health Authority (SHA, Kenya)** claims through the Digital Health Agency's
**AfyaConnect HIE eClaims API**. Async-first, typed, framework-free.

> Status: pre-release (`0.1.0.dev0`). 24 of 49 endpoints implemented. Eligibility, benefits and consent are
> verified live against DHA UAT; the claim lifecycle (`ClaimSession`) is contract-tested against the published
> spec and awaits a UAT beneficiary with a reachable phone for live verification. Pre-authorisation, emergency
> and ePrescriptions are not implemented yet. See [PLAN.md](PLAN.md).

## Install

```bash
pip install sha-claim
```

## Configure

Credentials come from DHA onboarding. The facility is implied by the credential (it is embedded in the token).

```bash
export SHA_ENVIRONMENT=uat          # uat | production (production also needs SHA_BASE_URL)
export SHA_CLIENT_ID=...
export SHA_CLIENT_SECRET=...
```

## Use

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

### A claim, end to end

```python
from sha_claim import (
    AsyncSHAClient,
    Money,
    Otp,
    ServiceType,
    DocumentType,
    Attachment,
    SubmissionOutcomeUnknownError,
)

async with AsyncSHAClient.from_env() as sha:
    patient = (await sha.eligibility.check("12345678", IdentificationType.NATIONAL_ID)).patient_id
    coverage = await sha.eligibility.interventions(patient, "SHA-12-SC-01")
    consultation = next(c for c in coverage if c.name == "Consultation")

    # 1. consent: this sends the OTP to the beneficiary's registered phone
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

    # 4. verify, then submit exactly once
    preview = await session.preview()
    try:
        claim = await session.submit(invoice_number="INV-2026-000123")
    except SubmissionOutcomeUnknownError:
        claim = await session.preview()  # the server knows whether it went through; ask it

    # later, from any process that persisted the token:
    status = await sha.claims.resume(claim.consent_token).payer_status("INV-2026-000123")
```

Every error is a subclass of `sha_claim.SHAClaimError`; see `sha_claim.errors`.

## Design in one paragraph

The server owns the claim: you open a *virtual claim*, receive a `consent_token`, mutate the claim
call by call, then submit. The SDK mirrors that faithfully — it holds **snapshots**, not a local
state machine — and only rejects locally what the server will certainly reject. Reads are retried
with backoff; `submit` is attempted exactly once. Layers follow Clean Architecture and are enforced
by `import-linter`. Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); API reference generated
from the official portal: [docs/api/](docs/api/README.md).

## Develop

```bash
make install      # venv + editable install with dev extras
make check        # ruff, mypy --strict, import-linter, pytest (≥ 90 % coverage)
make live         # RUN_LIVE=1: smoke tests against DHA UAT (needs .env)
```

## License

Apache-2.0
