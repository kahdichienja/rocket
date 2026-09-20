# sha-claim

Python SDK for **Social Health Authority (SHA, Kenya)** claims through the Digital Health Agency's
**AfyaConnect HIE eClaims API**. Async-first, typed, framework-free.

> Status: pre-release (`0.1.0.dev0`). Eligibility is implemented end-to-end against the DHA UAT
> environment; consent, virtual claims, billing, submission and pre-authorisation are in progress.
> See [PLAN.md](PLAN.md).

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
