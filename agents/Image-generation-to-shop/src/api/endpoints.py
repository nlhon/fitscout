"""
FastAPI endpoints for Image-generation-to-shop agent
Main orchestration: Generate outfit image + Search shopping links
"""

import uuid
import time
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List

from src.services.image_generator import generate_outfit_image, generate_multiple_outfits
from src.services.shopping_searcher import search_shopping_links, search_shopping_links_by_category, aggregate_shopping_results
from src.api.models import (
    OutfitGenerationRequest,
    ShoppingResult,
    OutfitToShopResponse,
    MultiOutfitToShopResponse,
    SearchShoppingRequest,
    SearchShoppingResponse,
    HealthCheckResponse
)
from config.settings import settings

router = APIRouter(prefix="/api/v1", tags=["image-generation-to-shop"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check service health and API configuration"""
    return HealthCheckResponse(
        status="operational",
        replicate_configured=bool(settings.REPLICATE_API_TOKEN),
        serpapi_configured=bool(settings.SERPAPI_API_KEY),
        message="Image-generation-to-shop agent is running"
    )


@router.post("/outfit-to-shop", response_model=OutfitToShopResponse)
async def outfit_to_shop(request: OutfitGenerationRequest) -> OutfitToShopResponse:
    """
    Main endpoint: Generate outfit image + Find shopping matches
    
    Two-stage process:
    1. Generate outfit image using Replicate
    2. Search for shopping matches using SerpApi Google Lens
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Step 1: Generate outfit image
        try:
            outfit_image_url = await generate_outfit_image(request.user_prompt)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Image generation failed: {str(e)}"
            )
        
        # Step 2: Search for shopping matches
        try:
            shopping_results_raw = await search_shopping_links(outfit_image_url)
            shopping_results = [ShoppingResult(**result) for result in shopping_results_raw]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Shopping search failed: {str(e)}"
            )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return OutfitToShopResponse(
            request_id=request_id,
            status="success",
            outfit_image_url=outfit_image_url,
            shopping_results=shopping_results,
            total_results=len(shopping_results),
            processing_time_ms=processing_time_ms,
            message=f"Successfully generated outfit and found {len(shopping_results)} shopping matches"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        raise HTTPException(
            status_code=500,
            detail=f"Outfit-to-shop processing failed: {str(e)}"
        )


@router.post("/multi-outfit-to-shop", response_model=MultiOutfitToShopResponse)
async def multi_outfit_to_shop(request: OutfitGenerationRequest) -> MultiOutfitToShopResponse:
    """
    Generate multiple outfit variations + Find shopping matches for each
    
    Args:
        request: OutfitGenerationRequest with count (1-10)
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Generate multiple outfits
        outfit_image_urls = await generate_multiple_outfits(request.user_prompt, request.count or 1)
        
        # Search shopping links for each image
        aggregated_shopping = await aggregate_shopping_results(outfit_image_urls)
        
        # Count unique products
        total_unique = sum(r.get("count", 0) for r in aggregated_shopping.values())
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return MultiOutfitToShopResponse(
            request_id=request_id,
            status="success",
            outfit_images=outfit_image_urls,
            aggregated_shopping=aggregated_shopping,
            total_unique_products=total_unique,
            processing_time_ms=processing_time_ms,
            message=f"Generated {len(outfit_image_urls)} outfits and found {total_unique} shopping matches"
        )
        
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        raise HTTPException(
            status_code=500,
            detail=f"Multi-outfit processing failed: {str(e)}"
        )


@router.post("/search-shopping", response_model=SearchShoppingResponse)
async def search_shopping(request: SearchShoppingRequest) -> SearchShoppingResponse:
    """
    Search for shopping matches for a provided outfit image URL
    
    Args:
        request: SearchShoppingRequest with image_url and optional category
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        if request.category:
            shopping_results_raw = await search_shopping_links_by_category(
                str(request.image_url),
                request.category
            )
        else:
            shopping_results_raw = await search_shopping_links(str(request.image_url))
        
        shopping_results = [ShoppingResult(**result) for result in shopping_results_raw]
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return SearchShoppingResponse(
            request_id=request_id,
            status="success",
            shopping_results=shopping_results,
            total_results=len(shopping_results),
            category_filter=request.category,
            processing_time_ms=processing_time_ms,
            message=f"Found {len(shopping_results)} shopping matches"
        )
        
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        raise HTTPException(
            status_code=500,
            detail=f"Shopping search failed: {str(e)}"
        )


@router.get("/")
async def root():
    """Root endpoint - service info"""
    return {
        "name": "Image-generation-to-shop Agent",
        "version": "1.0.0",
        "description": "Generate outfit images and find shopping links",
        "endpoints": {
            "POST /api/v1/outfit-to-shop": "Generate single outfit + find shopping matches",
            "POST /api/v1/multi-outfit-to-shop": "Generate multiple outfits + shopping matches",
            "POST /api/v1/search-shopping": "Search shopping for existing image",
            "GET /health": "Health check"
        }
    }
