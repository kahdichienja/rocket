"""The Shared Health Record wire contract, pinned against the published Postman collection.

Two things here are easy to get wrong and expensive when wrong:

* **The consent token is a credential.** It opens one patient's history across every facility that has
  treated them. It must not appear in a repr, a log line or an error.
* **`otp_record` is reissued by a resend.** Verifying with the value from the original request after a
  resend fails, and the failure looks like a wrong OTP — which sends a desk chasing the patient instead of
  the payload.
"""

from __future__ import annotations

import pytest

from sha_claim.adapters.wire import requests
from sha_claim.adapters.wire.mappers import (
    to_shr_bundle_receipt,
    to_shr_consent,
    to_shr_consent_state,
    to_shr_verification,
)
from sha_claim.adapters.wire.schemas.shr import (
    ShrBundleReceiptWire,
    ShrConsentStatusWire,
    ShrConsentWire,
    ShrVerificationWire,
)
from sha_claim.domain.shr import ShrConsentRequest, ShrConsentTokenValue, ShrVisitType

TOKEN = ShrConsentTokenValue("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")


class TestTheConsentRequest:
    def test_sends_exactly_what_postman_sends(self) -> None:
        wire = requests.request_shr_consent(
            ShrConsentRequest(
                "CR-2026-000256", "FID-47-115307-8", "Registration Clerk", ShrVisitType.INPATIENT
            )
        )
        assert wire.method == "POST"
        assert wire.path == "/shr/consents"
        assert wire.json == {
            "cr_id": "CR-2026-000256",
            "facility_id": "FID-47-115307-8",
            "requested_by": "Registration Clerk",
            "visit_type": "IP",
        }

    def test_visit_type_is_dhas_two_letter_spelling_not_the_claim_vocabulary(self) -> None:
        """A claim says OUTPATIENT; the SHR says OP. Sending the claim's word is rejected."""
        assert ShrVisitType.OUTPATIENT.value == "OP"
        assert ShrVisitType.INPATIENT.value == "IP"


class TestVerifying:
    def test_carries_the_otp_and_the_record_it_was_issued_against(self) -> None:
        wire = requests.verify_shr_consent("VCR-20260624-13698E26", "123456", "d67p9lhxxx")
        assert wire.path == "/shr/consents/VCR-20260624-13698E26/verify"
        assert wire.json == {"otp": "123456", "otp_record": "d67p9lhxxx"}

    def test_a_resend_answers_with_a_fresh_otp_record(self) -> None:
        """DHA's own note: verify with the value the *resend* returned, not the original."""
        first = to_shr_consent(ShrConsentWire.model_validate({"consentId": "VCR-1", "otpRecord": "first"}))
        resent = to_shr_consent(ShrConsentWire.model_validate({"consentId": "VCR-1", "otpRecord": "second"}))
        assert first.otp_record != resent.otp_record


class TestReadingRecords:
    def test_the_token_travels_in_the_header_not_the_query(self) -> None:
        """A token in a URL lands in access logs and browser history. It belongs in a header."""
        wire = requests.fetch_shr_records(TOKEN, "CR-1", "HWR-9", ["Observation", "Condition"])
        assert wire.headers["X-Consent-Token"] == TOKEN.value
        assert "consent" not in " ".join(wire.params).lower()

    def test_resources_are_sent_comma_separated(self) -> None:
        wire = requests.fetch_shr_records(TOKEN, "CR-1", "HWR-9", ["Observation", "Condition"])
        assert wire.params["resources"] == "Observation,Condition"

    def test_omits_the_filters_it_was_not_given(self) -> None:
        """An empty `_id` or `page_token` is a filter matching nothing, not an absent one."""
        wire = requests.fetch_shr_records(TOKEN, "CR-1", "HWR-9")
        assert "_id" not in wire.params
        assert "page_token" not in wire.params
        assert "resources" not in wire.params

    def test_forwards_further_fhir_search_parameters_untouched(self) -> None:
        wire = requests.fetch_shr_records(TOKEN, "CR-1", "HWR-9", search={"date": "ge2026-01-01"})
        assert wire.params["date"] == "ge2026-01-01"

    def test_is_a_read_so_it_may_be_retried(self) -> None:
        assert requests.fetch_shr_records(TOKEN, "CR-1", "HWR-9").idempotent


