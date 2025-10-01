"""
Configuration management module for txt2sql application.

This module handles loading and validating environment variables and application settings.
"""

from pathlib import Path
from dotenv import load_dotenv
import os
import logging
import sys

# Load environment variables from .env file
load_dotenv()

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'smartquery.log'),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)


class Config:
    """
    Application configuration class.

    Loads configuration from environment variables and provides validation methods.
    All paths are absolute and validated during initialization.
    """

    # Base directories
    BASE_DIR: Path = Path(__file__).parent.parent.absolute()
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "restaurant.db"

    # Gemini API configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Ollama configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:12b")

    # Application settings
    AI_TIMEOUT: int = int(os.getenv("AI_TIMEOUT_SECONDS", "120"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRY_COUNT", "3"))
    SQL_TIMEOUT: int = int(os.getenv("SQL_TIMEOUT_SECONDS", "30"))
    MAX_DISPLAY_ROWS: int = int(os.getenv("PREVIEW_LIMIT", "10"))

    @classmethod
    def validate(cls) -> None:
        """
        Validate configuration settings.

        Raises:
            ValueError: If required configuration is missing or invalid
            FileNotFoundError: If required files/directories don't exist
        """
        # Validate API key (at least one provider should be configured)
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Please set it in .env file or environment variables. "
                "Get your key from: https://makersuite.google.com/app/apikey"
            )

        # Validate database path
        if not cls.DB_PATH.exists():
            raise FileNotFoundError(
                f"Database file not found: {cls.DB_PATH}\n"
                f"Expected location: {cls.DB_PATH.absolute()}"
            )

        # Validate data directory
        if not cls.DATA_DIR.exists():
            raise FileNotFoundError(
                f"Data directory not found: {cls.DATA_DIR}\n"
                f"Expected location: {cls.DATA_DIR.absolute()}"
            )
