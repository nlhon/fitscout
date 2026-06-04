"""
Query Processor Service
Processes and interprets natural language fashion discovery queries
"""

import logging
import re
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

class QueryProcessor:
    """Processes fashion discovery queries"""
    
    # Fashion-related keywords
    PRODUCT_KEYWORDS = {
        "outerwear": ["coat", "puffer", "jacket", "blazer", "cardigan", "sweater", "hoodie", "windbreaker"],
        "shoes": ["shoes", "sneakers", "heels", "boots", "loafers", "oxfords", "flats", "sandals"],
        "accessories": ["bag", "purse", "belt", "scarf", "hat", "gloves", "jewelry", "watch"],
        "dresses": ["dress", "gown", "suit", "skirt", "tunic"],
        "pants": ["pants", "jeans", "leggings", "trousers", "shorts"],
    }
    
    QUALITY_KEYWORDS = {
        "luxury": ["luxury", "premium", "high-end", "designer", "exclusive", "bespoke", "couture"],
        "premium": ["premium", "quality", "mid-range", "contemporary"],
        "emerging": ["emerging", "indie", "boutique", "independent"],
    }
    
    STYLE_KEYWORDS = {
        "minimalist": ["minimalist", "minimal", "simple", "clean"],
        "maximalist": ["maximalist", "bold", "statement"],
        "classic": ["classic", "timeless", "traditional"],
        "modern": ["modern", "contemporary", "trendy"],
        "bohemian": ["bohemian", "boho", "hippie"],
        "sporty": ["sporty", "athletic", "casual"],
    }
    
    @staticmethod
    async def parse_query(query: str) -> Dict:
        """
        Parse natural language query into structured parameters
        
        Args:
            query: Natural language query (e.g., "luxury puffer jackets under $5000")
        
        Returns:
            Structured query parameters with:
            - product_type: Main product type
            - style: Fashion style descriptors
            - price_range: Extracted price constraints
            - quality_tier: Luxury, premium, etc.
        """
        query_lower = query.lower()
        
        # Extract price
        price_range = QueryProcessor._extract_price(query_lower)
        
        # Determine quality tier
        quality_tier = QueryProcessor._determine_quality_tier(query_lower)
        
        # Extract product type
        product_types = QueryProcessor._extract_product_types(query_lower)
        
        # Extract style descriptors
        styles = QueryProcessor._extract_styles(query_lower)
        
        log.debug(f"Parsed query: {query} -> products={product_types}, styles={styles}, quality={quality_tier}, price={price_range}")
        
        return {
            "product_type": product_types,
            "style": styles,
            "price_range": price_range,
            "quality_tier": quality_tier,
            "original_query": query
        }
    
    @staticmethod
    async def validate_query(query: str) -> bool:
        """
        Validate query is appropriate for fashion discovery
        
        Args:
            query: Query to validate
        
        Returns:
            True if valid fashion-related query
        """
        if not query or len(query.strip()) < 3:
            log.warning("Query too short")
            return False
        
        # Check for suspicious patterns
        if len(query) > 1000:
            log.warning("Query too long")
            return False
        
        query_lower = query.lower()
        
        # Check for fashion-related keywords
        fashion_keywords = [
            "fashion", "clothing", "outfit", "wear", "dress", "coat", "jacket",
            "shoe", "shirt", "pants", "designer", "luxury", "shop", "buy",
            "style", "outfit", "apparel", "garment", "sweater", "hoodie"
        ]
        
        has_fashion_keyword = any(keyword in query_lower for keyword in fashion_keywords)
        
        if not has_fashion_keyword:
            log.warning(f"Query doesn't appear to be fashion-related: {query}")
            # Still allow it - user might use different terminology
        
        return True
    
    @staticmethod
    async def extract_filters(query: str) -> Dict:
        """
        Extract filter constraints from query
        
        Args:
            query: Natural language query
        
        Returns:
            Dictionary with extracted filters
        """
        query_lower = query.lower()
        
        filters = {
            "max_price": None,
            "min_price": None,
            "categories": [],
            "colors": [],
            "brands": [],
            "sizes": []
        }
        
        # Extract price
        price_range = QueryProcessor._extract_price(query_lower)
        if price_range:
            filters["max_price"] = price_range.get("max")
            filters["min_price"] = price_range.get("min")
        
        # Extract colors
        colors = QueryProcessor._extract_colors(query_lower)
        filters["colors"] = colors
        
        # Extract categories (product types)
        categories = QueryProcessor._extract_product_types(query_lower)
        filters["categories"] = categories
        
        # Extract sizes
        sizes = QueryProcessor._extract_sizes(query_lower)
        filters["sizes"] = sizes
        
        return filters
    
    @staticmethod
    async def categorize_intent(query: str) -> str:
        """
        Categorize the query intent
        
        Args:
            query: Natural language query
        
        Returns:
            Intent category (e.g., "product_search", "trend_analysis", "price_comparison")
        """
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            return "comparison"
        elif any(word in query_lower for word in ["trend", "trending", "popular", "best"]):
            return "trend_analysis"
        elif any(word in query_lower for word in ["recommend", "suggest", "find", "show"]):
            return "product_search"
        elif any(word in query_lower for word in ["price", "cost", "how much", "expensive"]):
            return "price_search"
        else:
            return "product_search"
    
    @staticmethod
    def _extract_price(query_lower: str) -> Optional[Dict]:
        """Extract price range from query"""
        # Pattern: "under $5000" or "$5000" or "5000 dollars"
        price_patterns = [
            (r"under\s*\$?(\d+(?:,\d+)?)", "max"),
            (r"above?\s*\$?(\d+(?:,\d+)?)", "min"),
            (r"\$?(\d+(?:,\d+)?)\s*-\s*\$?(\d+(?:,\d+)?)", "range"),
            (r"\$?(\d+(?:,\d+)?)\s*(?:or\s*less|or\s*cheaper)", "max"),
        ]
        
        for pattern, pattern_type in price_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if pattern_type == "range":
                    return {
                        "min": int(match.group(1).replace(",", "")),
                        "max": int(match.group(2).replace(",", ""))
                    }
                elif pattern_type == "max":
                    return {"max": int(match.group(1).replace(",", ""))}
                elif pattern_type == "min":
                    return {"min": int(match.group(1).replace(",", ""))}
        
        return None
    
    @staticmethod
    def _extract_colors(query_lower: str) -> List[str]:
        """Extract color preferences"""
        colors = {}
        color_keywords = ["red", "blue", "green", "black", "white", "gray", "grey", "brown", "beige", "navy"]
        
        for color in color_keywords:
            if color in query_lower:
                colors[color] = True
        
        return list(colors.keys())
    
    @staticmethod
    def _extract_sizes(query_lower: str) -> List[str]:
        """Extract size preferences"""
        sizes = []
        size_keywords = ["xs", "small", "medium", "large", "xl", "xxl", "one size"]
        
        for size in size_keywords:
            if size in query_lower:
                sizes.append(size)
        
        return sizes
    
    @staticmethod
    def _determine_quality_tier(query_lower: str) -> str:
        """Determine quality tier from query"""
        for tier, keywords in QueryProcessor.QUALITY_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                return tier
        
        return "luxury"  # Default to luxury
    
    @staticmethod
    def _extract_product_types(query_lower: str) -> List[str]:
        """Extract product types from query"""
        product_types = []
        
        for category, keywords in QueryProcessor.PRODUCT_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                product_types.append(category)
        
        return product_types if product_types else ["general"]
    
    @staticmethod
    def _extract_styles(query_lower: str) -> List[str]:
        """Extract style descriptors from query"""
        styles = []
        
        for style, keywords in QueryProcessor.STYLE_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                styles.append(style)
        
        return styles

# Singleton instance
query_processor = QueryProcessor()
