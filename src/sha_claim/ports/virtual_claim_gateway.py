from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from sha_claim.domain.attachments import Attachment
from sha_claim.domain.claim import (
    ClaimAttachment,
    ClaimDiagnosis,
    ClaimIntervention,
    ClaimLine,
    Discharge,
    LineEdit,
    LineResubmission,
    NewClaimLine,
    NextOfKin,
    NextOfKinContact,
    PayerClaimRecord,
    Submission,
    VirtualClaim,
)
from sha_claim.domain.codes import Icd11Code, InterventionCode
from sha_claim.domain.consent import ConsentProof
from sha_claim.domain.enums import CancelReason, ServiceType
from sha_claim.domain.identifiers import AttachmentId, ClaimGuid, ConsentToken, LineGuid, PatientId
from sha_claim.domain.practitioner import PractitionerRef


class VisitOpener(Protocol):
    """Role interface for the OpenVisit use case."""

    async def open_visit(
        self,
        patient: PatientId,
        service_type: ServiceType,
        interventions: Sequence[InterventionCode],
        proof: ConsentProof,
    ) -> VirtualClaim: ...


class ClaimSubmitter(Protocol):
    """Role interface for the SubmitClaim use case."""

    async def submit(self, token: ConsentToken, submission: Submission) -> VirtualClaim: ...


class VirtualClaimGateway(VisitOpener, ClaimSubmitter, Protocol):
    """Everything ClaimSession needs. Implemented by HttpVirtualClaimGateway."""

    async def add_intervention(self, token: ConsentToken, code: InterventionCode) -> ClaimIntervention: ...

    async def retire_intervention(self, token: ConsentToken, code: InterventionCode) -> None: ...

    async def restore_intervention(self, token: ConsentToken, code: InterventionCode) -> None: ...

    async def switch_intervention(
        self,
        token: ConsentToken,
        existing: InterventionCode,
        new: InterventionCode,
        retain_bill_items: bool,
        bill_from: datetime | None,
        bill_to: datetime | None,
    ) -> None: ...

    async def add_diagnosis(
        self, token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
    ) -> ClaimDiagnosis: ...

    async def remove_diagnosis(
        self, token: ConsentToken, icd: Icd11Code, intervention: InterventionCode
    ) -> None: ...

    async def add_line(self, token: ConsentToken, line: NewClaimLine) -> ClaimLine: ...

    async def remove_line(self, token: ConsentToken, line: LineGuid) -> None: ...

    async def edit_line(self, edit: LineEdit) -> ClaimLine: ...

    async def add_attachment(
        self, token: ConsentToken, attachment: Attachment, intervention: InterventionCode
    ) -> ClaimAttachment: ...

    async def remove_attachment(
        self, token: ConsentToken, attachment: AttachmentId, intervention: InterventionCode
    ) -> None: ...

    async def add_doctor(self, token: ConsentToken, doctor: PractitionerRef) -> str: ...

    async def preview(self, token: ConsentToken) -> VirtualClaim: ...

    async def close(self, token: ConsentToken, reason: CancelReason, text: str) -> VirtualClaim: ...

    async def payer_status(
        self, claim: ClaimGuid, provider_claim_no: str
    ) -> tuple[PayerClaimRecord, ...]: ...

    async def send_discharge_otp(self, token: ConsentToken, patient: PatientId) -> str: ...

    async def discharge(self, token: ConsentToken, discharge: Discharge) -> VirtualClaim: ...

    async def add_next_of_kin(self, token: ConsentToken, next_of_kin: NextOfKin) -> NextOfKinContact: ...

    async def resubmit_lines(self, token: ConsentToken) -> LineResubmission: ...
