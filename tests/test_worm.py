import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_write_and_read():
    # 1. Write a log
    payload = {"source": "AuthService", "message": "User admin logged in successfully."}
    response = client.post("/logs", json=payload)
    assert response.status_code == 201

    # 2. Read the logs and verify that it exists
    read_response = client.get("/logs")
    assert read_response.status_code == 200
    assert any("User administrator logged in successfully." in log for log in read_response.json()["logs"])

def test_worm_constraints():
    # Try to DELETE - Operation should be blocked
    delete_response = client.delete("/logs")
    assert delete_response.status_code == 403
    assert "WORM Policy Violation" in delete_response.json()["detail"]

    # Try to PUT (Modify) - Operation should be blocked
    put_response = client.put("/logs")
    assert put_response.status_code == 403