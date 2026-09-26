"""MemberGateway port."""

from __future__ import annotations

from typing import Protocol

from smart_access.domain.identifiers import PatientNumber, SessionId, VisitNumber
from smart_access.domain.member import CopaymentRule, SmartMember


class MemberGateway(Protocol):
    """Port for retrieving member bio, benefit pools, and copayment rules."""

    async def get_member_details(
        self, patient_number: PatientNumber, session_id: SessionId
    ) -> tuple[SmartMember, ...]:
        """Fetch member profile and balance pools."""
        ...

    async def get_copayment_rule(
        self, benefit_id: int, provider_key: str, visit_number: VisitNumber
    ) -> CopaymentRule | None:
        """Fetch copay rules for a specific benefit pool."""
        ...
