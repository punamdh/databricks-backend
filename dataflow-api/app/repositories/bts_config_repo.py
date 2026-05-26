from __future__ import annotations

from delta.tables import DeltaTable
from pyspark.sql import functions as F

from app.database.connection import get_spark
from app.repositories.delta_utils import append_rows, next_id, now_utc_iso, paginate, table_name


class BTSConfigRepository:
    table = table_name("bts_config")

    @staticmethod
    def create(payload: dict) -> dict:
        spark = get_spark()
        row = {"bts_config_id": next_id(BTSConfigRepository.table, "bts_config_id"), **payload}
        append_rows(BTSConfigRepository.table, [row])
        return row

    @staticmethod
    def get(bts_config_id: int) -> dict | None:
        spark = get_spark()
        rows = (
            spark.table(BTSConfigRepository.table)
            .filter((F.col("bts_config_id") == bts_config_id) & (F.col("is_active") == 1))
            .limit(1)
            .collect()
        )
        return rows[0].asDict() if rows else None

    @staticmethod
    def list(page: int, page_size: int, env_type: str | None, dataset_name: str | None):
        spark = get_spark()
        df = spark.table(BTSConfigRepository.table).filter(F.col("is_active") == 1)
        if env_type:
            df = df.filter(F.col("env_type") == env_type)
        if dataset_name:
            df = df.filter(F.lower(F.col("dataset_name")).contains(dataset_name.lower()))
        return paginate(df, page, page_size, "bts_config_id")

    @staticmethod
    def update(bts_config_id: int, payload: dict) -> None:
        spark = get_spark()
        DeltaTable.forName(spark, BTSConfigRepository.table).update(
            condition=(F.col("bts_config_id") == bts_config_id) & (F.col("is_active") == 1),
            set={k: F.lit(v) for k, v in payload.items()},
        )

    @staticmethod
    def soft_delete(bts_config_id: int, actor: str) -> None:
        spark = get_spark()
        DeltaTable.forName(spark, BTSConfigRepository.table).update(
            condition=(F.col("bts_config_id") == bts_config_id) & (F.col("is_active") == 1),
            set={"is_active": F.lit(0), "updated_by": F.lit(actor), "updated_at": F.lit(now_utc_iso())},
        )
