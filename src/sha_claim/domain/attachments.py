"""Files attached to claims and preauthorizations."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path

from sha_claim.domain.codes import DocumentType

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # conservative; the API does not publish a limit


def document_type_value(value: DocumentType | str) -> str:
    """The wire value for a document type, whether it arrived as the enum or as a string.

    Both are legitimate. `DocumentType` is the vocabulary for **claim** attachments; a pre-authorisation
    has its own, shorter list (`LOU`, `CLINICAL_DOCUMENTATION`, `PROFORMA_INVOICE` …) that DHA publishes
    only in the Postman collection and that this enum does not carry. Forcing a pre-auth attachment
    through `DocumentType` would reject types SHA accepts.

    Written because the wire builders called `.value` unconditionally and a caller passing the string it
    read off a form got `AttributeError: 'str' object has no attribute 'value'` — a 500 from NaCare's own
    backend, on every pre-auth with a document attached.
    """
    return value.value if isinstance(value, DocumentType) else str(value).strip()


@dataclass(frozen=True, slots=True)
class Attachment:
    filename: str
    content: bytes
    document_type: DocumentType | str
    """The enum for a claim attachment, or a plain string for a vocabulary it does not carry."""
    content_type: str = "application/octet-stream"

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError("attachment filename cannot be empty")
        if not self.content:
            raise ValueError("attachment content cannot be empty")
        if len(self.content) > MAX_ATTACHMENT_BYTES:
            raise ValueError(f"attachment exceeds {MAX_ATTACHMENT_BYTES} bytes")
        if not document_type_value(self.document_type):
            raise ValueError("attachment needs a document type; SHA rejects one sent without")

    @classmethod
    def from_path(cls, path: str | Path, document_type: DocumentType | str) -> Attachment:
        p = Path(path)
        guessed, _ = mimetypes.guess_type(p.name)
        return cls(p.name, p.read_bytes(), document_type, guessed or "application/octet-stream")

    @property
    def wire_document_type(self) -> str:
        """What goes on the wire, normalised."""
        return document_type_value(self.document_type)

    @property
    def size(self) -> int:
        return len(self.content)
