"""Standalone file storage (`/uploads`). Claim attachments normally go inline; this is for everything else."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from sha_claim.domain.identifiers import FileId


@dataclass(frozen=True, slots=True)
class StoredFile:
    """Result of `POST /uploads`. The documented response is `{}`; the id/path surface when the server sends them."""

    file_id: FileId | None
    path: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class DownloadLink:
    url: str
    message: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
