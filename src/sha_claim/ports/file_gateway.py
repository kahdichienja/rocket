from __future__ import annotations

from typing import Protocol

from sha_claim.domain.files import DownloadLink, StoredFile
from sha_claim.domain.identifiers import FileId


class FileGateway(Protocol):
    async def upload(self, filename: str, content: bytes, content_type: str) -> StoredFile: ...

    async def download_link(self, file_id: FileId) -> DownloadLink: ...
