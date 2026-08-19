from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class EnterpriseSettings(BaseSettings):
    secret_key: str = Field("SUPER_SECRET_HEX_STRING_CHANGE_THIS_IN_PRODUCTION", alias="SECRET_KEY")
    algorithm: str = Field("HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field("sqlite+aiosqlite:///./server_manager.db", alias="DATABASE_URL")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = EnterpriseSettings()
