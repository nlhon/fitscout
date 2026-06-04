"""
CLI utilities for database and agent management
"""

import asyncio
import sys
import logging
from src.database import db
from src.database.seed import seed_database, clear_database, reset_database

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def init_db():
    """Initialize database"""
    db.initialize()
    log.info("Database initialized")

def seed_db():
    """Seed database with sample data"""
    db.initialize()
    seed_database()
    log.info("Database seeded")

def clear_db():
    """Clear database"""
    db.initialize()
    clear_database()
    log.info("Database cleared")

def reset_db():
    """Reset database"""
    db.initialize()
    reset_database()
    log.info("Database reset")

async def show_stats():
    """Show registry statistics"""
    db.initialize()
    from src.services.registry import registry_service
    stats = await registry_service.get_stats()
    
    print("\n" + "="*50)
    print("REGISTRY STATISTICS")
    print("="*50)
    for key, value in stats.items():
        print(f"{key}: {value}")
    print("="*50 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage.py [command]")
        print("\nCommands:")
        print("  init-db      - Initialize database")
        print("  seed-db      - Seed database with sample data")
        print("  clear-db     - Clear all database")
        print("  reset-db     - Reset database")
        print("  stats        - Show registry statistics")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init-db":
        init_db()
    elif command == "seed-db":
        seed_db()
    elif command == "clear-db":
        clear_db()
    elif command == "reset-db":
        reset_db()
    elif command == "stats":
        asyncio.run(show_stats())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
