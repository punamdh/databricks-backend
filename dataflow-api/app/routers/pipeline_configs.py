from fastapi import APIRouter, Query

from app.schemas.common import PaginationMeta, success_response
from app.schemas.pipeline_config import (
    PipelineConfigCreate,
    PipelineConfigUpdate,
    PiiPayload,
    SchemaVersionPayload,
    WatermarkPayload,
)
from app.services.pipeline_config_service import PipelineConfigService

router = APIRouter(prefix="/pipeline-configs", tags=["pipeline-configs"])


@router.post("")
def create_pipeline_config(payload: PipelineConfigCreate):
    return success_response(PipelineConfigService.create(payload.model_dump()))


@router.get("")
def list_pipeline_configs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    env_type: str | None = None,
    connection_source_id: int | None = None,
    config_group: str | None = None,
    load_type: str | None = None,
    is_active: int = 1,
):
    rows, total = PipelineConfigService.list(
        page,
        page_size,
        {
            "env_type": env_type,
            "connection_source_id": connection_source_id,
            "config_group": config_group,
            "load_type": load_type,
            "is_active": is_active,
        },
    )
    return success_response(
        rows,
        PaginationMeta(page=page, page_size=page_size, total=total, total_pages=(total + page_size - 1) // page_size),
    )


@router.get("/{table_config_id}")
def get_pipeline_config(table_config_id: int):
    return success_response(PipelineConfigService.get(table_config_id))


@router.put("/{table_config_id}")
def update_pipeline_config(table_config_id: int, payload: PipelineConfigUpdate):
    return success_response(PipelineConfigService.update(table_config_id, payload.model_dump()))


@router.delete("/{table_config_id}")
def delete_pipeline_config(table_config_id: int, updated_by: str = Query(default="system")):
    PipelineConfigService.soft_delete(table_config_id, updated_by)
    return success_response({"deleted": True})


@router.post("/bulk")
def bulk_create_pipeline_configs(payload: list[PipelineConfigCreate]):
    return success_response(PipelineConfigService.bulk_create([item.model_dump() for item in payload]))


@router.get("/{table_config_id}/watermark")
def get_watermark(table_config_id: int):
    return success_response(PipelineConfigService.get_watermark(table_config_id))


@router.put("/{table_config_id}/watermark")
def upsert_watermark(table_config_id: int, payload: WatermarkPayload):
    return success_response(PipelineConfigService.upsert_watermark(table_config_id, payload.model_dump()))


@router.get("/{table_config_id}/pii")
def list_pii(table_config_id: int):
    return success_response(PipelineConfigService.get_pii(table_config_id))


@router.post("/{table_config_id}/pii")
def set_pii(table_config_id: int, payload: list[PiiPayload], env_type: str = Query(default="dev"), created_by: str = Query(default="system")):
    return success_response(PipelineConfigService.set_pii(table_config_id, env_type, created_by, [item.model_dump() for item in payload]))


@router.get("/{table_config_id}/schema-versions")
def list_schema_versions(table_config_id: int):
    return success_response(PipelineConfigService.list_schema_versions(table_config_id))


@router.post("/{table_config_id}/schema-versions")
def add_schema_version(table_config_id: int, payload: SchemaVersionPayload):
    return success_response(PipelineConfigService.add_schema_version(table_config_id, payload.model_dump()))
