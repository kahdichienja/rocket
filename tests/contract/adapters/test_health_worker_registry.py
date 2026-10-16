"""The Health Worker Registry wire contract, pinned against what UAT actually sends.

The registry resolves a regulator's registration number to the id the Shared Health Record wants as
`practitioner_id`. Nothing else can produce that id, so a lookup that silently yields nothing stops a
clinician reading a patient's history — and says, wrongly, that the registry has never heard of them.

Which is what happened. The shape here was guessed, DHA sends something else entirely, and because
every field is optional the envelope *validated* and mapped to a practitioner with no registry id.
Captured from UAT on 2026-10-16.
"""

from __future__ import annotations

from sha_claim.adapters.wire.mappers import to_health_worker
from sha_claim.adapters.wire.schemas.registry import HealthWorkerWire

# Verbatim from `GET /professionals?identification_number=T-80000781&identification_type=registration_number&regulator=KMPDC`.
MEMBERSHIP = {
    "id": "PUID-0035218-8",
    "full_name": "Dr Eight  One",
    "gender": "Female",
    "first_name": "Eight",
    "last_name": "One",
    "registration_id": "PUID-035219",
    "external_reference_id": "T-80000781",
    "licensing_body": "KMPDC",
    "specialty": "MEDICINE",
    "is_active": 1,
}


class TestWhatTheRegistryActuallySends:
    def test_reads_the_registry_id_from_membership_id(self) -> None:
        """`practitioner_id` on every SHR read. Empty here means no record can be read at all."""
        worker = to_health_worker(HealthWorkerWire.model_validate(MEMBERSHIP))
        assert worker.registry_id == "PUID-0035218-8"

    def test_reads_the_name_the_regulator_holds(self) -> None:
        """Shown to the reader: a name that is not theirs means the wrong number is on file."""
        worker = to_health_worker(HealthWorkerWire.model_validate(MEMBERSHIP))
        assert worker.name == "Dr Eight  One"

    def test_reads_the_registration_number_from_external_reference_id(self) -> None:
        worker = to_health_worker(HealthWorkerWire.model_validate(MEMBERSHIP))
        assert worker.registration_number == "T-80000781"
        assert worker.regulator == "KMPDC"

    def test_translates_the_integer_active_flag_into_a_status(self) -> None:
        """`is_active` is 1 or 0 where the domain matches a status word. `"1"` would read as struck off,
        and `is_active` treats anything unrecognised as not active — deliberately, so the failure is to
        say a licensed practitioner is not, never the reverse."""
        assert to_health_worker(HealthWorkerWire.model_validate(MEMBERSHIP)).is_active is True
        assert (
            to_health_worker(HealthWorkerWire.model_validate({**MEMBERSHIP, "is_active": 0})).is_active
            is False
        )

    def test_still_reads_the_flat_shape_the_documentation_implies(self) -> None:
        """Kept in case DHA ever flattens it; the two spellings share no keys."""
        worker = to_health_worker(
            HealthWorkerWire.model_validate(
                {
                    "registry_id": "PUID-1",
                    "registration_number": "A123",
                    "name": "Dr Flat",
                    "regulator": "NCK",
                    "status": "ACTIVE",
                }
            )
        )
        assert (worker.registry_id, worker.registration_number, worker.name) == ("PUID-1", "A123", "Dr Flat")
        assert worker.is_active is True

    def test_the_spelled_out_regulator_is_passed_through(self) -> None:
        """PPB answers `Pharmacy and Poisons Board` where KMPDC answers `KMPDC`. Taken verbatim —
        normalising it would invent a code DHA did not send."""
        worker = to_health_worker(
            HealthWorkerWire.model_validate({**MEMBERSHIP, "licensing_body": "Pharmacy and Poisons Board"})
        )
        assert worker.regulator == "Pharmacy and Poisons Board"
