from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ADMIN_SECRET_KEY: str

    # API
    API_VERSION: str = "v1"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate_required(self):
        """Validate that critical env vars are set and non-empty."""
        required = {
            "SUPABASE_URL": self.SUPABASE_URL,
            "SUPABASE_KEY": self.SUPABASE_KEY,
            "SUPABASE_SERVICE_KEY": self.SUPABASE_SERVICE_KEY,
            "SECRET_KEY": self.SECRET_KEY,
            "ADMIN_SECRET_KEY": self.ADMIN_SECRET_KEY,
        }
        missing = [k for k, v in required.items() if not v or not v.strip()]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        logger.info("All required environment variables validated successfully")

settings = Settings()