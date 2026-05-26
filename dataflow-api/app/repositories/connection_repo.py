from __future__ import annotations

from delta.tables import DeltaTable
from pyspark.sql import functions as F

from app.database.connection import get_spark
from app.repositories.delta_utils import append_rows, next_id, now_utc_iso, paginate, table_name


class ConnectionRepository:
    master_table = table_name("conn_master")
    details_table = table_name("connection_details")
    auth_table = table_name("connection_auth")

    @staticmethod
    def create_connection(payload: dict) -> dict:
        spark = get_spark()
        actor = payload.get("created_by", "system")
        now = now_utc_iso()

        connection_id = next_id(ConnectionRepository.master_table, "connection_id")
        master = {
            "connection_id": connection_id,
            "connection_name": payload["connection_name"],
            "connection_type": payload["connection_type"],
            "connection_domain_name": payload["connection_domain_name"],
            "is_target": payload.get("is_target", 0),
            "env_type": payload["env_type"],
            "is_active": 1,
            "created_by": actor,
            "created_at": now,
            "updated_by": payload.get("updated_by", actor),
            "updated_at": now,
        }
        append_rows(ConnectionRepository.master_table, [master])

        details = payload.get("details", {})
        if details:
            detail_rows = []
            detail_id = next_id(ConnectionRepository.details_table, "connection_details_id")
            for idx, (key, value) in enumerate(details.items(), start=1):
                detail_rows.append(
                    {
                        "connection_details_id": detail_id,
                        "connection_id": connection_id,
                        "connection_property_id": idx,
                        "connection_property": key,
                        "connection_property_value": str(value),
                        "env_type": payload["env_type"],
                        "is_active": 1,
                        "created_by": actor,
                        "created_at": now,
                        "updated_by": actor,
                        "updated_at": now,
                    }
                )
                detail_id += 1
            append_rows(ConnectionRepository.details_table, detail_rows)

        auth = payload.get("auth", {})
        if auth:
            auth_rows = []
            auth_id = next_id(ConnectionRepository.auth_table, "connection_auth_id")
            for idx, (key, value) in enumerate(auth.items(), start=1):
                auth_rows.append(
                    {
                        "connection_auth_id": auth_id,
                        "connection_id": connection_id,
                        "auth_property_id": idx,
                        "auth_property": key,
                        "auth_property_value": str(value),
                        "env_type": payload["env_type"],
                        "is_active": 1,
                        "created_by": actor,
                        "created_at": now,
                        "updated_by": actor,
                        "updated_at": now,
                    }
                )
                auth_id += 1
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
            df = df.filter(F.col("is_active") == filters["is_active"])
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
            .filter((F.col("connection_id") == connection_id) & (F.col("is_active") == 1))
            .limit(1)
            .collect()
        )
        return rows[0].asDict() if rows else None

    @staticmethod
    def get_details_dict(connection_id: int) -> dict[str, str]:
        spark = get_spark()
        rows = (
            spark.table(ConnectionRepository.details_table)
            .filter((F.col("connection_id") == connection_id) & (F.col("is_active") == 1))
            .orderBy(F.col("connection_property_id").asc())
            .collect()
        )
        return {row["connection_property"]: row["connection_property_value"] or "" for row in rows}

    @staticmethod
    def get_auth_dict(connection_id: int) -> dict[str, str]:
        spark = get_spark()
        rows = (
            spark.table(ConnectionRepository.auth_table)
            .filter((F.col("connection_id") == connection_id) & (F.col("is_active") == 1))
            .orderBy(F.col("auth_property_id").asc())
            .collect()
        )
        return {row["auth_property"]: row["auth_property_value"] or "" for row in rows}

    @staticmethod
    def update_connection(connection_id: int, payload: dict) -> None:
        spark = get_spark()
        actor = payload.get("updated_by", "system")
        now = now_utc_iso()

        update_set = {"updated_by": F.lit(actor), "updated_at": F.lit(now)}
        if payload.get("connection_domain_name") is not None:
            update_set["connection_domain_name"] = F.lit(payload["connection_domain_name"])
        if payload.get("is_target") is not None:
            update_set["is_target"] = F.lit(payload["is_target"])

        DeltaTable.forName(spark, ConnectionRepository.master_table).update(
            condition=(F.col("connection_id") == connection_id) & (F.col("is_active") == 1),
            set=update_set,
        )

        if payload.get("details") is not None:
            DeltaTable.forName(spark, ConnectionRepository.details_table).update(
                condition=(F.col("connection_id") == connection_id) & (F.col("is_active") == 1),
                set={"is_active": F.lit(0), "updated_by": F.lit(actor), "updated_at": F.lit(now)},
            )
            details_rows = []
            detail_id = next_id(ConnectionRepository.details_table, "connection_details_id")
            for idx, (key, value) in enumerate(payload["details"].items(), start=1):
                details_rows.append(
                    {
                        "connection_details_id": detail_id,
                        "connection_id": connection_id,
                        "connection_property_id": idx,
                        "connection_property": key,
                        "connection_property_value": str(value),
                        "env_type": payload["env_type"],
                        "is_active": 1,
                        "created_by": actor,
                        "created_at": now,
                        "updated_by": actor,
                        "updated_at": now,
                    }
                )
                detail_id += 1
            if details_rows:
                append_rows(ConnectionRepository.details_table, details_rows)

        if payload.get("auth") is not None:
            DeltaTable.forName(spark, ConnectionRepository.auth_table).update(
                condition=(F.col("connection_id") == connection_id) & (F.col("is_active") == 1),
                set={"is_active": F.lit(0), "updated_by": F.lit(actor), "updated_at": F.lit(now)},
            )
            auth_rows = []
            auth_id = next_id(ConnectionRepository.auth_table, "connection_auth_id")
            for idx, (key, value) in enumerate(payload["auth"].items(), start=1):
                auth_rows.append(
                    {
                        "connection_auth_id": auth_id,
                        "connection_id": connection_id,
                        "auth_property_id": idx,
                        "auth_property": key,
                        "auth_property_value": str(value),
                        "env_type": payload["env_type"],
                        "is_active": 1,
                        "created_by": actor,
                        "created_at": now,
                        "updated_by": actor,
                        "updated_at": now,
                    }
                )
                auth_id += 1
            if auth_rows:
                append_rows(ConnectionRepository.auth_table, auth_rows)

    @staticmethod
    def soft_delete_connection(connection_id: int, actor: str) -> None:
        spark = get_spark()
        now = now_utc_iso()
        for table in (ConnectionRepository.master_table, ConnectionRepository.details_table, ConnectionRepository.auth_table):
            DeltaTable.forName(spark, table).update(
                condition=(F.col("connection_id") == connection_id) & (F.col("is_active") == 1),
                set={"is_active": F.lit(0), "updated_by": F.lit(actor), "updated_at": F.lit(now)},
            )
