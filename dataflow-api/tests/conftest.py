import os
import sys
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.connection import get_spark  # noqa: E402
from app.database.schema import get_effective_schema  # noqa: E402
from database.init_db import init_db  # noqa: E402
from main import app  # noqa: E402


TABLES = [
    "conn_master",
    "connection_details",
    "connection_auth",
    "tbl_source_table",
    "tbl_watermark",
    "tbl_schema_version",
    "tbl_pii_attribute",
    "aud_table_run",
    "bts_config",
]


@pytest.fixture(autouse=True)
def reset_tables():
    spark = get_spark()
    schema = get_effective_schema()
    for table in TABLES:
        spark.sql(f"DROP TABLE IF EXISTS `{schema}`.{table}")
    warehouse_db_path = Path.cwd() / "spark-warehouse" / f"{schema}.db"
    if warehouse_db_path.exists():
        shutil.rmtree(warehouse_db_path)
    init_db()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
