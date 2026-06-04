"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class OutfitGenerationRequest(BaseModel):
    """Request model for outfit image generation"""
    user_prompt: str = Field(..., min_length=5, max_length=500, description="Outfit description")
    style: Optional[str] = Field(None, description="Style preference (casual, formal, sporty, etc.)")
    count: Optional[int] = Field(1, ge=1, le=10, description="Number of variations to generate")
    
    class Config:
        example = {
            "user_prompt": "casual summer dress with sandals",
            "style": "casual",
            "count": 3
        }


class ShoppingResult(BaseModel):
    """Individual shopping result"""
    title: str = Field(..., description="Product title")
    source: str = Field(..., description="Retailer name")
    link: str = Field(..., description="Product link")
    thumbnail: Optional[str] = Field(None, description="Product thumbnail URL")
    price: str = Field(..., description="Product price")
    rating: Optional[str] = Field(None, description="Product rating")
    reviews: Optional[str] = Field(None, description="Number of reviews")


class OutfitToShopResponse(BaseModel):
    """Response model for complete outfit-to-shop process"""
    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Request status (success, processing, failed)")
    outfit_image_url: Optional[str] = Field(None, description="Generated outfit image URL")
    shopping_results: List[ShoppingResult] = Field(..., description="Matching shopping products")
    total_results: int = Field(..., description="Total number of shopping results")
    processing_time_ms: int = Field(..., description="Time taken to process in milliseconds")
    message: str = Field(..., description="Status message")
    
    class Config:
        example = {
            "request_id": "req-12345",
            "status": "success",
            "outfit_image_url": "https://...",
            "shopping_results": [
                {
                    "title": "Summer Dress",
                    "source": "ASOS",
                    "link": "https://asos.com/...",
                    "price": "$45",
                    "thumbnail": "https://..."
                }
            ],
            "total_results": 5,
            "processing_time_ms": 2500,
            "message": "Successfully generated outfit and found shopping matches"
        }


class MultiOutfitToShopResponse(BaseModel):
    """Response model for multiple outfit variations"""
    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Request status")
    outfit_images: List[str] = Field(..., description="List of generated outfit image URLs")
    aggregated_shopping: dict = Field(..., description="Shopping results per image")
    total_unique_products: int = Field(..., description="Total unique products found")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    message: str = Field(..., description="Status message")


class SearchShoppingRequest(BaseModel):
    """Request model for shopping search by image URL"""
    image_url: HttpUrl = Field(..., description="Image URL to search")
    category: Optional[str] = Field(None, description="Optional category filter")


class SearchShoppingResponse(BaseModel):
    """Response model for shopping search"""
    request_id: str = Field(...)
    status: str = Field(...)
    shopping_results: List[ShoppingResult] = Field(...)
    total_results: int = Field(...)
    category_filter: Optional[str] = Field(None)
    processing_time_ms: int = Field(...)
    message: str = Field(...)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    replicate_configured: bool = Field(..., description="Replicate API configured")
    serpapi_configured: bool = Field(..., description="SerpApi configured")
    message: str = Field(...)
