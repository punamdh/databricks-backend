from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.repositories.audit_repo import AuditRepository
from app.schemas.common import raise_api_error


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditRepository(db)

    def _as_dict(self, row):
        return {
            "table_run_id": row.table_run_id,
            "run_id": row.run_id,
            "table_config_id": row.table_config_id,
            "connection_source_id": row.connection_source_id,
            "source_attributes": json.loads(row.source_attributes) if row.source_attributes else None,
            "target_attributes": json.loads(row.target_attributes) if row.target_attributes else None,
            "batch_id": row.batch_id,
            "load_type": row.load_type,
            "start_time": row.start_time,
            "end_time": row.end_time,
            "elapsed_seconds": row.elapsed_seconds,
            "rows_read": row.rows_read,
            "rows_written": row.rows_written,
            "watermark_start": row.watermark_start,
            "watermark_end": row.watermark_end,
            "status": row.status,
            "error_message": row.error_message,
            "error_type": row.error_type,
            "env_type": row.env_type,
            "is_active": row.is_active,
        }

    def create(self, payload: dict):
        actor = payload.get("created_by", "system")
        row_payload = dict(payload)
        row_payload["created_by"] = actor
        row_payload["updated_by"] = actor
        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            row = self.repo.create(row_payload)
        return self._as_dict(row)

    def list(self, page: int, page_size: int, run_id: str | None, table_config_id: int | None, status: str | None):
        rows, total = self.repo.list(page, page_size, run_id, table_config_id, status)
        return [self._as_dict(row) for row in rows], total

    def get(self, table_run_id: int):
        row = self.repo.get(table_run_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Audit run not found")
        return self._as_dict(row)

    def update(self, table_run_id: int, payload: dict):
        row = self.repo.get(table_run_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Audit run not found")

        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            for key, value in payload.items():
                if value is None or key == "updated_by":
                    continue
                setattr(row, key, value)
            row.updated_by = payload.get("updated_by", "system")

        self.db.refresh(row)
        return self._as_dict(row)
