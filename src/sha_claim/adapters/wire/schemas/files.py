from __future__ import annotations

from typing import Any

from sha_claim.adapters.wire.schemas.common import WireModel


class StoredFileWire(WireModel):
    id: str = ""
    file_id: str = ""
    path: str = ""
    url: str = ""


class DownloadLinkWire(WireModel):
    message: str = ""
    data: Any = None
