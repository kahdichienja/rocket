"""The set of gateways a ClaimSession needs, bundled so the session's constructor stays stable."""

from __future__ import annotations

from dataclasses import dataclass

from sha_claim.ports.emergency_gateway import EmergencyGateway
from sha_claim.ports.preauth_gateway import PreauthGateway
from sha_claim.ports.prescription_gateway import PrescriptionGateway
from sha_claim.ports.virtual_claim_gateway import VirtualClaimGateway


@dataclass(frozen=True, slots=True)
class ClaimGateways:
    claims: VirtualClaimGateway
    preauths: PreauthGateway
    prescriptions: PrescriptionGateway
    emergency: EmergencyGateway
