# DataFlow API (Databricks Delta Edition)

FastAPI backend for metadata management using **PySpark + Delta Lake** with schema **`dbx_data_platform_poc.ui_metadata`**.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Databricks Connect configuration

Set env vars in `.env`:

```env
DATABRICKS_HOST=https://adb-xxx.azuredatabricks.net
DATABRICKS_TOKEN=your_pat
DATABRICKS_CLUSTER_ID=your_cluster_id
DATABRICKS_PORT=15001
DBX_SCHEMA=dbx_data_platform_poc.ui_metadata
```

If `DATABRICKS_*` values are empty, the app runs on local Spark (`SPARK_MASTER`) for development/testing.

## Delta DDL bootstrap

All PRD data domains are represented as Delta tables in `database/schema.sql`:

- `conn_master`, `connection_details`, `connection_auth`
- `tbl_source_table`, `tbl_watermark`, `tbl_schema_version`, `tbl_pii_attribute`
- `bts_config`
- `aud_table_run`

At startup, `database.init_db` creates the schema and these Delta tables.

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Test

```bash
pytest -q
```

## PRD feature coverage via Delta tables

- Connectors + connection validation endpoints
- Connection CRUD with soft delete + uniqueness checks (`connection_name`, `env_type`)
- Pipeline config CRUD, filtering/pagination, watermark upsert
- PII attribute replace/list and schema-version tracking
- BTS config CRUD + soft delete
- Audit run create/list/update
- Audit fields (`created_by/at`, `updated_by/at`) on all persisted tables
