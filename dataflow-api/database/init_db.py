from pathlib import Path

from app.database.connection import get_spark
from app.database.schema import get_effective_schema


def init_db() -> None:
    spark = get_spark()
    schema = get_effective_schema()

    spark.sql(f"CREATE DATABASE IF NOT EXISTS `{schema}`")

    schema_path = Path(__file__).with_name("schema.sql")
    ddl = schema_path.read_text(encoding="utf-8").replace("`dbx_data_platform_poc.ui_metadata`", f"`{schema}`")
    for statement in [chunk.strip() for chunk in ddl.split(";") if chunk.strip()]:
        spark.sql(statement)


if __name__ == "__main__":
    init_db()
