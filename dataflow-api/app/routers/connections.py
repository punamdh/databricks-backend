from fastapi import APIRouter, Query

from app.schemas.common import PaginationMeta, success_response
from app.schemas.connection import ConnectionCreate, ConnectionUpdate
from app.services.connection_service import ConnectionService

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post("")
def create_connection(payload: ConnectionCreate):
    return success_response(ConnectionService.create_connection(payload.model_dump()))


@router.get("")
def list_connections(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    env_type: str | None = None,
    connection_type: str | None = None,
    is_target: int | None = None,
    is_active: bool = True,
    search: str | None = None,
):
    rows, total = ConnectionService.list_connections(
        page,
        page_size,
        {"env_type": env_type, "connection_type": connection_type, "is_target": is_target, "is_active": is_active},
        search,
    )
    return success_response(
        rows,
        PaginationMeta(page=page, page_size=page_size, total=total, total_pages=(total + page_size - 1) // page_size),
    )


@router.get("/{connection_id}")
def get_connection(connection_id: int):
    return success_response(ConnectionService.get_connection(connection_id))


@router.put("/{connection_id}")
def update_connection(connection_id: int, payload: ConnectionUpdate):
    return success_response(ConnectionService.update_connection(connection_id, payload.model_dump()))


@router.delete("/{connection_id}")
def delete_connection(connection_id: int, updated_by: str = Query(default="system")):
    ConnectionService.soft_delete_connection(connection_id, updated_by)
    return success_response({"deleted": True})


@router.post("/{connection_id}/test")
def test_connection(connection_id: int):
    return success_response(ConnectionService.test_connection(connection_id))
