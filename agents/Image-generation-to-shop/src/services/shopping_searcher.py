"""
Shopping Links Search Service using SerpApi Google Lens
Finds retail products matching generated outfit images
"""

import requests
from typing import List, Dict
from config.settings import settings


async def search_shopping_links(image_url: str) -> List[Dict]:
    """
    Step 2: Takes an outfit image URL and queries Google Lens 
    via SerpApi to find matching retail products.
    
    Args:
        image_url: URL of the outfit image
        
    Returns:
        list: Shopping results with title, source, link, thumbnail, price
        
    Raises:
        ValueError: If API key is not configured
        Exception: If SerpApi request fails
    """
    if not settings.SERPAPI_API_KEY:
        raise ValueError("SERPAPI_API_KEY not configured")
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": settings.SERPAPI_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.Timeout:
        raise Exception("SerpApi request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"SerpApi request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to parse SerpApi response: {str(e)}")
    
    shopping_results = []
    visual_matches = data.get("visual_matches", [])
    
    for match in visual_matches:
        if "link" in match and "title" in match:
            result = {
                "title": match.get("title", "Unknown Item"),
                "source": match.get("source", "Unknown Retailer"),
                "link": match.get("link", ""),
                "thumbnail": match.get("thumbnail", ""),
                "price": match.get("price", {}).get("extracted", "N/A"),
                "rating": match.get("rating", "N/A"),
                "reviews": match.get("reviews", "N/A")
            }
            shopping_results.append(result)
    
    return shopping_results


async def search_shopping_links_by_category(image_url: str, category: str = None) -> List[Dict]:
    """
    Search for shopping links filtered by category.
    
    Args:
        image_url: URL of the outfit image
        category: Optional category filter (e.g., 'dresses', 'shoes', 'accessories')
        
    Returns:
        list: Filtered shopping results
    """
    results = await search_shopping_links(image_url)
    
    if not category:
        return results
    
    # Filter results by category in title or source
    category_lower = category.lower()
    filtered = [
        r for r in results 
        if category_lower in r.get("title", "").lower() 
        or category_lower in r.get("source", "").lower()
    ]
    
    return filtered if filtered else results


async def aggregate_shopping_results(image_urls: List[str]) -> Dict:
    """
    Aggregate shopping results from multiple images.
    
    Args:
        image_urls: List of image URLs
        
    Returns:
        dict: Aggregated results by image
    """
    aggregated = {}
    
    for idx, image_url in enumerate(image_urls):
        try:
            results = await search_shopping_links(image_url)
            aggregated[f"image_{idx + 1}"] = {
                "url": image_url,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            aggregated[f"image_{idx + 1}"] = {
                "url": image_url,
                "error": str(e),
                "results": []
            }
    
    return aggregated
