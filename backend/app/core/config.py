"""
Configuration management for the Wall Finishing Robot Control System.
Uses pydantic-settings for environment variable management.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Configuration
    API_TITLE: str = "Wall Finishing Robot Control System"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = """
    Robust database-driven control system for autonomous wall-finishing robot.
    Handles intelligent path planning, trajectory storage, and real-time visualization.
    """

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./wall_robot.db"
    DATABASE_ECHO: bool = False

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS Configuration
    ALLOWED_ORIGINS: list = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # Path Planning Configuration
    DEFAULT_TOOL_WIDTH: float = 0.25  # 25cm tool width in meters
    OVERLAP_PERCENTAGE: float = 0.1  # 10% overlap for complete coverage
    DEFAULT_SPEED: float = 0.5  # m/s

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
