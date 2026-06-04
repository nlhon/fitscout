"""
A2A Protocol API endpoints for Fashion Discovery Sub-Agent
"""

import logging
import time
from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from src.api.models import (
    FashionDiscoveryRequest,
    FashionDiscoveryResponse,
    RetailerMatch,
    ErrorResponse
)
from src.services.registry import registry_service
from src.services.query_processor import query_processor
from src.database import db
from src.database.models import SearchQuery

log = logging.getLogger(__name__)
router = APIRouter()

@router.post("/fashion-discovery", response_model=FashionDiscoveryResponse)
async def fashion_discovery(
    request: FashionDiscoveryRequest,
    x_agent_id: Optional[str] = Header(None)
):
    """
    Main A2A Protocol endpoint for fashion retailer discovery
    
    Args:
        request: FashionDiscoveryRequest with query and filters
        x_agent_id: Optional agent ID from header (for tracing)
    
    Returns:
        FashionDiscoveryResponse with matching retailers
    
    Example Request:
        {
            "agent_id": "orchestrator-123",
            "request_id": "req-456",
            "query": "luxury puffer jackets under $5000",
            "filters": {
                "max_price": 5000,
                "categories": ["outerwear", "jackets"],
                "quality_tiers": ["luxury", "premium"]
            },
            "x402_budget": 0.05
        }
    """
    start_time = time.time()
    
    try:
        log.info(f"Received discovery request: {request.request_id} from agent: {request.agent_id}")
        
        # Validate query
        if not await query_processor.validate_query(request.query):
            raise ValueError("Invalid or empty query")
        
        # Parse filters
        filters = request.filters or {}
        quality_tiers = filters.quality_tiers if filters else ["luxury", "premium"]
        categories = filters.categories if filters else []
        
        # Search registry
        matches_data = await registry_service.search(
            categories=categories if categories else None,
            quality_tiers=quality_tiers if quality_tiers else None,
            max_price=filters.max_price if filters else None
        )
        
        # Convert to RetailerMatch objects
        matches = []
        for retailer in matches_data:
            match = RetailerMatch(
                retailer_id=retailer["retailer_id"],
                retailer_name=retailer["name"],
                website_url=retailer["website_url"],
                agent_endpoint=retailer["agent_endpoint"],
                category=",".join(retailer.get("categories", [])),
                confidence_score=retailer.get("verification_score", 0.85),
                x402_endpoint=f"{retailer['website_url']}/payments" if retailer.get("x402_payment_address") else None
            )
            matches.append(match)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        query_cost = 0.001  # Base cost per query
        
        response = FashionDiscoveryResponse(
            request_id=request.request_id,
            matches=matches,
            total_matches=len(matches),
            query_cost=query_cost,
            message=f"Found {len(matches)} luxury fashion retailers matching your criteria"
        )
        
        # Log query to analytics
        with db.session_scope() as session:
            search_log = SearchQuery(
                request_id=request.request_id,
                agent_id=request.agent_id,
                query=request.query,
                filters=dict(filters) if filters else {},
                results_count=len(matches),
                query_cost=query_cost,
                response_time_ms=response_time_ms
            )
            session.add(search_log)
        
        log.info(f"Returning {len(matches)} matches for request: {request.request_id} ({response_time_ms:.2f}ms)")
        return response
        
    except ValueError as e:
        log.warning(f"Validation error in discovery request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        log.error(f"Error processing discovery request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing discovery request: {str(e)}"
        )

@router.get("/registry/health")
async def registry_health():
    """
    Check registry service health and statistics
    """
    try:
        stats = await registry_service.get_stats()
        return {
            "status": "operational",
            "registry": "active",
            "last_sync": "2026-06-04T00:00:00Z",
            "statistics": stats
        }
    except Exception as e:
        log.error(f"Error getting registry health: {str(e)}")
        return {
            "status": "degraded",
            "registry": "error",
            "error": str(e)
        }

@router.get("/tavily/status")
async def tavily_status():
    """
    Check Tavily search integration status
    """
    try:
        from src.services.tavily_search import tavily_service
        config = tavily_service.get_exclusion_config()
        return {
            "status": "operational",
            "api": "connected",
            "exclusions": f"{len(config['exclude_domains'])} domains excluded",
            "search_depth": config['depth'],
            "max_results": config['max_results']
        }
    except Exception as e:
        log.error(f"Error checking Tavily status: {str(e)}")
        return {
            "status": "error",
            "api": "unavailable",
            "error": str(e)
        }

@router.get("/statistics")
async def statistics():
    """
    Get agent statistics and metrics
    """
    try:
        stats = await registry_service.get_stats()
        
        # Get query stats
        with db.session_scope() as session:
            total_queries = session.query(SearchQuery).count()
            from sqlalchemy import func
            avg_response_time = session.query(
                func.avg(SearchQuery.response_time_ms)
            ).scalar() or 0.0
        
        return {
            "total_retailers": stats["total_retailers"],
            "active_retailers": stats["active_retailers"],
            "verified_retailers": stats["verified_retailers"],
            "blacklist_domains": stats["blacklist_entries"],
            "total_discovery_requests": total_queries,
            "average_response_time_ms": round(avg_response_time, 2),
            "uptime": "operational"
        }
    except Exception as e:
        log.error(f"Error getting statistics: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
