"""
Registry Service
Manages curated list of luxury fashion retailers
"""

import logging
from typing import List, Optional, Dict
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from src.database import db
from src.database.models import Retailer, BlacklistEntry

log = logging.getLogger(__name__)

class RegistryService:
    """Manages the fashion retailer registry"""
    
    def __init__(self):
        """Initialize registry service"""
        self._initialize_blacklist()
    
    def _initialize_blacklist(self):
        """Initialize blacklist in database"""
        default_blacklist = [
            ("amazon.com", "Mass-market retailer"),
            ("temu.com", "Mass-market retailer"),
            ("shein.com", "Mass-market fast fashion"),
            ("fashionnova.com", "Mass-market fashion"),
            ("hm.com", "Mass-market fashion"),
            ("zara.com", "Mass-market fashion"),
            ("target.com", "Mass-market retailer"),
            ("walmart.com", "Mass-market retailer"),
            ("ebay.com", "Mass-market marketplace"),
            ("aliexpress.com", "Mass-market marketplace"),
            ("etsy.com", "General marketplace"),
        ]
        
        with db.session_scope() as session:
            for domain, reason in default_blacklist:
                existing = session.query(BlacklistEntry).filter_by(domain=domain).first()
                if not existing:
                    session.add(BlacklistEntry(domain=domain, reason=reason, is_active=True))
                    log.debug(f"Added blacklist entry: {domain}")
    
    async def search(
        self,
        categories: Optional[List[str]] = None,
        quality_tiers: Optional[List[str]] = None,
        max_price: Optional[float] = None
    ) -> List[Dict]:
        """
        Search registry with filters
        
        Args:
            categories: List of product categories to filter by
            quality_tiers: List of quality tiers (luxury, premium, emerging)
            max_price: Maximum price filter (not used yet, for future)
        
        Returns:
            List of matching retailers
        """
        with db.session_scope() as session:
            query = session.query(Retailer).filter(
                Retailer.status == "active",
                Retailer.is_verified == True
            )
            
            if quality_tiers:
                query = query.filter(Retailer.quality_tier.in_(quality_tiers))
            
            if categories:
                # Search for retailers that have any of the requested categories
                filters = [Retailer.categories.contains(cat) for cat in categories]
                query = query.filter(or_(*filters))
            
            retailers = query.all()
            log.info(f"Found {len(retailers)} retailers matching filters")
            
            return [r.to_dict() for r in retailers]
    
    async def search_by_name(self, name: str) -> Optional[Dict]:
        """
        Search for a retailer by name
        
        Args:
            name: Retailer name
        
        Returns:
            Retailer record if found, None otherwise
        """
        with db.session_scope() as session:
            retailer = session.query(Retailer).filter(
                Retailer.name.ilike(f"%{name}%")
            ).first()
            
            return retailer.to_dict() if retailer else None
    
    async def get_all_active(self) -> List[Dict]:
        """
        Get all active retailers
        
        Returns:
            List of all active retailers
        """
        with db.session_scope() as session:
            retailers = session.query(Retailer).filter(
                Retailer.status == "active"
            ).all()
            
            return [r.to_dict() for r in retailers]
    
    async def validate_retailer_url(self, url: str) -> bool:
        """
        Validate if a retailer URL is acceptable (not blacklisted)
        
        Args:
            url: Retailer URL
        
        Returns:
            True if acceptable, False if blacklisted
        """
        with db.session_scope() as session:
            blacklist_entries = session.query(BlacklistEntry).filter(
                BlacklistEntry.is_active == True
            ).all()
            
            for entry in blacklist_entries:
                if entry.domain.lower() in url.lower():
                    log.warning(f"Retailer URL blocked: {url} (blacklisted domain: {entry.domain})")
                    return False
        
        return True
    
    async def add_retailer(self, retailer_data: Dict) -> Dict:
        """
        Add a new retailer to registry
        
        Args:
            retailer_data: Retailer information
            - retailer_id (required)
            - name (required)
            - website_url (required)
            - agent_endpoint (required)
            - quality_tier (default: luxury)
            - categories (default: [])
            - x402_payment_address (optional)
        
        Returns:
            Created retailer record
        
        Raises:
            ValueError: If required fields missing or URL blacklisted
        """
        # Validate required fields
        required_fields = ["retailer_id", "name", "website_url", "agent_endpoint"]
        for field in required_fields:
            if field not in retailer_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate URL not blacklisted
        if not await self.validate_retailer_url(retailer_data["website_url"]):
            raise ValueError(f"URL is blacklisted: {retailer_data['website_url']}")
        
        with db.session_scope() as session:
            try:
                retailer = Retailer(
                    retailer_id=retailer_data["retailer_id"],
                    name=retailer_data["name"],
                    website_url=retailer_data["website_url"],
                    agent_endpoint=retailer_data["agent_endpoint"],
                    quality_tier=retailer_data.get("quality_tier", "luxury"),
                    categories=retailer_data.get("categories", []),
                    x402_payment_address=retailer_data.get("x402_payment_address"),
                    is_verified=retailer_data.get("is_verified", False),
                    status=retailer_data.get("status", "active")
                )
                
                session.add(retailer)
                session.flush()
                log.info(f"Added retailer: {retailer.name}")
                
                return retailer.to_dict()
                
            except IntegrityError as e:
                session.rollback()
                log.error(f"Retailer already exists: {retailer_data['retailer_id']}")
                raise ValueError(f"Retailer with ID {retailer_data['retailer_id']} already exists")
    
    async def sync_from_tavily(self, search_results: List[Dict]) -> List[Dict]:
        """
        Add verified retailers from Tavily search to registry
        
        Args:
            search_results: Results from Tavily search
        
        Returns:
            List of newly added retailers
        """
        added_retailers = []
        
        for result in search_results:
            try:
                # Extract retailer info from Tavily result
                retailer_data = {
                    "retailer_id": result.get("retailer_id"),
                    "name": result.get("name"),
                    "website_url": result.get("website_url"),
                    "agent_endpoint": result.get("agent_endpoint"),
                    "quality_tier": result.get("quality_tier", "premium"),
                    "categories": result.get("categories", []),
                    "is_verified": True,
                    "verification_score": result.get("confidence_score", 0.8)
                }
                
                added = await self.add_retailer(retailer_data)
                added_retailers.append(added)
                
            except ValueError as e:
                log.warning(f"Could not add retailer from Tavily: {str(e)}")
                continue
        
        log.info(f"Synced {len(added_retailers)} retailers from Tavily")
        return added_retailers
    
    async def get_stats(self) -> Dict:
        """
        Get registry statistics
        
        Returns:
            Dictionary with registry stats
        """
        with db.session_scope() as session:
            total = session.query(Retailer).count()
            active = session.query(Retailer).filter(Retailer.status == "active").count()
            verified = session.query(Retailer).filter(Retailer.is_verified == True).count()
            blacklist_count = session.query(BlacklistEntry).filter(
                BlacklistEntry.is_active == True
            ).count()
            
            return {
                "total_retailers": total,
                "active_retailers": active,
                "verified_retailers": verified,
                "blacklist_entries": blacklist_count
            }

# Singleton instance
registry_service = RegistryService()
