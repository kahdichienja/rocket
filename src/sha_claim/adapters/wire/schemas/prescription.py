from __future__ import annotations

from pydantic import Field

from sha_claim.adapters.wire.schemas.common import WireModel

Number = float | int | str | None


class DosageWire(WireModel):
    medication: str = ""
    medication_identifier: str = ""
    dose_quantity: Number = None
    dose_unit: str = ""
    frequency: Number = None
    period_unit: str = ""
    duration: Number = None
    duration_unit: str = ""
    route: str = ""
    start_date: str = ""
    end_date: str = ""
    medication_price: Number = None
    status: str = ""


class PrescriptionInterventionWire(WireModel):
    code: str = ""
    name: str = ""


class PrescriptionWire(WireModel):
    id: int | None = None
    guid: str = ""
    code: str = ""
    status: str = ""
    doctor_review_status: str = ""
    intervention: PrescriptionInterventionWire | None = None
    dosage: list[DosageWire] = Field(default_factory=list)


class DispenseWire(WireModel):
    id: int | None = None
    status: str = ""
    dispense_dosages: list[DosageWire] = Field(default_factory=list)
