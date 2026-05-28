from __future__ import annotations

from pyspark.sql import functions as F

from app.database.connection import get_spark
from app.repositories.delta_utils import append_rows, row_to_dict, table_name


class STBConfigRepository:
    table_group_table = table_name("table_group_s2b")

    @staticmethod
    def create_table_group(payload: dict) -> dict:
        spark = get_spark()
        append_rows(STBConfigRepository.table_group_table, [payload])
        result = (
            spark.table(STBConfigRepository.table_group_table)
            .orderBy(F.col("table_group_id").desc())
            .limit(1)
            .collect()[0]
        )
        return row_to_dict(result)

    @staticmethod
    def get_table_group(table_group_id: int) -> dict | None:
        spark = get_spark()
        rows = (
            spark.table(STBConfigRepository.table_group_table)
            .filter(F.col("table_group_id") == table_group_id)
            .limit(1)
            .collect()
        )
        return row_to_dict(rows[0]) if rows else None
