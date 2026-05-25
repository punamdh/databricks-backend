from __future__ import annotations

from app.config.connectors import AUTH_FIELDS, CONNECTOR_REGISTRY
from app.schemas.common import raise_api_error


class ConnectorService:
    @staticmethod
    def list_connectors() -> list[dict]:
        return [
            {"key": key, "label": value["label"], "auth_methods": value["auth_methods"]}
            for key, value in CONNECTOR_REGISTRY.items()
        ]

    @staticmethod
    def get_connector_fields(connector_key: str, auth_type: str | None = None) -> dict:
        connector = CONNECTOR_REGISTRY.get(connector_key)
        if not connector:
            raise_api_error(400, "INVALID_CONNECTOR_TYPE", f"Unsupported connector type: {connector_key}")

        selected_auth = auth_type or connector["auth_methods"][0]
        if selected_auth not in connector["auth_methods"]:
            raise_api_error(400, "INVALID_AUTH_TYPE", f"Unsupported auth type '{selected_auth}' for {connector_key}")

        base_fields = [
            {"name": f, "required": True, "type": "string", "default": connector["defaults"].get(f)}
            for f in connector["base_fields"]
        ]
        auth_fields = [{"name": f, "required": True, "type": "string"} for f in AUTH_FIELDS.get(selected_auth, [])]
        return {
            "connector": connector_key,
            "auth_type": selected_auth,
            "base_fields": base_fields,
            "auth_fields": auth_fields,
        }

    @staticmethod
    def validate_connector_auth(connector_type: str, auth_type: str) -> None:
        connector = CONNECTOR_REGISTRY.get(connector_type)
        if not connector:
            raise_api_error(400, "INVALID_CONNECTOR_TYPE", f"Unsupported connector type: {connector_type}")
        if auth_type not in connector["auth_methods"]:
            raise_api_error(400, "INVALID_AUTH_TYPE", f"Unsupported auth type '{auth_type}' for {connector_type}")
