from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    openai_api_key: str
    heygen_api_key: Optional[str] = None
    heygen_server_url: Optional[str] = "https://api.heygen.com"
    allowed_origins: Optional[str] = None  # Comma-separated list, or "*" for all
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

