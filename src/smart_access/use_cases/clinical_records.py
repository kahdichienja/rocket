"""Use cases for clinical records, requests, admission, discharge, and item mappings."""

from __future__ import annotations

from smart_access.domain.clinical import (
    AdmissionDetails,
    ClinicalRecord,
    ClinicalRequests,
    DischargeDetails,
    ItemMapping,
)
from smart_access.ports.clinical_gateway import ClinicalGateway


class PostClinicalRecord:
    """Post patient clinical diagnoses if not embedded in the claim."""

    def __init__(self, gateway: ClinicalGateway) -> None:
        self._gateway = gateway

    async def execute(self, record: ClinicalRecord) -> bool:
        return await self._gateway.post_clinical_record(record)


class PostClinicalRequests:
    """Post clinical orders (prescriptions, labs, radiology, procedures)."""

    def __init__(self, gateway: ClinicalGateway) -> None:
        self._gateway = gateway

    async def execute(self, requests: ClinicalRequests) -> bool:
        return await self._gateway.post_clinical_requests(requests)


class PostAdmission:
    """Post inpatient admission details to Smart."""

    def __init__(self, gateway: ClinicalGateway) -> None:
        self._gateway = gateway

    async def execute(self, admission: AdmissionDetails) -> bool:
        return await self._gateway.post_admission(admission)


class PostDischarge:
    """Post inpatient discharge details to Smart."""

    def __init__(self, gateway: ClinicalGateway) -> None:
        self._gateway = gateway

    async def execute(self, discharge: DischargeDetails) -> bool:
        return await self._gateway.post_discharge(discharge)


class PostItemMapping:
    """Post new hospital items or item groups for Smart Master List mapping."""

    def __init__(self, gateway: ClinicalGateway) -> None:
        self._gateway = gateway

    async def execute(self, mapping: ItemMapping) -> bool:
        return await self._gateway.post_item_mapping(mapping)
