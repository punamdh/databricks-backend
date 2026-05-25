# 📋 PRODUCT REQUIREMENTS DOCUMENT (PRD)
## DataFlow Pipeline Configuration Platform — Metadata Store V2

**Document Version:** 1.0  
**Date:** 2026-05-25  
**Status:** Ready for Development  
**Owner:** Engineering Team

---

## 1. EXECUTIVE SUMMARY

**Product Name:** DataFlow API  
**Objective:** Build a production-ready REST API backend for the DataFlow pipeline configuration platform that manages data source connections, pipeline configurations, transformation rules, schema versioning, PII classification, and audit logging.

**Key Capabilities:**
- Dynamic connector field management for 12+ data source types (RDBMS, cloud storage, APIs)
- Complete lifecycle management of source-to-bronze (ingestion) pipelines
- Bronze-to-silver (transformation) configuration
- Watermark tracking for incremental loads
- PII attribute classification and protection policy enforcement
- Comprehensive audit logging and run tracking
- Multi-environment support (dev/qa/prod)

**Tech Stack:**
- **Language:** Python 3.12
- **Framework:** FastAPI
- **Database:** SQLite (with SQLAlchemy ORM)
- **Validation:** Pydantic v2
- **Server:** Uvicorn (ASGI)
- **Testing:** pytest + httpx

---

## 2. PROBLEM STATEMENT

### Current State
Data engineering teams managing multi-source ETL pipelines lack a centralized metadata registry that:
- Dynamically supports diverse connector types with connector-specific field validation
- Manages connection credentials securely with environment-specific overrides
- Tracks pipeline ingestion configurations with comprehensive audit history
- Handles schema evolution and data quality rules
- Classifies and protects PII data across pipelines

### Desired State
A REST API that:
- Provides a single source of truth for pipeline metadata
- Enforces schema validation and consistency
- Enables multi-environment deployments (dev/qa/prod)
- Supports both UI-driven and bulk import workflows
- Maintains complete audit trails for compliance
- Allows programmatic access to pipeline configurations

---

## 3. SCOPE & DELIVERABLES

### In Scope
✅ RESTful API with 5 resource domains (Connectors, Connections, Pipeline Configs, BTS Configs, Audit)  
✅ SQLite database with 9 core tables + indexes  
✅ Dynamic connector registry with 12 connector types and 5 auth methods  
✅ Transactional CRUD operations with soft-delete pattern  
✅ Pagination, filtering, and search capabilities  
✅ PII attribute classification (6 categories, 4 protection methods)  
✅ Watermark management for incremental loads  
✅ Schema versioning with change tracking  
✅ Comprehensive audit logging (per-table run records)  
✅ Unit test suite with in-memory database  
✅ Docker/deployment-ready (with requirements.txt, env templates)  
✅ OpenAPI documentation (auto-generated via FastAPI)

### Out of Scope
❌ Actual credential encryption (references keyvault/secret manager paths)  
❌ Real database driver connectivity testing (mocked for non-SQLite)  
❌ Data quality rule execution (rules stored, not executed)  
❌ Transformation orchestration/execution  
❌ UI implementation (API only)  
❌ Production secrets management (assumes external vault)

---

## 4. REQUIREMENTS

### 4.1 Functional Requirements

#### 4.1.1 Connector Metadata Management
| Req ID | Description | Priority | Acceptance Criteria |
|--------|-------------|----------|---------------------|
| F-1.1 | Retrieve list of all supported connectors with auth type options | MUST | Returns 12 connector types (mssql, postgres, mysql, oracle, snowflake, bigquery, redshift, sqlite, s3, gcs, azure-blob, sftp, local) |
| F-1.2 | Get dynamic field schema for connector + auth combo | MUST | Returns base_fields + auth_fields with required flag, type, placeholder for each field |
| F-1.3 | Validate connector type against registry | MUST | Reject invalid connector_type with INVALID_CONNECTOR_TYPE error (400) |
| F-1.4 | Validate auth type for given connector | MUST | Reject unsupported auth type with INVALID_AUTH_TYPE error (400) |

