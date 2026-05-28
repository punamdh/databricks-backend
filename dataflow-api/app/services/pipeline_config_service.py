from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories.pipeline_config_repo import PipelineConfigRepository
from app.schemas.common import raise_api_error


class PipelineConfigService:
    LOAD_TYPES = {"full", "incremental", "cdc", "api", "file_autoloader"}

    @staticmethod
    def _validate_source_attributes(source_attributes: dict):
        if "file_path" in source_attributes:
            if not source_attributes.get("file_type"):
                raise_api_error(422, "MISSING_REQUIRED_FIELD", "file_type required for file sources")
        elif not (
            source_attributes.get("query")
            or (source_attributes.get("schema") and source_attributes.get("table"))
            or source_attributes.get("table")
        ):
            raise_api_error(422, "INVALID_SOURCE_ATTRIBUTES", "source_attributes must include 'table' or 'query' for database sources")

    @staticmethod
    def _as_dict(row: dict) -> dict:
        return {
            "table_config_id": row["table_config_id"],
            "connection_source_id": row["connection_source_id"],
            "connection_domain_name": row["connection_domain_name"],
            "table_group_id": row.get("table_group_id"),
            "source_attributes": json.loads(row["source_attributes"]),
            "target_attributes": json.loads(row["target_attributes"]),
            "load_type": row["load_type"],
            "natural_key_columns": row.get("natural_key_columns"),
            "hash_key_column": row.get("hash_key_column"),
            "partition_columns": row.get("partition_columns"),
            "watermark_enabled": bool(row.get("watermark_enabled", False)),
            "pii_scan_enabled": bool(row.get("pii_scan_enabled", False)),
            "ingestion_frequency": row.get("ingestion_frequency", "adhoc"),
            "tags": json.loads(row["tags"]) if row.get("tags") else [],
            "env_type": row["env_type"],
            "is_active": row["is_active"],
        }

    @staticmethod
    def create(payload: dict) -> dict:
        if payload["load_type"] not in PipelineConfigService.LOAD_TYPES:
            raise_api_error(422, "INVALID_LOAD_TYPE", "Load type not supported")
        PipelineConfigService._validate_source_attributes(payload["source_attributes"])

        actor = payload.get("created_by", "system")
        source = dict(payload)
        source.pop("watermark", None)
        source["source_attributes"] = json.dumps(source["source_attributes"])
        source["target_attributes"] = json.dumps(source["target_attributes"])
        source["tags"] = json.dumps(source.get("tags", []))
        source["is_active"] = True
        source["created_by"] = actor
        source["updated_by"] = payload.get("updated_by", actor)
        source["created_at"] = source["updated_at"] = source.get("created_at") or source.get("updated_at") or datetime.now(timezone.utc).isoformat()

        row = PipelineConfigRepository.create(source)
        if payload.get("watermark"):
            wm_payload = {**payload["watermark"], "updated_by": actor}
            PipelineConfigRepository.upsert_watermark(row["table_config_id"], wm_payload)

        return PipelineConfigService._as_dict(row)

    @staticmethod
    def list(page: int, page_size: int, filters: dict):
        rows, total = PipelineConfigRepository.list(page, page_size, filters)
        return [PipelineConfigService._as_dict(row) for row in rows], total

    @staticmethod
    def get(table_config_id: int) -> dict:
        row = PipelineConfigRepository.get(table_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        return PipelineConfigService._as_dict(row)

    @staticmethod
    def update(table_config_id: int, payload: dict) -> dict:
        row = PipelineConfigRepository.get(table_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")

        if payload.get("load_type") and payload["load_type"] not in PipelineConfigService.LOAD_TYPES:
            raise_api_error(422, "INVALID_LOAD_TYPE", "Load type not supported")
        if payload.get("source_attributes"):
            PipelineConfigService._validate_source_attributes(payload["source_attributes"])

        updates = {}
        for key, value in payload.items():
            if value is None or key == "updated_by":
                continue
            if key in {"source_attributes", "target_attributes", "tags"}:
                value = json.dumps(value)
            updates[key] = value
        updates["updated_by"] = payload.get("updated_by", "system")
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        PipelineConfigRepository.update(table_config_id, updates)
        return {"updated": True, "table_config_id": table_config_id}

    @staticmethod
    def soft_delete(table_config_id: int, actor: str) -> None:
        row = PipelineConfigRepository.get(table_config_id)
        if not row:
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        PipelineConfigRepository.soft_delete(table_config_id, actor)

    @staticmethod
    def bulk_create(payloads: list[dict]):
        created = 0
        failed = 0
        errors = []
        for idx, payload in enumerate(payloads):
            try:
                PipelineConfigService.create(payload)
                created += 1
            except (HTTPException, ValueError, TypeError):
                failed += 1
                errors.append({"index": idx, "error_code": "DB_ERROR", "message": "Failed to create pipeline config"})
        return {"created_count": created, "failed_count": failed, "errors": errors}

    @staticmethod
    def get_watermark(table_config_id: int):
        if not PipelineConfigRepository.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        row = PipelineConfigRepository.get_watermark(table_config_id)
        if not row:
            return None
        return {
            "watermark_id": row["watermark_id"],
            "table_config_id": row["table_config_id"],
            "watermark_column": row["watermark_column"],
            "watermark_type": row["watermark_type"],
            "last_value": row["last_value"],
            "last_run_id": row["last_run_id"],
            "env_type": row["env_type"],
        }

    @staticmethod
    def upsert_watermark(table_config_id: int, payload: dict):
        if not PipelineConfigRepository.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        row = PipelineConfigRepository.upsert_watermark(table_config_id, payload)
        return {
            "watermark_id": row["watermark_id"],
            "table_config_id": row["table_config_id"],
            "watermark_column": row["watermark_column"],
            "watermark_type": row["watermark_type"],
            "last_value": row["last_value"],
            "last_run_id": row["last_run_id"],
            "env_type": row["env_type"],
        }

    @staticmethod
    def get_pii(table_config_id: int):
        if not PipelineConfigRepository.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        rows = PipelineConfigRepository.list_pii(table_config_id)
        return [
            {
                "pii_id": row["pii_id"],
                "column_name": row["column_name"],
                "pii_category": row["pii_category"],
                "protection_method": row["protection_method"],
                "sensitivity": row["sensitivity"],
                "masking_policy": row.get("masking_policy"),
                "mask_pattern": row.get("mask_pattern"),
                "key_scope": row.get("key_scope"),
                "key_name": row.get("key_name"),
                "hash_algorithm": row.get("hash_algorithm"),
                "uc_tag_applied": bool(row.get("uc_tag_applied", False)),
                "uc_tag_key": row.get("uc_tag_key"),
                "uc_tag_value": row.get("uc_tag_value"),
                "access_tier": row.get("access_tier", "INTERNAL"),
                "allowed_groups": row.get("allowed_groups"),
            }
            for row in rows
        ]

    @staticmethod
    def set_pii(table_config_id: int, env_type: str, actor: str, items: list[dict]):
        if not PipelineConfigRepository.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        rows = PipelineConfigRepository.replace_pii(table_config_id, env_type, actor, items)
        return [{"pii_id": row["pii_id"], "column_name": row["column_name"]} for row in rows]

    @staticmethod
    def add_schema_version(table_config_id: int, payload: dict):
        if not PipelineConfigRepository.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        row = PipelineConfigRepository.add_schema_version(table_config_id, payload)
        return {
            "version_id": row["version_id"],
            "version_number": row["version_number"],
            "column_count": row["column_count"],
            "column_changes_json": json.loads(row["column_changes_json"]),
            "change_type": row["change_type"],
            "detected_by_run_id": row["detected_by_run_id"],
        }

    @staticmethod
    def list_schema_versions(table_config_id: int):
        if not PipelineConfigRepository.get(table_config_id):
            raise_api_error(404, "PIPELINE_CONFIG_NOT_FOUND", "Pipeline config not found")
        rows = PipelineConfigRepository.list_schema_versions(table_config_id)
        return [
            {
                "version_id": row["version_id"],
                "version_number": row["version_number"],
                "column_count": row["column_count"],
                "column_changes_json": json.loads(row["column_changes_json"]),
                "change_type": row["change_type"],
                "detected_by_run_id": row["detected_by_run_id"],
            }
            for row in rows
        ]
