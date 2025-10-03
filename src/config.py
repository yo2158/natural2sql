"""
Configuration management module for natural2sql application.

This module handles loading and validating environment variables and application settings.
"""

from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv
import os
import logging
import sys

# Load environment variables from .env file
# Explicitly specify .env path (project root)
# .env file takes precedence over system environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'natural2sql.log'),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)


def _parse_db_port() -> int:
    """
    DB_PORT環境変数を安全に解析（無効値は3306にフォールバック）

    Returns:
        int: ポート番号（デフォルト: 3306）
    """
    port_str = os.getenv("DB_PORT", "3306")
    try:
        return int(port_str)
    except ValueError:
        return 3306


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

    # Database configuration (v1.1)
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")

    # MySQL connection settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = _parse_db_port()
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "")

    # File paths (optional)
    LOGICAL_NAMES_PATH: Optional[str] = os.getenv("LOGICAL_NAMES_PATH")
    BUSINESS_TERMS_PATH: Optional[str] = os.getenv("BUSINESS_TERMS_PATH")

    @classmethod
    def resolve_path(cls, path_input: Union[str, Path]) -> Path:
        """
        相対パス・絶対パス両対応のパス解決

        Args:
            path_input: パス文字列またはPathオブジェクト

        Returns:
            解決済み絶対パス
        """
        path = Path(path_input)
        if path.is_absolute():
            return path
        else:
            return cls.BASE_DIR / path

    @classmethod
    def validate(cls) -> None:
        """
        Validate configuration settings.

        Raises:
            ValueError: If required configuration is missing or invalid
            FileNotFoundError: If required files/directories don't exist
        """
        # Validate API key (at least one provider should be configured)
        if not cls.GEMINI_API_KEY or cls.GEMINI_API_KEY == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEYが設定されていません。\n"
                ".envファイルに設定してください。"
            )

        # Validate database configuration based on DB_TYPE
        if cls.DB_TYPE.lower() == "sqlite":
            # Validate SQLite database path
            db_path = cls.resolve_path(cls.DB_PATH)
            if not db_path.exists():
                raise FileNotFoundError(
                    f"データベースファイルが見つかりません: {db_path}\n"
                    f"期待される場所: {db_path.absolute()}"
                )

        elif cls.DB_TYPE.lower() == "mysql":
            # Validate MySQL connection settings
            if not cls.DB_HOST:
                raise ValueError(
                    "DB_HOSTが設定されていません。\n"
                    "MySQLサーバーのホスト名を.envファイルに設定してください。"
                )
            if not cls.DB_USER:
                raise ValueError(
                    "DB_USERが設定されていません。\n"
                    "MySQLユーザー名を.envファイルに設定してください。"
                )
            if not cls.DB_NAME:
                raise ValueError(
                    "DB_NAMEが設定されていません。\n"
                    "MySQLデータベース名を.envファイルに設定してください。"
                )

        else:
            raise ValueError(
                f"サポートされていないDB_TYPEです: {cls.DB_TYPE}\n"
                "DB_TYPEには 'sqlite' または 'mysql' を指定してください。"
            )
