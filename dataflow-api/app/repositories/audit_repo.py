from __future__ import annotations

import json

from pyspark.sql import functions as F

from app.database.connection import get_spark
from app.repositories.delta_utils import append_rows, next_id, paginate, row_to_dict, table_name, update_rows


class AuditRepository:
    table = table_name("aud_table_run")

    @staticmethod
    def create(payload: dict) -> dict:
        spark = get_spark()
        row = {**payload}
        for key in ["source_attributes", "target_attributes"]:
            if row.get(key) is not None and not isinstance(row[key], str):
                row[key] = json.dumps(row[key])
        append_rows(AuditRepository.table, [row])
        
        # Fetch the generated table_run_id
        result = spark.table(AuditRepository.table).orderBy(F.col("table_run_id").desc()).limit(1).collect()[0]
        result_dict = result.asDict()
        table_run_id = result_dict["table_run_id"]
        row["table_run_id"] = table_run_id
        
        return row

    @staticmethod
    def get(table_run_id: int) -> dict | None:
        spark = get_spark()
        rows = (
            spark.table(AuditRepository.table)
            .filter((F.col("table_run_id") == table_run_id) & (F.col("is_active") == True))
            .limit(1)
            .collect()
        )
        return row_to_dict(rows[0]) if rows else None

    @staticmethod
    def list(page: int, page_size: int, run_id: str | None, table_config_id: int | None, status: str | None):
        spark = get_spark()
        df = spark.table(AuditRepository.table).filter(F.col("is_active") == True)
        if run_id:
            df = df.filter(F.col("run_id") == run_id)
        if table_config_id:
            df = df.filter(F.col("table_config_id") == table_config_id)
        if status:
            df = df.filter(F.col("status") == status)
        return paginate(df, page, page_size, "table_run_id")

    @staticmethod
    def update(table_run_id: int, payload: dict) -> None:
        update_rows(
            AuditRepository.table,
            f"table_run_id = {table_run_id} AND is_active = TRUE",
            payload
        )
