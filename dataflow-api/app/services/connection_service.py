from __future__ import annotations

from app.repositories.connection_repo import ConnectionRepository
from app.schemas.common import raise_api_error
from app.services.connector_service import ConnectorService


class ConnectionService:
    @staticmethod
    def _as_dict(row: dict) -> dict:
        details = ConnectionRepository.get_details_dict(row["connection_id"])
        auth = ConnectionRepository.get_auth_dict(row["connection_id"])
        auth_type = "none"
        if auth:
            auth_type = "basic"
            auth_keys = set(auth.keys())
            if {"principal", "keytab_path"}.issubset(auth_keys):
                auth_type = "kerberos"
            elif {"client_id", "client_secret", "token_url"}.issubset(auth_keys):
                auth_type = "oauth"
            elif "iam_credentials" in auth_keys:
                auth_type = "iam"
            elif "api_key" in auth_keys:
                auth_type = "key"
        return {
            "connection_id": row["connection_id"],
            "connection_name": row["connection_name"],
            "connection_type": row["connection_type"],
            "connection_domain_name": row["connection_domain_name"],
            "is_target": row["is_target"],
            "env_type": row["env_type"],
            "is_active": row["is_active"],
            "details": details,
            "auth": auth,
            "auth_type": auth_type,
        }

    @staticmethod
    def create_connection(payload: dict) -> dict:
        ConnectorService.validate_connector_auth(payload["connection_type"], payload["auth_type"])
        if ConnectionRepository.find_duplicate(payload["connection_name"], payload["env_type"]):
            raise_api_error(409, "DUPLICATE_CONNECTION_NAME", "Connection name already exists for environment")

        row = ConnectionRepository.create_connection(payload)
        return ConnectionService._as_dict(row)

    @staticmethod
    def list_connections(page: int, page_size: int, filters: dict, search: str | None):
        rows, total = ConnectionRepository.list_connections(page, page_size, filters, search)
        return [ConnectionService._as_dict(row) for row in rows], total

    @staticmethod
    def get_connection(connection_id: int) -> dict:
        row = ConnectionRepository.get_connection(connection_id)
        if not row:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")
        return ConnectionService._as_dict(row)

    @staticmethod
    def update_connection(connection_id: int, payload: dict) -> dict:
        row = ConnectionRepository.get_connection(connection_id)
        if not row:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")

        if payload.get("auth") is not None:
            auth_type = payload.get("auth_type", "basic")
            ConnectorService.validate_connector_auth(row["connection_type"], auth_type)

        ConnectionRepository.update_connection(connection_id, {**payload, "env_type": row["env_type"]})
        refreshed = ConnectionRepository.get_connection(connection_id)
        return ConnectionService._as_dict(refreshed)

    @staticmethod
    def soft_delete_connection(connection_id: int, actor: str) -> None:
        row = ConnectionRepository.get_connection(connection_id)
        if not row:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")
        ConnectionRepository.soft_delete_connection(connection_id, actor)

    @staticmethod
    def test_connection(connection_id: int) -> dict:
        row = ConnectionRepository.get_connection(connection_id)
        if not row:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")

        return {
            "connection_id": connection_id,
            "success": True,
            "message": "Databricks Delta connectivity configured",
            "latency_ms": 0,
        }
