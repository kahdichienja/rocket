from __future__ import annotations

from sha_claim.adapters.wire.schemas.common import WireModel


class EmergencyProtocolWire(WireModel):
    id: int | None = None
    guid: str = ""
    protocol_code: str = ""
    name: str = ""
    protocol_type: str = ""
    protocol_classification_type: str = ""
    status: str = ""
    applicable_tariff: str | float | int | None = None
