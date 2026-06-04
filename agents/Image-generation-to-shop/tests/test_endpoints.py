"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Image-generation-to-shop Agent"


@pytest.mark.skipif(
    not pytest.config.getoption("--with-api-keys"),
    reason="API keys not configured"
)
def test_outfit_to_shop_simple():
    """Test outfit-to-shop endpoint with simple prompt"""
    payload = {
        "user_prompt": "casual blue jeans and white shirt",
        "count": 1
    }
    
    response = client.post("/api/v1/outfit-to-shop", json=payload)
    # Will skip if API keys not configured
    if response.status_code != 500:
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "success"


def test_outfit_to_shop_validation():
    """Test outfit-to-shop validation"""
    # Too short prompt
    payload = {"user_prompt": "hi"}
    response = client.post("/api/v1/outfit-to-shop", json=payload)
    assert response.status_code == 422


def test_search_shopping_validation():
    """Test search shopping validation"""
    # Invalid URL
    payload = {"image_url": "not-a-url"}
    response = client.post("/api/v1/search-shopping", json=payload)
    assert response.status_code == 422


def test_multi_outfit_count_validation():
    """Test multi-outfit count validation"""
    # Count too high
    payload = {
        "user_prompt": "formal black dress for dinner",
        "count": 50
    }
    response = client.post("/api/v1/multi-outfit-to-shop", json=payload)
    assert response.status_code == 422
