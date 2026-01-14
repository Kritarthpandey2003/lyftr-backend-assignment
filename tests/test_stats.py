from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_stats_structure():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_messages" in data
    assert "senders_count" in data