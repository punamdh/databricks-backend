PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS conn_master (
    connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_name TEXT NOT NULL,
    connection_type TEXT NOT NULL,
    connection_domain_name TEXT NOT NULL,
    is_target INTEGER NOT NULL DEFAULT 0,
    env_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(connection_name, env_type)
);

CREATE TABLE IF NOT EXISTS connection_details (
    connection_details_id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id INTEGER NOT NULL,
    connection_property_id INTEGER NOT NULL,
    connection_property TEXT NOT NULL,
    connection_property_value TEXT,
    env_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(connection_id) REFERENCES conn_master(connection_id)
);

CREATE TABLE IF NOT EXISTS connection_auth (
    connection_auth_id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id INTEGER NOT NULL,
    auth_property_id INTEGER NOT NULL,
    auth_property TEXT NOT NULL,
    auth_property_value TEXT,
    env_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(connection_id) REFERENCES conn_master(connection_id)
);

CREATE TABLE IF NOT EXISTS tbl_source_table (
    table_config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_source_id INTEGER NOT NULL,
    connection_domain_name TEXT NOT NULL,
    config_group TEXT NOT NULL,
    source_attributes TEXT NOT NULL,
    target_attributes TEXT NOT NULL,
    load_type TEXT NOT NULL,
    natural_key_columns TEXT,
    hash_key_column TEXT,
    partition_columns TEXT,
    watermark_enabled INTEGER NOT NULL DEFAULT 0,
    pii_scan_enabled INTEGER NOT NULL DEFAULT 0,
    fail_mode TEXT NOT NULL DEFAULT 'halt',
    retry_count INTEGER NOT NULL DEFAULT 0,
    ingestion_frequency TEXT NOT NULL DEFAULT 'adhoc',
    tags TEXT,
    env_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(connection_source_id) REFERENCES conn_master(connection_id)
);

CREATE TABLE IF NOT EXISTS tbl_watermark (
    watermark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_config_id INTEGER NOT NULL,
    watermark_column TEXT NOT NULL,
    watermark_type TEXT NOT NULL,
    last_value TEXT,
    last_run_id TEXT,
    env_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(table_config_id) REFERENCES tbl_source_table(table_config_id)
);

CREATE TABLE IF NOT EXISTS tbl_schema_version (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_config_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    column_count INTEGER NOT NULL,
    column_changes_json TEXT NOT NULL,
    change_type TEXT NOT NULL,
    detected_by_run_id TEXT,
    env_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(table_config_id) REFERENCES tbl_source_table(table_config_id)
);

CREATE TABLE IF NOT EXISTS tbl_pii_attribute (
    pii_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_config_id INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    pii_category TEXT NOT NULL,
    protection_method TEXT NOT NULL,
    sensitivity TEXT NOT NULL,
    masking_policy TEXT,
    uc_tag_applied INTEGER NOT NULL DEFAULT 0,
    access_tier TEXT NOT NULL DEFAULT 'INTERNAL',
    env_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(table_config_id) REFERENCES tbl_source_table(table_config_id)
);

CREATE TABLE IF NOT EXISTS aud_table_run (
    table_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    table_config_id INTEGER NOT NULL,
    connection_source_id INTEGER NOT NULL,
    source_attributes TEXT,
    target_attributes TEXT,
    batch_id TEXT,
    load_type TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    elapsed_seconds INTEGER,
    rows_read INTEGER,
    rows_written INTEGER,
    watermark_start TEXT,
    watermark_end TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    error_type TEXT,
    env_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(table_config_id) REFERENCES tbl_source_table(table_config_id),
    FOREIGN KEY(connection_source_id) REFERENCES conn_master(connection_id)
);

CREATE TABLE IF NOT EXISTS bts_config (
    bts_config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_name TEXT NOT NULL,
    source_config_id INTEGER,
    silver_layout TEXT,
    dq_rules TEXT,
    std_rules TEXT,
    transformation_yaml TEXT,
    tags TEXT,
    env_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(source_config_id) REFERENCES tbl_source_table(table_config_id)
);

CREATE INDEX IF NOT EXISTS idx_conn_details_conn ON connection_details(connection_id);
CREATE INDEX IF NOT EXISTS idx_conn_auth_conn ON connection_auth(connection_id);
CREATE INDEX IF NOT EXISTS idx_src_table_conn ON tbl_source_table(connection_source_id);
CREATE INDEX IF NOT EXISTS idx_src_table_env ON tbl_source_table(env_type, is_active);
CREATE INDEX IF NOT EXISTS idx_watermark_cfg ON tbl_watermark(table_config_id);
CREATE INDEX IF NOT EXISTS idx_schema_ver_cfg ON tbl_schema_version(table_config_id);
CREATE INDEX IF NOT EXISTS idx_pii_cfg ON tbl_pii_attribute(table_config_id);
CREATE INDEX IF NOT EXISTS idx_aud_run_cfg ON aud_table_run(table_config_id);
CREATE INDEX IF NOT EXISTS idx_aud_run_id ON aud_table_run(run_id);
