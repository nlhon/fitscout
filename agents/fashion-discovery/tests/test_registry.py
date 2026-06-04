"""
Tests for Registry Service
"""

import pytest
import asyncio
from src.database import db
from src.services.registry import registry_service

# Setup and teardown
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database for tests"""
    db.initialize()
    yield
    db.close()

@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test"""
    from src.database.models import Retailer, BlacklistEntry, SearchQuery
    with db.session_scope() as session:
        session.query(SearchQuery).delete()
        session.query(Retailer).delete()
        # Don't delete blacklist - it's common for all tests
    yield

@pytest.mark.asyncio
async def test_validate_blacklist_amazon():
    """Test that amazon.com is blocked"""
    result = await registry_service.validate_retailer_url("https://amazon.com/luxury")
    assert result == False

@pytest.mark.asyncio
async def test_validate_blacklist_shein():
    """Test that shein.com is blocked"""
    result = await registry_service.validate_retailer_url("https://shein.com")
    assert result == False

@pytest.mark.asyncio
async def test_validate_luxury_retailer():
    """Test that luxury retailer URL passes validation"""
    result = await registry_service.validate_retailer_url("https://houseofnova.xyz")
    assert result == True

@pytest.mark.asyncio
async def test_add_retailer():
    """Test adding a new retailer"""
    retailer_data = {
        "retailer_id": "test-luxury-001",
        "name": "Test Luxury Store",
        "website_url": "https://testluxury.com",
        "agent_endpoint": "https://testluxury.com/api/agent",
        "quality_tier": "luxury",
        "categories": ["luxury-fashion", "designer"],
        "is_verified": True
    }
    
    added = await registry_service.add_retailer(retailer_data)
    
    assert added["retailer_id"] == "test-luxury-001"
    assert added["name"] == "Test Luxury Store"

@pytest.mark.asyncio
async def test_add_retailer_blacklisted_url():
    """Test that adding blacklisted retailer fails"""
    retailer_data = {
        "retailer_id": "amazon-attempt",
        "name": "Amazon",
        "website_url": "https://amazon.com",
        "agent_endpoint": "https://amazon.com/api",
        "quality_tier": "luxury"
    }
    
    with pytest.raises(ValueError):
        await registry_service.add_retailer(retailer_data)

@pytest.mark.asyncio
async def test_add_retailer_missing_fields():
    """Test that adding retailer without required fields fails"""
    retailer_data = {
        "retailer_id": "incomplete"
        # Missing required fields
    }
    
    with pytest.raises(ValueError):
        await registry_service.add_retailer(retailer_data)

@pytest.mark.asyncio
async def test_search_by_name():
    """Test searching for retailer by name"""
    # Add a retailer first
    retailer_data = {
        "retailer_id": "nova-001",
        "name": "House of Nova",
        "website_url": "https://houseofnova.xyz",
        "agent_endpoint": "https://houseofnova.xyz/api",
        "is_verified": True
    }
    await registry_service.add_retailer(retailer_data)
    
    # Search for it
    found = await registry_service.search_by_name("Nova")
    assert found is not None
    assert found["name"] == "House of Nova"

@pytest.mark.asyncio
async def test_search_by_category():
    """Test searching retailers by category"""
    # Add retailers with categories
    retailer1 = {
        "retailer_id": "coats-001",
        "name": "Coat Specialist",
        "website_url": "https://coats.com",
        "agent_endpoint": "https://coats.com/api",
        "categories": ["outerwear", "luxury-coats"],
        "is_verified": True
    }
    retailer2 = {
        "retailer_id": "shoes-001",
        "name": "Shoe Palace",
        "website_url": "https://shoes.com",
        "agent_endpoint": "https://shoes.com/api",
        "categories": ["shoes", "designer"],
        "is_verified": True
    }
    
    await registry_service.add_retailer(retailer1)
    await registry_service.add_retailer(retailer2)
    
    # Search by category
    results = await registry_service.search(categories=["outerwear"])
    assert len(results) >= 1
    assert any(r["retailer_id"] == "coats-001" for r in results)

@pytest.mark.asyncio
async def test_search_by_quality_tier():
    """Test searching by quality tier"""
    # Add retailers with different tiers
    luxury = {
        "retailer_id": "luxury-001",
        "name": "Luxury Brand",
        "website_url": "https://luxury.com",
        "agent_endpoint": "https://luxury.com/api",
        "quality_tier": "luxury",
        "is_verified": True
    }
    premium = {
        "retailer_id": "premium-001",
        "name": "Premium Brand",
        "website_url": "https://premium.com",
        "agent_endpoint": "https://premium.com/api",
        "quality_tier": "premium",
        "is_verified": True
    }
    
    await registry_service.add_retailer(luxury)
    await registry_service.add_retailer(premium)
    
    # Search for luxury only
    results = await registry_service.search(quality_tiers=["luxury"])
    assert any(r["retailer_id"] == "luxury-001" for r in results)

@pytest.mark.asyncio
async def test_get_stats():
    """Test getting registry statistics"""
    # Add some retailers
    for i in range(3):
        retailer_data = {
            "retailer_id": f"test-{i}",
            "name": f"Test Store {i}",
            "website_url": f"https://test{i}.com",
            "agent_endpoint": f"https://test{i}.com/api",
            "is_verified": True
        }
        await registry_service.add_retailer(retailer_data)
    
    stats = await registry_service.get_stats()
    
    assert stats["total_retailers"] >= 3
    assert stats["active_retailers"] >= 3
    assert stats["verified_retailers"] >= 3
    assert "blacklist_entries" in stats
