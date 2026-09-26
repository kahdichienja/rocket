"""Domain models for Smart SBB Rules validation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from smart_access.domain.identifiers import MedicalAidCode, MemberNumber, PolicyId


@dataclass(frozen=True)
class RulesCheckItem:
    """An invoice item candidate to check against payer rules."""

    provider_item_code: str
    item_net_amount: Decimal
    pool_number: int

    def __post_init__(self) -> None:
        if not self.provider_item_code.strip():
            raise ValueError("provider_item_code cannot be empty")
        if self.item_net_amount < 0:
            raise ValueError("item_net_amount cannot be negative")


@dataclass(frozen=True)
class RulesCheckRequest:
    """Full rules check payload for `/api/sbb-rules`."""

    items: tuple[RulesCheckItem, ...]
    medical_aid_code: MedicalAidCode
    medical_aid_number: MemberNumber
    medical_aid_plan: str
    policy_id: PolicyId

    def __post_init__(self) -> None:
        if not self.items:
            raise ValueError("items cannot be empty")


@dataclass(frozen=True)
class RuleItemValidation:
    """Validation response per item from the payer's rules engine."""

    item_code: str
    item_name: str
    preauth_required: bool
    preauth_amount: Decimal
    preauth_rule_code: str
    excluded: bool
    price_amount: Decimal


@dataclass(frozen=True)
class RuleValidationResult:
    """Aggregated rules check outcome."""

    code: str
    items: tuple[RuleItemValidation, ...]

    @property
    def any_preauth_required(self) -> bool:
        return any(item.preauth_required for item in self.items)

    @property
    def any_excluded(self) -> bool:
        return any(item.excluded for item in self.items)

    @property
    def preauth_items(self) -> tuple[RuleItemValidation, ...]:
        return tuple(item for item in self.items if item.preauth_required)

    @property
    def excluded_items(self) -> tuple[RuleItemValidation, ...]:
        return tuple(item for item in self.items if item.excluded)
