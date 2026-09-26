"""ClinicalGateway port."""

from __future__ import annotations

from typing import Protocol

from smart_access.domain.clinical import (
    AdmissionDetails,
    ClinicalRecord,
    ClinicalRequests,
    DischargeDetails,
    ItemMapping,
)


class ClinicalGateway(Protocol):
    """Port for posting clinical records, requests, admission, discharge, and item mappings."""

    async def post_clinical_record(self, record: ClinicalRecord) -> bool:
        """Post patient diagnostic info to `POST /api/clinic-record`."""
        ...

    async def post_clinical_requests(self, requests: ClinicalRequests) -> bool:
        """Post clinical orders/prescriptions to `POST /api/requests`."""
        ...

    async def post_admission(self, admission: AdmissionDetails) -> bool:
        """Post admission details to `POST /api/admission`."""
        ...

    async def post_discharge(self, discharge: DischargeDetails) -> bool:
        """Post discharge summary to `POST /api/discharge`."""
        ...

    async def post_item_mapping(self, mapping: ItemMapping) -> bool:
        """Post new items/services for Smart Master List mapping to `POST /api/new-mapping`."""
        ...
