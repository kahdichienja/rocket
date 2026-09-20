from sha_claim.adapters.wire import mappers, requests
from sha_claim.adapters.wire.schemas.benefits import BedOccupancyWire, UtilizationWire
from sha_claim.adapters.wire.schemas.files import DownloadLinkWire, StoredFileWire
from sha_claim.adapters.wire.transport import TimeoutKind
from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.identifiers import FacilityCode, FileId, PatientId
from sha_claim.domain.money import Money
from tests.conftest import load_examples


def test_requests() -> None:
    u = requests.utilization(PatientId("CR1"), InterventionCode("SHA-12-001"))
    assert u.idempotent and u.params == {"patient_id": "CR1", "intervention_code": "SHA-12-001"}
    p = requests.pomsf_balances(PatientId("CR1"), "2026", "P-1")
    assert p.params == {"patient_id": "CR1", "policy_year": "2026", "principal_member_number": "P-1"}
    assert "principal_member_number" not in requests.pomsf_balances(PatientId("CR1"), "2026", None).params
    b = requests.bed_occupancy(FacilityCode("FID-47-105963-0"))
    assert b.path == "/facilities/FID-47-105963-0/beds/occupancy" and b.authenticated
    up = requests.upload("x.pdf", b"%PDF", "application/pdf")
    assert (
        up.multipart
        and up.files == {"file": ("x.pdf", b"%PDF", "application/pdf")}
        and up.timeout is TimeoutKind.UPLOAD
    )
    assert requests.download_link(FileId("f1")).path == "/uploads/f1"


def test_utilization_maps_from_portal_example_and_computes_remaining() -> None:
    ex = load_examples()["eclaims"]["GET /api/v1/patients/benefits/utilization"]["responses"]["200"]
    u = mappers.to_utilization(UtilizationWire.model_validate(ex))
    assert u.patient_id == "crId" and u.limit_scope == "limitScope"
    assert u.individual_max == Money.kes(0) and u.individual_remaining == Money.kes(0)
    assert u.eligible is True and len(u.funds) == 1 and u.funds[0].fund_type == "fundType"
    real = mappers.to_utilization(
        UtilizationWire.model_validate({"individualMaxLimit": 10000, "individualUtilisedLimit": 2500.5})
    )
    assert real.individual_remaining == Money.kes("7499.50")
    assert mappers.to_utilization(
        UtilizationWire.model_validate({"computationalDetail": {"limitAvailableAmount": 300}})
    ).individual_remaining == Money.kes(300)


def test_bed_occupancy_maps_and_rate() -> None:
    ex = load_examples()["eclaims"]["GET /api/v1/facilities/{facilityCode}/beds/occupancy"]["responses"][
        "200"
    ]
    empty = mappers.to_bed_occupancy(BedOccupancyWire.model_validate(ex))
    assert empty.facility_name == "name" and empty.occupancy_rate is None
    busy = mappers.to_bed_occupancy(
        BedOccupancyWire.model_validate(
            {
                "name": "H",
                "bed_occupancy_rate": {
                    "total_number_of_bed": 40,
                    "total_ip_visits": 30,
                    "number_of_icu_bed": 4,
                },
            }
        )
    )
    assert busy.occupancy_rate == 0.75 and busy.icu_beds == 4


def test_file_mappers_tolerate_sparse_payloads() -> None:
    assert mappers.to_stored_file(StoredFileWire.model_validate({})).file_id is None
    stored = mappers.to_stored_file(StoredFileWire.model_validate({"file_id": "f1", "path": "bucket/f1.pdf"}))
    assert stored.file_id == FileId("f1") and stored.path == "bucket/f1.pdf"
    link = mappers.to_download_link(
        DownloadLinkWire.model_validate({"message": "ok", "data": {"url": "https://x/y"}})
    )
    assert link.url == "https://x/y"
    assert (
        mappers.to_download_link(DownloadLinkWire.model_validate({"data": "https://direct"})).url
        == "https://direct"
    )
    assert mappers.to_download_link(DownloadLinkWire.model_validate({"data": {}})).url == ""
