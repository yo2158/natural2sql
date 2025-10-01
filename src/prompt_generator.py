"""
Prompt generation module for Text-to-SQL conversion.

This module generates prompts for AI models to convert natural language queries
into SQL statements, including schema information and business terminology.
"""

from typing import Optional, Dict


class PromptGenerator:
    """
    Generates prompts for Text-to-SQL conversion.

    This class maintains database schema information and business terminology,
    and generates structured prompts for AI models to convert natural language
    queries into SQL statements.
    """

    def __init__(self) -> None:
        """Initialize PromptGenerator with schema information and business terms."""
        # Database schema information (6 business tables)
        self.schema_info = """
CREATE TABLE members (
    member_id INTEGER PRIMARY KEY,
    postal_code TEXT,
    gender TEXT,
    age INTEGER,
    registration_date TEXT
);

CREATE TABLE restaurants (
    restaurant_id INTEGER PRIMARY KEY,
    name TEXT,
    genre TEXT,
    postal_code TEXT,
    registration_date TEXT
);

CREATE TABLE reservations (
    reservation_id INTEGER PRIMARY KEY,
    member_id INTEGER,
    restaurant_id INTEGER,
    reservation_date TEXT,
    visit_date TEXT
);

CREATE TABLE access_logs (
    session_id TEXT PRIMARY KEY,
    member_id INTEGER,
    restaurant_id INTEGER,
    access_date TEXT
);

CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY,
    member_id INTEGER,
    restaurant_id INTEGER,
    rating INTEGER,
    post_date TEXT
);

CREATE TABLE favorites (
    member_id INTEGER,
    restaurant_id INTEGER,
    registration_date TEXT,
    PRIMARY KEY (member_id, restaurant_id)
);
"""

        # Business terminology dictionary
        self.business_terms = {
            "休眠会員": "90日以上予約していない会員（reservations.reservation_dateで判定）",
            "アクティブ会員": "30日以内に予約した会員（reservations.reservation_dateで判定）",
            "人気店舗": "予約数が多い店舗（reservationsテーブルで集計）",
            "高評価店舗": "rating >= 4のレビューが多い店舗（reviewsテーブルで集計）",
            "常連会員": "同じ店舗に3回以上予約している会員（reservationsで集計）",
            "新規会員": "registration_dateが30日以内の会員",
            "先月": "date('now', '-30 days') から date('now', 'start of month') の期間",
            "今月": "date('now', 'start of month') から date('now') の期間",
        }

    def generate(self, user_input: str, error_context: Optional[Dict] = None) -> str:
        """
        Generate a prompt for Text-to-SQL conversion.

        Args:
            user_input: Natural language query from user
            error_context: Optional context from previous error (for retry)
                          Contains 'sql' and 'error_message' keys

        Returns:
            Formatted prompt string for AI model

        Example:
            >>> generator = PromptGenerator()
            >>> prompt = generator.generate("30代の会員は何人いますか？")
        """
        # System prompt
        system_prompt = """あなたはSQLエキスパートです。
自然言語の質問をSQLiteクエリに変換してください。

以下のデータベーススキーマを使用してください:"""

        # User input section
        user_section = f"""

ユーザーの質問:
{user_input}

"""

        # Business terms section (Task 11)
        business_section = "\n\n**ビジネス用語の定義:**\n"
        for term, definition in self.business_terms.items():
            business_section += f"- {term}: {definition}\n"

        # Important constraints section (Task 11 - TEST-F09)
        constraints = """

**重要な制約:**
- データベースに無関係な質問（天気、ニュース、一般知識等）には、以下の形式で応答してください:
  ERROR: この質問はデータベースクエリに変換できません
- 利用可能なテーブル: members, restaurants, reservations, access_logs, reviews, favorites のみ
- SQLite構文を使用してください（MySQL構文は不可）
- 日付関数: date('now'), date('now', '-30 days') 等を使用
"""

        # Output format specification
        output_format = """
**出力形式:**
SQLクエリのみを出力してください。説明文は不要です。
以下のいずれかの形式で出力してください:

1. ```sql で囲む形式:
```sql
SELECT * FROM members WHERE age >= 30
```

2. JSON形式:
{"sql": "SELECT * FROM members WHERE age >= 30"}

3. 直接SQL文:
SELECT * FROM members WHERE age >= 30
"""

        # Error context section (Task 12)
        error_section = ""
        if error_context:
            error_section = f"""

**前回のエラー情報（修正してください）:**
- 実行したSQL: {error_context.get('sql', 'N/A')}
- エラーメッセージ: {error_context.get('error_message', 'N/A')}

上記のエラーを修正したSQLクエリを生成してください。
"""

        # Construct complete prompt
        prompt = (
            system_prompt
            + "\n\n"
            + self.schema_info
            + business_section
            + constraints
            + user_section
            + error_section
            + output_format
        )

        return prompt
