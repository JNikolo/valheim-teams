from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    """
    Application settings with validation.
    
    Environment variables are automatically loaded and validated.
    Missing required variables will raise a validation error on startup.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )
    
    # Application Settings
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Database Configuration
    db_driver: str = Field(
        default="postgresql+psycopg2",
        description="Database driver"
    )
    db_user: str = Field(..., description="Database username")
    db_password: str = Field(..., description="Database password")
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    db_name: str = Field(..., description="Database name")
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: Literal["simple", "detailed"] = Field(
        default="detailed",
        description="Log format style"
    )
    log_file: str | None = Field(
        default=None,
        description="Optional log file path"
    )
    
    
    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is uppercase"""
        if isinstance(v, str):
            return v.upper()
        return v
    
    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v) -> bool:
        """Parse debug value from string or bool"""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)


# Create a singleton settings instance
# This will validate environment variables on import
settings = Settings()
