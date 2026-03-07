import pytest
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_multimodal_request_parse():
    payload = {
        "message": "Hello",
        "images": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="],
        "history": [],
        "summary": ""
    }
    with client.stream("POST", "/chat", json=payload) as response:
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__])
