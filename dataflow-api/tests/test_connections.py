def _payload(name="conn_a"):
    return {
        "connection_name": name,
        "connection_type": "sqlite",
        "connection_domain_name": "finance",
        "is_target": 0,
        "env_type": "dev",
        "auth_type": "none",
        "details": {"db_file_path": "/tmp/workspace/punamdh/databricks-backend/dataflow-api/test.db"},
        "auth": {},
        "created_by": "tester",
        "updated_by": "tester",
    }


def test_create_get_and_list_connection(client):
    created = client.post("/api/v1/connections", json=_payload())
    assert created.status_code == 200
    cid = created.json()["data"]["connection_id"]

    fetched = client.get(f"/api/v1/connections/{cid}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["connection_name"] == "conn_a"

    listed = client.get("/api/v1/connections", params={"page": 1, "page_size": 20})
    assert listed.status_code == 200
    assert listed.json()["pagination"]["total"] == 1


def test_connection_duplicate_name_rejected(client):
    first = client.post("/api/v1/connections", json=_payload("dup"))
    assert first.status_code == 200

    second = client.post("/api/v1/connections", json=_payload("dup"))
    assert second.status_code == 409
    assert second.json()["detail"]["error_code"] == "DUPLICATE_CONNECTION_NAME"
