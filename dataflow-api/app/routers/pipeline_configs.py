from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_session
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
def create_pipeline_config(payload: PipelineConfigCreate, db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).create(payload.model_dump()))


@router.get("")
def list_pipeline_configs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    env_type: str | None = None,
    connection_source_id: int | None = None,
    config_group: str | None = None,
    load_type: str | None = None,
    is_active: int = 1,
    db: Session = Depends(get_session),
):
    rows, total = PipelineConfigService(db).list(
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
def get_pipeline_config(table_config_id: int, db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).get(table_config_id))


@router.put("/{table_config_id}")
def update_pipeline_config(table_config_id: int, payload: PipelineConfigUpdate, db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).update(table_config_id, payload.model_dump()))


@router.delete("/{table_config_id}")
def delete_pipeline_config(table_config_id: int, updated_by: str = Query(default="system"), db: Session = Depends(get_session)):
    PipelineConfigService(db).soft_delete(table_config_id, updated_by)
    return success_response({"deleted": True})


@router.post("/bulk")
def bulk_create_pipeline_configs(payload: list[PipelineConfigCreate], db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).bulk_create([item.model_dump() for item in payload]))


@router.get("/{table_config_id}/watermark")
def get_watermark(table_config_id: int, db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).get_watermark(table_config_id))


@router.put("/{table_config_id}/watermark")
def upsert_watermark(table_config_id: int, payload: WatermarkPayload, db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).upsert_watermark(table_config_id, payload.model_dump()))


@router.get("/{table_config_id}/pii")
def list_pii(table_config_id: int, db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).get_pii(table_config_id))


@router.post("/{table_config_id}/pii")
def set_pii(table_config_id: int, payload: list[PiiPayload], env_type: str = Query(default="dev"), created_by: str = Query(default="system"), db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).set_pii(table_config_id, env_type, created_by, [item.model_dump() for item in payload]))


@router.get("/{table_config_id}/schema-versions")
def list_schema_versions(table_config_id: int, db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).list_schema_versions(table_config_id))


@router.post("/{table_config_id}/schema-versions")
def add_schema_version(table_config_id: int, payload: SchemaVersionPayload, db: Session = Depends(get_session)):
    return success_response(PipelineConfigService(db).add_schema_version(table_config_id, payload.model_dump()))
