"""The Facility Registry: resolving a facility to the code the rest of DHA insists on.

Everywhere else in this SDK a facility is *implied* — the credential carries it, or `activate_facility`
names it. This module is for the other case: naming a facility that is **not** us. A referral has to say
which hospital the patient is being sent to, and saying it as a string (`"Kenyatta National Hospital"`)
gets it nowhere, because the SHR addresses referrals by FR code:

    performer: [{"reference": "Organization/FID-17-116073-1"}]

So a referral desk needs to search by name and get back a code. That is what `GET /facilities/search`
does, and it is the only DHA search in this SDK that takes a free-text name.

**A code is not the same as a facility that can receive the patient.** The registry answers for hospitals
that are suspended, that never contracted with SHA, and that do not offer the service being referred. The
record carries all of that, and `FacilityRecord.is_referable` is the one-line reading of it — sending a
patient across a county to a facility SHA will not pay for is a worse outcome than not finding it at all.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class FacilityIdentifierType(StrEnum):
    """`identifier-type` on the facility search.

    Five identifiers, all in live use for the same hospital: the FR code the HIE uses, the Master Facility
    List number the Ministry of Health uses, the licence and registration numbers the regulator issues, and
    the internal `fid`. Values are DHA's own hyphenated spellings, which is why they are not just the member
    names lower-cased.
    """

    FR_CODE = "fr-code"
    MFL = "mfl"
    LICENSE_NUMBER = "license-number"
    REGISTRATION_NUMBER = "registration-number"
    FID = "fid"


@dataclass(frozen=True, slots=True)
class FacilityAddress:
    """Where the facility is. Enough to tell two similarly-named hospitals apart in a picker."""

    county: str = ""
    sub_county: str = ""
    constituency: str = ""
    ward: str = ""
    town: str = ""
    latitude: float | None = None
    longitude: float | None = None

    @property
    def summary(self) -> str:
        """`Kiambu · Juja` — the line a picker shows under the name. Empty when the registry said nothing."""
        return " · ".join(p for p in (self.county, self.constituency or self.sub_county) if p)


@dataclass(frozen=True, slots=True)
class FacilityBeds:
    """Bed capacity as the registry holds it.

    Distinct from `GET /facilities/{code}/beds/occupancy`, which is *live* occupancy for our own facility.
    These are the establishment figures, and they are the only capacity signal available for somebody
    else's hospital — useful for choosing where to send an admission, but not a statement that a bed is
    free right now.
    """

    normal_beds: int = 0
    icu_beds: int = 0
    hdu_beds: int = 0
    maternity_beds: int = 0
    dialysis_beds: int = 0
    cots: int = 0
    isolation_beds: int = 0
    theatres: int = 0

    @property
    def total(self) -> int:
        return (
            self.normal_beds
            + self.icu_beds
            + self.hdu_beds
            + self.maternity_beds
            + self.dialysis_beds
            + self.cots
            + self.isolation_beds
        )


@dataclass(frozen=True, slots=True)
class FacilityRecord:
    """A facility as `GET /facilities/search` returns it.

    Only the fields a referral actually turns on are named; the rest of DHA's (large, and changing) payload
    is kept whole in `extra` rather than dropped, so a caller that needs something unmodelled can reach it
    without this class having to grow first.
    """

    fr_code: str
    name: str = ""
    uuid: str = ""
    facility_type: str = ""
    keph_level: str = ""
    """KEPH level 2 to 6. A referral is normally *upward*, so this is what tells a clinician whether the
    facility they picked can actually take the case."""
    owner: str = ""
    operation_status: str = ""
    sha_operation_status: str = ""
    sha_contract_status: str = ""
    sha_contracted_services: tuple[str, ...] = ()
    suspension_reason: str = ""
    is_hub: bool = False
    phone: str = ""
    email: str = ""
    administrator_name: str = ""
    address: FacilityAddress = field(default_factory=FacilityAddress)
    beds: FacilityBeds = field(default_factory=FacilityBeds)
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_operational(self) -> bool:
        """Open for business, as far as SHA is concerned.

        Matched leniently and **negatively**: anything that says suspended, closed or inactive is not
        operational, and a status nobody here recognises is treated as operational rather than hidden. The
        asymmetry is deliberate — wrongly hiding a hospital that could have taken the patient is the worse
        failure, and the status is shown beside the name either way.
        """
        status = f"{self.sha_operation_status} {self.operation_status}".strip().upper()
        if not status:
            return True
        return not any(w in status for w in ("SUSPEND", "CLOSE", "INACTIVE", "DEREGISTER", "REVOK"))

    @property
    def sha_contract_known(self) -> bool:
        """Whether DHA said anything at all about SHA contracting.

        It frequently does not: every row of a live name search comes back with `shaContractStatus: ""`.
        That is silence, not a negative, and the distinction matters — see `is_referable`.
        """
        return bool(self.sha_contract_status.strip())

    @property
    def is_sha_contracted(self) -> bool:
        """Contracted, as far as DHA has said. `False` also covers *not said*, so check `sha_contract_known`."""
        status = self.sha_contract_status.strip().upper()
        if not status:
            return False
        return any(w in status for w in ("CONTRACT", "ACTIVE", "APPROVED")) and "NOT" not in status

    @property
    def is_referable(self) -> bool:
        """Whether a patient can sensibly be sent here.

        Operational, and **not explicitly** un-contracted. The asymmetry is deliberate: DHA leaves
        `shaContractStatus` empty on most records, so requiring a positive contract would mark every
        facility in a live search as un-referable — including Kenyatta National Hospital. Telling a
        clinician that is worse than telling them nothing, because it is false and it is specific.

        A facility DHA *has* said is not contracted is a different matter, and that one is reported. Either
        way a referral screen should let a clinician choose anyway — some referrals are clinically necessary
        regardless of who pays — but it must say which it is.
        """
        return self.is_operational and not (self.sha_contract_known and not self.is_sha_contracted)

    def offers(self, service: str) -> bool:
        """Whether a named service appears in the facility's SHA contract.

        Substring-matched case-insensitively, because the contract list holds SHA's service names and a
        clinician is searching with a specialty's name. `False` when the registry listed no services at
        all — which means *unknown*, not *not offered*, so a caller should not use this to hide a facility.
        """
        needle = service.strip().lower()
        if not needle:
            return False
        return any(needle in s.lower() for s in self.sha_contracted_services)
