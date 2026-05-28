from __future__ import annotations

import json
from datetime import datetime, timezone

from app.repositories.audit_repo import AuditRepository
from app.schemas.common import raise_api_error


class AuditService:
    @staticmethod
    def _as_dict(row: dict):
        return {
            "table_run_id": row["table_run_id"],
            "run_id": row["run_id"],
            "table_config_id": row["table_config_id"],
            "connection_source_id": row["connection_source_id"],
            "connection_target_id": row.get("connection_target_id"),
            "source_attributes": json.loads(row["source_attributes"]) if row.get("source_attributes") else None,
            "target_attributes": json.loads(row["target_attributes"]) if row.get("target_attributes") else None,
            "batch_id": row.get("batch_id"),
            "load_type": row.get("load_type"),
            "start_time": row["start_time"],
            "end_time": row.get("end_time"),
            "elapsed_seconds": row.get("elapsed_seconds"),
            "rows_read": row.get("rows_read"),
            "rows_written": row.get("rows_written"),
            "watermark_start": row.get("watermark_start"),
            "watermark_end": row.get("watermark_end"),
            "status": row["status"],
            "error_message": row.get("error_message"),
            "error_type": row.get("error_type"),
            "env_type": row["env_type"],
            "is_active": row["is_active"],
        }

    @staticmethod
    def create(payload: dict):
        actor = payload.get("created_by", "system")
        now = datetime.now(timezone.utc).isoformat()
        row = AuditRepository.create(
            {
                **payload,
                "is_active": True,
                "created_by": actor,
                "updated_by": payload.get("updated_by", actor),
                "created_at": now,
                "updated_at": now,
            }
        )
        return AuditService._as_dict(row)

    @staticmethod
    def list(page: int, page_size: int, run_id: str | None, table_config_id: int | None, status: str | None):
        rows, total = AuditRepository.list(page, page_size, run_id, table_config_id, status)
        return [AuditService._as_dict(row) for row in rows], total

    @staticmethod
    def get(table_run_id: int):
        row = AuditRepository.get(table_run_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Audit run not found")
        return AuditService._as_dict(row)

    @staticmethod
    def update(table_run_id: int, payload: dict):
        if not AuditRepository.get(table_run_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Audit run not found")
        updates = {k: v for k, v in payload.items() if v is not None and k != "updated_by"}
        updates["updated_by"] = payload.get("updated_by", "system")
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        AuditRepository.update(table_run_id, updates)
        return AuditService.get(table_run_id)
