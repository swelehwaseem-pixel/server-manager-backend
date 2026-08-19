from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class EnterpriseSettings(BaseSettings):
    # Core Security
    secret_key: str = Field(..., alias="SECRET_KEY")  # Removed default, now REQUIRED via .env
    algorithm: str = Field("HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database
    database_url: str = Field("sqlite+aiosqlite:///./server_manager.db", alias="DATABASE_URL")
    
    # 🔐 NEW: Secure Admin Bootstrapping (No hardcoded passwords!)
    first_superuser: str = Field(None, alias="FIRST_SUPERUSER")
    first_superuser_password: str = Field(None, alias="FIRST_SUPERUSER_PASSWORD")
    
    # 🔐 NEW: Strict CORS (No wildcard "*" with credentials!)
    cors_origins: str = Field("http://localhost:3000,http://localhost:8000", alias="CORS_ORIGINS")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = EnterpriseSettings()
