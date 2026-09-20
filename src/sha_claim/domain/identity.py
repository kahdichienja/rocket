"""Who the credentials say we are. Read off the access token's claims — informational, never a security check."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sha_claim.domain.identifiers import FacilityCode


@dataclass(frozen=True, slots=True)
class Identity:
    facility: FacilityCode | None
    facility_id_type: str
    tenant_id: str
    tenant_name: str
    issuer: str
    client_id: str
    issued_at: datetime | None
    expires_at: datetime | None

    @property
    def seconds_remaining(self) -> int | None:
        if self.expires_at is None:
            return None
        from datetime import UTC
        from datetime import datetime as _dt

        return max(0, int((self.expires_at - _dt.now(UTC)).total_seconds()))
