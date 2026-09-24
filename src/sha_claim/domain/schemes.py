"""DHA names a scheme two ways: a short code in eligibility (`UHC`, `SHIF`, `POMSF`) and a full title on the
claim (`Universal Health Coverage`, `Public Officers Medical Scheme Fund`). One vocabulary, two spellings.

`canonical_scheme` turns either into the short code, so a claim's own answer can be compared with — and can
correct — whatever an HMIS recorded when the visit was opened. DHA is the authority: it decides which of a
member's schemes a visit is actually billed to, and it does not take the caller's word for it.
"""

from __future__ import annotations

#: Full titles observed on claims, mapped to the short code eligibility uses.
_TITLES: dict[str, str] = {
    "universal health coverage": "UHC",
    "social health insurance fund": "SHIF",
    "public officers medical scheme fund": "POMSF",
    "emergency chronic and critical illness fund": "ECCIF",
    "primary health care fund": "PHC",
}

#: Prefixes DHA puts on intervention and sub-benefit codes, mapped to the scheme family they belong to.
#: `PMF-12-001` is a Public Officers service; `SHA-12-001` is a general one (UHC or SHIF — DHA picks).
_CODE_PREFIXES: dict[str, str] = {"PMF": "POMSF", "SHA": "SHA"}


def canonical_scheme(name: str | None) -> str:
    """`"Public Officers Medical Scheme Fund"` → `"POMSF"`; an already-short code is returned unchanged."""
    if not name or not name.strip():
        return ""
    cleaned = name.strip()
    if len(cleaned) <= 6 and cleaned.isalpha():
        return cleaned.upper()
    return _TITLES.get(cleaned.casefold(), cleaned)


def scheme_family(code: str | None) -> str:
    """The family an intervention or sub-benefit code belongs to: `PMF-12-004` → `POMSF`, `SHA-12-004` → `SHA`.

    `SHA` means "any general scheme": DHA decides between UHC and SHIF itself when the visit opens, so no
    caller can narrow it further.
    """
    if not code or "-" not in code:
        return ""
    return _CODE_PREFIXES.get(code.split("-", 1)[0].strip().upper(), "")


def belongs_to_scheme(code: str | None, scheme: str | None) -> bool:
    """Whether an intervention code can be billed under a scheme the member holds.

    Only the POMSF/general split is decidable: a `PMF-*` service belongs to POMSF and nothing else, a `SHA-*`
    service belongs to any general scheme. An unknown prefix is allowed rather than guessed at.
    """
    family = scheme_family(code)
    if not family:
        return True
    return family == "POMSF" if canonical_scheme(scheme) == "POMSF" else family == "SHA"
