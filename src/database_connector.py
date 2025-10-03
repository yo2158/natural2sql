"""
データベース接続の抽象基底クラスとFactory関数

このモジュールは、異なるデータベース種別（SQLite、MySQL等）に対する
統一的なインターフェースを提供する抽象基底クラスと、
適切なConnectorインスタンスを生成するFactory関数を定義します。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import pandas as pd


class DatabaseConnector(ABC):
    """
    データベース接続の抽象基底クラス

    Strategy Patternを実装し、データベース種別ごとの具象クラスで
    具体的な接続・クエリ実行方法を実装します。
    """

    @abstractmethod
    def connect(self) -> None:
        """
        データベースへの接続を確立

        Raises:
            Exception: 接続に失敗した場合
        """
        pass

    @abstractmethod
    def get_schema(self) -> List[Dict[str, Any]]:
        """
        データベースのスキーマ情報を取得

        Returns:
            スキーマ情報のリスト。各要素は以下のキーを持つ辞書:
            - table_name: str - テーブル名
            - columns: List[Dict] - カラム情報のリスト
                - column_name: str - カラム名
                - data_type: str - データ型
                - is_primary_key: bool - 主キーか否か

        Raises:
            Exception: スキーマ取得に失敗した場合
        """
        pass

    @abstractmethod
    def execute_query(self, sql: str, limit: int = 1000) -> pd.DataFrame:
        """
        SQLクエリを実行し、結果をDataFrameで返す

        Args:
            sql: 実行するSQLクエリ
            limit: 最大取得行数（デフォルト: 1000）

        Returns:
            クエリ結果のDataFrame

        Raises:
            Exception: クエリ実行に失敗した場合
        """
        pass

    @abstractmethod
    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        SQLクエリの妥当性を検証

        Args:
            sql: 検証するSQLクエリ

        Returns:
            検証結果の辞書:
            - valid: 妥当性（True/False）
            - error_type: エラー種別（妥当な場合はNone）
            - message: エラーメッセージ（妥当な場合はNone）
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        データベース接続をクローズ
        """
        pass


def create_database_connector() -> DatabaseConnector:
    """
    Factory function to create appropriate DatabaseConnector instance.

    Creates SQLiteConnector or MySQLConnector based on Config.DB_TYPE setting.

    Returns:
        DatabaseConnector instance (SQLiteConnector or MySQLConnector)

    Raises:
        ValueError: If DB_TYPE is invalid or required configuration is missing
    """
    from src.config import Config
    from src.sqlite_connector import SQLiteConnector
    from src.mysql_connector import MySQLConnector

    db_type = Config.DB_TYPE.lower()

    if db_type == "sqlite":
        db_path = Config.resolve_path(Config.DB_PATH)
        return SQLiteConnector(str(db_path))

    elif db_type == "mysql":
        # Validate MySQL configuration
        if not all([Config.DB_HOST, Config.DB_USER, Config.DB_NAME]):
            raise ValueError(
                "MySQL接続に必要な設定が不足しています。\n"
                "DB_HOST, DB_USER, DB_NAMEを.envファイルに設定してください。"
            )

        return MySQLConnector(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )

    else:
        raise ValueError(
            f"サポートされていないデータベースタイプです: {Config.DB_TYPE}\n"
            "DB_TYPEには 'sqlite' または 'mysql' を指定してください。"
        )
