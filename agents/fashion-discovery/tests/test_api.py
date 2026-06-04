"""
Tests for API Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import db

# Initialize database
db.initialize()

client = TestClient(app)

def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_registry_health():
    """Test registry health endpoint"""
    response = client.get("/api/v1/registry/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "statistics" in data

def test_tavily_status():
    """Test Tavily status endpoint"""
    response = client.get("/api/v1/tavily/status")
    assert response.status_code in [200, 500]  # May fail if API key not set

def test_statistics():
    """Test statistics endpoint"""
    response = client.get("/api/v1/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_retailers" in data
    assert "average_response_time_ms" in data

def test_fashion_discovery_simple():
    """Test basic fashion discovery request"""
    payload = {
        "agent_id": "test-orchestrator",
        "request_id": "test-req-001",
        "query": "luxury puffer jackets",
        "x402_budget": 0.01
    }
    
    response = client.post("/api/v1/fashion-discovery", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["request_id"] == "test-req-001"
    assert "matches" in data
    assert "total_matches" in data
    assert "query_cost" in data

def test_fashion_discovery_with_filters():
    """Test discovery request with filters"""
    payload = {
        "agent_id": "test-orchestrator",
        "request_id": "test-req-002",
        "query": "luxury designer shoes",
        "filters": {
            "max_price": 5000,
            "categories": ["shoes"],
            "quality_tiers": ["luxury"]
        },
        "x402_budget": 0.05
    }
    
    response = client.post("/api/v1/fashion-discovery", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["request_id"] == "test-req-002"
    assert isinstance(data["matches"], list)

def test_fashion_discovery_invalid_query():
    """Test discovery with invalid query"""
    payload = {
        "agent_id": "test-orchestrator",
        "request_id": "test-req-003",
        "query": ""  # Empty query
    }
    
    response = client.post("/api/v1/fashion-discovery", json=payload)
    assert response.status_code == 400

def test_fashion_discovery_missing_required_field():
    """Test discovery with missing required fields"""
    payload = {
        "agent_id": "test-orchestrator",
        # Missing request_id and query
    }
    
    response = client.post("/api/v1/fashion-discovery", json=payload)
    assert response.status_code in [400, 422]  # Validation error

@pytest.mark.asyncio
async def test_discovery_response_format():
    """Test that discovery response has correct format"""
    payload = {
        "agent_id": "test-agent",
        "request_id": "format-test",
        "query": "luxury outerwear"
    }
    
    response = client.post("/api/v1/fashion-discovery", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check top-level fields
    assert "request_id" in data
    assert "matches" in data
    assert "total_matches" in data
    assert "query_cost" in data
    
    # Check match structure
    for match in data.get("matches", []):
        assert "retailer_id" in match
        assert "retailer_name" in match
        assert "website_url" in match
        assert "agent_endpoint" in match
        assert "category" in match
        assert "confidence_score" in match
