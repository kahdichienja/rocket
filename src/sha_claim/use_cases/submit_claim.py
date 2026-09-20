"""Finalise a virtual claim. The one call that moves money — attempted exactly once."""

from __future__ import annotations

from sha_claim.domain.claim import VirtualClaim
from sha_claim.domain.identifiers import ConsentToken, InvoiceNumber
from sha_claim.errors import SubmissionOutcomeUnknownError, TransportError
from sha_claim.ports.virtual_claim_gateway import ClaimSubmitter


class SubmitClaim:
    def __init__(self, gateway: ClaimSubmitter) -> None:
        self._gateway = gateway

    async def execute(
        self,
        token: ConsentToken,
        invoice: InvoiceNumber | None = None,
        reason_for_unknown_patient: str | None = None,
    ) -> VirtualClaim:
        try:
            return await self._gateway.submit(token, invoice, reason_for_unknown_patient)
        except TransportError as exc:
            # The request may or may not have reached the server. Never retry blindly:
            # the caller resolves the ambiguity with `preview` and decides.
            raise SubmissionOutcomeUnknownError(
                f"submit for {token} did not complete ({exc}); call preview() to learn the claim's state",
                trace_id=exc.trace_id,
            ) from exc
