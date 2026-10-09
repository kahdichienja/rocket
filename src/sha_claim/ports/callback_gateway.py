"""Port: registering where the HIE should deliver status callbacks."""

from __future__ import annotations

from typing import Protocol

from sha_claim.domain.callbacks import (
    CallbackEndpoint,
    CallbackEndpointUpdate,
    CallbackEntityType,
    CallbackOperation,
    CallbackOperationUpdate,
    NewCallbackEndpoint,
    NewCallbackOperation,
)


class CallbackGateway(Protocol):
    async def list_endpoints(
        self, tenant: str, entity_type: CallbackEntityType | None = None
    ) -> tuple[CallbackEndpoint, ...]: ...

    async def register_endpoint(self, tenant: str, endpoint: NewCallbackEndpoint) -> CallbackEndpoint: ...

    async def update_endpoint(
        self, endpoint_id: str, changes: CallbackEndpointUpdate
    ) -> CallbackEndpoint: ...

    async def delete_endpoint(self, endpoint_id: str) -> None: ...

    async def list_operations(
        self, tenant: str, endpoint_id: str, action: str = ""
    ) -> tuple[CallbackOperation, ...]: ...

    async def register_operation(
        self, tenant: str, endpoint_id: str, operation: NewCallbackOperation
    ) -> CallbackOperation: ...

    async def read_operation(self, operation_id: str) -> CallbackOperation: ...

    async def update_operation(
        self, operation_id: str, changes: CallbackOperationUpdate
    ) -> CallbackOperation: ...

    async def delete_operation(self, operation_id: str) -> None: ...
