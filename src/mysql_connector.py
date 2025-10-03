"""
MySQL database connector with security protection.

This module provides MySQLConnector class that implements DatabaseConnector interface
for MySQL databases.
"""

import mysql.connector
import pandas as pd
from typing import Dict, Any, List

from src.database_connector import DatabaseConnector


class MySQLConnector(DatabaseConnector):
    """
    MySQL database connector.

    Implements security defense similar to SQLiteConnector:
    - Layer 1: Forbidden pattern validation
    - Layer 3: Automatic LIMIT clause injection
    - Layer 4: Timeout protection
    """

    # Forbidden SQL patterns (same as SQLiteConnector)
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

    def __init__(self, host: str, port: int, user: str, password: str, database: str) -> None:
        """
        Initialize MySQLConnector.

        Args:
            host: MySQL server host
            port: MySQL server port
            user: MySQL username
            password: MySQL password
            database: Database name
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None

    def connect(self) -> None:
        """
        Establish persistent connection to MySQL database.

        Tries utf8mb4 charset first, falls back to utf8 if unsupported.

        Raises:
            mysql.connector.Error: If connection fails
        """
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                use_unicode=True,
                connection_timeout=10
            )
        except mysql.connector.Error as e:
            # Fallback to utf8 if utf8mb4 is not supported
            if 'charset' in str(e).lower() or 'character set' in str(e).lower():
                self.conn = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8',
                    use_unicode=True,
                    connection_timeout=10
                )
            else:
                raise

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
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        schema = []
        for table in tables:
            # Get column information for each table
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            columns_info = cursor.fetchall()

            columns = []
            for col in columns_info:
                # col: (Field, Type, Null, Key, Default, Extra)
                columns.append({
                    "column_name": col[0],  # Field
                    "data_type": col[1],    # Type
                    "is_primary_key": col[3] == 'PRI'  # Key
                })

            schema.append({
                "table_name": table,
                "columns": columns
            })

        cursor.close()
        return schema

    def execute_query(self, sql: str, limit: int = 1000) -> pd.DataFrame:
        """
        Execute SQL query with security defense.

        Args:
            sql: SQL query to execute
            limit: Maximum rows to return (default: 1000)

        Returns:
            Query results as DataFrame

        Raises:
            Exception: If query execution fails

        Security layers:
            1. Pattern validation (validate_sql)
            3. Automatic LIMIT injection
            4. Timeout (connection_timeout)
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

        # Execute query
        try:
            df = pd.read_sql_query(sql_executed, self.conn)
            return df

        except mysql.connector.Error as e:
            raise RuntimeError(f"MySQL実行エラー: {str(e)}")

    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL query for security.

        Args:
            sql: SQL query to validate

        Returns:
            Dictionary with validation result:
            - valid: bool - Whether SQL is safe
            - error_type: str or None - Error type if invalid
            - message: str or None - Error message if invalid

        Security checks:
            - Forbidden patterns (INSERT/UPDATE/DELETE etc.)
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