#### 4.1.2 Connection Management
| Req ID | Description | Priority | Acceptance Criteria |
|--------|-------------|----------|---------------------|
| F-2.1 | Create connection with atomic transaction | MUST | Inserts conn_master + connection_details + connection_auth in single transaction; rolls back all on failure |
| F-2.2 | Enforce connection_name + env_type uniqueness | MUST | Rejects duplicate with DUPLICATE_CONNECTION_NAME error (409) |
| F-2.3 | List connections with pagination | MUST | Returns paginated results (page, page_size, total, total_pages); defaults to page=1, page_size=20 |
| F-2.4 | Filter connections by env_type, connection_type, is_target, is_active | MUST | Returns filtered list matching all criteria |
| F-2.5 | Search connections by name/domain | MUST | Substring search on connection_name + connection_domain_name |
| F-2.6 | Get full connection detail with all properties | MUST | Returns connection_details and connection_auth arrays nested in response |
| F-2.7 | Update connection (replace details + auth) | MUST | Soft-deletes old rows, inserts new ones, maintains audit trail (updated_by, updated_at) |
| F-2.8 | Soft-delete connection | MUST | Sets is_active=0 on conn_master + all child rows; no hard delete |
| F-2.9 | Test connection | MUST | For SQLite: checks file existence; for others: returns mock success; response includes latency_ms |

#### 4.1.3 Pipeline Configuration Management (Source-to-Bronze)
| Req ID | Description | Priority | Acceptance Criteria |
|--------|-------------|----------|---------------------|
| F-3.1 | Create pipeline config (table load config) | MUST | Inserts tbl_source_table + optional watermark; validates source attrs + target attrs |
| F-3.2 | Validate source attributes (DB vs file) | MUST | For DB: requires schema + table; for file: requires file_path + file_type; rejects invalid with MISSING_REQUIRED_FIELD (422) |
| F-3.3 | List pipeline configs with pagination + filters | MUST | Filter by env_type, connection_id, config_group, load_type; paginated output |
| F-3.4 | Get full pipeline config detail | MUST | Returns source_attributes + target_attributes as parsed JSON objects |
| F-3.5 | Update pipeline config | MUST | Replaces source + target attributes, updates audit fields |
| F-3.6 | Soft-delete pipeline config | MUST | Sets is_active=0 on tbl_source_table + cascades to watermark, schema_versions, pii_attributes |
| F-3.7 | Upsert watermark | MUST | Creates or updates tbl_watermark; supports timestamp, integer, hashkey types |
| F-3.8 | Get/list watermarks for config | MUST | Returns watermark details including last_value, last_run_id |
| F-3.9 | Batch create pipeline configs | MUST | Accepts array of configs; returns created count, failed count, and error details |
| F-3.10 | PII attribute management | MUST | Add/replace PII attributes per column; store category, protection_method, sensitivity, masking_policy |
| F-3.11 | Get PII attributes for config | MUST | Returns all PII records for given table_config_id |
| F-3.12 | Schema version tracking | MUST | Append-only log; tracks column_count, added/removed/modified columns, change_type (additive/deletion) |

#### 4.1.4 Bronze-to-Silver Configuration
| Req ID | Description | Priority | Acceptance Criteria |
|--------|-------------|----------|---------------------|
| F-4.1 | Create BTS config | MUST | Inserts bts_config with silver_layout, dq_rules, std_rules, transformation_yaml |
| F-4.2 | List BTS configs (paginated) | MUST | Filter by env_type, dataset_name; returns paginated results |
| F-4.3 | Get BTS config detail | MUST | Returns all config fields including rules and transformation YAML |
| F-4.4 | Update BTS config | MUST | Replaces rules and YAML; maintains audit trail |
| F-4.5 | Soft-delete BTS config | MUST | Sets is_active=0 |

#### 4.1.5 Audit Logging
| Req ID | Description | Priority | Acceptance Criteria |
|--------|-------------|----------|---------------------|
| F-5.1 | Create audit run record | MUST | Inserts aud_table_run; captures start_time, source attrs, target attrs, batch_id |
| F-5.2 | Update audit run on completion | MUST | Sets end_time, elapsed_seconds, rows_read, rows_written, watermark_end, status, error_details |
| F-5.3 | List audit runs with filters | MUST | Filter by run_id, table_config_id, status (running/succeeded/failed); pagination |
| F-5.4 | Get audit run detail | MUST | Returns full run record including error message + type |

