from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from sha_claim.settings import SHASettings

FIXTURES = Path(__file__).parent / "fixtures"
SPEC = Path(__file__).parent.parent / "docs" / "api" / "spec"


@pytest.fixture
def settings() -> SHASettings:
    return SHASettings(client_id="cid", client_secret="secret", base_url="https://uat.example/uat-middleware")


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text())


def load_spec(api: str) -> Any:
    return json.loads((SPEC / f"{api}.json").read_text())


def load_examples() -> Any:
    return json.loads((SPEC / "examples.json").read_text())
