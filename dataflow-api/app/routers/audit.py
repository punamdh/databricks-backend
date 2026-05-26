from fastapi import APIRouter, Query

from app.schemas.audit import AuditRunCreate, AuditRunUpdate
from app.schemas.common import PaginationMeta, success_response
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/runs")
def create_audit_run(payload: AuditRunCreate):
    return success_response(AuditService.create(payload.model_dump()))


@router.get("/runs")
def list_audit_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    run_id: str | None = None,
    table_config_id: int | None = None,
    status: str | None = None,
):
    rows, total = AuditService.list(page, page_size, run_id, table_config_id, status)
    return success_response(
        rows,
        PaginationMeta(page=page, page_size=page_size, total=total, total_pages=(total + page_size - 1) // page_size),
    )


@router.get("/runs/{table_run_id}")
def get_audit_run(table_run_id: int):
    return success_response(AuditService.get(table_run_id))


@router.patch("/runs/{table_run_id}")
def update_audit_run(table_run_id: int, payload: AuditRunUpdate):
    return success_response(AuditService.update(table_run_id, payload.model_dump()))