### 4.2 Non-Functional Requirements

| Req ID | Category | Description | Acceptance Criteria |
|--------|----------|-------------|---------------------|
| NF-1 | Performance | All GET list endpoints must complete in <500ms | Indexed queries on connection_id, env_type, is_active |
| NF-2 | Reliability | All transactional operations must rollback atomically on failure | Use SQLAlchemy session.begin() for multi-table inserts |
| NF-3 | Compatibility | Database must support SQLite 3.40+ | Schema uses standard SQL + PRAGMA foreign_keys |
| NF-4 | Compliance | Soft-delete all records, never hard-delete | is_active flag mandatory on all tables |
| NF-5 | Documentation | Auto-generated OpenAPI spec (Swagger) | FastAPI /docs endpoint functional |
| NF-6 | Testing | Minimum 80% code coverage for core services | pytest with in-memory SQLite DB |
| NF-7 | Maintainability | All responses follow standard envelope format | {"status": ..., "data": ...} or {"status": "error", "error_code": ..., "message": ...} |
| NF-8 | Multi-tenancy | Support multiple environments (dev/qa/prod) | env_type field on all config tables |
| NF-9 | Audit Trail | Maintain created_by, created_at, updated_by, updated_at on all tables | Automatic via SQLAlchemy defaults + trigger on update |

---

## 5. DATABASE DESIGN

### 5.1 Entity-Relationship Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE ENTITIES                            │
├──────────────────────────────────────────────────────────��──┤
│ conn_master ────→ connection_details (1:N)                 │
│            ────→ connection_auth (1:N)                     │
│                                                             │
│ tbl_source_table ─→ tbl_watermark (1:1)                   │
│                  ─→ tbl_schema_version (1:N)              │
│                  ─→ tbl_pii_attribute (1:N)               │
│                  ─→ aud_table_run (1:N)                   │
│                  ←─ bts_config (optional)                 │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Core Tables

#### Table 1: conn_master
| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| connection_id | INT | PK, AUTOINCREMENT | Unique identifier |
| connection_name | TEXT | NOT NULL | User-friendly name |
| connection_type | TEXT | NOT NULL | Connector type (mssql, postgres, etc.) |
| connection_domain_name | TEXT | NOT NULL | Business domain (HR, SALES, ORDERS) |
| is_target | INT | NOT NULL, DEFAULT 0 | 0=source, 1=target |
| env_type | TEXT | NOT NULL | dev, qa, prod |
| is_active | INT | NOT NULL, DEFAULT 1 | Soft-delete flag |
| created_by, created_at, updated_by, updated_at | TEXT | NOT NULL | Audit trail |
| **Constraint** | | UNIQUE(connection_name, env_type) | Prevent duplicate names per env |

#### Table 2: connection_details (EAV pattern)
| Column | Type | Purpose |
|--------|------|---------|
| connection_details_id | INT | PK |
| connection_id | INT | FK → conn_master |
| connection_property_id | INT | Sequential ID for property |
| connection_property | TEXT | host, port, database, schema, bucket_name, etc. |
| connection_property_value | TEXT | The actual value |
| env_type | TEXT | Environment override |
| is_active | INT | Soft-delete |
| Audit fields | | created_by, created_at, updated_by, updated_at |

