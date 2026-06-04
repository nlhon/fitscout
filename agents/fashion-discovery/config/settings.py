from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_TITLE: str = "Fashion Discovery Sub-Agent"
    API_VERSION: str = "0.1.0"
    API_DESCRIPTION: str = "AI agent for discovering luxury fashion retailers"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Tavily Configuration
    TAVILY_API_KEY: str
    TAVILY_SEARCH_DEPTH: str = "advanced"
    TAVILY_MAX_RESULTS: int = 15
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    DB_ECHO: bool = False
    
    # Cache Configuration
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour
    
    # XRPL Configuration (for X402 payments)
    XRPL_NETWORK: str = "testnet"  # or "mainnet"
    XRPL_RIPPLED_URL: str = "https://s.altnet.rippletest.net:51234"
    X402_WALLET_ADDRESS: Optional[str] = None
    X402_WALLET_SECRET: Optional[str] = None
    
    # Blacklist Configuration
    BLACKLIST_DOMAINS: list = [
        "amazon.com",
        "temu.com",
        "shein.com",
        "fashionnova.com",
        "hm.com",
        "zara.com",
        "target.com",
        "walmart.com",
        "ebay.com"
    ]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
