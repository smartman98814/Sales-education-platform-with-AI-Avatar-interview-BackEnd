"""
Application configuration and settings management.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    Attributes:
        openai_api_key: OpenAI API key for agent functionality
        allowed_origins: Comma-separated list of allowed CORS origins, or "*" for all
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_existing_assistants: Whether to use existing assistants from config (default: True)
        jwt_secret_key: Secret key for JWT token signing (default: development key)
        livekit_url: LiveKit server URL (for token generation only)
        livekit_api_key: LiveKit API key (for token generation only)
        livekit_api_secret: LiveKit API secret (for token generation only)
    """
    openai_api_key: Optional[str] = None
    allowed_origins: Optional[str] = None
    log_level: str = "INFO"
    use_existing_assistants: bool = True
    jwt_secret_key: str = "your-secret-key-change-in-production-use-strong-random-key"
    livekit_url: Optional[str] = None
    livekit_api_key: Optional[str] = None
    livekit_api_secret: Optional[str] = None
    livekit_agent_name: Optional[str] = "Dakota-1e0"  # Default agent name
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env (like old SHARED_VECTOR_STORE_ID)

# Try to load settings, but don't fail if .env doesn't exist
try:
    settings = Settings()
except Exception as e:
    # If settings fail to load, create a default instance
    # This allows the app to start even without .env file
    import warnings
    warnings.warn(
        f"Could not load settings from .env file: {e}\n"
        "Please create a .env file with OPENAI_API_KEY=your_key_here",
        UserWarning
    )
    settings = Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        allowed_origins=os.getenv("ALLOWED_ORIGINS"),
    )

