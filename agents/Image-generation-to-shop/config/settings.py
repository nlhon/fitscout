"""
Configuration management with Pydantic Settings
Loads from environment variables
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    REPLICATE_API_TOKEN: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    
    # Application
    APP_NAME: str = "Image-generation-to-shop Agent"
    APP_VERSION: str = "1.0.0"
    
    # Image Generation
    IMAGE_MODEL: str = "black-forest-labs/flux-schnell"
    GUIDANCE_SCALE: float = 3.5
    INFERENCE_STEPS: int = 4
    
    # Shopping Search
    SEARCH_ENGINE: str = "google_lens"
    SEARCH_TIMEOUT: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = "config/.env"
        case_sensitive = True


settings = Settings()
