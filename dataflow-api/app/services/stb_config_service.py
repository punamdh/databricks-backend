from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories.pipeline_config_repo import PipelineConfigRepository
from app.repositories.stb_config_repo import STBConfigRepository
from app.schemas.common import raise_api_error
from app.services.pipeline_config_service import PipelineConfigService


class STBConfigService:
    @staticmethod
    def create(payload: dict) -> dict:
        actor = payload.get("created_by", "system")
        now = datetime.now(timezone.utc).isoformat()

        # 1. Create the table group
        group_row = STBConfigRepository.create_table_group(
            {"description": payload.get("description")}
        )
        table_group_id = group_row["table_group_id"]

        connection_source_id = payload["connection_source_id"]
        created_configs = []
        errors = []

        for idx, cfg in enumerate(payload.get("config_groups", [])):
            try:
                if cfg["load_type"] not in PipelineConfigService.LOAD_TYPES:
                    raise_api_error(422, "INVALID_LOAD_TYPE", "Load type not supported")
                PipelineConfigService._validate_source_attributes(cfg["source_attributes"])

                pipeline_payload = {
                    "connection_source_id": connection_source_id,
                    "connection_domain_name": cfg["connection_domain_name"],
                    "table_group_id": table_group_id,
                    "source_attributes": json.dumps(cfg["source_attributes"]),
                    "target_attributes": json.dumps(cfg["target_attributes"]),
                    "load_type": cfg["load_type"],
                    "natural_key_columns": cfg.get("natural_key_columns"),
                    "hash_key_column": cfg.get("hash_key_column"),
                    "partition_columns": cfg.get("partition_columns"),
                    "watermark_enabled": cfg.get("watermark_enabled", False),
                    "pii_scan_enabled": cfg.get("pii_scan_enabled", False),
                    "ingestion_frequency": cfg.get("ingestion_frequency", "adhoc"),
                    "tags": json.dumps(cfg.get("tags", [])),
                    "env_type": cfg.get("env_type", "dev"),
                    "is_active": cfg.get("is_active", True),
                    "created_by": actor,
                    "updated_by": payload.get("updated_by", actor),
                    "created_at": now,
                    "updated_at": now,
                }

                row = PipelineConfigRepository.create(pipeline_payload)
                table_config_id = row["table_config_id"]

                # Watermark
                if cfg.get("watermark"):
                    PipelineConfigRepository.upsert_watermark(
                        table_config_id, {**cfg["watermark"], "updated_by": actor}
                    )

                # PII columns
                pii_items = cfg.get("pii_columns", [])
                if pii_items:
                    PipelineConfigRepository.replace_pii(
                        table_config_id, cfg.get("env_type", "dev"), actor, pii_items
                    )

                created_configs.append({
                    "table_config_id": table_config_id,
                    "connection_domain_name": cfg["connection_domain_name"],
                    "load_type": cfg["load_type"],
                    "env_type": cfg.get("env_type", "dev"),
                })

            except (HTTPException, ValueError, TypeError) as exc:
                errors.append({
                    "index": idx,
                    "connection_domain_name": cfg.get("connection_domain_name"),
                    "error": str(exc),
                })

        return {
            "table_group_id": table_group_id,
            "description": payload.get("description"),
            "connection_source_id": connection_source_id,
            "created_count": len(created_configs),
            "failed_count": len(errors),
            "config_groups": created_configs,
            "errors": errors,
        }
