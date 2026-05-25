def test_list_connectors(client):
    response = client.get("/api/v1/connectors")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert len(body["data"]) >= 12


def test_connector_fields_with_auth(client):
    response = client.get("/api/v1/connectors/postgres/fields", params={"auth_type": "iam"})
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["auth_type"] == "iam"
    assert body["data"]["auth_fields"][0]["name"] == "iam_credentials"
