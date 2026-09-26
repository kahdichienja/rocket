"""Use case for validating billed items against payer rules."""

from __future__ import annotations

from smart_access.domain.rules import RulesCheckRequest, RuleValidationResult
from smart_access.ports.rules_gateway import RulesGateway


class ValidateRules:
    """Evaluates planned billed items against insurance rules for exclusions and preauthorizations."""

    def __init__(self, gateway: RulesGateway) -> None:
        self._gateway = gateway

    async def execute(self, request: RulesCheckRequest) -> RuleValidationResult:
        return await self._gateway.validate_rules(request)
