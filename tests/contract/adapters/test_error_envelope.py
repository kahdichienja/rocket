"""Real 4xx shapes observed on UAT (2026-09-20)."""

from sha_claim.adapters.wire.schemas.common import ErrorEnvelope


def test_plain_envelope() -> None:
    env = ErrorEnvelope.model_validate(
        {
            "error": "Bad Request",
            "message": "error validating request input: invalid identification type ''",
            "trace_id": "abc",
        }
    )
    assert env.detail() == "error validating request input: invalid identification type ''"
    assert env.status_text == "Bad Request"


def test_upstream_json_in_error_field_is_unwrapped() -> None:
    env = ErrorEnvelope.model_validate(
        {
            "error": '{"error":"Kindly note the intervention Consultation(SHA-12-001) is not supported for service type OUTPATIENT."}',
            "message": "could not create the authorization",
            "details": ['could not create the authorization: {"error":"Kindly note ..."}'],
            "trace_id": "t",
        }
    )
    assert env.detail().startswith("Kindly note the intervention Consultation")
    assert env.status_text == ""


def test_trailing_json_in_message_is_unwrapped() -> None:
    env = ErrorEnvelope.model_validate(
        {
            "error": "Bad Request",
            "message": 'failed to start visit for patient: {"Edi Error":{"detail":"OTP was not found for contact: +254700000000"}}',
        }
    )
    assert env.detail() == "failed to start visit for patient: OTP was not found for contact: +254700000000"


def test_details_used_when_error_and_message_are_generic() -> None:
    env = ErrorEnvelope.model_validate(
        {"error": "Bad Request", "message": "", "details": ["field x is required"]}
    )
    assert env.detail() == "field x is required"


def test_malformed_json_falls_back_gracefully() -> None:
    env = ErrorEnvelope.model_validate({"error": "{not json", "message": "m"})
    assert env.detail() == "{not json"
