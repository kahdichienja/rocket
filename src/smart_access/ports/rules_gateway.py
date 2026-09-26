"""RulesGateway port."""

from __future__ import annotations

from typing import Protocol

from smart_access.domain.rules import RulesCheckRequest, RuleValidationResult


class RulesGateway(Protocol):
    """Port for validating billing items against insurer rules engine."""

    async def validate_rules(self, request: RulesCheckRequest) -> RuleValidationResult:
        """Post items to `/api/sbb-rules` and return preauth/exclusion evaluations."""
        ...
