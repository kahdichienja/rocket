"""The Facility Registry wire contract, pinned against a **live UAT response**.

`GET /facilities/search?name=Nairobi West Hospital` was captured from UAT and the rows below are copied from
it verbatim. That matters: this SDK's first attempt at these models was written from the documentation, and
it failed against the real payload in three separate ways. Each has a test here, because each of them made a
working endpoint look broken:

* the name arrives as `officialName`, so a wrong alias yields nameless facilities — a silent failure;
* the operational statuses are **objects**, so typing them as strings raises on every row — a loud failure
  that reads as "the registry is down";
* `latitude`/`longitude` are strings and usually `""`, which is another raise on the rows that have an
  address.

The other property worth guarding: `shaContractStatus` is empty on every live row, and empty must not be
read as "not contracted".
"""

from __future__ import annotations

from typing import Any

import pytest

from sha_claim.adapters.wire import requests
from sha_claim.adapters.wire.http_gateways import HttpFacilityRegistryGateway
from sha_claim.adapters.wire.mappers import to_facility_record
from sha_claim.adapters.wire.schemas.facility import FacilityRecordWire
from sha_claim.domain.facility import FacilityIdentifierType
from sha_claim.errors import RequestValidationError

# ── Rows copied verbatim from a live UAT search for "Nairobi West Hospital" ──

NAIROBI_WEST: dict[str, Any] = {
    "registrationNumber": "000516",
    "frCode": "FID-47-108846-4",
    "facilityLicenseStatus": "LICENSED",
    "licenseNumber": "6912943",
    "regulatoryBody": "kmpdc",
    "shaContractStatus": "",
    "insuranceContracts": None,
    "officialName": "THE NAIROBI WEST HOSPITAL LIMITED",
    "kephLevel": "LEVEL 6B",
    "fidCode": "108846",
    "facilityOwnership": "Private",
    "facilityType": "SPECIALIZED TERTIARY REFERRAL HOSPITAL ",
    "pcnCode": "",
    "isHub": False,
    "facilityPhoneNumber": "0722200944",
    "facilityEmail": "info@nairobiwesthospital.com",
    "facilityAdministratorName": "SIVAPRASAD  KOVILAKATH",
    "facilityAdministratorEmail": "info@nairobiwesthospital.com",
    "address": {
        "country": "Kenya",
        "countyCode": "47",
        "county": "NAIROBI",
        "subCounty": "LANGATA",
        "postalAddress": "P.O BOX 43375-00100 NAIROBI",
        "physicalLocation": "NAIROBI WEST-GANDHI ROAD NAIROBI",
        "town": "NAIROBI",
        "latitude": "-1.30648",
        "longitude": "36.825409",
    },
    "bedOccupancy": {
        "totalBeds": 458,
        "normalBeds": 375,
        "icuBeds": 35,
        "hduBeds": 23,
        "dialysisBeds": 25,
        "numberOfCots": 0,
    },
    "shaContractedServices": [],
    "regulatoryOperationalStatus": {
        "operationalStatus": "ACTIVE",
        "operationalStatusReason": "",
        "suspensionReason": "",
        "reinstatementRecommendations": "",
        "earliestReinstatementDate": "",
    },
    "SHAOperationStatus": {
        "operationalStatus": "ACTIVE",
        "operationalStatusReason": "",
        "suspensionReason": "",
        "reinstatementRecommendations": "",
        "earliestReinstatementDate": "",
    },
}

# A pharmacy-board row from the same response: a `PID` code, no KEPH level, no coordinates.
PPB_ROW: dict[str, Any] = {
    "registrationNumber": "23130",
    "frCode": "PID-47-915513-8",
    "facilityLicenseStatus": "LICENSED",
    "regulatoryBody": "ppb",
    "shaContractStatus": "",
    "officialName": "The Nairobi West Hospital Ltd.",
    "kephLevel": "",
    "fidCode": "915513",
    "facilityOwnership": "",
    "facilityType": "",
    "isHub": False,
    "facilityPhoneNumber": "",
    "address": {
        "country": "",
        "countyCode": "47",
        "county": "NAIROBI",
        "ward": "NAIROBI WEST",
        "constituency": "LANGATA",
        "postalAddress": "P.O BOX 00100-42275",
        "town": "",
    },
    "bedOccupancy": {
        "totalBeds": 0,
        "normalBeds": 0,
        "icuBeds": 0,
        "hduBeds": 0,
        "dialysisBeds": 0,
        "numberOfCots": 0,
    },
    "shaContractedServices": [],
    "regulatoryOperationalStatus": {"operationalStatus": "ACTIVE"},
    "SHAOperationStatus": {"operationalStatus": "ACTIVE"},
}


