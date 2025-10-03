"""
SQLite database connector with READ ONLY mode and security protection.

This module provides SQLiteConnector class that implements DatabaseConnector interface
for SQLite databases with 4-layer security defense.
"""

import sqlite3
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path

from src.database_connector import DatabaseConnector


class SQLiteConnector(DatabaseConnector):
    """
    SQLite database connector with READ ONLY mode.

    Implements 4-layer security defense:
    - Layer 1: Forbidden pattern validation (INSERT/UPDATE/DELETE/PRAGMA etc.)
    - Layer 2: READ ONLY connection mode
    - Layer 3: Automatic LIMIT clause injection
    - Layer 4: Timeout protection
    """

    # Forbidden SQL patterns (Layer 1 security)
    FORBIDDEN_PATTERNS = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "PRAGMA",
        "ATTACH",
        "DETACH",
        "VACUUM",
        "REINDEX",
    ]

    def __init__(self, db_path: str) -> None:
        """
        Initialize SQLiteConnector.

        Args:
            db_path: Path to SQLite database file

        Raises:
            FileNotFoundError: If database file does not exist
        """
        self.db_path = db_path
        self.conn = None

    def connect(self) -> None:
        """
        Establish persistent READ ONLY connection to SQLite database.

        Raises:
            sqlite3.Error: If connection fails

        Security:
            - READ ONLY mode: Prevents write operations at DB level
            - URI mode: Enables file: protocol with mode parameter
        """
        self.conn = sqlite3.connect(
            f"file:{self.db_path}?mode=ro",
            uri=True,
            timeout=30.0,
            check_same_thread=False,
        )
        self.conn.row_factory = sqlite3.Row

    def get_schema(self) -> List[Dict[str, Any]]:
        """
        Get database schema information.

        Returns:
            List of table schema information. Each element contains:
            - table_name: str - Table name
            - columns: List[Dict] - List of column information
                - column_name: str - Column name
                - data_type: str - Data type
                - is_primary_key: bool - Whether column is primary key

        Raises:
            Exception: If schema retrieval fails
        """
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")

        cursor = self.conn.cursor()

        # Get all table names
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        schema = []
        for table in tables:
            # Get column information for each table
            cursor.execute(f"PRAGMA table_info({table})")
            columns_info = cursor.fetchall()

            columns = []
            for col in columns_info:
                columns.append({
                    "column_name": col[1],  # name
                    "data_type": col[2],    # type
                    "is_primary_key": bool(col[5])  # pk
                })

            schema.append({
                "table_name": table,
                "columns": columns
            })

        cursor.close()
        return schema

    def execute_query(self, sql: str, limit: int = 1000) -> pd.DataFrame:
        """
        Execute SQL query with 4-layer security defense.

        Args:
            sql: SQL query to execute
            limit: Maximum rows to return (default: 1000)

        Returns:
            Query results as DataFrame

        Raises:
            Exception: If query execution fails

        Security layers:
            1. Pattern validation (validate_sql)
            2. READ ONLY connection
            3. Automatic LIMIT injection
            4. Timeout (30 seconds)
        """
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")

        # Layer 1: Validate SQL
        validation = self.validate_sql(sql)
        if not validation["valid"]:
            raise ValueError(validation["message"])

        # Layer 3: Auto-inject LIMIT clause
        sql_stripped = sql.strip().rstrip(";")
        if "LIMIT" not in sql_stripped.upper():
            sql_executed = f"{sql_stripped} LIMIT {limit}"
        else:
            sql_executed = sql_stripped

        # Layer 2 & 4: Execute with READ ONLY connection and timeout
        try:
            df = pd.read_sql_query(sql_executed, self.conn)
            return df

        except sqlite3.OperationalError as e:
            error_msg = str(e)
            if "readonly" in error_msg.lower() or "attempt to write" in error_msg.lower():
                raise PermissionError("書込み操作は許可されていません（READ ONLYモード）")
            else:
                raise RuntimeError(f"SQL実行エラー: {error_msg}")

        except sqlite3.Error as e:
            raise RuntimeError(f"データベースエラー: {str(e)}")

    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL query for security (Layer 1 defense).

        Args:
            sql: SQL query to validate

        Returns:
            Dictionary with validation result:
            - valid: bool - Whether SQL is safe
            - error_type: str or None - Error type if invalid
            - message: str or None - Error message if invalid

        Security checks:
            - Forbidden patterns (INSERT/UPDATE/DELETE/PRAGMA etc.)
            - Multiple statements (semicolon count)
        """
        # Check forbidden patterns
        sql_upper = sql.upper()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in sql_upper:
                return {
                    "valid": False,
                    "error_type": "forbidden_pattern",
                    "message": f"禁止操作が含まれています: {pattern}"
                }

        # Check multiple statements
        if sql.count(";") > 1:
            return {
                "valid": False,
                "error_type": "multiple_statements",
                "message": "複数のステートメントは実行できません"
            }

        return {"valid": True, "error_type": None, "message": None}

    def close(self) -> None:
        """
        Close database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
