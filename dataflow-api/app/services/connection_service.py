from __future__ import annotations

import time
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.connection_repo import ConnectionRepository
from app.schemas.common import raise_api_error
from app.services.connector_service import ConnectorService


class ConnectionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ConnectionRepository(db)

    def _as_dict(self, row) -> dict:
        details = self.repo.get_details_dict(row.connection_id)
        auth = self.repo.get_auth_dict(row.connection_id)
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
            "connection_id": row.connection_id,
            "connection_name": row.connection_name,
            "connection_type": row.connection_type,
            "connection_domain_name": row.connection_domain_name,
            "is_target": row.is_target,
            "env_type": row.env_type,
            "is_active": row.is_active,
            "details": details,
            "auth": auth,
            "auth_type": auth_type,
        }

    def create_connection(self, payload: dict) -> dict:
        ConnectorService.validate_connector_auth(payload["connection_type"], payload["auth_type"])
        if self.repo.find_duplicate(payload["connection_name"], payload["env_type"]):
            raise_api_error(409, "DUPLICATE_CONNECTION_NAME", "Connection name already exists for environment")

        actor = payload.get("created_by", "system")
        try:
            with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
                master = self.repo.create_master(
                    {
                        "connection_name": payload["connection_name"],
                        "connection_type": payload["connection_type"],
                        "connection_domain_name": payload["connection_domain_name"],
                        "is_target": payload.get("is_target", 0),
                        "env_type": payload["env_type"],
                        "created_by": actor,
                        "updated_by": actor,
                    }
                )
                self.repo.add_details(master.connection_id, payload["env_type"], payload.get("details", {}), actor)
                self.repo.add_auth(master.connection_id, payload["env_type"], payload.get("auth", {}), actor)
        except IntegrityError as exc:
            raise_api_error(409, "DUPLICATE_CONNECTION_NAME", "Connection name already exists for environment", {"error": str(exc)})

        return self._as_dict(master)

    def list_connections(self, page: int, page_size: int, filters: dict, search: str | None):
        rows, total = self.repo.list_connections(page, page_size, filters, search)
        return [self._as_dict(row) for row in rows], total

    def get_connection(self, connection_id: int) -> dict:
        row = self.repo.get_connection(connection_id)
        if not row:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")
        return self._as_dict(row)

    def update_connection(self, connection_id: int, payload: dict) -> dict:
        row = self.repo.get_connection(connection_id)
        if not row:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")

        actor = payload.get("updated_by", "system")
        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            if payload.get("connection_domain_name") is not None:
                row.connection_domain_name = payload["connection_domain_name"]
            if payload.get("is_target") is not None:
                row.is_target = payload["is_target"]
            row.updated_by = actor

            if payload.get("details") is not None:
                for old in row.details:
                    old.is_active = 0
                    old.updated_by = actor
                self.repo.add_details(row.connection_id, row.env_type, payload["details"], actor)

            if payload.get("auth") is not None:
                auth_type = payload.get("auth_type", "basic")
                ConnectorService.validate_connector_auth(row.connection_type, auth_type)
                for old in row.auth:
                    old.is_active = 0
                    old.updated_by = actor
                self.repo.add_auth(row.connection_id, row.env_type, payload["auth"], actor)

        self.db.refresh(row)
        return self._as_dict(row)

    def soft_delete_connection(self, connection_id: int, actor: str) -> None:
        row = self.repo.get_connection(connection_id)
        if not row:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")
        with (self.db.begin_nested() if self.db.in_transaction() else self.db.begin()):
            row.is_active = 0
            row.updated_by = actor
            for item in row.details:
                item.is_active = 0
                item.updated_by = actor
            for item in row.auth:
                item.is_active = 0
                item.updated_by = actor

    def test_connection(self, connection_id: int) -> dict:
        row = self.repo.get_connection(connection_id)
        if not row:
            raise_api_error(404, "CONNECTION_NOT_FOUND", "Connection not found")

        start = time.perf_counter()
        success = True
        message = "Mock connectivity success"

        details = self.repo.get_details_dict(connection_id)
        if row.connection_type == "sqlite":
            db_file_path = details.get("db_file_path", "")
            success = Path(db_file_path).exists()
            message = "SQLite file exists" if success else "SQLite file not found"

        latency_ms = int((time.perf_counter() - start) * 1000)
        return {"connection_id": connection_id, "success": success, "message": message, "latency_ms": latency_ms}
