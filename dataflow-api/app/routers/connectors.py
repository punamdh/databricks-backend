from fastapi import APIRouter, Query

from app.schemas.common import success_response
from app.services.connector_service import ConnectorService

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("")
def list_connectors():
    return success_response(ConnectorService.list_connectors())


@router.get("/{connector_key}/fields")
def get_connector_fields(connector_key: str, auth_type: str | None = Query(default=None)):
    return success_response(ConnectorService.get_connector_fields(connector_key, auth_type))
