from fastapi.testclient import TestClient
from app.main import app
import hmac
import hashlib
import json

client = TestClient(app)
SECRET = "testsecret"

def sign_payload(body: dict):
    body_bytes = json.dumps(body).encode()
    return hmac.new(SECRET.encode(), body_bytes, hashlib.sha256).hexdigest()

def test_webhook_valid_insert():
    payload = {
        "message_id": "test_m1",
        "from": "+1234567890",
        "to": "+0987654321",
        "ts": "2025-01-01T10:00:00Z",
        "text": "Hello World"
    }
    signature = sign_payload(payload)
    response = client.post("/webhook", json=payload, headers={"X-Signature": signature})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_webhook_duplicate():
    payload = {
        "message_id": "test_m1", # Same ID as above
        "from": "+1234567890",
        "to": "+0987654321",
        "ts": "2025-01-01T10:00:00Z",
        "text": "Hello World"
    }
    signature = sign_payload(payload)
    response = client.post("/webhook", json=payload, headers={"X-Signature": signature})
    assert response.status_code == 200 # Should still be 200 (idempotent)

def test_webhook_invalid_signature():
    payload = {"message_id": "bad_sig"}
    response = client.post("/webhook", json=payload, headers={"X-Signature": "wrong"})
    assert response.status_code == 401