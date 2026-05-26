from __future__ import annotations

import json

from delta.tables import DeltaTable
from pyspark.sql import functions as F

from app.database.connection import get_spark
from app.repositories.delta_utils import append_rows, next_id, now_utc_iso, paginate, table_name


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
        table_config_id = next_id(PipelineConfigRepository.source_table, "table_config_id")
        row = {"table_config_id": table_config_id, **payload}
        append_rows(PipelineConfigRepository.source_table, [row])
        return row

    @staticmethod
    def get(table_config_id: int) -> dict | None:
        spark = get_spark()
        rows = (
            spark.table(PipelineConfigRepository.source_table)
            .filter((F.col("table_config_id") == table_config_id) & (F.col("is_active") == 1))
            .limit(1)
            .collect()
        )
        return rows[0].asDict() if rows else None

    @staticmethod
    def list(page: int, page_size: int, filters: dict):
        spark = get_spark()
        df = spark.table(PipelineConfigRepository.source_table)
        if filters.get("is_active") is not None:
            df = df.filter(F.col("is_active") == filters["is_active"])
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
        spark = get_spark()
        update_set = {k: F.lit(v) for k, v in payload.items()}
        DeltaTable.forName(spark, PipelineConfigRepository.source_table).update(
            condition=(F.col("table_config_id") == table_config_id) & (F.col("is_active") == 1),
            set=update_set,
        )

    @staticmethod
    def soft_delete(table_config_id: int, actor: str) -> None:
        spark = get_spark()
        now = now_utc_iso()
        DeltaTable.forName(spark, PipelineConfigRepository.source_table).update(
            condition=(F.col("table_config_id") == table_config_id) & (F.col("is_active") == 1),
            set={"is_active": F.lit(0), "updated_by": F.lit(actor), "updated_at": F.lit(now)},
        )
        cascade_tables = [
            (PipelineConfigRepository.watermark_table, "table_config_id"),
            (PipelineConfigRepository.schema_table, "table_config_id"),
            (PipelineConfigRepository.pii_table, "table_config_id"),
            (PipelineConfigRepository.audit_table, "table_config_id"),
            (PipelineConfigRepository.bts_table, "source_config_id"),
        ]
        for table, key in cascade_tables:
            DeltaTable.forName(spark, table).update(
                condition=(F.col(key) == table_config_id) & (F.col("is_active") == 1),
                set={"is_active": F.lit(0), "updated_by": F.lit(actor), "updated_at": F.lit(now)},
            )

    @staticmethod
    def get_watermark(table_config_id: int) -> dict | None:
        spark = get_spark()
        rows = (
            spark.table(PipelineConfigRepository.watermark_table)
            .filter((F.col("table_config_id") == table_config_id) & (F.col("is_active") == 1))
            .orderBy(F.col("watermark_id").desc())
            .limit(1)
            .collect()
        )
        return rows[0].asDict() if rows else None

    @staticmethod
    def upsert_watermark(table_config_id: int, payload: dict) -> dict:
        spark = get_spark()
        actor = payload.get("updated_by", "system")
        now = now_utc_iso()
        existing = PipelineConfigRepository.get_watermark(table_config_id)
        if existing:
            update_values = {k: F.lit(v) for k, v in payload.items()}
            update_values["updated_by"] = F.lit(actor)
            update_values["updated_at"] = F.lit(now)
            DeltaTable.forName(spark, PipelineConfigRepository.watermark_table).update(
                condition=(F.col("watermark_id") == existing["watermark_id"]) & (F.col("is_active") == 1),
                set=update_values,
            )
            existing.update(payload)
            existing["updated_by"] = actor
            existing["updated_at"] = now
            return existing

        watermark_id = next_id(PipelineConfigRepository.watermark_table, "watermark_id")
        row = {
            "watermark_id": watermark_id,
            "table_config_id": table_config_id,
            "watermark_column": payload["watermark_column"],
            "watermark_type": payload["watermark_type"],
            "last_value": payload.get("last_value"),
            "last_run_id": payload.get("last_run_id"),
            "env_type": payload.get("env_type", "dev"),
            "is_active": 1,
            "created_by": payload.get("updated_by", "system"),
            "created_at": now,
            "updated_by": payload.get("updated_by", "system"),
            "updated_at": now,
        }
        append_rows(PipelineConfigRepository.watermark_table, [row])
        return row

    @staticmethod
    def replace_pii(table_config_id: int, env_type: str, actor: str, items: list[dict]) -> list[dict]:
        spark = get_spark()
        now = now_utc_iso()
        DeltaTable.forName(spark, PipelineConfigRepository.pii_table).update(
            condition=(F.col("table_config_id") == table_config_id) & (F.col("is_active") == 1),
            set={"is_active": F.lit(0), "updated_by": F.lit(actor), "updated_at": F.lit(now)},
        )

        if not items:
            return []

        pii_id = next_id(PipelineConfigRepository.pii_table, "pii_id")
        rows = []
        for item in items:
            rows.append(
                {
                    "pii_id": pii_id,
                    "table_config_id": table_config_id,
                    "column_name": item["column_name"],
                    "pii_category": item["pii_category"],
                    "protection_method": item["protection_method"],
                    "sensitivity": item["sensitivity"],
                    "masking_policy": item.get("masking_policy"),
                    "uc_tag_applied": item.get("uc_tag_applied", 0),
                    "access_tier": item.get("access_tier", "INTERNAL"),
                    "env_type": env_type,
                    "is_active": 1,
                    "created_by": actor,
                    "created_at": now,
                    "updated_by": actor,
                    "updated_at": now,
                }
            )
            pii_id += 1
        append_rows(PipelineConfigRepository.pii_table, rows)
        return rows

    @staticmethod
    def list_pii(table_config_id: int) -> list[dict]:
        spark = get_spark()
        rows = (
            spark.table(PipelineConfigRepository.pii_table)
            .filter((F.col("table_config_id") == table_config_id) & (F.col("is_active") == 1))
            .orderBy(F.col("pii_id").desc())
            .collect()
        )
        return [row.asDict() for row in rows]

    @staticmethod
    def add_schema_version(table_config_id: int, payload: dict) -> dict:
        spark = get_spark()
        now = now_utc_iso()

        if payload.get("version_number") is None:
            max_version = (
                spark.table(PipelineConfigRepository.schema_table)
                .filter(F.col("table_config_id") == table_config_id)
                .agg(F.max(F.col("version_number")).alias("max_version"))
                .collect()[0]["max_version"]
            )
            payload["version_number"] = int(max_version or 0) + 1

        version_id = next_id(PipelineConfigRepository.schema_table, "version_id")
        row = {
            "version_id": version_id,
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
        return row

    @staticmethod
    def list_schema_versions(table_config_id: int) -> list[dict]:
        spark = get_spark()
        rows = (
            spark.table(PipelineConfigRepository.schema_table)
            .filter((F.col("table_config_id") == table_config_id) & (F.col("is_active") == 1))
            .orderBy(F.col("version_number").desc())
            .collect()
        )
        return [row.asDict() for row in rows]
