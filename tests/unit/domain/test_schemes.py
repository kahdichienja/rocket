"""DHA spells a scheme two ways and decides the visit's scheme itself; these are the rules for both."""

from sha_claim.domain.schemes import belongs_to_scheme, canonical_scheme, scheme_family


def test_canonical_scheme_folds_both_spellings() -> None:
    assert canonical_scheme("Public Officers Medical Scheme Fund") == "POMSF"
    assert canonical_scheme("Universal Health Coverage") == "UHC"
    assert canonical_scheme("POMSF") == "POMSF"
    assert canonical_scheme("shif") == "SHIF"
    assert canonical_scheme("") == "" and canonical_scheme(None) == ""
    # An unknown title is passed through rather than mangled into a wrong code.
    assert canonical_scheme("Some New Fund") == "Some New Fund"


def test_scheme_family_reads_the_code_prefix() -> None:
    assert scheme_family("PMF-12-004") == "POMSF"
    assert scheme_family("SHA-12-001") == "SHA"
    assert scheme_family("SHA-01-SC-01") == "SHA"
    assert scheme_family("weird") == "" and scheme_family(None) == ""


def test_only_the_pomsf_split_is_decidable() -> None:
    """DHA picks UHC vs SHIF itself, so a general code is allowed under either."""
    assert belongs_to_scheme("PMF-12-004", "POMSF")
    assert not belongs_to_scheme("PMF-12-004", "SHIF")
    assert not belongs_to_scheme("SHA-12-001", "POMSF")
    assert belongs_to_scheme("SHA-12-001", "UHC")
    assert belongs_to_scheme("SHA-12-001", "SHIF")
    assert belongs_to_scheme("UNKNOWN-1", "POMSF")  # never guess at an unfamiliar prefix
