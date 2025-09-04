"""
Configuration management for RewardOps Analytics POC.

This module handles all configuration settings including environment variables,
database connections, MCP server configurations, and application settings.
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseSettings, Field, validator

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Base configuration
    DEBUG: bool = Field(False, env="DEBUG")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    BASE_DIR: Path = Path(__file__).parent.parent
    
    # Database configuration
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field("redis://localhost:6379", env="REDIS_URL")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    GEMINI_API_KEY: Optional[str] = Field(None, env="GEMINI_API_KEY")
    
    # MCP Server configuration
    MCP_DATABASE_CONFIG: str = Field("mcp_servers/database_config.json", env="MCP_DATABASE_CONFIG")
    MCP_VIZRO_CONFIG: str = Field("mcp_servers/vizro_config.json", env="MCP_VIZRO_CONFIG")
    
    # WebSocket configuration
    WS_HEARTBEAT_INTERVAL: int = Field(30, env="WS_HEARTBEAT_INTERVAL")
    WS_MAX_CONNECTIONS: int = Field(100, env="WS_MAX_CONNECTIONS")
    
    # Application configuration
    APP_NAME: str = Field("RewardOps Analytics POC", env="APP_NAME")
    APP_VERSION: str = Field("1.0.0", env="APP_VERSION")
    
    # CORS configuration
    CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://127.0.0.1:3000"], 
        env="CORS_ORIGINS"
    )
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(3600, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Query processing
    MAX_QUERY_LENGTH: int = Field(1000, env="MAX_QUERY_LENGTH")
    QUERY_TIMEOUT: int = Field(30, env="QUERY_TIMEOUT")  # seconds
    
    # Visualization
    DEFAULT_CHART_TYPE: str = Field("bar", env="DEFAULT_CHART_TYPE")
    MAX_DATA_POINTS: int = Field(1000, env="MAX_DATA_POINTS")
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of {valid_levels}')
        return v.upper()
    
    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('DATABASE_URL must be a PostgreSQL connection string')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Database configuration
DATABASE_CONFIG = {
    "url": settings.DATABASE_URL,
    "pool_size": 20,
    "max_overflow": 30,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": settings.DEBUG
}

# Redis configuration
REDIS_CONFIG = {
    "url": settings.REDIS_URL,
    "max_connections": 20,
    "retry_on_timeout": True,
    "decode_responses": True
}

# MCP Server configurations
MCP_CONFIGS = {
    "database": {
        "config_path": settings.MCP_DATABASE_CONFIG,
        "server_name": "database",
        "tools": ["db-toolbox:query", "db-toolbox:get_schema", "db-toolbox:list_tables"]
    },
    "vizro": {
        "config_path": settings.MCP_VIZRO_CONFIG,
        "server_name": "vizro",
        "tools": ["vizro-mcp:create_dashboard", "vizro-mcp:create_chart", "vizro-mcp:get_chart_types"]
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
            "level": settings.LOG_LEVEL,
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "detailed",
            "filename": "app.log",
            "mode": "a",
        },
    },
    "loggers": {
        "": {
            "level": settings.LOG_LEVEL,
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
    "company_name": "RewardOps",
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
    return settings.DATABASE_URL

def get_redis_url() -> str:
    """Get the Redis URL from settings."""
    return settings.REDIS_URL

def get_mcp_config(server_name: str) -> dict:
    """Get MCP configuration for a specific server."""
    return MCP_CONFIGS.get(server_name, {})

def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return settings.DEBUG

def get_log_level() -> str:
    """Get the current log level."""
    return settings.LOG_LEVEL

def validate_configuration() -> bool:
    """
    Validate the current configuration.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Validate required settings
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")
        
        # Validate file paths
        if not Path(settings.MCP_DATABASE_CONFIG).exists():
            raise ValueError(f"MCP database config file not found: {settings.MCP_DATABASE_CONFIG}")
        
        if not Path(settings.MCP_VIZRO_CONFIG).exists():
            raise ValueError(f"MCP Vizro config file not found: {settings.MCP_VIZRO_CONFIG}")
        
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
