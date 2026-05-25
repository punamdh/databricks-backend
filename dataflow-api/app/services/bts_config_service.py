from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.repositories.bts_config_repo import BTSConfigRepository
from app.schemas.common import raise_api_error


class BTSConfigService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BTSConfigRepository(db)

    def _as_dict(self, row):
        return {
            "bts_config_id": row.bts_config_id,
            "dataset_name": row.dataset_name,
            "source_config_id": row.source_config_id,
            "silver_layout": json.loads(row.silver_layout) if row.silver_layout else [],
            "dq_rules": json.loads(row.dq_rules) if row.dq_rules else [],
            "std_rules": json.loads(row.std_rules) if row.std_rules else [],
            "transformation_yaml": row.transformation_yaml,
            "tags": json.loads(row.tags) if row.tags else [],
            "env_type": row.env_type,
            "is_active": row.is_active,
        }

    def create(self, payload: dict):
        actor = payload.get("created_by", "system")
        row_payload = dict(payload)
        row_payload["silver_layout"] = json.dumps(row_payload.get("silver_layout", []))
        row_payload["dq_rules"] = json.dumps(row_payload.get("dq_rules", []))
        row_payload["std_rules"] = json.dumps(row_payload.get("std_rules", []))
        row_payload["tags"] = json.dumps(row_payload.get("tags", []))
        row_payload["created_by"] = actor
        row_payload["updated_by"] = actor

        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            row = self.repo.create(row_payload)
        return self._as_dict(row)

    def list(self, page: int, page_size: int, env_type: str | None, dataset_name: str | None):
        rows, total = self.repo.list(page, page_size, env_type, dataset_name)
        return [self._as_dict(row) for row in rows], total

    def get(self, bts_config_id: int):
        row = self.repo.get(bts_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "BTS config not found")
        return self._as_dict(row)

    def update(self, bts_config_id: int, payload: dict):
        row = self.repo.get(bts_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "BTS config not found")

        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            for key, value in payload.items():
                if value is None or key == "updated_by":
                    continue
                if key in {"silver_layout", "dq_rules", "std_rules", "tags"}:
                    value = json.dumps(value)
                setattr(row, key, value)
            row.updated_by = payload.get("updated_by", "system")

        self.db.refresh(row)
        return self._as_dict(row)

    def soft_delete(self, bts_config_id: int, actor: str):
        row = self.repo.get(bts_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "BTS config not found")
        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            row.is_active = 0
            row.updated_by = actor
