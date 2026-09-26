"""Unit tests for smart_access settings."""

import os
from unittest import mock

import pytest

from smart_access.errors import SmartConfigurationError
from smart_access.settings import SmartEnvironment, SmartSettings


def test_settings_validation_missing_credentials() -> None:
    with pytest.raises(SmartConfigurationError, match="SMART_USERNAME cannot be empty"):
        SmartSettings(provider_key="KEY", username="", password="PWD")

    with pytest.raises(SmartConfigurationError, match="SMART_PASSWORD cannot be empty"):
        SmartSettings(provider_key="KEY", username="USER", password="")

    with pytest.raises(SmartConfigurationError, match="SMART_PROVIDER_KEY cannot be empty"):
        SmartSettings(provider_key="", username="USER", password="PWD")


def test_settings_from_env() -> None:
    env = {
        "SMART_PROVIDER_KEY": "MY_KEY",
        "SMART_USERNAME": "my_user",
        "SMART_PASSWORD": "my_password",
        "SMART_ENVIRONMENT": "prod",
        "SMART_LOCATION_CODE": "126",
        "SMART_LOCATION_NAME": "CASHIER1",
    }
    with mock.patch.dict(os.environ, env, clear=True):
        s = SmartSettings.from_env()
        assert s.provider_key == "MY_KEY"
        assert s.username == "my_user"
        assert s.password == "my_password"
        assert s.environment == SmartEnvironment.PROD
        assert s.location_code == "126"
        assert s.location_name == "CASHIER1"
        assert "providerapi" in s.base_url
