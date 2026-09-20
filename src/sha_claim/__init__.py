"""sha-claim: Python SDK for Kenya SHA claims via the DHA AfyaConnect HIE eClaims API."""

from sha_claim.client import AsyncSHAClient
from sha_claim.domain.attachments import Attachment
from sha_claim.domain.codes import DocumentType, Icd11Code, InterventionCode, RegulationBody, SchemeCode
from sha_claim.domain.consent import Authorization, BiometricGuid, Otp
from sha_claim.domain.eligibility import Coverage, Eligibility, Scheme
from sha_claim.domain.enums import (
    CancelReason,
    CoverageStatus,
    DischargeReason,
    EligibilityStatus,
    IdentificationType,
    ServiceType,
)
from sha_claim.domain.identifiers import ClaimGuid, ConsentToken, FacilityCode, InvoiceNumber, PatientId
from sha_claim.domain.money import Money
from sha_claim.domain.practitioner import PractitionerRef
from sha_claim.errors import (
    AuthenticationError,
    BadRequestError,
    ConfigurationError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    RequestValidationError,
    ServerError,
    SHAClaimError,
    SubmissionOutcomeUnknownError,
    TransportError,
    UnexpectedResponseError,
)
from sha_claim.settings import Environment, SHASettings, Timeouts

__version__ = "0.1.0.dev0"

__all__ = [
    "AsyncSHAClient",
    "Attachment",
    "AuthenticationError",
    "Authorization",
    "BadRequestError",
    "BiometricGuid",
    "CancelReason",
    "ClaimGuid",
    "ConfigurationError",
    "ConsentToken",
    "Coverage",
    "CoverageStatus",
    "DischargeReason",
    "DocumentType",
    "Eligibility",
    "EligibilityStatus",
    "Environment",
    "FacilityCode",
    "Icd11Code",
    "IdentificationType",
    "InterventionCode",
    "InvoiceNumber",
    "Money",
    "NotFoundError",
    "Otp",
    "PatientId",
    "PermissionDeniedError",
    "PractitionerRef",
    "RateLimitedError",
    "RegulationBody",
    "RequestValidationError",
    "SHAClaimError",
    "SHASettings",
    "Scheme",
    "SchemeCode",
    "ServerError",
    "ServiceType",
    "SubmissionOutcomeUnknownError",
    "Timeouts",
    "TransportError",
    "UnexpectedResponseError",
    "__version__",
]
