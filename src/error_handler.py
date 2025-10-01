"""
Error handling module for Text-to-SQL system.

This module provides error classification, user-friendly messages,
and retry logic for SQL generation and execution errors.
"""

from typing import Dict, Optional


class ErrorHandler:
    """
    Handler for errors in Text-to-SQL workflow.

    Classifies errors into types and provides:
    - User-friendly error messages
    - Retry decision logic
    - Error context for AI retry
    """

    # Error type to user message mapping
    ERROR_MESSAGES = {
        "invalid_question": (
            "❌ この質問はデータベースクエリに変換できません\n\n"
            "💡 レストラン予約データ（会員、店舗、予約、レビュー等）に関する質問をしてください。"
        ),
        "timeout_error": (
            "⏱️ タイムアウトエラー\n\n"
            "処理に時間がかかりすぎました。より単純なクエリをお試しください。"
        ),
        "permission_error": (
            "🔒 権限エラー\n\n"
            "データベースへの書込み操作は許可されていません。SELECT文のみ実行可能です。"
        ),
        "column_error": (
            "📋 カラムエラー\n\n"
            "指定されたカラムが存在しません。利用可能なカラムを確認してください。"
        ),
        "table_error": (
            "📊 テーブルエラー\n\n"
            "指定されたテーブルが存在しません。利用可能なテーブル: members, restaurants, reservations, access_logs, reviews, favorites"
        ),
        "syntax_error": (
            "⚠️ SQL構文エラー\n\n"
            "SQLクエリの構文に誤りがあります。自動修正を試みます..."
        ),
        "extraction_failed": (
            "🔍 SQL抽出失敗\n\n"
            "AI応答からSQLを抽出できませんでした。別の表現でお試しください。"
        ),
    }

    def __init__(self) -> None:
        """Initialize ErrorHandler."""
        pass

    def handle_error(
        self, error_type: str, error_message: str, sql: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Handle error and return user-friendly message.

        Args:
            error_type: Error type key
            error_message: Raw error message
            sql: Optional SQL that caused the error

        Returns:
            Dictionary with error handling result:
            - display_message: User-friendly message
            - error_context: Context for AI retry (if applicable)

        Example:
            >>> handler = ErrorHandler()
            >>> result = handler.handle_error('syntax_error', 'no such column: foo', 'SELECT foo FROM members')
            >>> print(result['display_message'])
            ⚠️ SQL構文エラー...
        """
        # Get user-friendly message
        display_message = self.ERROR_MESSAGES.get(
            error_type,
            f"❌ エラーが発生しました\n\n{error_message}",
        )

        # Create error context for AI retry
        error_context = f"エラー種別: {error_type}\n"
        if sql:
            error_context += f"実行SQL: {sql}\n"
        error_context += f"エラー詳細: {error_message}"

        return {
            "display_message": display_message,
            "error_context": error_context,
        }

    def should_retry(self, error_type: str) -> bool:
        """
        Determine if error should trigger AI retry.

        Args:
            error_type: Error type key

        Returns:
            True if retry should be attempted, False otherwise

        Retry logic:
            - Retry: syntax_error, column_error, table_error, extraction_failed
            - No retry: invalid_question, timeout_error, permission_error

        Example:
            >>> handler = ErrorHandler()
            >>> handler.should_retry('syntax_error')
            True
            >>> handler.should_retry('invalid_question')
            False
        """
        # Errors that should trigger retry
        retryable_errors = [
            "syntax_error",
            "column_error",
            "table_error",
            "extraction_failed",
        ]

        # Errors that should NOT trigger retry
        non_retryable_errors = [
            "invalid_question",  # User question is out of scope
            "timeout_error",  # Retry won't help
            "permission_error",  # Security restriction
        ]

        if error_type in retryable_errors:
            return True
        elif error_type in non_retryable_errors:
            return False
        else:
            # Unknown error: retry by default
            return True
