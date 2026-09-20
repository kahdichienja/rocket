"""ePrescriptions: what a doctor orders for an intervention, and what the pharmacy dispenses against it."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from sha_claim.domain.codes import InterventionCode
from sha_claim.domain.money import Money
from sha_claim.domain.practitioner import PractitionerRef


@dataclass(frozen=True, slots=True)
class MedicationOrder:
    """One prescribed medication (an `items[]` entry of `POST /prescriptions`)."""

    generic_concept_code: str
    dose_quantity: Decimal | int
    dose_unit: str
    frequency: int
    period_unit: str  # e.g. "DAY"
    duration: int
    duration_unit: str  # e.g. "DAY", "WEEK"
    start_date: date
    end_date: date | None = None
    patient_instruction: str = ""
    additional_instruction: str = ""
    needs_refill: bool = False
    refill_count: int = 0

    def __post_init__(self) -> None:
        if not self.generic_concept_code.strip():
            raise ValueError("generic_concept_code cannot be empty")
        if Decimal(self.dose_quantity) <= 0:
            raise ValueError("dose_quantity must be positive")
        if self.frequency <= 0 or self.duration <= 0:
            raise ValueError("frequency and duration must be positive")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        if self.refill_count < 0 or (self.needs_refill and self.refill_count == 0):
            raise ValueError("refill_count must be positive when needs_refill is set")


@dataclass(frozen=True, slots=True)
class PrescriptionRequest:
    intervention_code: InterventionCode
    items: tuple[MedicationOrder, ...]
    prescriber: PractitionerRef | None = None

    def __post_init__(self) -> None:
        if not self.items:
            raise ValueError("at least one medication is required")


@dataclass(frozen=True, slots=True)
class Dosage:
    """A dosage line as the server stores it."""

    medication: str
    medication_identifier: str
    dose_quantity: Decimal | None
    dose_unit: str
    frequency: int | None
    period_unit: str
    duration: str
    duration_unit: str
    route: str = ""
    start_date: date | None = None
    end_date: date | None = None
    price: Money | None = None
    status: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class Prescription:
    guid: str
    code: str
    status: str
    doctor_review_status: str
    intervention_code: InterventionCode | None
    dosage: tuple[Dosage, ...]
    record_id: int | None = None
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class DispensedProduct:
    """An `actual_products[]` entry of `POST /prescriptions/dispenses`."""

    product_code: str
    quantity: Decimal | int
    price: Money

    def __post_init__(self) -> None:
        if not self.product_code.strip():
            raise ValueError("product_code cannot be empty")
        if Decimal(self.quantity) <= 0:
            raise ValueError("quantity must be positive")
        if self.price.is_negative:
            raise ValueError("price cannot be negative")


@dataclass(frozen=True, slots=True)
class DispenseRequest:
    intervention_code: InterventionCode
    products: tuple[DispensedProduct, ...]
    dispensers: tuple[PractitionerRef, ...]

    def __post_init__(self) -> None:
        if not self.products:
            raise ValueError("at least one dispensed product is required")
        if not self.dispensers:
            raise ValueError("at least one dispensing practitioner is required")


@dataclass(frozen=True, slots=True)
class Dispense:
    record_id: int | None
    status: str
    dosages: tuple[Dosage, ...]
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
