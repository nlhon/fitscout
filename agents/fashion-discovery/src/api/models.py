"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Request Models
class SearchFilters(BaseModel):
    """Filter parameters for fashion discovery"""
    max_price: Optional[float] = Field(None, description="Maximum price in USD")
    categories: Optional[List[str]] = Field(None, description="Fashion categories (e.g., outerwear, jackets)")
    quality_tiers: Optional[List[str]] = Field(None, description="Quality tiers (luxury, premium, emerging)")
    exclude_retailers: Optional[List[str]] = Field(None, description="Retailer names to exclude")

class FashionDiscoveryRequest(BaseModel):
    """A2A Protocol request for fashion discovery"""
    agent_id: str = Field(..., description="ID of the requesting orchestrator")
    request_id: str = Field(..., description="Unique request ID")
    query: str = Field(..., description="Natural language search query (e.g., 'luxury puffer jackets under $5000')")
    filters: Optional[SearchFilters] = Field(None, description="Additional filter parameters")
    x402_budget: Optional[float] = Field(None, description="X402 micropayment budget (in XRP)")

# Response Models
class RetailerMatch(BaseModel):
    """Individual retailer match in discovery results"""
    retailer_id: str
    retailer_name: str
    website_url: str
    agent_endpoint: str
    category: str
    confidence_score: float = Field(..., description="Match confidence (0.0 to 1.0)")
    x402_endpoint: Optional[str] = Field(None, description="Payment endpoint for X402 protocol")

class FashionDiscoveryResponse(BaseModel):
    """A2A Protocol response with discovery results"""
    request_id: str
    matches: List[RetailerMatch]
    total_matches: int
    query_cost: float = Field(0.0, description="X402 cost in XRP for this query")
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
