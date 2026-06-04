"""
Database initialization and utilities
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import logging

from config.settings import settings
from src.database.models import Base

log = logging.getLogger(__name__)

class Database:
    """Database connection and session management"""
    
    def __init__(self):
        """Initialize database"""
        self.database_url = settings.DATABASE_URL
        self.engine = None
        self.SessionLocal = None
    
    def initialize(self):
        """Initialize database engine and session factory"""
        if not self.database_url:
            log.warning("DATABASE_URL not configured. Using SQLite for development.")
            self.database_url = "sqlite:///./fashion_discovery.db"
        
        self.engine = create_engine(
            self.database_url,
            echo=settings.DB_ECHO,
            pool_pre_ping=True
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        log.info("Database initialized successfully")
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            log.info("Database connection closed")

# Singleton instance
db = Database()
