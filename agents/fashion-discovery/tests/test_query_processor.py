"""
Tests for Query Processor Service
"""

import pytest
from src.services.query_processor import query_processor

@pytest.mark.asyncio
async def test_parse_luxury_query():
    """Test parsing luxury fashion query"""
    result = await query_processor.parse_query("luxury puffer jackets under $5000")
    
    assert result["quality_tier"] == "luxury"
    assert "outerwear" in result["product_type"]
    assert result["price_range"]["max"] == 5000

@pytest.mark.asyncio
async def test_parse_premium_query():
    """Test parsing premium quality query"""
    result = await query_processor.parse_query("premium designer shoes")
    
    assert result["quality_tier"] == "premium"
    assert "shoes" in result["product_type"]

@pytest.mark.asyncio
async def test_parse_query_with_color():
    """Test parsing query with color preference"""
    result = await query_processor.parse_query("black luxury coats")
    
    assert "black" in result.get("style", [])  # Or check filters
    assert "outerwear" in result["product_type"]

@pytest.mark.asyncio
async def test_validate_short_query():
    """Test validation of too-short query"""
    result = await query_processor.validate_query("xy")
    assert result == False

@pytest.mark.asyncio
async def test_validate_empty_query():
    """Test validation of empty query"""
    result = await query_processor.validate_query("")
    assert result == False

@pytest.mark.asyncio
async def test_validate_long_query():
    """Test validation of excessively long query"""
    long_query = "x" * 1001
    result = await query_processor.validate_query(long_query)
    assert result == False

@pytest.mark.asyncio
async def test_validate_valid_query():
    """Test validation of valid query"""
    result = await query_processor.validate_query("luxury puffer jackets")
    assert result == True

@pytest.mark.asyncio
async def test_extract_filters_price():
    """Test price filter extraction"""
    filters = await query_processor.extract_filters("coats under $3000")
    
    assert filters["max_price"] == 3000

@pytest.mark.asyncio
async def test_extract_filters_color():
    """Test color filter extraction"""
    filters = await query_processor.extract_filters("white luxury coat")
    
    assert "white" in filters["colors"]

@pytest.mark.asyncio
async def test_categorize_intent_search():
    """Test intent classification for search"""
    intent = await query_processor.categorize_intent("find luxury jackets")
    assert intent == "product_search"

@pytest.mark.asyncio
async def test_categorize_intent_comparison():
    """Test intent classification for comparison"""
    intent = await query_processor.categorize_intent("compare luxury vs premium coats")
    assert intent == "comparison"

@pytest.mark.asyncio
async def test_categorize_intent_price():
    """Test intent classification for price search"""
    intent = await query_processor.categorize_intent("how much are luxury puffer jackets")
    assert intent == "price_search"
