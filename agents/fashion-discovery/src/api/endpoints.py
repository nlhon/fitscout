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
    
    This is the primary endpoint that orchestrators call to discover fashion retailers.
    It implements a multi-stage fallback strategy:
    1. Query local registry with filters
    2. If insufficient results, use Tavily to search web
    3. Optionally call matching retailers' agents for real-time data
    
    Args:
        request: FashionDiscoveryRequest with query and filters
        x_agent_id: Optional agent ID from header (for tracing)
    
    Returns:
        FashionDiscoveryResponse with matching retailers
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
        
        # Stage 1: Search registry
        log.debug(f"Stage 1: Searching registry with categories={categories}, tiers={quality_tiers}")
        matches_data = await registry_service.search(
            categories=categories if categories else None,
            quality_tiers=quality_tiers if quality_tiers else None,
            max_price=filters.max_price if filters else None
        )
        
        # Stage 2: If insufficient results, use Tavily fallback
        if len(matches_data) < 3:
            log.info(f"Registry returned {len(matches_data)} results, using Tavily fallback...")
            
            try:
                from src.services.tavily_search import tavily_service
                tavily_results = await tavily_service.search_retailers(
                    query=request.query,
                    categories=categories if categories else None
                )
                
                if tavily_results:
                    # Validate and add verified retailers to registry
                    for result in tavily_results[:5]:  # Limit to top 5
                        try:
                            # Verify URL is not blacklisted
                            if await registry_service.validate_retailer_url(result.get("website_url", "")):
                                log.debug(f"Adding Tavily result to registry: {result['name']}")
                                # Only add if not already in registry
                                existing = await registry_service.search_by_name(result['name'])
                                if not existing:
                                    result_copy = result.copy()
                                    result_copy["quality_tier"] = "premium"
                                    result_copy["is_verified"] = False  # Mark as unverified from Tavily
                                    # Don't add to DB here, just include in results
                                    matches_data.append(result_copy)
                        except Exception as e:
                            log.warning(f"Could not process Tavily result: {str(e)}")
                            continue
                            
            except Exception as e:
                log.warning(f"Tavily fallback search failed: {str(e)}")
        
        # Convert to RetailerMatch objects
        matches = []
        for retailer in matches_data[:10]:  # Limit to top 10 results
            match = RetailerMatch(
                retailer_id=retailer.get("retailer_id", f"retailer-{len(matches)}"),
                retailer_name=retailer.get("name", retailer.get("title", "Unknown")),
                website_url=retailer.get("website_url", retailer.get("source_url", "")),
                agent_endpoint=retailer.get("agent_endpoint", ""),
                category=",".join(retailer.get("categories", [])),
                confidence_score=retailer.get("confidence_score", retailer.get("verification_score", 0.75)),
                x402_endpoint=f"{retailer.get('website_url', '')}/payments" if retailer.get("x402_payment_address") else None
            )
            matches.append(match)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        query_cost = 0.001  # Base cost per query
        
        # Adjust cost based on result count and Tavily usage
        if len(matches_data) >= 5:
            query_cost = 0.0005  # Discount for good registry hit
        else:
            query_cost = 0.002  # Higher cost for Tavily fallback
        
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
        log.error(f"Error processing discovery request: {str(e)}", exc_info=True)
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
