"""Files attached to claims and preauthorizations."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path

from sha_claim.domain.codes import DocumentType

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # conservative; the API does not publish a limit


@dataclass(frozen=True, slots=True)
class Attachment:
    filename: str
    content: bytes
    document_type: DocumentType
    content_type: str = "application/octet-stream"

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError("attachment filename cannot be empty")
        if not self.content:
            raise ValueError("attachment content cannot be empty")
        if len(self.content) > MAX_ATTACHMENT_BYTES:
            raise ValueError(f"attachment exceeds {MAX_ATTACHMENT_BYTES} bytes")

    @classmethod
    def from_path(cls, path: str | Path, document_type: DocumentType) -> Attachment:
        p = Path(path)
        guessed, _ = mimetypes.guess_type(p.name)
        return cls(p.name, p.read_bytes(), document_type, guessed or "application/octet-stream")

    @property
    def size(self) -> int:
        return len(self.content)