class TestTheSearchRequest:
    def test_identifier_type_is_hyphenated(self) -> None:
        """`identifier-type`, not `identifier_type`. DHA ignores the snake_case spelling silently."""
        wire = requests.search_facilities("FID-47-108521-3", FacilityIdentifierType.FR_CODE)
        assert wire.method == "GET"
        assert wire.path == "/facilities/search"
        assert wire.params == {"identifier": "FID-47-108521-3", "identifier-type": "fr-code"}

    def test_a_name_search_sends_only_the_name(self) -> None:
        """Exactly what the captured curl sent, and it works: `?name=Nairobi West Hospital`."""
        wire = requests.search_facilities(name="Nairobi West Hospital")
        assert wire.params == {"name": "Nairobi West Hospital"}

    def test_every_identifier_type_uses_dhas_own_spelling(self) -> None:
        assert FacilityIdentifierType.FR_CODE.value == "fr-code"
        assert FacilityIdentifierType.MFL.value == "mfl"
        assert FacilityIdentifierType.LICENSE_NUMBER.value == "license-number"
        assert FacilityIdentifierType.REGISTRATION_NUMBER.value == "registration-number"
        assert FacilityIdentifierType.FID.value == "fid"

    def test_a_search_with_neither_is_refused(self) -> None:
        """DHA's own answer is a 400 — *"at least one facility search parameter is expected"* — so the
        round trip is skipped and the caller is told locally."""
        with pytest.raises(RequestValidationError):
            requests.search_facilities()


class TestReadingALiveRecord:
    def test_the_name_comes_from_official_name(self) -> None:
        """The alias that was missing. Without it every row parses fine and comes back **nameless**, which
        is worse than an error: a picker full of blank entries with no indication anything went wrong."""
        record = to_facility_record(FacilityRecordWire.model_validate(NAIROBI_WEST))
        assert record.name == "THE NAIROBI WEST HOSPITAL LIMITED"

    def test_the_operational_statuses_are_objects_not_strings(self) -> None:
        """Typed as `str`, these raise on every row — so a working endpoint reads as an outage."""
        record = to_facility_record(FacilityRecordWire.model_validate(NAIROBI_WEST))
        assert record.sha_operation_status == "ACTIVE"
        assert record.operation_status == "ACTIVE"
        assert record.is_operational is True

    def test_string_coordinates_are_parsed(self) -> None:
        record = to_facility_record(FacilityRecordWire.model_validate(NAIROBI_WEST))
        assert record.address.latitude == pytest.approx(-1.30648)
        assert record.address.longitude == pytest.approx(36.825409)

    def test_an_empty_coordinate_is_absent_rather_than_zero(self) -> None:
        """A facility at the equator and a facility with no coordinates are not the same place."""
        addr = dict(NAIROBI_WEST["address"])
        addr["latitude"] = ""
        addr["longitude"] = ""
        payload = dict(NAIROBI_WEST)
        payload["address"] = addr
        record = to_facility_record(FacilityRecordWire.model_validate(payload))
        assert record.address.latitude is None
        assert record.address.longitude is None

    def test_the_rest_of_the_fields_a_referral_turns_on(self) -> None:
        record = to_facility_record(FacilityRecordWire.model_validate(NAIROBI_WEST))
        assert record.fr_code == "FID-47-108846-4"
        assert record.keph_level == "LEVEL 6B"
        assert record.owner == "Private"
        assert record.phone == "0722200944"
        assert record.email == "info@nairobiwesthospital.com"
        assert record.address.county == "NAIROBI"
        assert record.address.summary == "NAIROBI · LANGATA"

    def test_cots_use_dhas_own_spelling(self) -> None:
        """`numberOfCots`; `cots` never matches, and the bed count silently loses them."""
        beds = dict(NAIROBI_WEST["bedOccupancy"])
        beds["numberOfCots"] = 12
        payload = dict(NAIROBI_WEST)
        payload["bedOccupancy"] = beds
        record = to_facility_record(FacilityRecordWire.model_validate(payload))
        assert record.beds.cots == 12
        assert record.beds.icu_beds == 35


class TestContractStatusIsUnknownNotNegative:
    """Every row of a live name search has `shaContractStatus: ""`."""

    def test_an_empty_contract_status_is_not_a_negative(self) -> None:
        record = to_facility_record(FacilityRecordWire.model_validate(NAIROBI_WEST))
        assert record.sha_contract_known is False
        assert record.is_sha_contracted is False

    def test_a_facility_with_no_published_contract_is_still_referable(self) -> None:
        """Requiring a positive contract would mark **every** facility in a live search as un-referable,
        including Kenyatta National Hospital. That is false, specific, and worse than saying nothing."""
        record = to_facility_record(FacilityRecordWire.model_validate(NAIROBI_WEST))
        assert record.is_referable is True

    def test_a_facility_dha_says_is_not_contracted_is_reported(self) -> None:
        record = to_facility_record(
            FacilityRecordWire.model_validate({**NAIROBI_WEST, "shaContractStatus": "Not Contracted"})
        )
        assert record.sha_contract_known is True
        assert record.is_sha_contracted is False
        assert record.is_referable is False

    def test_a_contracted_facility_reads_as_contracted(self) -> None:
        record = to_facility_record(
            FacilityRecordWire.model_validate({**NAIROBI_WEST, "shaContractStatus": "Contracted"})
        )
        assert record.is_sha_contracted is True
        assert record.is_referable is True


