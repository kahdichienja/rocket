"""Public Officers Medical Scheme Fund balances — what a civil servant has left to spend.

POMSF is not billed like the rest of SHA. The other funds set a limit per intervention, which
`benefits.utilization` answers; POMSF gives a **household** a pot against a policy, and dependants draw on
the principal member's pot. So "can this visit go ahead?" is a question about the family, not the patient,
and it has to be asked before a visit is opened rather than discovered at checkout.

**The shape of `benefit` is not in DHA's docs** — the portal publishes it as a bare `[{}]` — so it is
modelled from what UAT actually returns:

```json
{"benefitId": 77, "name": "Eye Health", "benefitCode": "SHA-05", "limit": 40000,
 "benefitShared": "FAMILY SHARED", "balance": [{"member": "<opaque id>", "balance": 40000}],
 "subBenefit": [{"subBenefitCode": "SHA-05-SC-01", "limit": 40000, "balance": [...]}]}
```

Two things there are easy to get wrong, and both were:

* **`balance` is a list, not a number** — one entry per member who can draw on the benefit.
* **`benefitShared: "FAMILY SHARED"` means those entries are the same pot seen from several sides.** Summing
  them multiplies a family's cover by the size of the family.

Where an amount still cannot be read, this reports *unknown* rather than zero. That distinction is the whole
point: a zero means "this family has spent their cover" and a desk will turn a patient away on it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from sha_claim.domain.money import Money

__all__ = [
    "PomsfBalance",
    "PomsfBenefit",
    "PomsfFamilyMember",
    "PomsfPolicy",
    "policy_year_for",
]


def policy_year_for(day: date | None = None) -> str:
    """The POMSF policy year covering `day`.

    Kenya's financial year turns on 1 July, and the collection says as much: "based on financial years that
    switch every 1st July". So 1 July 2026 to 30 June 2027 is all policy year 2026, and asking for the wrong
    one returns another year's balance — which reads as a real answer and is not.
    """
    today = day or date.today()
    return str(today.year if today.month >= 7 else today.year - 1)


def _money(value: object) -> Money | None:
    """A monetary amount, or None when the server did not state one.

    None and "not stated" are the same thing here; zero is emphatically not. Floats go through `str` because
    `Money` refuses them outright, and DHA does send JSON numbers.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return Money.kes(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _first(source: Mapping[str, Any], *names: str) -> Any:
    """The first of these keys the payload actually has, case-insensitively."""
    lowered = {str(k).lower(): v for k, v in source.items()}
    for name in names:
        if (value := lowered.get(name.lower())) is not None:
            return value
    return None


@dataclass(frozen=True, slots=True)
class PomsfBenefit:
    """One benefit line on a POMSF policy, and what is left on it.

    `limit`, `used` and `remaining` are each `None` when the payload did not say — see the module note. Read
    `is_known` before showing a number to anybody.
    """

    name: str
    code: str
    limit: Money | None
    used: Money | None
    remaining: Money | None
    shared: str = ""
    """`FAMILY SHARED` when the whole household draws on this one pot."""
    service_type: str = ""
    """`OUTPATIENT` / `INPATIENT` — which side of a visit the benefit pays for."""
    sub_benefits: tuple[PomsfBenefit, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_family_shared(self) -> bool:
        return "SHARED" in self.shared.upper()

    @property
    def is_known(self) -> bool:
        """Whether a remaining figure was actually reported or could be derived from limit and used."""
        return self.remaining is not None

    @property
    def is_exhausted(self) -> bool:
        """Known to be spent. Unknown is not exhausted — that is the mistake this guards."""
        return self.remaining is not None and self.remaining.amount <= 0

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> PomsfBenefit:
        limit = _money(_first(raw, "limit", "limitAmount", "benefitLimit", "totalLimit"))
        remaining = _balance_of(raw)
        used = _money(_first(raw, "used", "usedAmount", "utilized", "utilised", "consumed"))
        if used is None and limit is not None and remaining is not None:
            used = Money(limit.amount - remaining.amount, limit.currency)
        if remaining is None and limit is not None and used is not None:
            remaining = Money(limit.amount - used.amount, limit.currency)
        return cls(
            name=str(_first(raw, "name", "benefitName", "description", "benefit") or ""),
            code=str(_first(raw, "benefitCode", "code", "subBenefitCode") or ""),
            limit=limit,
            used=used,
            remaining=remaining,
            shared=str(_first(raw, "benefitShared", "subBenefitShared") or ""),
            service_type=str(_first(raw, "type") or ""),
            sub_benefits=tuple(
                PomsfBenefit.parse(sb) for sb in (raw.get("subBenefit") or ()) if isinstance(sb, Mapping)
            ),
            raw=dict(raw),
        )


def _balance_of(raw: Mapping[str, Any]) -> Money | None:
    """What is left on a benefit, from UAT's `balance` list.

    `[{"member": "<id>", "balance": 40000}]` — one entry per member entitled to draw on it. When the benefit
    is **family shared** those entries are one pot seen from several sides, so the largest is taken: summing
    would report a family of four as having four times their cover. Only a benefit that is not shared has
    genuinely separate per-member pots to add up.

    A scalar is still accepted, since other DHA endpoints send one.
    """
    value = _first(
        raw, "balance", "remaining", "remainingAmount", "availableAmount", "available", "balanceAmount"
    )
    if value is None:
        return None
    if isinstance(value, Mapping):
        return _money(_first(value, "balance", "amount"))
    if isinstance(value, (list, tuple)):
        amounts = [
            m for m in (_money(_first(e, "balance", "amount")) for e in value if isinstance(e, Mapping)) if m
        ]
        if not amounts:
            return None
        shared = "SHARED" in str(_first(raw, "benefitShared", "subBenefitShared") or "").upper()
        if shared:
            return max(amounts, key=lambda m: m.amount)
        total = amounts[0]
        for extra in amounts[1:]:
            total = total + extra
        return total
    return _money(value)


@dataclass(frozen=True, slots=True)
class PomsfPolicy:
    """A policy the member is on, with its benefit lines."""

    name: str
    policy_code: str
    scheme_name: str
    status: str
    policy_year: str
    benefit_count: int | None
    """`totalBenefit` on the wire — how many benefit lines the policy has, **not** an amount of money.
    UAT returns 21 for a policy carrying 21 benefits; reading it as KES 21.00 was the obvious trap."""
    benefits: tuple[PomsfBenefit, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_active(self) -> bool:
        return self.status.strip().upper() in {"ACTIVE", "A", "1", "TRUE"}

    @property
    def remaining(self) -> Money | None:
        """What is left across this policy's benefits, or None when nothing could be read.

        These are separate pots — Eye Health, Inpatient, Outpatient each have their own limit — so this is
        the policy's **total cover remaining**, not a single spendable balance. Which pot pays depends on the
        intervention, so read `benefits` for a decision about one service.

        Benefits whose figures are unknown are left out rather than counted as zero, and a policy where
        *none* is known totals to None — a missing answer, not an empty wallet.
        """
        known = [b.remaining for b in self.benefits if b.remaining is not None]
        if not known:
            return None
        total = known[0]
        for amount in known[1:]:
            total = total + amount
        return total

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> PomsfPolicy:
        candidate = raw.get("policy")
        policy: Mapping[str, Any] = candidate if isinstance(candidate, Mapping) else {}
        benefits = raw.get("benefit") or raw.get("benefits") or ()
        return cls(
            name=str(_first(policy, "name", "description") or ""),
            policy_code=str(_first(policy, "policyCode", "policyId") or ""),
            scheme_name=str(_first(policy, "schemeName", "schemeCode") or ""),
            status=str(_first(policy, "status") or ""),
            policy_year=str(_first(policy, "PolicyYear", "policyYear") or ""),
            benefit_count=_int(_first(policy, "totalBenefit")),
            benefits=tuple(PomsfBenefit.parse(b) for b in benefits if isinstance(b, Mapping)),
            raw=dict(raw),
        )


@dataclass(frozen=True, slots=True)
class PomsfFamilyMember:
    """Somebody else drawing on the same policy — the reason a balance is a household question."""

    member_number: str
    full_name: str
    relationship_type: str
    national_id: str = ""
    is_active: bool = True

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> PomsfFamilyMember:
        names = [str(_first(raw, n) or "") for n in ("firstName", "middleName", "lastName")]
        return cls(
            member_number=str(_first(raw, "memberNumber") or ""),
            full_name=" ".join(part for part in names if part).strip(),
            relationship_type=str(_first(raw, "relationshipType") or ""),
            national_id=str(_first(raw, "nationalId") or ""),
            is_active=bool(raw.get("isActive", True)),
        )


@dataclass(frozen=True, slots=True)
class PomsfBalance:
    """`GET /patients/pomsf-balances` — the member, their household, and what the policies have left."""

    member_number: str
    full_name: str
    national_id: str
    household_id: str
    relationship_type: str
    parent_member_number: str
    policies: tuple[PomsfPolicy, ...] = ()
    family_members: tuple[PomsfFamilyMember, ...] = ()
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_principal(self) -> bool:
        """True when this member holds the policy themselves rather than drawing on somebody else's.

        UAT does not leave `parentNumber` empty for a principal — it repeats their own member number, with
        `relationshipType: "SELF"`. Reading a missing parent as the only signal labelled the policyholder a
        dependant and told the desk to go and find a principal who was standing in front of them.
        """
        parent = self.parent_member_number.strip()
        if not parent or parent.casefold() == self.member_number.strip().casefold():
            return True
        return self.relationship_type.strip().upper() in {"SELF", "PRINCIPAL", "PRINCIPAL MEMBER"}

    @property
    def active_policies(self) -> tuple[PomsfPolicy, ...]:
        return tuple(p for p in self.policies if p.is_active)

    @property
    def remaining(self) -> Money | None:
        """What the member has left across active policies, or None when the payload did not say.

        **None is not zero.** A desk reads this to decide whether to open a visit at all, and a fabricated
        zero would turn away a patient who is covered.
        """
        known = [p.remaining for p in self.active_policies if p.remaining is not None]
        if not known:
            return None
        total = known[0]
        for amount in known[1:]:
            total = total + amount
        return total

    @property
    def is_exhausted(self) -> bool:
        """Known to have nothing left. Unknown is not exhausted."""
        remaining = self.remaining
        return remaining is not None and remaining.amount <= 0

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> PomsfBalance:
        names = [str(_first(raw, n) or "") for n in ("firstName", "middleName", "lastName")]
        policies = raw.get("memberPolicies") or ()
        family = raw.get("familyMembers") or ()
        return cls(
            member_number=str(_first(raw, "memberNumber", "shaNumber") or ""),
            full_name=" ".join(part for part in names if part).strip(),
            national_id=str(_first(raw, "nationalId") or ""),
            household_id=str(_first(raw, "householdId") or ""),
            relationship_type=str(_first(raw, "relationshipType") or ""),
            parent_member_number=str(_first(raw, "parentNumber", "parentMemberNumber") or ""),
            policies=tuple(PomsfPolicy.parse(p) for p in policies if isinstance(p, Mapping)),
            family_members=tuple(PomsfFamilyMember.parse(m) for m in family if isinstance(m, Mapping)),
            extra=dict(raw),
        )


def parse_pomsf_balances(payload: Mapping[str, Any] | Sequence[Any]) -> PomsfBalance | None:
    """The balance from whatever the server sent: an object, or a list with the member first.

    UAT has answered both ways on other endpoints, so neither is assumed. `None` means there was nothing to
    read — again, not a zero balance.
    """
    if isinstance(payload, Mapping):
        return PomsfBalance.parse(payload) if payload else None
    for entry in payload or ():
        if isinstance(entry, Mapping) and entry:
            return PomsfBalance.parse(entry)
    return None
