from __future__ import annotations

import json

from pyspark.sql import functions as F

from app.database.connection import get_spark
from app.repositories.delta_utils import append_rows, bool_value, next_id, now_utc, now_utc_iso, paginate, row_to_dict, table_name, update_rows


class PipelineConfigRepository:
    source_table = table_name("tbl_source_table")
    watermark_table = table_name("tbl_watermark")
    pii_table = table_name("tbl_pii_attribute")
    schema_table = table_name("tbl_schema_version")
    bts_table = table_name("bts_config")
    audit_table = table_name("aud_table_run")

    @staticmethod
    def create(payload: dict) -> dict:
        spark = get_spark()
        row = {**payload}
        append_rows(PipelineConfigRepository.source_table, [row])
        # Fetch the generated table_config_id
        result = spark.table(PipelineConfigRepository.source_table).orderBy(F.col("table_config_id").desc()).limit(1).collect()[0]
        result_dict = result.asDict()
        table_config_id = result_dict["table_config_id"]
        row["table_config_id"] = table_config_id
        return row

    @staticmethod
    def get(table_config_id: int) -> dict | None:
        spark = get_spark()
        rows = (
            spark.table(PipelineConfigRepository.source_table)
            .filter((F.col("table_config_id") == table_config_id) & (F.col("is_active") == bool_value(PipelineConfigRepository.source_table, "is_active", True)))
            .limit(1)
            .collect()
        )
        return rows[0].asDict() if rows else None

    @staticmethod
    def list(page: int, page_size: int, filters: dict):
        spark = get_spark()
        df = spark.table(PipelineConfigRepository.source_table)
        if filters.get("is_active") is not None:
            # Convert int to bool for backward compatibility, then convert to correct type for column
            is_active_val = filters["is_active"]
            if isinstance(is_active_val, int):
                is_active_val = bool(is_active_val)
            # Now convert to the appropriate type for the column (True/False or 1/0)
            is_active_val = bool_value(PipelineConfigRepository.source_table, "is_active", is_active_val)
            df = df.filter(F.col("is_active") == is_active_val)
        if filters.get("env_type"):
            df = df.filter(F.col("env_type") == filters["env_type"])
        if filters.get("connection_source_id"):
            df = df.filter(F.col("connection_source_id") == filters["connection_source_id"])
        if filters.get("config_group"):
            df = df.filter(F.col("config_group") == filters["config_group"])
        if filters.get("load_type"):
            df = df.filter(F.col("load_type") == filters["load_type"])

        return paginate(df, page, page_size, "table_config_id")

    @staticmethod
    def update(table_config_id: int, payload: dict) -> None:
        update_rows(
            PipelineConfigRepository.source_table,
            f"table_config_id = {table_config_id} AND is_active = TRUE",
            payload
        )

    @staticmethod
    def soft_delete(table_config_id: int, actor: str) -> None:
        spark = get_spark()
        now = now_utc_iso()
        update_rows(
            PipelineConfigRepository.source_table,
            f"table_config_id = {table_config_id} AND is_active = TRUE",
            {"is_active": False, "updated_by": actor, "updated_at": now}
        )
        cascade_tables = [
            (PipelineConfigRepository.watermark_table, "table_config_id"),
            (PipelineConfigRepository.schema_table, "table_config_id"),
            (PipelineConfigRepository.pii_table, "table_config_id"),
            (PipelineConfigRepository.audit_table, "table_config_id"),
            (PipelineConfigRepository.bts_table, "source_config_id"),
        ]
        for table, key in cascade_tables:
            update_rows(
                table,
                f"{key} = {table_config_id} AND is_active = TRUE",
                {"is_active": False, "updated_by": actor, "updated_at": now}
            )

    @staticmethod
    def get_watermark(table_config_id: int) -> dict | None:
        spark = get_spark()
        rows = (
            spark.table(PipelineConfigRepository.watermark_table)
            .filter((F.col("table_config_id") == table_config_id) & (F.col("is_active") == bool_value(PipelineConfigRepository.watermark_table, "is_active", True)))
            .orderBy(F.col("watermark_id").desc())
            .limit(1)
            .collect()
        )
        return row_to_dict(rows[0]) if rows else None

    @staticmethod
    def upsert_watermark(table_config_id: int, payload: dict) -> dict:
        spark = get_spark()
        actor = payload.get("updated_by", "system")
        now = now_utc_iso()
        existing = PipelineConfigRepository.get_watermark(table_config_id)
        if existing:
            updates = {**payload, "updated_by": actor, "updated_at": now}
            update_rows(
                PipelineConfigRepository.watermark_table,
                f"watermark_id = {existing['watermark_id']} AND is_active = TRUE",
                updates
            )
            existing.update(payload)
            existing["updated_by"] = actor
            existing["updated_at"] = now
            return existing

        row = {
            "table_config_id": table_config_id,
            "watermark_column": payload["watermark_column"],
            "watermark_type": payload["watermark_type"],
            "last_value": payload.get("last_value"),
            "last_run_id": payload.get("last_run_id"),
            "env_type": payload.get("env_type", "dev"),
            "is_active": True,
            "created_by": payload.get("updated_by", "system"),
            "created_at": now,
            "updated_by": payload.get("updated_by", "system"),
            "updated_at": now,
        }
        append_rows(PipelineConfigRepository.watermark_table, [row])
        # Fetch the generated watermark_id
        result = spark.table(PipelineConfigRepository.watermark_table).orderBy(F.col("watermark_id").desc()).limit(1).collect()[0]
        result_dict = result.asDict()
        watermark_id = result_dict["watermark_id"]
        row["watermark_id"] = watermark_id
        return row

    @staticmethod
    def replace_pii(table_config_id: int, env_type: str, actor: str, items: list[dict]) -> list[dict]:
        spark = get_spark()
        now = now_utc_iso()
        update_rows(
            PipelineConfigRepository.pii_table,
            f"table_config_id = {table_config_id} AND is_active = TRUE",
            {"is_active": False, "updated_by": actor, "updated_at": now}
        )

        if not items:
            return []

        rows = []
        for item in items:
            rows.append(
                {
                    "table_config_id": table_config_id,
                    "column_name": item["column_name"],
                    "pii_category": item["pii_category"],
                    "protection_method": item["protection_method"],
                    "sensitivity": item["sensitivity"],
                    "masking_policy": item.get("masking_policy"),
                    "uc_tag_applied": item.get("uc_tag_applied", 0),
                    "access_tier": item.get("access_tier", "INTERNAL"),
                    "env_type": env_type,
                    "is_active": True,
                    "created_by": actor,
                    "created_at": now,
                    "updated_by": actor,
                    "updated_at": now,
                }
            )
        append_rows(PipelineConfigRepository.pii_table, rows)
        
        # Fetch generated pii_ids
        inserted_rows = (
            spark.table(PipelineConfigRepository.pii_table)
            .filter((F.col("table_config_id") == table_config_id) & (F.col("is_active") == bool_value(PipelineConfigRepository.pii_table, "is_active", True)))
            .orderBy(F.col("pii_id").desc())
            .limit(len(rows))
            .collect()
        )
        return [row_to_dict(row) for row in inserted_rows]

    @staticmethod
    def list_pii(table_config_id: int) -> list[dict]:
        spark = get_spark()
        rows = (
            spark.table(PipelineConfigRepository.pii_table)
            .filter((F.col("table_config_id") == table_config_id) & (F.col("is_active") == bool_value(PipelineConfigRepository.pii_table, "is_active", True)))
            .orderBy(F.col("pii_id").desc())
            .collect()
        )
        return [row_to_dict(row) for row in rows]

    @staticmethod
    def add_schema_version(table_config_id: int, payload: dict) -> dict:
        spark = get_spark()
        now = now_utc_iso()

        if payload.get("version_number") is None:
            result = (
                spark.table(PipelineConfigRepository.schema_table)
                .filter(F.col("table_config_id") == table_config_id)
                .agg(F.max(F.col("version_number")).alias("max_version"))
                .collect()[0]
            )
            result_dict = result.asDict()
            max_version = result_dict.get("max_version")
            payload["version_number"] = int(max_version) + 1 if max_version is not None else 1

        row = {
            "table_config_id": table_config_id,
            "version_number": payload["version_number"],
            "column_count": payload["column_count"],
            "column_changes_json": json.dumps(payload["column_changes_json"]),
            "change_type": payload["change_type"],
            "detected_by_run_id": payload.get("detected_by_run_id"),
            "env_type": payload.get("env_type", "dev"),
            "is_active": 1,
            "created_by": payload.get("created_by", "system"),
            "created_at": now,
            "updated_by": payload.get("created_by", "system"),
            "updated_at": now,
        }
        append_rows(PipelineConfigRepository.schema_table, [row])
        # Fetch the generated version_id
        result = spark.table(PipelineConfigRepository.schema_table).orderBy(F.col("version_id").desc()).limit(1).collect()[0]
        result_dict = result.asDict()
        version_id = result_dict["version_id"]
        row["version_id"] = version_id
        return row

    @staticmethod
    def list_schema_versions(table_config_id: int) -> list[dict]:
        spark = get_spark()
        rows = (
            spark.table(PipelineConfigRepository.schema_table)
            .filter((F.col("table_config_id") == table_config_id) & (F.col("is_active") == bool_value(PipelineConfigRepository.schema_table, "is_active", True)))
            .orderBy(F.col("version_number").desc())
            .collect()
        )
        return [row_to_dict(row) for row in rows]
