"""
Database Models
SQLAlchemy models for retailer registry
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Retailer(Base):
    """Retailer registry model"""
    __tablename__ = "retailers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    retailer_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    website_url = Column(String(500), nullable=False)
    agent_endpoint = Column(String(500), nullable=False)
    quality_tier = Column(String(50), default="luxury")  # luxury, premium, emerging
    status = Column(String(20), default="active")  # active, inactive, suspended
    categories = Column(JSON, default=[])  # List of categories
    x402_payment_address = Column(String(100), nullable=True)
    response_time_avg = Column(Float, default=0.0)  # Average response time in ms
    last_verified = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_verified = Column(Boolean, default=False)
    verification_score = Column(Float, default=0.0)  # 0.0-1.0
    
    def __repr__(self):
        return f"<Retailer {self.name} ({self.retailer_id})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "retailer_id": self.retailer_id,
            "name": self.name,
            "website_url": self.website_url,
            "agent_endpoint": self.agent_endpoint,
            "quality_tier": self.quality_tier,
            "status": self.status,
            "categories": self.categories,
            "x402_payment_address": self.x402_payment_address,
            "response_time_avg": self.response_time_avg,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "is_verified": self.is_verified,
            "verification_score": self.verification_score
        }

class BlacklistEntry(Base):
    """Blacklist entry model"""
    __tablename__ = "blacklist"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    domain = Column(String(255), unique=True, nullable=False, index=True)
    reason = Column(String(255), nullable=True)  # Why it's blacklisted
    added_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<BlacklistEntry {self.domain}>"

class SearchQuery(Base):
    """Search query log for analytics"""
    __tablename__ = "search_queries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(100), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False)
    query = Column(String(1000), nullable=False)
    filters = Column(JSON, default={})
    results_count = Column(Integer, default=0)
    query_cost = Column(Float, default=0.0)
    response_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<SearchQuery {self.request_id}>"
