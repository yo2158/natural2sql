"""
SQL parser module for extracting SQL from AI responses.

This module provides SQL extraction with 4-level fallback patterns.
"""

import re
import json
from typing import Dict, Any, Optional


class SQLParser:
    """
    Parser for extracting SQL from AI responses.

    Implements 4-level fallback pattern matching:
    - Pattern 0: ERROR detection
    - Pattern 1: ```sql``` code blocks
    - Pattern 2: JSON format
    - Pattern 3: Direct SELECT/WITH statements
    - Pattern 4: Extraction failed
    """

    def __init__(self) -> None:
        """Initialize SQLParser."""
        pass

    def extract_sql(self, ai_response: str) -> Dict[str, Any]:
        """
        Extract SQL from AI response using 4-level fallback.

        Args:
            ai_response: Raw response from AI model

        Returns:
            Dictionary with extraction result:
            - success: bool - Whether extraction succeeded
            - sql: Optional[str] - Extracted SQL (None if failed)
            - error_type: Optional[str] - Error type if failed
            - error_message: Optional[str] - Error message if failed

        Example:
            >>> parser = SQLParser()
            >>> result = parser.extract_sql("```sql\\nSELECT * FROM members\\n```")
            >>> result['success']
            True
            >>> result['sql']
            'SELECT * FROM members'
        """
        # Pattern 0: ERROR detection (TEST-F09)
        if ai_response.strip().startswith("ERROR:"):
            return {
                "success": False,
                "sql": None,
                "error_type": "invalid_question",
                "error_message": ai_response.strip(),
            }

        # Pattern 1: ```sql``` code blocks
        pattern1 = r"```sql\s*(.*?)\s*```"
        match = re.search(pattern1, ai_response, re.DOTALL | re.IGNORECASE)
        if match:
            return {"success": True, "sql": match.group(1).strip()}

        # Pattern 2: JSON format
        try:
            data = json.loads(ai_response)
            if isinstance(data, dict) and "sql" in data:
                return {"success": True, "sql": data["sql"].strip()}
        except (json.JSONDecodeError, KeyError, AttributeError):
            pass

        # Pattern 3: Direct SELECT/WITH statements
        pattern3 = r"((?:WITH|SELECT)\s+.*?)(?:;|\Z)"
        match = re.search(pattern3, ai_response, re.DOTALL | re.IGNORECASE)
        if match:
            return {"success": True, "sql": match.group(1).strip()}

        # Pattern 4: Extraction failed
        return {
            "success": False,
            "sql": None,
            "error_type": "extraction_failed",
            "error_message": "AI応答からSQLを抽出できませんでした",
        }
