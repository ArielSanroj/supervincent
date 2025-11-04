"""
Configuration management using Pydantic Settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Alegra API settings
    alegra_email: str = Field("demo@example.com", env="ALEGRA_USER")
    alegra_token: str = Field("demo_token_12345", env="ALEGRA_TOKEN")
    alegra_base_url: str = Field("https://api.alegra.com/api/v1", env="ALEGRA_BASE_URL")
    alegra_timeout: int = Field(30, env="ALEGRA_TIMEOUT")
    alegra_max_retries: int = Field(3, env="ALEGRA_MAX_RETRIES")
    
    # Redis settings
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Celery settings
    celery_broker_url: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field("redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Logging settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/invoicebot.log", env="LOG_FILE")
    
    # File processing settings
    max_file_size_mb: int = Field(10, env="MAX_FILE_SIZE_MB")
    supported_formats: list = Field([".pdf", ".jpg", ".jpeg", ".png"], env="SUPPORTED_FORMATS")
    
    # Tax calculation settings
    tax_config_path: str = Field("config/tax_rules_CO_2025.json", env="TAX_CONFIG_PATH")

    # Ollama settings
    ollama_enabled: bool = Field(False, env="OLLAMA_ENABLED")
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_text_model: str = Field("llama3.1:latest", env="OLLAMA_TEXT_MODEL")
    ollama_vision_model: str = Field("llava:latest", env="OLLAMA_VISION_MODEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
