from pathlib import Path

from app.database.connection import get_spark
from app.database.schema import get_effective_schema


def init_db() -> None:
    spark = get_spark()
    schema = get_effective_schema()

    # For Databricks Unity Catalog format (catalog.schema), use CREATE SCHEMA
    # For simple schema names, use CREATE DATABASE
    if "." in schema:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    else:
        spark.sql(f"CREATE DATABASE IF NOT EXISTS `{schema}`")

    schema_path = Path(__file__).with_name("schema.sql")
    ddl = schema_path.read_text(encoding="utf-8")
    # Replace the schema reference - note: in Unity Catalog, table references should be catalog.schema.table
    # The SQL file has `dbx_data_platform_poc.ui_metadata`.table_name format
    # We need to replace just the schema part, not add backticks around it
    ddl = ddl.replace("`dbx_data_platform_poc.ui_metadata`.", f"{schema}.")
    for statement in [chunk.strip() for chunk in ddl.split(";") if chunk.strip()]:
        spark.sql(statement)


if __name__ == "__main__":
    init_db()
