"""POMSF balances: the household pot a civil servant's visit is spent from.

Two properties matter here.

**Unknown never reads as zero.** A desk decides whether to open a visit on this number, so a parser that
guessed wrong would turn away covered patients with a confident 0.00.

**A family-shared pot is not multiplied by the family.** UAT sends `balance` as a list with one entry per
member who can draw on the benefit; for a `FAMILY SHARED` benefit those entries are the same pot seen from
several sides, and summing them would report four times the cover that exists.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

import pytest

from sha_claim.domain.money import Money
from sha_claim.domain.pomsf import PomsfBalance, PomsfBenefit, parse_pomsf_balances, policy_year_for


class TestThePolicyYear:
    @pytest.mark.parametrize(
        ("day", "expected"),
        [
            (date(2026, 7, 1), "2026"),  # the financial year turns on 1 July
            (date(2026, 6, 30), "2025"),  # the day before belongs to the previous one
            (date(2026, 9, 26), "2026"),
            (date(2027, 1, 15), "2026"),  # January is still the year that began in July
            (date(2026, 12, 31), "2026"),
        ],
    )
    def test_follows_the_financial_year(self, day: date, expected: str) -> None:
        """Asking for the wrong year returns another year's balance, which reads as a real answer."""
        assert policy_year_for(day) == expected


def uat_benefit(**over: object) -> dict[str, Any]:
    """A benefit exactly as UAT returns one (DHA publishes this array as a bare `[{}]`)."""
    base = {
        "benefitId": 83,
        "name": "Outpatient Services",
        "benefitCode": "PMF-12",
        "type": "OUTPATIENT",
        "limit": 225000,
        "benefitShared": "FAMILY SHARED",
        "balance": [{"member": "6aa8a5ed237b78fb05fd5581", "balance": 225000}],
        "subBenefit": [
            {
                "subBenefitCode": "PMF-12-SC-01",
                "name": "Outpatient PHC",
                "limit": 225000,
                "subBenefitShared": "FAMILY SHARED",
                "balance": [{"member": "m1", "balance": 225000}],
            }
        ],
    }
    base.update(over)
    return base


class TestReadingABenefitLine:
    def test_reads_the_shape_uat_actually_sends(self) -> None:
        b = PomsfBenefit.parse(uat_benefit())
        assert b.code == "PMF-12"
        assert b.limit == Money.kes("225000")
        assert b.remaining == Money.kes("225000")
        assert b.used == Money.kes("0")
        assert b.is_family_shared and b.service_type == "OUTPATIENT"
        assert len(b.sub_benefits) == 1

    def test_does_not_multiply_a_family_shared_pot_by_the_family(self) -> None:
        """Four members all see the same KES 225,000 — the cover is 225,000, not 900,000."""
        b = PomsfBenefit.parse(
            uat_benefit(balance=[{"member": m, "balance": 225000} for m in ("a", "b", "c", "d")])
        )
        assert b.remaining == Money.kes("225000")

    def test_adds_up_genuinely_separate_pots(self) -> None:
        b = PomsfBenefit.parse(
            uat_benefit(
                benefitShared="INDIVIDUAL",
                balance=[{"member": "a", "balance": 100}, {"member": "b", "balance": 50}],
            )
        )
        assert b.remaining == Money.kes("150")

    def test_derives_what_has_been_spent(self) -> None:
        b = PomsfBenefit.parse(uat_benefit(balance=[{"member": "a", "balance": 25000}]))
        assert b.used == Money.kes("200000")
        assert not b.is_exhausted

    def test_takes_a_stated_balance(self) -> None:
        b = PomsfBenefit.parse({"name": "Outpatient", "code": "OP", "limit": 100000, "balance": 25000})
        assert b.remaining == Money.kes("25000")
        assert b.is_known and not b.is_exhausted

    def test_derives_the_balance_from_limit_and_used(self) -> None:
        b = PomsfBenefit.parse({"limit": "100000", "used": "40000"})
        assert b.remaining == Money.kes("60000")

    @pytest.mark.parametrize(
        "key", ["balance", "remaining", "remainingAmount", "availableAmount", "available"]
    )
    def test_reads_the_spellings_dha_might_use(self, key: str) -> None:
        """`benefit` is published as `[{}]`, so the key is a guess — several are tried before giving up."""
        assert PomsfBenefit.parse({key: 500}).remaining == Money.kes("500")

    def test_says_unknown_rather_than_zero_when_nothing_was_stated(self) -> None:
        b = PomsfBenefit.parse({"name": "Outpatient"})
        assert b.remaining is None
        assert not b.is_known
        assert not b.is_exhausted  # unknown is NOT exhausted — this is the safety property

    def test_a_real_zero_is_still_a_zero(self) -> None:
        b = PomsfBenefit.parse({"balance": 0})
        assert b.is_known and b.is_exhausted

    def test_survives_junk_without_inventing_a_number(self) -> None:
        value: Any
        for value in ["", "  ", "n/a", None, True, {}, [], [{}], [{"member": "a"}]]:
            assert PomsfBenefit.parse({"balance": value}).remaining is None


