"""
Retailer Agent Connector Service
Communicates with external retailer agents via A2A protocol
"""

import logging
import httpx
import json
from typing import List, Dict, Optional
from datetime import datetime

log = logging.getLogger(__name__)

class AgentConnector:
    """Service for connecting to retailer agents via A2A protocol"""
    
    def __init__(self):
        """Initialize agent connector"""
        self.timeout = 10.0
        self.retry_count = 2
    
    async def call_retailer_agent(
        self,
        agent_endpoint: str,
        query: str,
        filters: Optional[Dict] = None,
        x402_headers: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Call a retailer's agent via A2A protocol
        
        Args:
            agent_endpoint: URL of retailer's agent endpoint
            query: Search query
            filters: Optional filter parameters
            x402_headers: Optional X402 payment headers
        
        Returns:
            Response from retailer agent or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "FashionDiscoverySubAgent/0.1.0",
                    "Accept": "application/json"
                }
                
                # Add X402 payment headers if provided
                if x402_headers:
                    headers.update(x402_headers)
                    log.debug(f"Added X402 headers to request")
                
                payload = {
                    "query": query,
                    "filters": filters or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                log.info(f"Calling retailer agent: {agent_endpoint}")
                log.debug(f"Payload: {json.dumps(payload)}")
                
                response = await client.post(
                    agent_endpoint,
                    json=payload,
                    headers=headers
                )
                
                # Log response status
                log.debug(f"Agent response status: {response.status_code}")
                
                if response.status_code == 402:
                    # Payment required
                    log.warning(f"Payment required (402) from {agent_endpoint}")
                    log.debug(f"X402 headers: {response.headers}")
                    return {
                        "error": "payment_required",
                        "x402_headers": dict(response.headers),
                        "message": "This retailer agent requires payment for detailed search"
                    }
                
                response.raise_for_status()
                
                result = response.json()
                log.info(f"Retailer agent returned {len(result.get('results', []))} results")
                
                return result
                
        except httpx.TimeoutException:
            log.warning(f"Timeout calling retailer agent: {agent_endpoint}")
            return None
        except httpx.HTTPStatusError as e:
            log.warning(f"HTTP error from {agent_endpoint}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            log.warning(f"Request error calling {agent_endpoint}: {str(e)}")
            return None
        except json.JSONDecodeError:
            log.warning(f"Invalid JSON response from {agent_endpoint}")
            return None
        except Exception as e:
            log.error(f"Error calling retailer agent {agent_endpoint}: {str(e)}")
            return None
    
    async def aggregate_results(
        self,
        agent_responses: List[Dict],
        original_query: str = ""
    ) -> List[Dict]:
        """
        Aggregate and score results from multiple agents
        
        Args:
            agent_responses: List of responses from retailer agents
            original_query: Original search query for relevance scoring
        
        Returns:
            Aggregated and ranked results
        """
        aggregated = []
        
        for response in agent_responses:
            if response is None:
                continue
            
            if "error" in response:
                log.warning(f"Error response from agent: {response['error']}")
                continue
            
            results = response.get("results", [])
            for result in results:
                # Add relevance score
                relevance_score = self._calculate_relevance(result, original_query)
                
                aggregated_result = {
                    "title": result.get("title"),
                    "description": result.get("description"),
                    "price": result.get("price"),
                    "url": result.get("url"),
                    "image_url": result.get("image_url"),
                    "rating": result.get("rating"),
                    "in_stock": result.get("in_stock", True),
                    "relevance_score": relevance_score,
                    "source_agent": response.get("agent_name", "Unknown")
                }
                
                aggregated.append(aggregated_result)
        
        # Sort by relevance score
        aggregated.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        log.info(f"Aggregated {len(aggregated)} results from {len(agent_responses)} agents")
        return aggregated
    
    async def verify_agent_endpoint(self, endpoint: str) -> bool:
        """
        Verify retailer agent endpoint is responsive
        
        Args:
            endpoint: Agent endpoint URL
        
        Returns:
            True if endpoint is active
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to hit health/status endpoint
                health_urls = [
                    f"{endpoint}/health",
                    f"{endpoint}/status",
                    f"{endpoint}/ping",
                    endpoint  # Fallback to main endpoint
                ]
                
                for url in health_urls:
                    try:
                        response = await client.get(url, follow_redirects=True)
                        if response.status_code in [200, 400, 402]:  # 400/402 is ok, means endpoint exists
                            log.debug(f"Agent endpoint verified: {endpoint}")
                            return True
                    except Exception:
                        continue
                
                log.warning(f"Agent endpoint not responding: {endpoint}")
                return False
                
        except Exception as e:
            log.warning(f"Error verifying agent endpoint {endpoint}: {str(e)}")
            return False
    
    @staticmethod
    def _calculate_relevance(result: Dict, query: str) -> float:
        """
        Calculate relevance score for a result
        
        Args:
            result: Product result
            query: Original search query
        
        Returns:
            Relevance score 0.0-1.0
        """
        score = 0.5
        
        if not query:
            return score
        
        query_lower = query.lower()
        title = (result.get("title") or "").lower()
        description = (result.get("description") or "").lower()
        
        # Check title match
        if query_lower in title:
            score += 0.3
        
        # Check description match
        if query_lower in description:
            score += 0.1
        
        # Check individual words
        query_words = query_lower.split()
        title_words = title.split()
        
        matching_words = sum(1 for word in query_words if word in title_words)
        score += (matching_words / max(len(query_words), 1)) * 0.1
        
        # Boost for in-stock items
        if result.get("in_stock"):
            score += 0.1
        
        # Boost for rated items
        rating = result.get("rating")
        if rating and rating > 4.0:
            score += 0.05
        
        return min(score, 1.0)

# Singleton instance
agent_connector = AgentConnector()