class TestSuspension:
    def test_a_suspended_facility_is_not_operational(self) -> None:
        record = to_facility_record(
            FacilityRecordWire.model_validate(
                {
                    **NAIROBI_WEST,
                    "SHAOperationStatus": {
                        "operationalStatus": "SUSPENDED",
                        "suspensionReason": "Pending inspection",
                    },
                }
            )
        )
        assert record.is_operational is False
        assert record.is_referable is False
        assert record.suspension_reason == "Pending inspection"

    def test_shas_view_of_suspension_wins_over_the_regulators(self) -> None:
        """A facility its regulator is content with can still be suspended by SHA, and that is the one that
        stops the referral being paid for."""
        record = to_facility_record(
            FacilityRecordWire.model_validate(
                {
                    **NAIROBI_WEST,
                    "regulatoryOperationalStatus": {
                        "operationalStatus": "ACTIVE",
                        "suspensionReason": "none",
                    },
                    "SHAOperationStatus": {"operationalStatus": "SUSPENDED", "suspensionReason": "SHA audit"},
                }
            )
        )
        assert record.suspension_reason == "SHA audit"

    def test_an_unrecognised_status_reads_as_operational(self) -> None:
        """Wrongly hiding a hospital that could have taken the patient is the worse failure."""
        record = to_facility_record(
            FacilityRecordWire.model_validate(
                {**NAIROBI_WEST, "SHAOperationStatus": {"operationalStatus": "Under Review"}}
            )
        )
        assert record.is_operational is True


class TestPartialRows:
    """The same response mixes KMPDC hospitals with pharmacy-board rows that carry almost nothing."""

    def test_a_sparse_ppb_row_reads_without_error(self) -> None:
        record = to_facility_record(FacilityRecordWire.model_validate(PPB_ROW))
        assert record.fr_code == "PID-47-915513-8"
        assert record.name == "The Nairobi West Hospital Ltd."
        assert record.keph_level == ""
        assert record.address.summary == "NAIROBI · LANGATA"
        assert record.beds.total == 0

    def test_a_missing_address_or_bed_block_does_not_crash_the_read(self) -> None:
        record = to_facility_record(
            FacilityRecordWire.model_validate({"frCode": "FID-1", "officialName": "X"})
        )
        assert record.address.summary == ""
        assert record.beds.total == 0
        assert record.is_operational is True

    def test_services_given_as_objects_are_reduced_to_their_names(self) -> None:
        record = to_facility_record(
            FacilityRecordWire.model_validate(
                {
                    **NAIROBI_WEST,
                    "shaContractedServices": [
                        {"name": "Renal Dialysis", "code": "SHA-05"},
                        {"code": "SHA-09"},
                        {"unreadable": True},
                        "Oncology",
                    ],
                }
            )
        )
        assert record.sha_contracted_services == ("Renal Dialysis", "SHA-09", "Oncology")

    def test_offers_is_unknown_not_false_when_no_services_were_listed(self) -> None:
        record = to_facility_record(FacilityRecordWire.model_validate(NAIROBI_WEST))
        assert record.sha_contracted_services == ()
        assert record.offers("Oncology") is False

    def test_the_fr_code_is_read_whichever_key_it_arrived_under(self) -> None:
        for key in ("frCode", "facilityCode", "code"):
            record = to_facility_record(
                FacilityRecordWire.model_validate({key: "FID-1", "officialName": "X"})
            )
            assert record.fr_code == "FID-1", key


class TestUnwrappingTheEnvelope:
    def test_a_bare_list_is_what_the_live_search_returns(self) -> None:
        """The captured response is a bare JSON array of facilities."""
        records = HttpFacilityRegistryGateway._records([NAIROBI_WEST, PPB_ROW])
        assert [r.fr_code for r in records] == ["FID-47-108846-4", "PID-47-915513-8"]

    def test_a_bare_object_is_one_facility_not_an_envelope(self) -> None:
        """Read as an envelope it would yield a facility with no FR code and no name."""
        records = HttpFacilityRegistryGateway._records(NAIROBI_WEST)
        assert len(records) == 1
        assert records[0].fr_code == "FID-47-108846-4"

    def test_a_results_wrapper_is_unwrapped(self) -> None:
        records = HttpFacilityRegistryGateway._records({"status": "success", "results": [NAIROBI_WEST]})
        assert [r.fr_code for r in records] == ["FID-47-108846-4"]

    def test_a_data_wrapper_is_unwrapped(self) -> None:
        records = HttpFacilityRegistryGateway._records({"status": "success", "data": [NAIROBI_WEST]})
        assert [r.fr_code for r in records] == ["FID-47-108846-4"]

    def test_a_data_object_holding_results_is_unwrapped(self) -> None:
        records = HttpFacilityRegistryGateway._records({"data": {"results": [NAIROBI_WEST]}})
        assert [r.fr_code for r in records] == ["FID-47-108846-4"]

    def test_nothing_readable_is_no_facilities_rather_than_a_crash(self) -> None:
        assert HttpFacilityRegistryGateway._records(None) == []
        assert HttpFacilityRegistryGateway._records("unexpected") == []
