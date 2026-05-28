from __future__ import annotations

from pyspark.sql import functions as F

from app.database.connection import get_spark
from app.repositories.delta_utils import append_rows, bool_value, next_id, now_utc_iso, paginate, row_to_dict, table_name, update_rows


class BTSConfigRepository:
    table = table_name("bts_config")

    @staticmethod
    def create(payload: dict) -> dict:
        spark = get_spark()
        row = {**payload}
        append_rows(BTSConfigRepository.table, [row])
        
        # Fetch the generated bts_config_id
        result = spark.table(BTSConfigRepository.table).orderBy(F.col("bts_config_id").desc()).limit(1).collect()[0]
        result_dict = result.asDict()
        bts_config_id = result_dict["bts_config_id"]
        row["bts_config_id"] = bts_config_id
        
        return row

    @staticmethod
    def get(bts_config_id: int) -> dict | None:
        spark = get_spark()
        rows = (
            spark.table(BTSConfigRepository.table)
            .filter((F.col("bts_config_id") == bts_config_id) & (F.col("is_active") == bool_value(BTSConfigRepository.table, "is_active", True)))
            .limit(1)
            .collect()
        )
        return row_to_dict(rows[0]) if rows else None

    @staticmethod
    def list(page: int, page_size: int, env_type: str | None, dataset_name: str | None):
        spark = get_spark()
        df = spark.table(BTSConfigRepository.table).filter(F.col("is_active") == bool_value(BTSConfigRepository.table, "is_active", True))
        if env_type:
            df = df.filter(F.col("env_type") == env_type)
        if dataset_name:
            df = df.filter(F.lower(F.col("dataset_name")).contains(dataset_name.lower()))
        return paginate(df, page, page_size, "bts_config_id")

    @staticmethod
    def update(bts_config_id: int, payload: dict) -> None:
        print(f"[DEBUG] BTSConfigRepository.update called with bts_config_id={bts_config_id}, payload={payload}")
        update_rows(
            BTSConfigRepository.table,
            f"bts_config_id = {bts_config_id} AND is_active = TRUE",
            payload
        )
        print(f"[DEBUG] BTSConfigRepository.update completed")

    @staticmethod
    def soft_delete(bts_config_id: int, actor: str) -> None:
        update_rows(
            BTSConfigRepository.table,
            f"bts_config_id = {bts_config_id} AND is_active = TRUE",
            {"is_active": False, "updated_by": actor, "updated_at": now_utc_iso()}
        )
