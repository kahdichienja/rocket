import pytest

from sha_claim.errors import ConfigurationError
from sha_claim.settings import Environment, SHASettings


def test_from_env_uat_defaults() -> None:
    s = SHASettings.from_env({"SHA_CLIENT_ID": "a", "SHA_CLIENT_SECRET": "b"})
    assert s.environment is Environment.UAT
    assert s.api_root == "https://ilm-dev.dha.go.ke/uat-middleware/api/v1"
    assert s.timeouts.read == 30.0


def test_missing_credentials_fail_fast() -> None:
    with pytest.raises(ConfigurationError, match="client_secret"):
        SHASettings.from_env({"SHA_CLIENT_ID": "a"})


def test_production_requires_explicit_base_url() -> None:
    env = {"SHA_CLIENT_ID": "a", "SHA_CLIENT_SECRET": "b", "SHA_ENVIRONMENT": "production"}
    with pytest.raises(ConfigurationError, match="SHA_BASE_URL"):
        SHASettings.from_env(env)
    s = SHASettings.from_env({**env, "SHA_BASE_URL": "https://prod.example/"})
    assert s.api_root == "https://prod.example/api/v1"


@pytest.mark.parametrize(
    ("key", "value", "msg"),
    [
        ("SHA_ENVIRONMENT", "staging", "SHA_ENVIRONMENT"),
        ("SHA_READ_TIMEOUT", "fast", "number"),
        ("SHA_BASE_URL", "http://insecure", "https"),
    ],
)
def test_invalid_values(key: str, value: str, msg: str) -> None:
    with pytest.raises(ConfigurationError, match=msg):
        SHASettings.from_env({"SHA_CLIENT_ID": "a", "SHA_CLIENT_SECRET": "b", key: value})
