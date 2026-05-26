CONNECTOR_REGISTRY = {
    "mssql": {
        "label": "MSSQL",
        "base_fields": ["host", "port", "database", "schema", "odbc_driver"],
        "defaults": {"port": "1433"},
        "auth_methods": ["basic", "kerberos", "oauth"],
    },
    "postgres": {
        "label": "PostgreSQL",
        "base_fields": ["host", "port", "database", "schema"],
        "defaults": {"port": "5432"},
        "auth_methods": ["basic", "iam"],
    },
    "mysql": {
        "label": "MySQL",
        "base_fields": ["host", "port", "database"],
        "defaults": {"port": "3306"},
        "auth_methods": ["basic"],
    },
    "oracle": {
        "label": "Oracle",
        "base_fields": ["host", "port", "service_name", "schema"],
        "defaults": {"port": "1521"},
        "auth_methods": ["basic", "kerberos"],
    },
    "snowflake": {
        "label": "Snowflake",
        "base_fields": ["account_identifier", "warehouse", "database", "schema", "role"],
        "defaults": {},
        "auth_methods": ["basic", "oauth", "key"],
    },
    "bigquery": {
        "label": "BigQuery",
        "base_fields": ["project_id", "dataset", "location"],
        "defaults": {},
        "auth_methods": ["iam", "oauth", "key"],
    },
    "redshift": {
        "label": "Redshift",
        "base_fields": ["cluster_endpoint", "port", "database", "schema"],
        "defaults": {"port": "5439"},
        "auth_methods": ["basic", "iam"],
    },
    "s3": {
        "label": "S3",
        "base_fields": ["bucket_name", "region", "path_prefix"],
        "defaults": {},
        "auth_methods": ["iam", "key"],
    },
    "gcs": {
        "label": "GCS",
        "base_fields": ["bucket_name", "project_id", "path_prefix"],
        "defaults": {},
        "auth_methods": ["iam", "key"],
    },
    "azure-blob": {
        "label": "Azure Blob",
        "base_fields": ["storage_account_name", "container_name", "blob_path_prefix"],
        "defaults": {},
        "auth_methods": ["key", "oauth"],
    },
    "sftp": {
        "label": "SFTP",
        "base_fields": ["host", "port", "remote_path"],
        "defaults": {"port": "22"},
        "auth_methods": ["basic", "key"],
    },
    "local": {
        "label": "Local",
        "base_fields": ["base_path"],
        "defaults": {},
        "auth_methods": ["none"],
    },
}

AUTH_FIELDS = {
    "none": [],
    "basic": ["username", "password"],
    "kerberos": ["principal", "keytab_path"],
    "oauth": ["client_id", "client_secret", "token_url"],
    "iam": ["iam_credentials"],
    "key": ["api_key"],
}
