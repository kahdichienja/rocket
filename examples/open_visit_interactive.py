"""Walk the consent handshake on UAT with a real beneficiary and record the visit response.

    .venv/bin/python examples/open_visit_interactive.py

You will be asked for the beneficiary's national ID, then for the OTP that SHA sends to the
phone registered against that ID. On success, the virtual-claim response is written (sanitised)
to tests/fixtures/virtual_claim_opened.json so the SDK's contract tests can use the real shape.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from sha_claim import AsyncSHAClient, IdentificationType, Otp, SHAClaimError

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "virtual_claim_opened.json"
SENSITIVE = {
    "patient_name",
    "member_name",
    "member_number",
    "nhif_number",
    "created_by_name",
    "updated_by_name",
    "notes",
}


def sanitise(payload: dict[str, object]) -> dict[str, object]:
    out = dict(payload)
    for key in SENSITIVE & out.keys():
        if isinstance(out[key], str) and out[key]:
            out[key] = "REDACTED"
    if isinstance(out.get("authorization_code"), str):
        out["authorization_code"] = "CR0000000000000-0-TESTTOKEN"
    return out


async def main() -> int:
    load_dotenv()
    id_number = input("Beneficiary national ID: ").strip()  # noqa: ASYNC250 — interactive script, blocking is intended

    async with AsyncSHAClient.from_env() as sha:
        eligibility = await sha.eligibility.check(id_number, IdentificationType.NATIONAL_ID)
        if not eligibility.member_found or eligibility.patient_id is None:
            print(f"Not found: {eligibility.status_description}")
            return 1
        print(
            f"Member: {eligibility.full_name} ({eligibility.patient_id}) covered today: {eligibility.is_covered_on(date.today())}"
        )

        coverage = await sha.eligibility.interventions(eligibility.patient_id, "SHA-12-SC-01")
        consultation = next(c for c in coverage if c.name == "Consultation")
        service_type = consultation.service_type_for_authorization
        print(f"Authorising {consultation.code} as {service_type} — SHA will now SMS the registered phone…")

        auth = await sha.consent.authorize(eligibility.patient_id, service_type, [consultation.code])
        print(f"Authorization {auth.status} (guid={auth.guid}, expires {auth.expiry})")

        try:
            otp = Otp(input("OTP received: ").strip())  # noqa: ASYNC250
            claim = await sha.claims.open_visit(
                eligibility.patient_id, service_type, [consultation.code], otp
            )
        except SHAClaimError as exc:
            print(f"Visit failed: {exc}")
            await sha.consent.reject(auth.token)
            print("Pending authorization rejected (cleanup).")
            return 1

    print("\nVirtual claim opened:")
    print(f"  consent_token : {claim.consent_token}  (redacted; .value to use)")
    print(f"  claim_id      : {claim.claim_id}   guid: {claim.guid}")
    print(f"  workflow_state: {claim.workflow_state!r}   auth status: {claim.claim_auth_status!r}")
    print(f"  service_type  : {claim.service_type}   payer: {claim.payer_name}   scheme: {claim.scheme_name}")

    FIXTURE.write_text(json.dumps(sanitise(dict(claim.extra, **_modelled(claim))), indent=2))
    print(f"\nSanitised response saved to {FIXTURE.relative_to(Path.cwd())}")
    print("Keep the consent_token value if you want to continue building this claim:")
    print(f"  {claim.consent_token.value}")
    return 0


def _modelled(claim: object) -> dict[str, object]:
    # Re-emit the modelled fields alongside `extra` so the fixture is the full server payload.
    from dataclasses import fields

    out: dict[str, object] = {}
    for f in fields(claim):  # type: ignore[arg-type]
        if f.name == "extra":
            continue
        value = getattr(claim, f.name)
        out[f.name] = value.value if hasattr(value, "value") else (str(value) if value is not None else None)
    return out


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
