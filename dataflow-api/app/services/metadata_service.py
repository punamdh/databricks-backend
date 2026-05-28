from __future__ import annotations

from app.config.connectors import CONNECTOR_REGISTRY
from app.repositories.connection_repo import ConnectionRepository
from app.schemas.common import raise_api_error


class MetadataService:

    @staticmethod
    def list_tables(connection_id: int, schema_filter: str | None = None) -> list[dict]:
        master = ConnectionRepository.get_connection(connection_id)
        if not master:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")

        connection_type = master["connection_type"]
        connector = CONNECTOR_REGISTRY.get(connection_type)
        if not connector:
            raise_api_error(400, "UNSUPPORTED_CONNECTOR", f"Connector type '{connection_type}' is not supported")

        category = connector.get("connector_category", "database")

        details = ConnectionRepository.get_details_dict(connection_id)

        if category != "database":
            return MetadataService._list_storage_paths(connection_type, details)

        auth = ConnectionRepository.get_auth_dict(connection_id)
        jdbc_url = MetadataService._build_jdbc_url(connection_type, connector, details)
        sql = connector.get("list_tables_sql", "")
        if not sql:
            raise_api_error(400, "NO_METADATA_QUERY", f"Connector '{connection_type}' has no table listing query configured")

        if schema_filter:
            schema_col = "OWNER" if connection_type == "oracle" else "TABLE_SCHEMA"
            sql = f"SELECT * FROM ({sql}) AS t WHERE {schema_col} = '{schema_filter}'"

        return MetadataService._exec_jdbc(jdbc_url, connector, auth, sql, _map_table_row)

    @staticmethod
    def list_columns(connection_id: int, schema_name: str, table_name: str) -> list[dict]:
        master = ConnectionRepository.get_connection(connection_id)
        if not master:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")

        connection_type = master["connection_type"]
        connector = CONNECTOR_REGISTRY.get(connection_type)
        if not connector:
            raise_api_error(400, "UNSUPPORTED_CONNECTOR", f"Connector type '{connection_type}' is not supported")

        category = connector.get("connector_category", "database")
        if category != "database":
            raise_api_error(400, "NOT_APPLICABLE", "Column listing is not applicable for file/storage connectors")

        details = ConnectionRepository.get_details_dict(connection_id)
        auth = ConnectionRepository.get_auth_dict(connection_id)

        jdbc_url = MetadataService._build_jdbc_url(connection_type, connector, details)
        sql_template = connector.get("list_schema_columns_sql", "")
        if not sql_template:
            raise_api_error(400, "NO_METADATA_QUERY", f"Connector '{connection_type}' has no column listing query configured")

        escaped_schema = schema_name.replace("'", "''")
        escaped_table = table_name.replace("'", "''")
        sql = sql_template.format(schema=escaped_schema, table=escaped_table)

        return MetadataService._exec_jdbc(jdbc_url, connector, auth, sql, _map_column_row)

    @staticmethod
    def _build_jdbc_url(connection_type: str, connector: dict, details: dict) -> str:
        template = connector.get("jdbc_url_template", "")
        try:
            return template.format(**details)
        except KeyError as e:
            raise_api_error(400, "MISSING_CONNECTION_DETAIL", f"Connection is missing required property: {e}")

    @staticmethod
    def _exec_jdbc(jdbc_url: str, connector: dict, auth: dict, sql: str, row_mapper) -> list[dict]:
        from app.database.connection import get_spark
        spark = get_spark()

        props = {"driver": connector["jdbc_driver_class"]}
        if auth.get("username"):
            props["user"] = auth["username"]
        if auth.get("password"):
            props["password"] = auth["password"]

        try:
            df = spark.read.jdbc(
                url=jdbc_url,
                table=f"({sql}) AS _meta_q",
                properties=props,
            )
            return [row_mapper(row.asDict()) for row in df.collect()]
        except Exception as exc:
            raise_api_error(500, "METADATA_QUERY_FAILED", f"Failed to execute metadata query: {exc}")

    @staticmethod
    def _list_storage_paths(connection_type: str, details: dict) -> list[dict]:
        path_keys = {
            "s3": "path_prefix",
            "gcs": "path_prefix",
            "azure-blob": "blob_path_prefix",
            "sftp": "remote_path",
            "local": "base_path",
        }
        path = details.get(path_keys.get(connection_type, ""), "/")
        return [{"schema_name": connection_type, "table_name": path}]


def _map_table_row(d: dict) -> dict:
    schema = (
        d.get("TABLE_SCHEMA") or d.get("table_schema")
        or d.get("OWNER") or d.get("owner") or ""
    )
    table = (
        d.get("TABLE_NAME") or d.get("table_name") or ""
    )
    return {"schema_name": schema, "table_name": table}


def _map_column_row(d: dict) -> dict:
    return {
        "column_name": d.get("COLUMN_NAME") or d.get("column_name") or "",
        "data_type": d.get("DATA_TYPE") or d.get("data_type") or "",
        "is_nullable": d.get("IS_NULLABLE") or d.get("is_nullable") or d.get("NULLABLE") or "YES",
        "ordinal_position": int(d.get("ORDINAL_POSITION") or d.get("ordinal_position") or d.get("COLUMN_ID") or 0),
    }
