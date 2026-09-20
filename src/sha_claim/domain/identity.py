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


@dataclass(frozen=True, slots=True)
class BearerToken:
    """The raw OAuth2 grant as DHA returns it. Only for callers that must talk to the HIE directly.

    Treat it like the client secret: it authorises every claim operation for the facility. `repr` is redacted.
    """

    access_token: str
    expires_in: int
    token_type: str = "Bearer"

    def __repr__(self) -> str:
        return f"BearerToken(access_token='{self.access_token[:8]}…', expires_in={self.expires_in}, token_type={self.token_type!r})"

    def as_dict(self) -> dict[str, str | int]:
        """`{access_token, expires_in, token_type}` — byte-for-byte the shape of `POST /tenants/token`."""
        return {
            "access_token": self.access_token,
            "expires_in": self.expires_in,
            "token_type": self.token_type,
        }
