"""
Database seeding utility
Loads sample data into registry
"""

import logging
from src.database import db
from src.database.models import Retailer, BlacklistEntry
from src.fixtures.sample_data import SAMPLE_RETAILERS, SAMPLE_BLACKLIST

log = logging.getLogger(__name__)

def seed_database():
    """Load sample data into database"""
    log.info("Starting database seed...")
    
    with db.session_scope() as session:
        # Seed blacklist
        log.info("Seeding blacklist entries...")
        for domain, reason in SAMPLE_BLACKLIST:
            existing = session.query(BlacklistEntry).filter_by(domain=domain).first()
            if not existing:
                session.add(BlacklistEntry(domain=domain, reason=reason, is_active=True))
                log.debug(f"  Added blacklist: {domain}")
        
        # Seed retailers
        log.info("Seeding retailer data...")
        for retailer_data in SAMPLE_RETAILERS:
            existing = session.query(Retailer).filter_by(
                retailer_id=retailer_data["retailer_id"]
            ).first()
            
            if not existing:
                retailer = Retailer(**retailer_data)
                session.add(retailer)
                log.debug(f"  Added retailer: {retailer_data['name']}")
        
        session.commit()
        log.info("Database seed completed successfully")

def clear_database():
    """Clear all data from database"""
    log.warning("Clearing database...")
    
    with db.session_scope() as session:
        session.query(Retailer).delete()
        session.query(BlacklistEntry).delete()
        session.commit()
    
    log.info("Database cleared")

def reset_database():
    """Reset database to clean state with sample data"""
    log.info("Resetting database...")
    clear_database()
    seed_database()
    log.info("Database reset completed")
