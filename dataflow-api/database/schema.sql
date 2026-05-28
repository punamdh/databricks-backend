CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.conn_master (
    connection_id BIGINT,
    connection_name STRING,
    connection_type STRING,
    connection_domain_name STRING,
    is_target BOOLEAN,
    env_type STRING,
    is_active BOOLEAN,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.connection_details (
    connection_details_id BIGINT,
    connection_id BIGINT,
    connection_property_id INT,
    connection_property STRING,
    connection_property_value STRING,
    env_type STRING,
    is_active BOOLEAN,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.connection_auth (
    connection_auth_id BIGINT,
    connection_id BIGINT,
    auth_property_id INT,
    auth_property STRING,
    auth_property_value STRING,
    env_type STRING,
    is_active BOOLEAN,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.table_group_s2b (
    table_group_id BIGINT,
    description STRING,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.tbl_source_table (
    table_config_id BIGINT,
    connection_domain_name STRING,
    connection_source_id BIGINT,
    source_attributes STRING,
    target_attributes STRING,
    load_type STRING,
    natural_key_columns STRING,
    hash_key_column STRING,
    partition_columns STRING,
    pii_scan_enabled BOOLEAN,
    watermark_enabled BOOLEAN,
    tags STRING,
    ingestion_frequency STRING,
    env_type STRING,
    is_active BOOLEAN,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP,
    table_group_id BIGINT
) USING DELTA;

CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.tbl_watermark (
    watermark_id BIGINT,
    table_config_id BIGINT,
    watermark_column STRING,
    watermark_type STRING,
    last_value STRING,
    last_run_id STRING,
    env_type STRING,
    is_active BOOLEAN,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.tbl_schema_version (
    version_id BIGINT,
    table_config_id BIGINT,
    version_number INT,
    column_count INT,
    column_changes_json STRING,
    change_type STRING,
    detected_by_run_id STRING,
    env_type STRING,
    is_active BOOLEAN,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.tbl_pii_attribute (
    pii_id BIGINT,
    table_config_id BIGINT,
    column_name STRING,
    pii_category STRING,
    protection_method STRING,
    sensitivity STRING,
    masking_policy STRING,
    mask_pattern STRING,
    key_scope STRING,
    key_name STRING,
    hash_algorithm STRING,
    uc_tag_applied BOOLEAN,
    uc_tag_key STRING,
    uc_tag_value STRING,
    access_tier STRING,
    allowed_groups STRING,
    env_type STRING,
    is_active BOOLEAN,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.aud_table_run (
    table_run_id BIGINT,
    run_id STRING,
    table_config_id BIGINT,
    connection_source_id BIGINT,
    connection_target_id BIGINT,
    source_attributes STRING,
    target_attributes STRING,
    batch_id STRING,
    source_file STRING,
    pipeline_version STRING,
    load_type STRING,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    elapsed_seconds INT,
    rows_read INT,
    rows_written INT,
    watermark_start STRING,
    watermark_end STRING,
    status STRING,
    error_message STRING,
    error_type STRING,
    env_type STRING,
    is_active BOOLEAN,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS `dbx_data_platform_poc.ui_metadata`.bts_config (
    bts_config_id BIGINT,
    dataset_name STRING,
    source_config_id BIGINT,
    silver_layout STRING,
    dq_rules STRING,
    std_rules STRING,
    transformation_yaml STRING,
    tags STRING,
    env_type STRING,
    is_active BOOLEAN,
    created_by STRING,
    created_at TIMESTAMP,
    updated_by STRING,
    updated_at TIMESTAMP
) USING DELTA;