class TestWritingABundle:
    def test_carries_the_token_and_the_bundle(self) -> None:
        bundle = {"resourceType": "Bundle", "type": "collection", "entry": []}
        wire = requests.submit_shr_bundle(TOKEN, bundle)
        assert wire.path == "/shr/bundles"
        assert wire.headers["X-Consent-Token"] == TOKEN.value
        assert wire.json == bundle

    def test_the_callback_header_is_omitted_when_there_is_none(self) -> None:
        wire = requests.submit_shr_bundle(TOKEN, {"resourceType": "Bundle"})
        assert "X-HIE-Callback" not in wire.headers

    def test_a_write_is_never_retried_blindly(self) -> None:
        """Retrying could file the same encounter twice into a national record."""
        assert not requests.submit_shr_bundle(TOKEN, {"resourceType": "Bundle"}).idempotent

    def test_success_means_the_envelope_was_accepted_not_that_it_was_stored(self) -> None:
        receipt = to_shr_bundle_receipt(
            ShrBundleReceiptWire.model_validate({"status": "success", "mediatorId": "b3f0a3f6"})
        )
        assert receipt.accepted
        assert receipt.mediator_id == "b3f0a3f6"


class TestResourceLabels:
    def test_refuses_a_lookup_with_no_filter(self) -> None:
        wire = requests.shr_resource_labels("Observation")
        assert wire.params == {"resource_name": "Observation"}


class TestTheTokenIsACredential:
    def test_repr_redacts_it(self) -> None:
        assert TOKEN.value not in repr(TOKEN)
        assert TOKEN.value not in str(TOKEN)

    def test_a_short_token_is_fully_masked_rather_than_half_shown(self) -> None:
        assert "•" in repr(ShrConsentTokenValue("abc"))


class TestConsentStatus:
    @pytest.mark.parametrize("status", ["Approved", "APPROVED", "approved"])
    def test_approved_however_it_is_spelled(self, status: str) -> None:
        assert to_shr_consent_state(
            ShrConsentStatusWire.model_validate({"consentStatus": status})
        ).is_approved

    @pytest.mark.parametrize(
        "status", ["Pending", "Pending Approval", "Rejected", "Expired", "", "Something New"]
    )
    def test_everything_else_is_not_approved(self, status: str) -> None:
        """Reading a pending consent as granted means reading a patient's records without their say-so."""
        assert not to_shr_consent_state(
            ShrConsentStatusWire.model_validate({"consentStatus": status})
        ).is_approved

    def test_verification_wraps_the_token_in_the_credential_type(self) -> None:
        v = to_shr_verification(
            ShrVerificationWire.model_validate({"consentToken": "eyJhbGciOi", "visitId": "f5c2fd92"})
        )
        assert isinstance(v.consent_token, ShrConsentTokenValue)
        assert v.visit_id == "f5c2fd92"


class TestTheResponseIsActuallyRead:
    """`WireResponse.json` is a *method*.

    Written because the first cut of this gateway did `response.json if isinstance(response.json, Mapping)`,
    which compares a bound method against `Mapping` — always false, so every record fetch returned `{}`.
    The panel would have shown "no records" for every patient and nothing would have looked broken.
    """

    async def test_records_come_back_rather_than_an_empty_mapping(self) -> None:
        from sha_claim.adapters.wire.http_gateways import HttpShrGateway
        from sha_claim.adapters.wire.transport import WireResponse

        bundle = {"resourceType": "Bundle", "type": "searchset", "entry": [{"resource": {"id": "obs-1"}}]}

        class _Transport:
            async def send(self, request: object) -> WireResponse:
                import json as _json

                return WireResponse(status=200, headers={}, body=_json.dumps(bundle).encode())

        got = await HttpShrGateway(_Transport()).patient_records(TOKEN, "CR-1", "HWR-9", ["Observation"])
        assert got == bundle, "the FHIR bundle must survive the gateway, not be flattened to {}"

    async def test_a_body_that_is_not_an_object_becomes_an_empty_mapping(self) -> None:
        from sha_claim.adapters.wire.http_gateways import HttpShrGateway
        from sha_claim.adapters.wire.transport import WireResponse

        class _Transport:
            async def send(self, request: object) -> WireResponse:
                return WireResponse(status=200, headers={}, body=b"[]")

        assert await HttpShrGateway(_Transport()).patient_records(TOKEN, "CR-1", "HWR-9") == {}


