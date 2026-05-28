from __future__ import annotations

from pyspark.sql import functions as F

from app.database.connection import get_spark
from app.repositories.delta_utils import append_rows, bool_value, next_id, now_utc, now_utc_iso, paginate, row_to_dict, table_name, update_rows


class ConnectionRepository:
    master_table = table_name("conn_master")
    details_table = table_name("connection_details")
    auth_table = table_name("connection_auth")

    @staticmethod
    def create_connection(payload: dict) -> dict:
        spark = get_spark()
        actor = payload.get("created_by", "system")
        now = now_utc()

        master = {
            "connection_name": payload["connection_name"],
            "connection_type": payload["connection_type"],
            "connection_domain_name": payload["connection_domain_name"],
            "is_target": payload.get("is_target", 0),
            "env_type": payload["env_type"],
            "is_active": True,
            "created_by": actor,
            "created_at": now,
            "updated_by": payload.get("updated_by", actor),
            "updated_at": now,
        }
        append_rows(ConnectionRepository.master_table, [master])
        
        # Fetch the generated connection_id
        result = spark.table(ConnectionRepository.master_table).orderBy(F.col("connection_id").desc()).limit(1).collect()[0]
        result_dict = result.asDict()
        connection_id = result_dict["connection_id"]
        master["connection_id"] = connection_id

        details = payload.get("details", {})
        if details:
            detail_rows = []
            for idx, (key, value) in enumerate(details.items(), start=1):
                detail_rows.append(
                    {
                        "connection_id": connection_id,
                        "connection_property_id": idx,
                        "connection_property": key,
                        "connection_property_value": str(value),
                        "env_type": payload["env_type"],
                        "is_active": True,
                        "created_by": actor,
                        "created_at": now,
                        "updated_by": actor,
                        "updated_at": now,
                    }
                )
            append_rows(ConnectionRepository.details_table, detail_rows)

        auth = payload.get("auth", {})
        if auth:
            auth_rows = []
            for idx, (key, value) in enumerate(auth.items(), start=1):
                auth_rows.append(
                    {
                        "connection_id": connection_id,
                        "auth_property_id": idx,
                        "auth_property": key,
                        "auth_property_value": str(value),
                        "env_type": payload["env_type"],
                        "is_active": True,
                        "created_by": actor,
                        "created_at": now,
                        "updated_by": actor,
                        "updated_at": now,
                    }
                )
            append_rows(ConnectionRepository.auth_table, auth_rows)

        return master

    @staticmethod
    def find_duplicate(connection_name: str, env_type: str, exclude_id: int | None = None) -> bool:
        spark = get_spark()
        df = spark.table(ConnectionRepository.master_table).filter(
            (F.col("connection_name") == connection_name) & (F.col("env_type") == env_type)
        )
        if exclude_id is not None:
            df = df.filter(F.col("connection_id") != exclude_id)
        return df.limit(1).count() > 0

    @staticmethod
    def list_connections(page: int, page_size: int, filters: dict, search: str | None):
        spark = get_spark()
        df = spark.table(ConnectionRepository.master_table)

        if filters.get("is_active") is not None:
            # Convert int to bool for backward compatibility, then convert to correct type for column
            is_active_val = filters["is_active"]
            if isinstance(is_active_val, int):
                is_active_val = bool(is_active_val)
            is_active_val = bool_value(ConnectionRepository.master_table, "is_active", is_active_val)
            df = df.filter(F.col("is_active") == is_active_val)
        if filters.get("env_type"):
            df = df.filter(F.col("env_type") == filters["env_type"])
        if filters.get("connection_type"):
            df = df.filter(F.col("connection_type") == filters["connection_type"])
        if filters.get("is_target") is not None:
            df = df.filter(F.col("is_target") == filters["is_target"])
        if search:
            search_lc = search.lower()
            df = df.filter(
                F.lower(F.col("connection_name")).contains(search_lc)
                | F.lower(F.col("connection_domain_name")).contains(search_lc)
            )

        return paginate(df, page, page_size, "connection_id")

    @staticmethod
    def get_connection(connection_id: int) -> dict | None:
        spark = get_spark()
        rows = (
            spark.table(ConnectionRepository.master_table)
            .filter((F.col("connection_id") == connection_id) & (F.col("is_active") == bool_value(ConnectionRepository.master_table, "is_active", True)))
            .limit(1)
            .collect()
        )
        return row_to_dict(rows[0]) if rows else None

    @staticmethod
    def get_details_dict(connection_id: int) -> dict[str, str]:
        spark = get_spark()
        rows = (
            spark.table(ConnectionRepository.details_table)
            .filter((F.col("connection_id") == connection_id) & (F.col("is_active") == bool_value(ConnectionRepository.details_table, "is_active", True)))
            .orderBy(F.col("connection_property_id").asc())
            .collect()
        )
        result = {}
        for row in rows:
            row_dict = row.asDict()
            key = row_dict.get("connection_property")
            value = row_dict.get("connection_property_value")
            if key is not None:
                result[key] = value if value is not None else ""
        return result

    @staticmethod
    def get_auth_dict(connection_id: int) -> dict[str, str]:
        spark = get_spark()
        rows = (
            spark.table(ConnectionRepository.auth_table)
            .filter((F.col("connection_id") == connection_id) & (F.col("is_active") == bool_value(ConnectionRepository.auth_table, "is_active", True)))
            .orderBy(F.col("auth_property_id").asc())
            .collect()
        )
        result = {}
        for row in rows:
            row_dict = row.asDict()
            key = row_dict.get("auth_property")
            value = row_dict.get("auth_property_value")
            if key is not None:
                result[key] = value if value is not None else ""
        return result

    @staticmethod
    def update_connection(connection_id: int, payload: dict) -> None:
        spark = get_spark()
        actor = payload.get("updated_by", "system")
        now = now_utc_iso()

        updates = {"updated_by": actor, "updated_at": now}
        if payload.get("connection_domain_name") is not None:
            updates["connection_domain_name"] = payload["connection_domain_name"]
        if payload.get("is_target") is not None:
            updates["is_target"] = payload["is_target"]

        update_rows(
            ConnectionRepository.master_table,
            f"connection_id = {connection_id} AND is_active = TRUE",
            updates
        )

        if payload.get("details") is not None:
            update_rows(
                ConnectionRepository.details_table,
                f"connection_id = {connection_id} AND is_active = TRUE",
                {"is_active": False, "updated_by": actor, "updated_at": now}
            )
            details_rows = []
            for idx, (key, value) in enumerate(payload["details"].items(), start=1):
                details_rows.append(
                    {
                        "connection_id": connection_id,
                        "connection_property_id": idx,
                        "connection_property": key,
                        "connection_property_value": str(value),
                        "env_type": payload["env_type"],
                        "is_active": True,
                        "created_by": actor,
                        "created_at": now,
                        "updated_by": actor,
                        "updated_at": now,
                    }
                )
            if details_rows:
                append_rows(ConnectionRepository.details_table, details_rows)

        if payload.get("auth") is not None:
            update_rows(
                ConnectionRepository.auth_table,
                f"connection_id = {connection_id} AND is_active = TRUE",
                {"is_active": False, "updated_by": actor, "updated_at": now}
            )
            auth_rows = []
            for idx, (key, value) in enumerate(payload["auth"].items(), start=1):
                auth_rows.append(
                    {
                        "connection_id": connection_id,
                        "auth_property_id": idx,
                        "auth_property": key,
                        "auth_property_value": str(value),
                        "env_type": payload["env_type"],
                        "is_active": True,
                        "created_by": actor,
                        "created_at": now,
                        "updated_by": actor,
                        "updated_at": now,
                    }
                )
            if auth_rows:
                append_rows(ConnectionRepository.auth_table, auth_rows)

    @staticmethod
    def soft_delete_connection(connection_id: int, actor: str) -> None:
        spark = get_spark()
        now = now_utc_iso()
        for table in (ConnectionRepository.master_table, ConnectionRepository.details_table, ConnectionRepository.auth_table):
            update_rows(
                table,
                f"connection_id = {connection_id} AND is_active = TRUE",
                {"is_active": False, "updated_by": actor, "updated_at": now}
            )
