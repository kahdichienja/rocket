"""Configuration and settings for Smart Access Provider API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from smart_access.errors import SmartConfigurationError


class SmartEnvironment(StrEnum):
    DEV = "dev"
    PROD = "prod"


BASE_URL_DEV = "https://data.smartapplicationsgroup.com/providerapi-dev"
BASE_URL_PROD = "https://data.smartapplicationsgroup.com/providerapi"


@dataclass(frozen=True)
class SmartTimeouts:
    connect: float = 5.0
    read: float = 30.0
    upload: float = 120.0


@dataclass(frozen=True)
class SmartSettings:
    """Settings required to communicate with Smart Provider API."""

    provider_key: str
    username: str
    password: str
    client_id: str = ""
    client_secret: str = ""
    base_url: str = BASE_URL_DEV
    environment: SmartEnvironment = SmartEnvironment.DEV
    location_code: str = ""
    location_name: str = ""
    language: str = "en"
    token_expiry_skew_seconds: int = 60
    timeouts: SmartTimeouts = SmartTimeouts()

    def __post_init__(self) -> None:
        if not self.provider_key.strip():
            raise SmartConfigurationError("SMART_PROVIDER_KEY cannot be empty")
        if not self.username.strip():
            raise SmartConfigurationError("SMART_USERNAME cannot be empty")
        if not self.password.strip():
            raise SmartConfigurationError("SMART_PASSWORD cannot be empty")

    @classmethod
    def from_env(cls) -> Self:
        env_str = os.getenv("SMART_ENVIRONMENT", "dev").strip().lower()
        is_prod = env_str in ("prod", "production", "live")
        environment = SmartEnvironment.PROD if is_prod else SmartEnvironment.DEV

        default_base = BASE_URL_PROD if is_prod else BASE_URL_DEV
        base_url = os.getenv("SMART_BASE_URL", default_base).rstrip("/")

        provider_key = os.getenv("SMART_PROVIDER_KEY", "SKSP_6245").strip()
        username = os.getenv("SMART_USERNAME", "").strip()
        password = os.getenv("SMART_PASSWORD", "").strip()
        client_id = os.getenv("SMART_CLIENT_ID", "").strip()
        client_secret = os.getenv("SMART_CLIENT_SECRET", "").strip()

        location_code = os.getenv("SMART_LOCATION_CODE", "").strip()
        location_name = os.getenv("SMART_LOCATION_NAME", "").strip()
        language = os.getenv("SMART_LANGUAGE", "en").strip()

        connect = float(os.getenv("SMART_CONNECT_TIMEOUT", "5.0"))
        read = float(os.getenv("SMART_READ_TIMEOUT", "30.0"))
        upload = float(os.getenv("SMART_UPLOAD_TIMEOUT", "120.0"))
        skew = int(os.getenv("SMART_TOKEN_SKEW_SECONDS", "60"))

        return cls(
            provider_key=provider_key,
            username=username,
            password=password,
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            environment=environment,
            location_code=location_code,
            location_name=location_name,
            language=language,
            token_expiry_skew_seconds=skew,
            timeouts=SmartTimeouts(connect=connect, read=read, upload=upload),
        )
