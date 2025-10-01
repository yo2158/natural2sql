"""
SQL executor module for safe SQLite query execution.

This module provides READ ONLY SQLite execution with 4-layer security defense.
"""

import sqlite3
from typing import Dict, Any, List
from pathlib import Path


class SQLExecutor:
    """
    Executor for safe SQL query execution with READ ONLY mode.

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
        Initialize SQLExecutor.

        Args:
            db_path: Path to SQLite database file

        Raises:
            FileNotFoundError: If database file does not exist
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get READ ONLY database connection.

        Returns:
            SQLite connection in READ ONLY mode

        Raises:
            sqlite3.Error: If connection fails

        Security:
            - READ ONLY mode: Prevents write operations at DB level
            - URI mode: Enables file: protocol with mode parameter
            - Timeout: 30 seconds for query execution
        """
        conn = sqlite3.connect(
            f"file:{self.db_path}?mode=ro",
            uri=True,
            timeout=30.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        return conn

    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL query for security (Layer 1 defense).

        Args:
            sql: SQL query to validate

        Returns:
            Dictionary with validation result:
            - valid: bool - Whether SQL is safe
            - error: Optional[str] - Error message if invalid

        Security checks:
            - Forbidden patterns (INSERT/UPDATE/DELETE/PRAGMA etc.)
            - Multiple statements (semicolon count)
        """
        # Check forbidden patterns
        sql_upper = sql.upper()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in sql_upper:
                return {"valid": False, "error": f"禁止操作が含まれています: {pattern}"}

        # Check multiple statements
        if sql.count(";") > 1:
            return {"valid": False, "error": "複数のステートメントは実行できません"}

        return {"valid": True}

    def execute_query(self, sql: str, max_rows: int = 1000) -> Dict[str, Any]:
        """
        Execute SQL query with 4-layer security defense.

        Args:
            sql: SQL query to execute
            max_rows: Maximum rows to return (default: 1000)

        Returns:
            Dictionary with execution result:
            - success: bool - Whether execution succeeded
            - data: Optional[List[Dict]] - Query results as list of dicts
            - columns: Optional[List[str]] - Column names
            - row_count: Optional[int] - Number of rows returned
            - error: Optional[str] - Error message if failed
            - sql_executed: str - SQL that was actually executed

        Security layers:
            1. Pattern validation (_validate_sql)
            2. READ ONLY connection
            3. Automatic LIMIT injection
            4. Timeout (30 seconds)

        Example:
            >>> executor = SQLExecutor('data/restaurant.db')
            >>> result = executor.execute_query('SELECT * FROM members WHERE age >= 30')
            >>> result['success']
            True
            >>> len(result['data'])
            150
        """
        # Layer 1: Validate SQL
        validation = self._validate_sql(sql)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "sql_executed": sql,
            }

        # Layer 3: Auto-inject LIMIT clause
        sql_stripped = sql.strip().rstrip(";")
        if "LIMIT" not in sql_stripped.upper():
            sql_executed = f"{sql_stripped} LIMIT {max_rows}"
        else:
            sql_executed = sql_stripped

        # Layer 2 & 4: READ ONLY connection with timeout
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Execute query
            cursor.execute(sql_executed)
            rows = cursor.fetchall()

            # Extract column names
            columns = [desc[0] for desc in cursor.description]

            # Convert rows to list of dictionaries
            data = [dict(zip(columns, row)) for row in rows]

            cursor.close()
            conn.close()

            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "sql_executed": sql_executed,
            }

        except sqlite3.OperationalError as e:
            error_msg = str(e)
            if "readonly" in error_msg.lower() or "attempt to write" in error_msg.lower():
                return {
                    "success": False,
                    "error": "書込み操作は許可されていません（READ ONLYモード）",
                    "sql_executed": sql_executed,
                }
            else:
                return {
                    "success": False,
                    "error": f"SQL実行エラー: {error_msg}",
                    "sql_executed": sql_executed,
                }

        except sqlite3.Error as e:
            return {
                "success": False,
                "error": f"データベースエラー: {str(e)}",
                "sql_executed": sql_executed,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"予期しないエラー: {str(e)}",
                "sql_executed": sql_executed,
            }