#### Table 3: connection_auth (EAV pattern)
| Column | Type | Purpose |
|--------|------|---------|
| connection_auth_id | INT | PK |
| connection_id | INT | FK → conn_master |
| auth_property_id | INT | Sequential ID |
| auth_property | TEXT | username, password_key, client_id, private_key, etc. |
| auth_property_value | TEXT | Secret scope ref (kv://...) or non-secret value |
| env_type | TEXT | Environment |
| is_active | INT | Soft-delete |
| Audit fields | | created_by, created_at, updated_by, updated_at |

#### Table 4: tbl_source_table (Pipeline Config)
| Column | Type | Purpose |
|--------|------|---------|
| table_config_id | INT | PK |
| connection_source_id | INT | FK → conn_master |
| connection_domain_name | TEXT | Domain context |
| config_group | TEXT | Logical grouping (marketing_pipelines) |
| source_attributes | TEXT | JSON: {schema, table, query, file_path, file_type, delimiter, has_header} |
| target_attributes | TEXT | JSON: {catalog, schema, table} |
| load_type | TEXT | full, incremental, cdc, api, file_autoloader |
| natural_key_columns | TEXT | Comma-separated |
| hash_key_column | TEXT | Column name for row hashing |
| partition_columns | TEXT | Comma-separated |
| watermark_enabled | INT | 0 or 1 |
| pii_scan_enabled | INT | 0 or 1 |
| fail_mode | TEXT | halt, skip, quarantine |
| retry_count | INT | Default 0 |
| ingestion_frequency | TEXT | daily, weekly, monthly, adhoc |
| tags | TEXT | JSON array: ["tag1","tag2"] |
| env_type, is_active | TEXT, INT | Environment & soft-delete |
| Audit fields | | created_by, created_at, updated_by, updated_at |

#### Table 5: tbl_watermark
| Column | Type | Purpose |
|--------|------|---------|
| watermark_id | INT | PK |
| table_config_id | INT | FK → tbl_source_table |
| watermark_column | TEXT | Column to track |
| watermark_type | TEXT | timestamp, integer, hashkey |
| last_value | TEXT | Last extracted high-water mark |
| last_run_id | TEXT | Associated run identifier |
| env_type, is_active | TEXT, INT | Environment & soft-delete |
| Audit fields | | created_by, created_at, updated_by, updated_at |

#### Table 6: tbl_schema_version (Append-only)
| Column | Type | Purpose |
|--------|------|---------|
| version_id | INT | PK |
| table_config_id | INT | FK → tbl_source_table |
| version_number | INT | Incremental version |
| column_count | INT | Count of columns detected |
| column_changes_json | TEXT | JSON: {added: [...], removed: [...], type_changed: [...]} |
| change_type | TEXT | additive, deletion |
| detected_by_run_id | TEXT | Which run detected it |
| env_type, is_active | TEXT, INT | Environment & soft-delete |
| Audit fields | | created_by, created_at, updated_by, updated_at |

#### Table 7: tbl_pii_attribute
| Column | Type | Purpose |
|--------|------|---------|
| pii_id | INT | PK |
| table_config_id | INT | FK → tbl_source_table |
| column_name | TEXT | Column being classified |
| pii_category | TEXT | email, phone, full_name, national_id, financial, health |
| protection_method | TEXT | ENCRYPT, MASK, PSEUDONYMIZE, REDACT |
| sensitivity | TEXT | PII, PCI, PHI, CONFIDENTIAL, PUBLIC |
| masking_policy | TEXT | Specific masking rule |
| uc_tag_applied | INT | 0 or 1 (Unity Catalog tag) |
| access_tier | TEXT | PUBLIC, INTERNAL, RESTRICTED, HIGHLY_RESTRICTED |
| env_type, is_active | TEXT, INT | Environment & soft-delete |
| Audit fields | | created_by, created_at, updated_by, updated_at |

#### Table 8: aud_table_run
| Column | Type | Purpose |
|--------|------|---------|
| table_run_id | INT | PK |
| run_id | TEXT | Pipeline run identifier |
| table_config_id | INT | FK → tbl_source_table |
| connection_source_id | INT | FK → conn_master |
| source_attributes | TEXT | JSON snapshot at run time |
| target_attributes | TEXT | JSON snapshot at run time |
| batch_id | TEXT | Batch identifier |
| load_type | TEXT | Load type used |
| start_time, end_time | TEXT | ISO 8601 timestamps |
| elapsed_seconds | INT | Duration |
| rows_read, rows_written | INT | Data movement metrics |
| watermark_start, watermark_end | TEXT | Watermark values |
| status | TEXT | running, succeeded, failed |
| error_message, error_type | TEXT | connection, schema, dq, compute, timeout, unknown |
| env_type, is_active | TEXT, INT | Environment & soft-delete |
| Audit fields | | created_by, created_at, updated_by, updated_at |

#### Table 9: bts_config (Bronze-to-Silver)
| Column | Type | Purpose |
|--------|------|---------|
| bts_config_id | INT | PK |
| dataset_name | TEXT | Silver dataset name |
| source_config_id | INT | FK → tbl_source_table (optional) |
| silver_layout | TEXT | JSON: [{name, type, nullable}, ...] |
| dq_rules | TEXT | JSON: [{rule_name, expression}, ...] |
| std_rules | TEXT | JSON: [{field, rule_type, rule_value}, ...] |
| transformation_yaml | TEXT | YAML transformation content |
| tags | TEXT | JSON array |
| env_type, is_active | TEXT, INT | Environment & soft-delete |
| Audit fields | | created_by, created_at, updated_by, updated_at |

### 5.3 Indexes

```sql
CREATE INDEX idx_conn_details_conn   ON connection_details(connection_id);
CREATE INDEX idx_conn_auth_conn      ON connection_auth(connection_id);
CREATE INDEX idx_src_table_conn      ON tbl_source_table(connection_source_id);
CREATE INDEX idx_src_table_env       ON tbl_source_table(env_type, is_active);
CREATE INDEX idx_watermark_cfg       ON tbl_watermark(table_config_id);
CREATE INDEX idx_schema_ver_cfg      ON tbl_schema_version(table_config_id);
CREATE INDEX idx_pii_cfg             ON tbl_pii_attribute(table_config_id);
CREATE INDEX idx_aud_run_cfg         ON aud_table_run(table_config_id);
CREATE INDEX idx_aud_run_id          ON aud_table_run(run_id);
```

---

## 6. CONNECTOR REGISTRY

### 6.1 Connector Types & Fields

| Connector | Type | Base Fields | Auth Methods | Notes |
|-----------|------|------------|--------------|-------|
| MSSQL | mssql | host*, port(1433), database*, schema, odbc_driver | basic, kerberos, oauth | Windows/SQL auth |
| PostgreSQL | postgres | host*, port(5432), database*, schema | basic, iam | IAM auth for RDS |
| MySQL | mysql | host*, port(3306), database* | basic | Standard port 3306 |
| Oracle | oracle | host*, port(1521), service_name*, schema | basic, kerberos | TNS or direct connect |
| Snowflake | snowflake | account_identifier*, warehouse*, database*, schema, role | basic, oauth, key | Cloud warehouse |
| BigQuery | bigquery | project_id*, dataset, location | iam, oauth, key | GCP native |
| Redshift | redshift | cluster_endpoint*, port(5439), database*, schema | basic, iam | AWS data warehouse |
| SQLite | sqlite | db_file_path* | none | Local embedded DB |
| S3 | s3 | bucket_name*, region*, path_prefix | iam, key | AWS object storage |
| GCS | gcs | bucket_name*, project_id*, path_prefix | iam, key | GCP object storage |
| Azure Blob | azure-blob | storage_account_name*, container_name*, blob_path_prefix | key, oauth | Azure object storage |
| SFTP | sftp | host*, port(22), remote_path | basic, key | SSH file protocol |
| Local | local | base_path* | none | Local filesystem |

**Legend:** `*` = required field

### 6.2 Auth Methods

| Auth Type | Connectors | Properties |
|-----------|-----------|-----------|
| **basic** | mssql, postgres, mysql, oracle, snowflake, redshift, sftp | username*, password* |
| **kerberos** | mssql, oracle | principal*, keytab_path* |
| **oauth** | mssql, snowflake, bigquery, azure-blob | client_id*, client_secret*, token_url* |
| **iam** | postgres, bigquery, redshift, s3, gcs | iam_credentials |
| **key** | snowflake, bigquery, s3, gcs, azure-blob, sftp | api_key / private_key / access_key |

---

## 7. API SPECIFICATION

### 7.1 Standard Response Envelope

**Success Response (2xx):**
```json
{
  "status": "success",
  "data": { ... },
  "pagination": { "page": 1, "page_size": 20, "total": 100, "total_pages": 5 }
}
```

**Error Response (4xx, 5xx):**
```json
{
  "status": "error",
  "error_code": "ERROR_CODE_NAME",
  "message": "Human-readable error message",
  "details": { ... }
}
```

### 7.2 Connector Metadata Endpoints

#### GET /api/v1/connectors
Retrieve metadata for all supported connectors

#### GET /api/v1/connectors/{connector_key}/fields
Get dynamic field schema for connector + auth combo

**Query Params:** `auth_type` (optional)

### 7.3 Connection Management Endpoints

#### POST /api/v1/connections
Create a new connection with atomic transaction

#### GET /api/v1/connections
List connections with pagination and filtering

#### GET /api/v1/connections/{id}
Retrieve full connection details

#### PUT /api/v1/connections/{id}
Update connection (replace details + auth)

#### DELETE /api/v1/connections/{id}
Soft-delete connection

#### POST /api/v1/connections/{id}/test
Test connectivity

### 7.4 Pipeline Configuration Endpoints

#### POST /api/v1/pipeline-configs
Create pipeline configuration

#### GET /api/v1/pipeline-configs
List pipeline configs

#### GET /api/v1/pipeline-configs/{id}
Get pipeline config detail

#### PUT /api/v1/pipeline-configs/{id}
Update pipeline config

#### DELETE /api/v1/pipeline-configs/{id}
Soft-delete config

#### POST /api/v1/pipeline-configs/bulk
Batch create pipeline configs

#### GET /api/v1/pipeline-configs/{id}/watermark
Get watermark for config

#### PUT /api/v1/pipeline-configs/{id}/watermark
Upsert watermark

#### GET /api/v1/pipeline-configs/{id}/pii
Get PII attributes

#### POST /api/v1/pipeline-configs/{id}/pii
Add/replace PII attributes

#### GET /api/v1/pipeline-configs/{id}/schema-versions
List schema versions

#### POST /api/v1/pipeline-configs/{id}/schema-versions
Add new schema version

### 7.5 BTS Configuration Endpoints

#### POST /api/v1/bts-configs
Create Bronze-to-Silver config

#### GET /api/v1/bts-configs
List BTS configs

#### GET /api/v1/bts-configs/{id}
Get BTS config detail

#### PUT /api/v1/bts-configs/{id}
Update BTS config

#### DELETE /api/v1/bts-configs/{id}
Soft-delete BTS config

### 7.6 Audit Endpoints

#### POST /api/v1/audit/runs
Create audit run record

#### GET /api/v1/audit/runs
List audit runs

#### GET /api/v1/audit/runs/{table_run_id}
Get single run detail

#### PATCH /api/v1/audit/runs/{table_run_id}
Update run on completion

---

## 8. UI INTEGRATION POINTS

### 8.1 Page → API Mapping

| UI Page | Key Endpoints |
|---------|---------------|
| Connectors → View | GET /api/v1/connectors |
| Connectors → Create | GET /api/v1/connectors/{key}/fields, POST /api/v1/connections |
| Source to Bronze → Create | GET /api/v1/connections, POST /api/v1/pipeline-configs |
| Source to Bronze → View | GET /api/v1/pipeline-configs |
| Bronze to Silver → Create | POST /api/v1/bts-configs |
| Bronze to Silver → View | GET /api/v1/bts-configs |

### 8.2 Create Pipeline Config Wizard (8 Steps)

1. **Basics** → config_group name
2. **Source Definition** → connection, schema/table or file path
3. **Load Strategy** → load_type, watermark details
4. **Destination** → target catalog, schema, table
5. **Execution** → fail_mode, retry_count, env_type
6. **PII Scan** → Enable/disable, column classifications
7. **Other Settings** → is_active flag, tags
8. **Review** → Summary and submit

---

## 9. SECURITY & VALIDATION

### 9.1 Input Validation

- **Connector Type:** Must exist in CONNECTOR_REGISTRY
- **Auth Type:** Must be supported for given connector
- **Required Fields:** Must be present and non-empty
- **Source Attributes:** Validate DB vs file requirements
- **Environment:** Must be one of: dev, qa, prod
- **Load Type:** Must be one of: full, incremental, cdc, api, file_autoloader

### 9.2 Sensitive Data Handling

- **Secrets:** Store as vault references (e.g., `kv://vault/secret-name`)
- **Log Redaction:** Omit auth values from logs
- **Database:** SQLite (no encryption at rest)
- **HTTPS:** Enforcement at API gateway level

### 9.3 Uniqueness Constraints

- `connection_name + env_type` must be unique
- `table_config_id` unique per table
- `bts_config_id` unique per config

---

## 10. ERROR HANDLING

### 10.1 Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| INVALID_CONNECTOR_TYPE | 400 | Connector type not in registry |
| INVALID_AUTH_TYPE | 400 | Auth type not supported |
| MISSING_REQUIRED_FIELD | 422 | Required field missing |
| DUPLICATE_CONNECTION_NAME | 409 | Name + env already exists |
| CONNECTION_NOT_FOUND | 404 | Connection not found |
| PIPELINE_CONFIG_NOT_FOUND | 404 | Config not found |
| INVALID_SOURCE_ATTRIBUTES | 422 | Invalid source attributes |
| INVALID_LOAD_TYPE | 422 | Load type not recognized |
| DB_ERROR | 500 | Database operation failed |

---

## 11. TESTING STRATEGY

### 11.1 Test Coverage Goals

- **Unit Tests:** 80%+ coverage of service layer
- **Integration Tests:** End-to-end CRUD
- **Edge Cases:** Nulls, duplicates, constraints, malformed JSON

### 11.2 Test Database

- **Type:** SQLite in-memory (`:memory:`)
- **Isolation:** Fresh DB per test
- **Fixtures:** conftest.py provides DB session, test client, seed functions

### 11.3 Key Test Scenarios

**Connections:**
- Create valid connection
- Reject duplicates (409)
- List with pagination + filters
- Get full detail
- Update connection
- Soft-delete
- Test connectivity

**Pipeline Configs:**
- Create with watermark
- Reject invalid attributes (422)
- Batch create
- Upsert watermark
- Add PII attributes
- Track schema versions
- Soft-delete with cascade

**Audit:**
- Create run record
- Update run completion
- Query by status/config

---

## 12. DEPLOYMENT & OPERATIONS

### 12.1 Deployment Artifact

- **Python Version:** 3.12
- **Package Manager:** pip
- **ASGI Server:** Uvicorn
- **Database:** SQLite file

### 12.2 Environment Configuration

```
DB_PATH=./dataflow.db
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000
APP_RELOAD=false
LOG_LEVEL=INFO
```

### 12.3 Running the Application

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 13. DELIVERABLES CHECKLIST

### Code Files
- [ ] `main.py` — FastAPI app
- [ ] `requirements.txt` — Dependencies
- [ ] `.env.example` — Environment template
- [ ] `README.md` — Setup instructions

### Database
- [ ] `database/schema.sql` — DDL with indexes
- [ ] `database/init_db.py` — DB initialization

### Application Structure
- [ ] `app/config/settings.py` — Settings
- [ ] `app/config/connectors.py` — CONNECTOR_REGISTRY
- [ ] `app/database/connection.py` — DB connection
- [ ] `app/models/orm.py` — ORM models
- [ ] `app/schemas/*.py` — Pydantic schemas
- [ ] `app/repositories/*.py` — DB queries
- [ ] `app/services/*.py` — Business logic
- [ ] `app/routers/*.py` — API endpoints

### Testing
- [ ] `tests/conftest.py` — Fixtures
- [ ] `tests/test_connections.py` — Connection tests
- [ ] `tests/test_pipeline_configs.py` — Config tests
- [ ] `tests/test_connectors.py` — Connector tests

---

## 14. ACCEPTANCE CRITERIA

### Functional Acceptance

✅ All 22+ API endpoints implemented and tested  
✅ CONNECTOR_REGISTRY with 12 connectors + 5 auth methods  
✅ Transactional CRUD with atomic rollback  
✅ Soft-delete pattern on all tables  
✅ Pagination and filtering  
✅ Unique constraint enforcement  
✅ Watermark upsert logic  
✅ PII classification  
✅ Schema versioning  
✅ Audit logging  

### Non-Functional Acceptance

✅ 80%+ test coverage  
✅ GET list queries <500ms  
✅ Standard error envelope  
✅ SQLite schema compliance  
✅ OpenAPI docs  
✅ README with setup/testing  
✅ Pinned dependencies  
✅ Pydantic ConfigDict compliance  
✅ SQLAlchemy ORM mapping  

---

## 15. REVISION HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-25 | Engineering | Initial PRD |

---

**End of PRD**
