"""
Configuration management for LoyaltyAnalytics POC.

This module handles all configuration settings including environment variables,
database connections, MCP server configurations, and application settings.
"""
import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Base configuration
    debug: bool = Field(False, description="Debug mode flag")
    log_level: str = Field("INFO", description="Logging level")
    base_dir: Path = Path(__file__).parent.parent
    
    # Database configuration - Individual components for flexibility
    postgres_host: str = Field("localhost", description="PostgreSQL host")
    postgres_port: int = Field(5432, description="PostgreSQL port")
    postgres_database: str = Field("loyalty_analytics", description="PostgreSQL database name")
    postgres_user: str = Field("postgres", description="PostgreSQL username")
    postgres_password: str = Field("postgres", description="PostgreSQL password")
    
    # Computed database URL
    @property
    def database_url(self) -> str:
        """Build database URL from components."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
    
    # Redis configuration  
    redis_url: str = Field("redis://localhost:6379", description="Redis connection URL")
    
    # API Keys
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for LLM")
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API key for LLM")
    
    # MCP Server configuration
    mcp_database_config: str = Field("mcp_servers/mcp_config.json", description="MCP database server config file path")
    mcp_ui_config: str = Field("mcp_servers/ui_config.json", description="MCP UI server config file path")
    
    # WebSocket configuration
    ws_heartbeat_interval: int = Field(30, description="WebSocket heartbeat interval in seconds")
    ws_max_connections: int = Field(100, description="Maximum WebSocket connections")
    
    # Application configuration
    app_name: str = Field("LoyaltyAnalytics", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    
    # FastAPI Configuration
    host: str = Field("0.0.0.0", description="FastAPI host")
    port: int = Field(8000, description="FastAPI port")
    
    # CORS configuration
    cors_origins_str: str = Field(
        "http://localhost:3000,http://127.0.0.1:3000", 
        description="Allowed CORS origins (comma-separated)"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(',')]
    
    # Rate limiting
    rate_limit_requests: int = Field(100, description="Rate limit requests per window")
    rate_limit_window: int = Field(3600, description="Rate limit window in seconds")
    
    # Query processing
    max_query_length: int = Field(1000, description="Maximum query length")
    query_timeout: int = Field(30, description="Query timeout in seconds")
    
    # Visualization
    default_chart_type: str = Field("bar", description="Default chart type")
    max_data_points: int = Field(1000, description="Maximum data points for visualization")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
        env_parse_none_str='',
        env_parse_enums=True
    )

# Global settings instance
settings = Settings()

# Debug: Print configuration loading status
print(f"🔧 Configuration loaded:")
print(f"  - OpenAI API Key: {'✅ Set' if settings.openai_api_key else '❌ Not set'}")
print(f"  - Database URL: {settings.database_url}")
print(f"  - Debug mode: {settings.debug}")
print(f"  - Environment file loading complete")

# Database configuration
DATABASE_CONFIG = {
    "url": settings.database_url,
    "pool_size": 20,
    "max_overflow": 30,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": settings.debug
}

# Redis configuration
REDIS_CONFIG = {
    "url": settings.redis_url,
    "max_connections": 20,
    "retry_on_timeout": True,
    "decode_responses": True
}

# MCP Server configurations
MCP_CONFIGS = {
    "database": {
        "config_path": settings.mcp_database_config,
        "server_name": "database",
        "tools": ["postgres:query", "postgres:get_schema", "postgres:list_tables"]
    },
    "ui": {
        "config_path": settings.mcp_ui_config,
        "server_name": "ui",
        "tools": ["ui:create_chart", "ui:create_table", "ui:create_dashboard", "ui:create_form"]
    }
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.log_level,
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": settings.log_level,
            "formatter": "detailed",
            "filename": "app.log",
            "mode": "a",
        },
    },
    "loggers": {
        "": {
            "level": settings.log_level,
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "fastapi": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

# Business domain configuration
BUSINESS_CONFIG = {
    "company_name": "Analytics",
    "domain": "loyalty_and_rewards",
    "sample_queries": [
        "Show me the top 10 merchants by redemption volume",
        "What are the most popular redemption categories?",
        "How many users redeemed rewards this month?",
        "Which merchants have the highest average redemption value?",
        "Show me redemption trends over the last 6 months"
    ],
    "supported_chart_types": ["bar", "line", "pie", "scatter", "area", "heatmap"],
    "default_limits": {
        "merchants": 10,
        "users": 100,
        "redemptions": 1000,
        "time_range_days": 365
    }
}

# Error messages
ERROR_MESSAGES = {
    "database_connection": "Unable to connect to database. Please try again later.",
    "query_timeout": "Query took too long to process. Please try a simpler query.",
    "invalid_query": "Invalid query format. Please rephrase your question.",
    "no_data": "No data found for your query. Please try different parameters.",
    "mcp_server_error": "Analytics service temporarily unavailable. Please try again later.",
    "rate_limit_exceeded": "Too many requests. Please wait a moment before trying again.",
    "websocket_error": "Connection lost. Please refresh the page to reconnect."
}

# Success messages
SUCCESS_MESSAGES = {
    "query_processed": "Query processed successfully",
    "visualization_created": "Visualization created successfully",
    "connection_established": "Connected to analytics service",
    "data_loaded": "Data loaded successfully"
}

def get_database_url() -> str:
    """Get the database URL from settings."""
    return settings.database_url

def get_redis_url() -> str:
    """Get the Redis URL from settings."""
    return settings.redis_url

def get_mcp_config(server_name: str) -> dict:
    """Get MCP configuration for a specific server."""
    return MCP_CONFIGS.get(server_name, {})

def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return settings.debug

def get_log_level() -> str:
    """Get the current log level."""
    return settings.log_level

def validate_configuration() -> bool:
    """
    Validate the current configuration.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Validate required settings
        if not settings.database_url:
            raise ValueError("database_url is required")
        
        # Validate file paths (create if missing)
        db_config_path = Path(settings.mcp_database_config)
        if not db_config_path.exists():
            print(f"Warning: MCP database config file not found: {settings.mcp_database_config}")
            # Create directory if it doesn't exist
            db_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        ui_config_path = Path(settings.mcp_ui_config)
        if not ui_config_path.exists():
            print(f"Warning: MCP UI config file not found: {settings.mcp_ui_config}")
            # Create directory if it doesn't exist
            ui_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        return True
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False

# Initialize configuration validation
if __name__ == "__main__":
    if validate_configuration():
        print("Configuration is valid")
    else:
        print("Configuration validation failed")
        exit(1)
