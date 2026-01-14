from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_messages_pagination():
    # Basic call to ensure endpoint works
    response = client.get("/messages?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data

def test_list_messages_filter():
    response = client.get("/messages?from=+1234567890")
    assert response.status_code == 200