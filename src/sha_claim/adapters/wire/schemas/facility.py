"""`GET /facilities/search` payloads, pinned against a live UAT response.

This endpoint answers with a **bare JSON array** of facilities and with camelCase keys, and three of its
shapes are not what a reasonable reading of the docs suggests. Each of them broke this SDK once:

* **The name is `officialName`.** Not `name`, not `facilityName`. Without that alias every facility parses
  cleanly and comes back *nameless*, which is worse than an error — a picker full of blank rows.
* **The operational statuses are objects, not strings.** `SHAOperationStatus` and
  `regulatoryOperationalStatus` each arrive as `{"operationalStatus": "ACTIVE", …}`. Typing them as `str`
  raises a `ValidationError` on every row, so the whole search fails and reads as "the registry is down".
* **`latitude` and `longitude` are strings, and usually empty.** `""` against a `float` is another
  `ValidationError` on the rows that happen to carry an address.

The lesson worth keeping: a wrong alias fails *silently* and a wrong type fails *loudly but misleadingly*.
Both look like an endpoint that does not work.
"""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, Field

from sha_claim.adapters.wire.schemas.common import WireModel


class FacilityAddressWire(WireModel):
    """Where the facility is.

    `latitude`/`longitude` are **strings** here and frequently `""`. They are kept as strings at the wire and
    parsed in the mapper, so an empty one is an absent coordinate rather than a failed parse of the record.
    """

    country: str = ""
    county: str = ""
    county_code: str = ""
    sub_county: str = ""
    constituency: str = ""
    ward: str = ""
    town: str = ""
    postal_address: str = ""
    physical_location: str = ""
    latitude: str = ""
    longitude: str = ""


class FacilityBedsWire(WireModel):
    """Bed capacity. `numberOfCots` is DHA's spelling — `cots` never matches."""

    total_beds: int = 0
    normal_beds: int = 0
    icu_beds: int = 0
    hdu_beds: int = 0
    maternity_beds: int = 0
    dialysis_beds: int = 0
    number_of_cots: int = Field(0, validation_alias=AliasChoices("numberOfCots", "number_of_cots", "cots"))
    isolation_beds: int = 0
    theatres: int = 0


class OperationalStatusWire(WireModel):
    """The shape both `regulatoryOperationalStatus` and `SHAOperationStatus` arrive in.

    A facility can be operational for its regulator and suspended by SHA, so the two are kept apart rather
    than collapsed — they answer different questions and a referral cares about both.
    """

    operational_status: str = ""
    operational_status_reason: str = ""
    suspension_reason: str = ""
    reinstatement_recommendations: str = ""
    earliest_reinstatement_date: str = ""


class FacilityRecordWire(WireModel):
    """A facility as the registry returns it.

    Every identifier spelling DHA has used for the FR code is accepted, because the field it arrives under
    differs by lookup: the live name search answers with `frCode`, and the portal examples have used
    `facilityCode` and `code`. Picking one and being wrong yields a record with no code at all — which a
    referral cannot address.
    """

    fr_code: str = Field(
        "", validation_alias=AliasChoices("frCode", "fr_code", "facilityCode", "facility_code", "code")
    )
    fid_code: str = ""
    registration_number: str = ""
    # `officialName` is what the live endpoint sends; the others are the portal's older spellings.
    name: str = Field(
        "",
        validation_alias=AliasChoices(
            "officialName", "official_name", "name", "facilityName", "facility_name"
        ),
    )
    uuid: str = ""
    facility_type: str = ""
    keph_level: str = Field("", validation_alias=AliasChoices("kephLevel", "keph_level", "level"))
    owner: str = Field("", validation_alias=AliasChoices("facilityOwnership", "facility_ownership", "owner"))
    regulatory_body: str = ""
    license_number: str = ""
    facility_license_status: str = ""
    pcn_code: str = ""

    regulatory_operational_status: OperationalStatusWire | None = None
    sha_operation_status: OperationalStatusWire | None = Field(
        None,
        validation_alias=AliasChoices("SHAOperationStatus", "shaOperationStatus", "sha_operation_status"),
    )
    sha_contract_status: str = Field(
        "", validation_alias=AliasChoices("shaContractStatus", "SHAContractStatus", "sha_contract_status")
    )
    sha_contracted_services: list[Any] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "shaContractedServices", "SHAContractedServices", "sha_contracted_services"
        ),
    )

    is_hub: bool = False
    facility_phone_number: str = Field(
        "", validation_alias=AliasChoices("facilityPhoneNumber", "facility_phone_number", "phone")
    )
    facility_email: str = ""
    facility_administrator_email: str = Field(
        "",
        validation_alias=AliasChoices("facilityAdministratorEmail", "facility_administrator_email", "email"),
    )
    facility_administrator_name: str = Field(
        "", validation_alias=AliasChoices("facilityAdministratorName", "facility_administrator_name")
    )
    address: FacilityAddressWire | None = None
    bed_occupancy: FacilityBedsWire | None = Field(
        None, validation_alias=AliasChoices("bedOccupancy", "bed_occupancy", "beds")
    )


class FacilitySearchWire(WireModel):
    """The search envelope.

    The live endpoint answers with a **bare array**; the portal examples have used a bare object and a
    `data`/`results` wrapper. All are unwrapped in the gateway, since which one arrives is a property of the
    request rather than of the payload.
    """

    data: Any = None
    results: list[FacilityRecordWire] = Field(default_factory=list)
    message: str = ""
    status: str = ""
