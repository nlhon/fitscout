"""
Tavily Search Integration Service
Performs intelligent web searches for fashion retailers
"""

import logging
import httpx
import json
from typing import List, Dict, Optional
from config.settings import settings

log = logging.getLogger(__name__)

class TavilySearchService:
    """Service for Tavily-based web search"""
    
    def __init__(self):
        """Initialize Tavily search service"""
        self.api_key = settings.TAVILY_API_KEY
        self.search_depth = settings.TAVILY_SEARCH_DEPTH
        self.max_results = settings.TAVILY_MAX_RESULTS
        self.excluded_domains = settings.BLACKLIST_DOMAINS
        self.base_url = "https://api.tavily.com"
    
    async def search_retailers(
        self,
        query: str,
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search for luxury fashion retailers using Tavily API
        
        Args:
            query: Search query (e.g., "luxury puffer jackets")
            categories: Optional product categories to refine search
        
        Returns:
            List of search results with retailer information
        
        Note:
            - Automatically excludes blacklist domains
            - Returns AI-ready structured responses
        """
        try:
            log.info(f"Starting Tavily search: {query}")
            
            # Build search query with category enrichment
            search_query = query
            if categories:
                search_query += f" {' '.join(categories)}"
            
            # Build Tavily API request
            payload = {
                "api_key": self.api_key,
                "query": search_query,
                "search_depth": self.search_depth,
                "max_results": self.max_results,
                "include_images": False,
                "include_answer": False,
                "exclude_domains": self.excluded_domains
            }
            
            log.debug(f"Tavily request: {json.dumps({k: v for k, v in payload.items() if k != 'api_key'})}")
            
            # Make API call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload
                )
                response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            log.info(f"Tavily search completed: {len(results)} results")
            
            # Parse results into structured format
            parsed_results = []
            for result in results:
                parsed_result = {
                    "retailer_id": f"tavily-{len(parsed_results):03d}",
                    "name": self._extract_retailer_name(result.get("title", "")),
                    "website_url": result.get("url", ""),
                    "source_url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "title": result.get("title", ""),
                    "confidence_score": self._calculate_confidence(result),
                    "categories": self._extract_categories(result.get("content", ""), query),
                }
                parsed_results.append(parsed_result)
            
            return parsed_results
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                log.error("Tavily API authentication failed. Check API key.")
            else:
                log.error(f"Tavily API error: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            log.error(f"Tavily request error: {str(e)}")
            return []
        except Exception as e:
            log.error(f"Tavily search failed: {str(e)}")
            return []
    
    async def verify_retailer(self, url: str) -> bool:
        """
        Verify retailer is active and luxury-tier using Tavily
        
        Args:
            url: Retailer website URL
        
        Returns:
            True if verified as active luxury retailer
        """
        try:
            log.debug(f"Verifying retailer: {url}")
            
            # Search specifically for this retailer
            query = f"site:{self._extract_domain(url)} luxury fashion shopping"
            
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 1,
                "include_answer": False
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload
                )
                response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            is_verified = len(results) > 0
            log.debug(f"Retailer verification result: {url} = {is_verified}")
            
            return is_verified
            
        except Exception as e:
            log.warning(f"Error verifying retailer {url}: {str(e)}")
            return False
    
    def get_exclusion_config(self) -> Dict:
        """
        Get Tavily exclusion configuration
        
        Returns:
            Configuration for excluding blacklist domains
        """
        return {
            "exclude_domains": self.excluded_domains,
            "depth": self.search_depth,
            "max_results": self.max_results,
            "total_excluded": len(self.excluded_domains)
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return url
    
    def _extract_retailer_name(self, title: str) -> str:
        """Extract retailer name from search result title"""
        # Remove common suffixes
        for suffix in [" | Buy Online", " | Shop", " | Official", " - Buy", " Online"]:
            if suffix in title:
                title = title.split(suffix)[0]
        return title.strip()
    
    def _calculate_confidence(self, result: Dict) -> float:
        """
        Calculate confidence score for search result
        
        Args:
            result: Tavily search result
        
        Returns:
            Confidence score 0.0-1.0
        """
        score = 0.5  # Base score
        
        # Boost for official domain indicators
        url = result.get("url", "").lower()
        if ".com" in url or ".net" in url:
            score += 0.2
        
        # Check content for luxury indicators
        content = (result.get("content", "") + result.get("title", "")).lower()
        luxury_keywords = ["luxury", "designer", "premium", "haute couture", "exclusive", "bespoke"]
        for keyword in luxury_keywords:
            if keyword in content:
                score += 0.1
                break
        
        return min(score, 1.0)
    
    def _extract_categories(self, content: str, query: str) -> List[str]:
        """
        Extract product categories from search result
        
        Args:
            content: Search result content
            query: Original search query
        
        Returns:
            List of detected categories
        """
        categories = []
        content_lower = (content + " " + query).lower()
        
        # Fashion category keywords
        category_keywords = {
            "outerwear": ["coat", "puffer", "jacket", "blazer"],
            "luxury-fashion": ["designer", "luxury", "premium", "haute"],
            "shoes": ["shoes", "footwear", "sneakers", "heels"],
            "accessories": ["accessories", "bags", "purse", "belt"],
            "menswear": ["mens", "men's", "gentleman"],
            "womenswear": ["womens", "women's", "lady"],
            "contemporary": ["contemporary", "modern", "minimalist"]
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    if category not in categories:
                        categories.append(category)
                    break
        
        return categories if categories else ["luxury-fashion"]

# Singleton instance
tavily_service = TavilySearchService()
