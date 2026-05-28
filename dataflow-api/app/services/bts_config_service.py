from __future__ import annotations

import json
from datetime import datetime, timezone

from app.repositories.bts_config_repo import BTSConfigRepository
from app.schemas.common import raise_api_error


class BTSConfigService:
    @staticmethod
    def _as_dict(row: dict):
        return {
            "bts_config_id": row["bts_config_id"],
            "dataset_name": row["dataset_name"],
            "source_config_id": row["source_config_id"],
            "silver_layout": json.loads(row["silver_layout"]) if row.get("silver_layout") else [],
            "dq_rules": json.loads(row["dq_rules"]) if row.get("dq_rules") else [],
            "std_rules": json.loads(row["std_rules"]) if row.get("std_rules") else [],
            "transformation_yaml": row.get("transformation_yaml"),
            "tags": json.loads(row["tags"]) if row.get("tags") else [],
            "env_type": row["env_type"],
            "is_active": row["is_active"],
        }

    @staticmethod
    def create(payload: dict):
        actor = payload.get("created_by", "system")
        now = datetime.now(timezone.utc).isoformat()
        row_payload = {
            **payload,
            "silver_layout": json.dumps(payload.get("silver_layout", [])),
            "dq_rules": json.dumps(payload.get("dq_rules", [])),
            "std_rules": json.dumps(payload.get("std_rules", [])),
            "tags": json.dumps(payload.get("tags", [])),
            "is_active": 1,
            "created_by": actor,
            "updated_by": payload.get("updated_by", actor),
            "created_at": now,
            "updated_at": now,
        }
        row = BTSConfigRepository.create(row_payload)
        return BTSConfigService._as_dict(row)

    @staticmethod
    def list(page: int, page_size: int, env_type: str | None, dataset_name: str | None):
        rows, total = BTSConfigRepository.list(page, page_size, env_type, dataset_name)
        return [BTSConfigService._as_dict(row) for row in rows], total

    @staticmethod
    def get(bts_config_id: int):
        row = BTSConfigRepository.get(bts_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "BTS config not found")
        return BTSConfigService._as_dict(row)

    @staticmethod
    def update(bts_config_id: int, payload: dict):
        print(f"[DEBUG] BTSConfigService.update called with bts_config_id={bts_config_id}, payload={payload}")
        
        if not BTSConfigRepository.get(bts_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "BTS config not found")

        updates = {}
        for key, value in payload.items():
            if value is None or key == "updated_by":
                continue
            if key in {"silver_layout", "dq_rules", "std_rules", "tags"}:
                value = json.dumps(value)
            updates[key] = value
        updates["updated_by"] = payload.get("updated_by", "system")
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        print(f"[DEBUG] Updates dict to be applied: {updates}")
        
        BTSConfigRepository.update(bts_config_id, updates)
        return {"updated": True, "bts_config_id": bts_config_id}

    @staticmethod
    def soft_delete(bts_config_id: int, actor: str):
        if not BTSConfigRepository.get(bts_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "BTS config not found")
        BTSConfigRepository.soft_delete(bts_config_id, actor)
