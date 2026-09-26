"""Use cases for member details, benefit pools, and copayments."""

from __future__ import annotations

from smart_access.domain.identifiers import PatientNumber, SessionId, VisitNumber
from smart_access.domain.member import CopaymentRule, SmartMember
from smart_access.ports.member_gateway import MemberGateway


class GetMemberDetails:
    """Retrieve insurance benefits, copay indicators, and card details for a session."""

    def __init__(self, gateway: MemberGateway) -> None:
        self._gateway = gateway

    async def execute(
        self, patient_number: PatientNumber | str, session_id: SessionId | int
    ) -> tuple[SmartMember, ...]:
        patient = PatientNumber.of(patient_number)
        sid = SessionId.of(session_id)
        return await self._gateway.get_member_details(patient, sid)


class GetCopaymentRule:
    """Retrieve specific copayment rule set by the payer for a benefit."""

    def __init__(self, gateway: MemberGateway) -> None:
        self._gateway = gateway

    async def execute(
        self, benefit_id: int, provider_key: str, visit_number: VisitNumber | str
    ) -> CopaymentRule | None:
        vnum = VisitNumber.of(visit_number)
        return await self._gateway.get_copayment_rule(benefit_id, provider_key, vnum)
