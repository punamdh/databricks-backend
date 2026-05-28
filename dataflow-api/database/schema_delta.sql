-- Databricks Delta Lake Schema for dbx_data_platform_poc.ui_metadata
-- Run these DDL statements in Databricks SQL Warehouse or Notebook

CREATE TABLE IF NOT EXISTS dbx_data_platform_poc.ui_metadata.conn_master (
    connection_id BIGINT NOT NULL,
    connection_name STRING NOT NULL,
    connection_type STRING NOT NULL,
    connection_domain_name STRING NOT NULL,
    is_target INT NOT NULL DEFAULT 0,
    env_type STRING NOT NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_conn_master PRIMARY KEY(connection_id)
) USING DELTA;

CREATE TABLE IF NOT EXISTS dbx_data_platform_poc.ui_metadata.connection_details (
    connection_details_id BIGINT NOT NULL,
    connection_id BIGINT NOT NULL,
    connection_property_id INT NOT NULL,
    connection_property STRING NOT NULL,
    connection_property_value STRING,
    env_type STRING NOT NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_connection_details PRIMARY KEY(connection_details_id)
) USING DELTA;

CREATE TABLE IF NOT EXISTS dbx_data_platform_poc.ui_metadata.connection_auth (
    connection_auth_id BIGINT NOT NULL,
    connection_id BIGINT NOT NULL,
    auth_property_id INT NOT NULL,
    auth_property STRING NOT NULL,
    auth_property_value STRING,
    env_type STRING NOT NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_connection_auth PRIMARY KEY(connection_auth_id)
) USING DELTA;

CREATE TABLE IF NOT EXISTS dbx_data_platform_poc.ui_metadata.tbl_source_table (
    table_config_id BIGINT NOT NULL,
    connection_source_id BIGINT NOT NULL,
    connection_domain_name STRING NOT NULL,
    config_group STRING NOT NULL,
    source_attributes STRING NOT NULL,
    target_attributes STRING NOT NULL,
    load_type STRING NOT NULL,
    natural_key_columns STRING,
    hash_key_column STRING,
    partition_columns STRING,
    watermark_enabled INT NOT NULL DEFAULT 0,
    pii_scan_enabled INT NOT NULL DEFAULT 0,
    fail_mode STRING NOT NULL DEFAULT 'halt',
    retry_count INT NOT NULL DEFAULT 0,
    ingestion_frequency STRING NOT NULL DEFAULT 'adhoc',
    tags STRING,
    env_type STRING NOT NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_tbl_source_table PRIMARY KEY(table_config_id)
) USING DELTA;

CREATE TABLE IF NOT EXISTS dbx_data_platform_poc.ui_metadata.tbl_watermark (
    watermark_id BIGINT NOT NULL,
    table_config_id BIGINT NOT NULL,
    watermark_column STRING NOT NULL,
    watermark_type STRING NOT NULL,
    last_value STRING,
    last_run_id STRING,
    env_type STRING NOT NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_tbl_watermark PRIMARY KEY(watermark_id)
) USING DELTA;

CREATE TABLE IF NOT EXISTS dbx_data_platform_poc.ui_metadata.tbl_schema_version (
    version_id BIGINT NOT NULL,
    table_config_id BIGINT NOT NULL,
    version_number INT NOT NULL,
    column_count INT NOT NULL,
    column_changes_json STRING NOT NULL,
    change_type STRING NOT NULL,
    detected_by_run_id STRING,
    env_type STRING NOT NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_tbl_schema_version PRIMARY KEY(version_id)
) USING DELTA;

CREATE TABLE IF NOT EXISTS dbx_data_platform_poc.ui_metadata.tbl_pii_attribute (
    pii_id BIGINT NOT NULL,
    table_config_id BIGINT NOT NULL,
    column_name STRING NOT NULL,
    pii_category STRING NOT NULL,
    protection_method STRING NOT NULL,
    sensitivity STRING NOT NULL,
    masking_policy STRING,
    uc_tag_applied INT NOT NULL DEFAULT 0,
    access_tier STRING NOT NULL DEFAULT 'INTERNAL',
    env_type STRING NOT NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_tbl_pii_attribute PRIMARY KEY(pii_id)
) USING DELTA;

CREATE TABLE IF NOT EXISTS dbx_data_platform_poc.ui_metadata.aud_table_run (
    table_run_id BIGINT NOT NULL,
    run_id STRING NOT NULL,
    table_config_id BIGINT NOT NULL,
    connection_source_id BIGINT NOT NULL,
    connection_target_id BIGINT,
    source_attributes STRING,
    target_attributes STRING,
    batch_id STRING,
    load_type STRING,
    start_time STRING NOT NULL,
    end_time STRING,
    elapsed_seconds INT,
    rows_read INT,
    rows_written INT,
    watermark_start STRING,
    watermark_end STRING,
    status STRING NOT NULL,
    error_message STRING,
    error_type STRING,
    env_type STRING NOT NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_aud_table_run PRIMARY KEY(table_run_id)
) USING DELTA;

CREATE TABLE IF NOT EXISTS dbx_data_platform_poc.ui_metadata.bts_config (
    bts_config_id BIGINT NOT NULL,
    dataset_name STRING NOT NULL,
    source_config_id BIGINT,
    silver_layout STRING,
    dq_rules STRING,
    std_rules STRING,
    transformation_yaml STRING,
    tags STRING,
    env_type STRING NOT NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_bts_config PRIMARY KEY(bts_config_id)
) USING DELTA;

-- Note: Databricks Delta Lake does not support traditional foreign key constraints
-- Foreign key relationships are enforced at the application level via SQLAlchemy ORM
