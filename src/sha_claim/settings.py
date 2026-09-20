"""Environment-driven configuration. Fails fast; never holds defaults for secrets."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from sha_claim.errors import ConfigurationError


class Environment(StrEnum):
    UAT = "uat"
    PRODUCTION = "production"


_BASE_URLS: dict[Environment, str] = {
    Environment.UAT: "https://ilm-dev.dha.go.ke/uat-middleware",
    # Not published on the developer portal; must be supplied via SHA_BASE_URL.
    Environment.PRODUCTION: "",
}


@dataclass(frozen=True, slots=True)
class Timeouts:
    connect: float = 5.0
    read: float = 30.0
    upload: float = 120.0


@dataclass(frozen=True, slots=True)
class SHASettings:
    client_id: str
    client_secret: str
    base_url: str
    environment: Environment = Environment.UAT
    timeouts: Timeouts = Timeouts()
    token_expiry_skew_seconds: int = 60

    def __post_init__(self) -> None:
        missing = [
            n for n, v in (("client_id", self.client_id), ("client_secret", self.client_secret)) if not v
        ]
        if missing:
            raise ConfigurationError(f"missing required settings: {', '.join(missing)}")
        if not self.base_url.startswith("https://"):
            raise ConfigurationError("base_url must be an https:// URL")

    @property
    def api_root(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v1"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> SHASettings:
        e = os.environ if env is None else env
        try:
            environment = Environment(e.get("SHA_ENVIRONMENT", "uat").lower())
        except ValueError as exc:
            raise ConfigurationError("SHA_ENVIRONMENT must be 'uat' or 'production'") from exc
        base_url = e.get("SHA_BASE_URL") or _BASE_URLS[environment]
        if not base_url:
            raise ConfigurationError("SHA_BASE_URL is required for the production environment")
        timeouts = Timeouts(
            connect=_float(e, "SHA_CONNECT_TIMEOUT", 5.0),
            read=_float(e, "SHA_READ_TIMEOUT", 30.0),
            upload=_float(e, "SHA_UPLOAD_TIMEOUT", 120.0),
        )
        return cls(
            client_id=e.get("SHA_CLIENT_ID", ""),
            client_secret=e.get("SHA_CLIENT_SECRET", ""),
            base_url=base_url,
            environment=environment,
            timeouts=timeouts,
        )


def _float(env: Mapping[str, str], key: str, default: float) -> float:
    raw = env.get(key)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{key} must be a number, got {raw!r}") from exc
