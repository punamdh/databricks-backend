from fastapi import APIRouter, Query

from app.schemas.bts_config import BTSConfigCreate, BTSConfigUpdate
from app.schemas.common import PaginationMeta, success_response
from app.services.bts_config_service import BTSConfigService

router = APIRouter(prefix="/bts-configs", tags=["bts-configs"])


@router.post("")
def create_bts_config(payload: BTSConfigCreate):
    return success_response(BTSConfigService.create(payload.model_dump()))


@router.get("")
def list_bts_configs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    env_type: str | None = None,
    dataset_name: str | None = None,
):
    rows, total = BTSConfigService.list(page, page_size, env_type, dataset_name)
    return success_response(
        rows,
        PaginationMeta(page=page, page_size=page_size, total=total, total_pages=(total + page_size - 1) // page_size),
    )


@router.get("/{bts_config_id}")
def get_bts_config(bts_config_id: int):
    return success_response(BTSConfigService.get(bts_config_id))


@router.put("/{bts_config_id}")
def update_bts_config(bts_config_id: int, payload: BTSConfigUpdate):
    return success_response(BTSConfigService.update(bts_config_id, payload.model_dump()))


@router.delete("/{bts_config_id}")
def delete_bts_config(bts_config_id: int, updated_by: str = Query(default="system")):
    BTSConfigService.soft_delete(bts_config_id, updated_by)
    return success_response({"deleted": True})
