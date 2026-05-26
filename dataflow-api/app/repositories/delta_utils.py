from __future__ import annotations

from datetime import datetime, timezone

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from app.database.connection import get_spark
from app.database.schema import get_effective_schema


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def table_name(name: str) -> str:
    schema = get_effective_schema()
    return f"`{schema}`.{name}"


def next_id(table: str, id_column: str) -> int:
    spark = get_spark()
    max_id = spark.table(table).agg(F.max(F.col(id_column)).alias("max_id")).collect()[0]["max_id"]
    return int(max_id or 0) + 1


def append_rows(table: str, rows: list[dict]) -> None:
    if not rows:
        return
    spark = get_spark()
    schema = spark.table(table).schema
    spark.createDataFrame(rows, schema=schema).write.format("delta").mode("append").saveAsTable(table)


def paginate(df: DataFrame, page: int, page_size: int, order_col: str):
    total = df.count()
    start = (page - 1) * page_size
    end = start + page_size
    window = Window.orderBy(F.col(order_col).desc())
    paged = (
        df.withColumn("__row_num", F.row_number().over(window))
        .filter((F.col("__row_num") > start) & (F.col("__row_num") <= end))
        .drop("__row_num")
    )
    return [row.asDict() for row in paged.collect()], total