def _payload(**over: object) -> dict[str, Any]:
    base: dict[str, Any] = {
        "memberNumber": "POMSF-5CA73992",
        "firstName": "ROSE",
        "lastName": "CHEBET",
        "nationalId": "12345678",
        "householdId": "HH-1",
        "relationshipType": "SELF",
        "parentNumber": "POMSF-5CA73992",
        "memberPolicies": [
            {
                "policy": {
                    "name": "Civil Servants",
                    "policyCode": "PC-1",
                    "status": "ACTIVE",
                    "PolicyYear": "2026",
                },
                "benefit": [uat_benefit(limit=100000, balance=[{"member": "m", "balance": 75000}])],
            }
        ],
        "familyMembers": [
            {
                "memberNumber": "POMSF-2",
                "firstName": "JOHN",
                "lastName": "CHEBET",
                "relationshipType": "SPOUSE",
            }
        ],
    }
    base.update(over)
    return base


class TestTheWholeBalance:
    def test_reads_the_member_their_household_and_what_is_left(self) -> None:
        b = PomsfBalance.parse(_payload())
        assert b.member_number == "POMSF-5CA73992"
        assert b.full_name == "ROSE CHEBET"
        assert b.is_principal
        assert b.remaining == Money.kes("75000")
        assert [m.full_name for m in b.family_members] == ["JOHN CHEBET"]

    def test_the_policyholder_is_the_principal_even_though_uat_repeats_their_own_number(self) -> None:
        """UAT sets `parentNumber` to the member's own number with `relationshipType: SELF`. Read as a
        missing parent, that labelled the policyholder a dependant and sent the desk looking for one."""
        assert PomsfBalance.parse(_payload()).is_principal

    def test_a_dependant_is_not_the_principal(self) -> None:
        """Dependants draw on the principal's pot, so the caller must pass the principal's number."""
        b = PomsfBalance.parse(_payload(parentNumber="POMSF-PRINCIPAL", relationshipType="CHILD"))
        assert not b.is_principal
        assert b.parent_member_number == "POMSF-PRINCIPAL"

    def test_an_inactive_policy_is_left_out_of_the_total(self) -> None:
        payload = _payload()
        payload["memberPolicies"][0]["policy"]["status"] = "TERMINATED"
        assert PomsfBalance.parse(payload).remaining is None

    def test_unreadable_amounts_leave_the_total_unknown_not_zero(self) -> None:
        """The failure this module exists to prevent: a parse miss printed as an empty wallet."""
        payload = _payload()
        payload["memberPolicies"][0]["benefit"] = [{"name": "Outpatient", "benefitCode": "PMF-12"}]
        balance = PomsfBalance.parse(payload)
        assert balance.remaining is None
        assert not balance.is_exhausted

    def test_a_genuinely_spent_pot_reads_as_exhausted(self) -> None:
        payload = _payload()
        payload["memberPolicies"][0]["benefit"] = [
            uat_benefit(limit=100000, balance=[{"member": "m", "balance": 0}])
        ]
        balance = PomsfBalance.parse(payload)
        assert balance.remaining == Money.kes("0")
        assert balance.is_exhausted

    def test_sums_across_several_benefit_lines(self) -> None:
        payload = _payload()
        payload["memberPolicies"][0]["benefit"] = [
            uat_benefit(balance=[{"member": "m", "balance": 1000}]),
            uat_benefit(balance=[{"member": "m", "balance": 2500}]),
            {"name": "unknown one"},
        ]
        assert PomsfBalance.parse(payload).remaining == Money.kes("3500")


class TestWhateverTheServerSends:
    def test_accepts_an_object(self) -> None:
        assert parse_pomsf_balances(_payload()) is not None

    def test_accepts_a_list_with_the_member_first(self) -> None:
        assert parse_pomsf_balances([_payload()]) is not None

    def test_nothing_at_all_is_none_rather_than_an_empty_balance(self) -> None:
        empty: Mapping[str, Any] | Sequence[Any]
        for empty in ({}, []):
            assert parse_pomsf_balances(empty) is None
        assert parse_pomsf_balances(None) is None  # type: ignore[arg-type]  # UAT sends null where the guides promise an object
