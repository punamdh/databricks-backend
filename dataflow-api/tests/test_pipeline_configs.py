def _connection_payload():
    return {
        "connection_name": "source_conn",
        "connection_type": "sqlite",
        "connection_domain_name": "sales",
        "is_target": 0,
        "env_type": "dev",
        "auth_type": "none",
        "details": {"db_file_path": "/tmp/workspace/punamdh/databricks-backend/dataflow-api/test.db"},
        "auth": {},
        "created_by": "tester",
        "updated_by": "tester",
    }


def _pipeline_payload(connection_id):
    return {
        "connection_source_id": connection_id,
        "connection_domain_name": "sales",
        "config_group": "grp_a",
        "source_attributes": {"schema": "main", "table": "orders"},
        "target_attributes": {"catalog": "cat", "schema": "silver", "table": "orders_s"},
        "load_type": "full",
        "env_type": "dev",
        "created_by": "tester",
        "updated_by": "tester",
    }


def test_pipeline_config_crud_and_watermark(client):
    conn = client.post("/api/v1/connections", json=_connection_payload()).json()["data"]

    created = client.post("/api/v1/pipeline-configs", json=_pipeline_payload(conn["connection_id"]))
    assert created.status_code == 200
    table_config_id = created.json()["data"]["table_config_id"]

    wm = client.put(
        f"/api/v1/pipeline-configs/{table_config_id}/watermark",
        json={"watermark_column": "updated_at", "watermark_type": "timestamp", "last_value": "2026-01-01T00:00:00Z", "env_type": "dev", "updated_by": "tester"},
    )
    assert wm.status_code == 200

    fetched = client.get(f"/api/v1/pipeline-configs/{table_config_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["config_group"] == "grp_a"


def test_pipeline_invalid_source_attrs(client):
    conn = client.post("/api/v1/connections", json=_connection_payload()).json()["data"]
    payload = _pipeline_payload(conn["connection_id"])
    payload["source_attributes"] = {"schema": "missing_table"}
    response = client.post("/api/v1/pipeline-configs", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "INVALID_SOURCE_ATTRIBUTES"