class TestTheHealthWorkerRegistry:
    """Established on UAT, 2026-09-27, because none of it is documented."""

    def test_the_regulator_is_required(self) -> None:
        """Omitting it is refused outright: `invalid practitioner regulator: valid choices are
        [kmpdc coc ppb nck]`. Better to say so here than to spend a round trip finding out."""
        import pytest

        with pytest.raises(ValueError, match="regulator"):
            requests.find_health_worker("A12345")

    def test_the_regulator_is_sent_upper_case(self) -> None:
        """DHA's rejection lists `[kmpdc coc ppb nck]` in lower case and then **refuses** lower case.

        One spelling at a time on UAT, 2026-09-27: `kmpdc`, `Kmpdc` and `ppb` were rejected as invalid;
        `KMPDC` and `PPB` reached the registry. The message describes a set it does not implement, so
        following it literally is what broke this.
        """
        assert requests.find_health_worker("A12345", regulator="kmpdc").params["regulator"] == "KMPDC"
        assert requests.find_health_worker("A12345", regulator="KMPDC").params["regulator"] == "KMPDC"

    def test_it_looks_up_by_registration_number_by_default(self) -> None:
        wire = requests.find_health_worker("A12345", regulator="KMPDC")
        assert wire.params["identification_number"] == "A12345"
        assert wire.params["identification_type"] == "registration_number"


class TestErrorsAreNotMistakenForData:
    """`parse_as` enforces the status; these two gateways bypassed it and had to be corrected.

    The failure was quiet and bad: a 400 body was handed to `model_validate`, which accepted it because the
    wire models allow extra fields, and out came a `HealthWorker` with every field empty. A desk validating
    a registration number would have been shown a blank name and read it as "found".
    """

    async def test_a_registry_error_is_not_returned_as_an_empty_worker(self) -> None:
        from sha_claim.adapters.wire.http_gateways import HttpHealthWorkerGateway
        from sha_claim.adapters.wire.transport import WireResponse
        from sha_claim.domain.enums import IdentificationType

        class _Transport:
            async def send(self, request: object) -> WireResponse:
                return WireResponse(
                    status=400,
                    headers={},
                    body=b'{"error":"Bad Request","message":"failed to fetch practitioner: something else"}',
                )

        import pytest

        from sha_claim.errors import SHAClaimError

        with pytest.raises(SHAClaimError):
            await HttpHealthWorkerGateway(_Transport()).find(
                "A12345", IdentificationType.REGISTRATION_NUMBER, "KMPDC"
            )

    async def test_no_membership_is_a_not_found_rather_than_a_failure(self) -> None:
        """The registry holding nobody with that number is an answer; DHA just spells it as a 400."""
        from sha_claim.adapters.wire.http_gateways import HttpHealthWorkerGateway
        from sha_claim.adapters.wire.transport import WireResponse
        from sha_claim.domain.enums import IdentificationType

        class _Transport:
            async def send(self, request: object) -> WireResponse:
                return WireResponse(
                    status=400,
                    headers={},
                    body=b'{"message":"failed to fetch practitioner: no practitioner membership returned from health worker registry"}',
                )

        got = await HttpHealthWorkerGateway(_Transport()).find(
            "A12345", IdentificationType.REGISTRATION_NUMBER, "KMPDC"
        )
        assert got is None

    async def test_an_shr_read_failure_raises_instead_of_returning_the_error_body(self) -> None:
        from sha_claim.adapters.wire.http_gateways import HttpShrGateway
        from sha_claim.adapters.wire.transport import WireResponse

        class _Transport:
            async def send(self, request: object) -> WireResponse:
                return WireResponse(status=403, headers={}, body=b'{"error":"Forbidden"}')

        import pytest

        from sha_claim.errors import SHAClaimError

        with pytest.raises(SHAClaimError):
            await HttpShrGateway(_Transport()).patient_records(TOKEN, "CR-1", "HWR-9")
