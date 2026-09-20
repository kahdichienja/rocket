import pytest

from sha_claim.domain.codes import Icd11Code, InterventionCode


@pytest.mark.parametrize("raw", ["1A00", "ba00.1", "XN5Y", "J18.9", "1a00.zz"])
def test_icd_code_accepts_and_normalises(raw: str) -> None:
    assert Icd11Code(raw).value == raw.upper()


@pytest.mark.parametrize("raw", ["", "1", "malaria", "1A00.", ".1", "1A00.12345"])
def test_icd_code_rejects_malformed(raw: str) -> None:
    with pytest.raises(ValueError):
        Icd11Code(raw)


def test_intervention_code_uppercased() -> None:
    assert InterventionCode("sha-01-001").value == "SHA-01-001"
