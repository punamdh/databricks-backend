import time
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import get_settings

_PK_COLUMN = {
    "conn_master": "connection_id",
    "connection_details": "connection_details_id",
    "connection_auth": "connection_auth_id",
    "tbl_source_table": "table_config_id",
    "tbl_watermark": "watermark_id",
    "tbl_schema_version": "version_id",
    "tbl_pii_attribute": "pii_id",
    "aud_table_run": "table_run_id",
    "bts_config": "bts_config_id",
}


def generate_id(db: Session, table_name: str) -> int:
    pk_column = _PK_COLUMN.get(table_name)
    if not pk_column:
        raise ValueError(f"Unknown table: {table_name}")
    schema = get_settings().databricks_schema
    result = db.execute(
        text(f"SELECT COALESCE(MAX({pk_column}), 0) + 1 AS next_id FROM {schema}.{table_name}")
    ).fetchone()
    return result[0] if result else 1


def generate_snowflake_id() -> int:
    """
    Generate a Snowflake-style ID (timestamp-based).
    Format: 41 bits for timestamp + 10 bits for machine + 12 bits for sequence
    Simplified version using only timestamp and random bits.
    """
    timestamp = int(time.time() * 1000)  # milliseconds
    # Shift timestamp and add some randomness
    return (timestamp << 22) | (int(time.time() * 1000000) & 0x3FFFFF)
