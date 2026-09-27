"""The package version is written in two places, and they must agree.

0.1.22 shipped with `pyproject.toml` at 0.1.22 and `__version__` still at "0.1.21". NaCare gates startup on
`sha_claim.__version__`, so a correctly-pinned backend refused to start, insisting the version it had was
older than the one it needed. The two are a few lines apart and a release bumps one of them by hand; this
is the check that stops that reaching PyPI again.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import sha_claim

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_version_matches_pyproject() -> None:
    declared = tomllib.loads(PYPROJECT.read_text())["project"]["version"]
    assert sha_claim.__version__ == declared, (
        f"sha_claim.__version__ is {sha_claim.__version__!r} but pyproject.toml says {declared!r}. "
        "Bump both, or a release ships a package that misreports its own version."
    )
