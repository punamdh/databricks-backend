CONNECTOR_REGISTRY = {
    "mssql": {
        "label": "MSSQL",
        "base_fields": ["host", "port", "database", "schema", "odbc_driver"],
        "defaults": {"port": "1433"},
        "auth_methods": ["basic", "kerberos", "oauth"],
        "connector_category": "database",
        "jdbc_url_template": "jdbc:sqlserver://{host}:{port};databaseName={database}",
        "jdbc_driver_class": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        "list_tables_sql": (
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE'"
        ),
        "list_schema_columns_sql": (
            "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION "
            "FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}' "
            "ORDER BY ORDINAL_POSITION"
        ),
    },
    "postgres": {
        "label": "PostgreSQL",
        "base_fields": ["host", "port", "database", "schema"],
        "defaults": {"port": "5432"},
        "auth_methods": ["basic", "iam"],
        "connector_category": "database",
        "jdbc_url_template": "jdbc:postgresql://{host}:{port}/{database}",
        "jdbc_driver_class": "org.postgresql.Driver",
        "list_tables_sql": (
            "SELECT table_schema AS TABLE_SCHEMA, table_name AS TABLE_NAME "
            "FROM information_schema.tables "
            "WHERE table_type = 'BASE TABLE' "
            "AND table_schema NOT IN ('pg_catalog', 'information_schema')"
        ),
        "list_schema_columns_sql": (
            "SELECT column_name AS COLUMN_NAME, data_type AS DATA_TYPE, "
            "is_nullable AS IS_NULLABLE, ordinal_position AS ORDINAL_POSITION "
            "FROM information_schema.columns "
            "WHERE table_schema = '{schema}' AND table_name = '{table}' "
            "ORDER BY ordinal_position"
        ),
    },
    "mysql": {
        "label": "MySQL",
        "base_fields": ["host", "port", "database"],
        "defaults": {"port": "3306"},
        "auth_methods": ["basic"],
        "connector_category": "database",
        "jdbc_url_template": "jdbc:mysql://{host}:{port}/{database}",
        "jdbc_driver_class": "com.mysql.cj.jdbc.Driver",
        "list_tables_sql": (
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE'"
        ),
        "list_schema_columns_sql": (
            "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION "
            "FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}' "
            "ORDER BY ORDINAL_POSITION"
        ),
    },
    "oracle": {
        "label": "Oracle",
        "base_fields": ["host", "port", "service_name", "schema"],
        "defaults": {"port": "1521"},
        "auth_methods": ["basic", "kerberos"],
        "connector_category": "database",
        "jdbc_url_template": "jdbc:oracle:thin:@//{host}:{port}/{service_name}",
        "jdbc_driver_class": "oracle.jdbc.driver.OracleDriver",
        "list_tables_sql": (
            "SELECT OWNER AS TABLE_SCHEMA, TABLE_NAME FROM ALL_TABLES"
        ),
        "list_schema_columns_sql": (
            "SELECT COLUMN_NAME, DATA_TYPE, NULLABLE AS IS_NULLABLE, COLUMN_ID AS ORDINAL_POSITION "
            "FROM ALL_TAB_COLUMNS "
            "WHERE OWNER = '{schema}' AND TABLE_NAME = '{table}' "
            "ORDER BY COLUMN_ID"
        ),
    },
    "snowflake": {
        "label": "Snowflake",
        "base_fields": ["account_identifier", "warehouse", "database", "schema", "role"],
        "defaults": {},
        "auth_methods": ["basic", "oauth", "key"],
        "connector_category": "database",
        "jdbc_url_template": (
            "jdbc:snowflake://{account_identifier}.snowflakecomputing.com/"
            "?warehouse={warehouse}&db={database}&schema={schema}&role={role}"
        ),
        "jdbc_driver_class": "net.snowflake.client.jdbc.SnowflakeDriver",
        "list_tables_sql": (
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE'"
        ),
        "list_schema_columns_sql": (
            "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION "
            "FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}' "
            "ORDER BY ORDINAL_POSITION"
        ),
    },
    "bigquery": {
        "label": "BigQuery",
        "base_fields": ["project_id", "dataset", "location"],
        "defaults": {},
        "auth_methods": ["iam", "oauth", "key"],
        "connector_category": "database",
        "jdbc_url_template": (
            "jdbc:bigquery://https://www.googleapis.com/bigquery/v2:443"
            ";ProjectId={project_id};OAuthType=0"
        ),
        "jdbc_driver_class": "com.simba.googlebigquery.jdbc.Driver",
        "list_tables_sql": (
            "SELECT table_schema AS TABLE_SCHEMA, table_name AS TABLE_NAME "
            "FROM `{project_id}.INFORMATION_SCHEMA.TABLES` "
            "WHERE table_type = 'BASE TABLE'"
        ),
        "list_schema_columns_sql": (
            "SELECT column_name AS COLUMN_NAME, data_type AS DATA_TYPE, "
            "is_nullable AS IS_NULLABLE, ordinal_position AS ORDINAL_POSITION "
            "FROM `{project_id}.{schema}.INFORMATION_SCHEMA.COLUMNS` "
            "WHERE table_name = '{table}' "
            "ORDER BY ordinal_position"
        ),
    },
    "redshift": {
        "label": "Redshift",
        "base_fields": ["cluster_endpoint", "port", "database", "schema"],
        "defaults": {"port": "5439"},
        "auth_methods": ["basic", "iam"],
        "connector_category": "database",
        "jdbc_url_template": "jdbc:redshift://{cluster_endpoint}:{port}/{database}",
        "jdbc_driver_class": "com.amazon.redshift.jdbc.Driver",
        "list_tables_sql": (
            "SELECT schemaname AS TABLE_SCHEMA, tablename AS TABLE_NAME "
            "FROM pg_tables "
            "WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
        ),
        "list_schema_columns_sql": (
            "SELECT column_name AS COLUMN_NAME, data_type AS DATA_TYPE, "
            "is_nullable AS IS_NULLABLE, ordinal_position AS ORDINAL_POSITION "
            "FROM information_schema.columns "
            "WHERE table_schema = '{schema}' AND table_name = '{table}' "
            "ORDER BY ordinal_position"
        ),
    },
    "s3": {
        "label": "S3",
        "base_fields": ["bucket_name", "region", "path_prefix"],
        "defaults": {},
        "auth_methods": ["iam", "key"],
        "connector_category": "storage",
    },
    "gcs": {
        "label": "GCS",
        "base_fields": ["bucket_name", "project_id", "path_prefix"],
        "defaults": {},
        "auth_methods": ["iam", "key"],
        "connector_category": "storage",
    },
    "azure-blob": {
        "label": "Azure Blob",
        "base_fields": ["storage_account_name", "container_name", "blob_path_prefix"],
        "defaults": {},
        "auth_methods": ["key", "oauth"],
        "connector_category": "storage",
    },
    "sftp": {
        "label": "SFTP",
        "base_fields": ["host", "port", "remote_path"],
        "defaults": {"port": "22"},
        "auth_methods": ["basic", "key"],
        "connector_category": "sftp",
    },
    "local": {
        "label": "Local",
        "base_fields": ["base_path"],
        "defaults": {},
        "auth_methods": ["none"],
        "connector_category": "storage",
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
