from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import BTSConfig, PiiAttribute, SchemaVersion, SourceTable, Watermark
from app.repositories.pipeline_config_repo import PipelineConfigRepository
from app.schemas.common import raise_api_error


class PipelineConfigService:
    LOAD_TYPES = {"full", "incremental", "cdc", "api", "file_autoloader"}

    def __init__(self, db: Session):
        self.db = db
        self.repo = PipelineConfigRepository(db)

    def _validate_source_attributes(self, source_attributes: dict):
        if "file_path" in source_attributes:
            if not source_attributes.get("file_type"):
                raise_api_error(422, "MISSING_REQUIRED_FIELD", "file_type required for file sources")
        elif not (source_attributes.get("schema") and source_attributes.get("table")):
            raise_api_error(422, "INVALID_SOURCE_ATTRIBUTES", "schema and table required for database sources")

    def _as_dict(self, row: SourceTable) -> dict:
        return {
            "table_config_id": row.table_config_id,
            "connection_source_id": row.connection_source_id,
            "connection_domain_name": row.connection_domain_name,
            "config_group": row.config_group,
            "source_attributes": json.loads(row.source_attributes),
            "target_attributes": json.loads(row.target_attributes),
            "load_type": row.load_type,
            "natural_key_columns": row.natural_key_columns,
            "hash_key_column": row.hash_key_column,
            "partition_columns": row.partition_columns,
            "watermark_enabled": row.watermark_enabled,
            "pii_scan_enabled": row.pii_scan_enabled,
            "fail_mode": row.fail_mode,
            "retry_count": row.retry_count,
            "ingestion_frequency": row.ingestion_frequency,
            "tags": json.loads(row.tags) if row.tags else [],
            "env_type": row.env_type,
            "is_active": row.is_active,
        }

    def create(self, payload: dict) -> dict:
        if payload["load_type"] not in self.LOAD_TYPES:
            raise_api_error(422, "INVALID_LOAD_TYPE", "Load type not supported")
        self._validate_source_attributes(payload["source_attributes"])

        actor = payload.get("created_by", "system")
        source = dict(payload)
        watermark = source.pop("watermark", None)
        source["source_attributes"] = json.dumps(source["source_attributes"])
        source["target_attributes"] = json.dumps(source["target_attributes"])
        source["tags"] = json.dumps(source.get("tags", []))

        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            row = self.repo.create({**source, "created_by": actor, "updated_by": actor})
            if watermark:
                watermark_payload = watermark
                watermark_payload["created_by"] = actor
                self.repo.upsert_watermark(row.table_config_id, watermark_payload)

        return self._as_dict(row)

    def list(self, page: int, page_size: int, filters: dict):
        rows, total = self.repo.list(page, page_size, filters)
        return [self._as_dict(row) for row in rows], total

    def get(self, table_config_id: int) -> dict:
        row = self.repo.get(table_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        return self._as_dict(row)

    def update(self, table_config_id: int, payload: dict) -> dict:
        row = self.repo.get(table_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")

        if payload.get("load_type") and payload["load_type"] not in self.LOAD_TYPES:
            raise_api_error(422, "INVALID_LOAD_TYPE", "Load type not supported")

        if payload.get("source_attributes"):
            self._validate_source_attributes(payload["source_attributes"])

        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            for key, value in payload.items():
                if value is None or key == "updated_by":
                    continue
                if key in {"source_attributes", "target_attributes", "tags"}:
                    value = json.dumps(value)
                setattr(row, key, value)
            row.updated_by = payload.get("updated_by", "system")

        self.db.refresh(row)
        return self._as_dict(row)

    def soft_delete(self, table_config_id: int, actor: str) -> None:
        row = self.repo.get(table_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")

        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            row.is_active = 0
            row.updated_by = actor
            for model in (Watermark, SchemaVersion, PiiAttribute, BTSConfig):
                items = self.db.execute(
                    select(model).where(getattr(model, "table_config_id", getattr(model, "source_config_id")) == table_config_id)
                ).scalars().all()
                for item in items:
                    item.is_active = 0
                    item.updated_by = actor

    def bulk_create(self, payloads: list[dict]):
        created = 0
        failed = 0
        errors = []
        for idx, payload in enumerate(payloads):
            try:
                self.create(payload)
                created += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                errors.append({"index": idx, "error": str(exc)})
        return {"created_count": created, "failed_count": failed, "errors": errors}

    def get_watermark(self, table_config_id: int):
        if not self.repo.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        row = self.repo.get_watermark(table_config_id)
        if not row:
            return None
        return {
            "watermark_id": row.watermark_id,
            "table_config_id": row.table_config_id,
            "watermark_column": row.watermark_column,
            "watermark_type": row.watermark_type,
            "last_value": row.last_value,
            "last_run_id": row.last_run_id,
            "env_type": row.env_type,
        }

    def upsert_watermark(self, table_config_id: int, payload: dict):
        if not self.repo.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            row = self.repo.upsert_watermark(table_config_id, payload)
        return {
            "watermark_id": row.watermark_id,
            "table_config_id": row.table_config_id,
            "watermark_column": row.watermark_column,
            "watermark_type": row.watermark_type,
            "last_value": row.last_value,
            "last_run_id": row.last_run_id,
            "env_type": row.env_type,
        }

    def get_pii(self, table_config_id: int):
        if not self.repo.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        rows = self.repo.list_pii(table_config_id)
        return [
            {
                "pii_id": row.pii_id,
                "column_name": row.column_name,
                "pii_category": row.pii_category,
                "protection_method": row.protection_method,
                "sensitivity": row.sensitivity,
                "masking_policy": row.masking_policy,
                "uc_tag_applied": row.uc_tag_applied,
                "access_tier": row.access_tier,
            }
            for row in rows
        ]

    def set_pii(self, table_config_id: int, env_type: str, actor: str, items: list[dict]):
        if not self.repo.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            rows = self.repo.replace_pii(table_config_id, env_type, actor, items)
        return [{"pii_id": row.pii_id, "column_name": row.column_name} for row in rows]

    def add_schema_version(self, table_config_id: int, payload: dict):
        if not self.repo.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            row = self.repo.add_schema_version(table_config_id, payload)
        return {
            "version_id": row.version_id,
            "version_number": row.version_number,
            "column_count": row.column_count,
            "column_changes_json": json.loads(row.column_changes_json),
            "change_type": row.change_type,
            "detected_by_run_id": row.detected_by_run_id,
        }

    def list_schema_versions(self, table_config_id: int):
        if not self.repo.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        rows = self.repo.list_schema_versions(table_config_id)
        return [
            {
                "version_id": row.version_id,
                "version_number": row.version_number,
                "column_count": row.column_count,
                "column_changes_json": json.loads(row.column_changes_json),
                "change_type": row.change_type,
                "detected_by_run_id": row.detected_by_run_id,
            }
            for row in rows
        ]
