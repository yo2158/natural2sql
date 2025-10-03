"""
Prompt generation module for Text-to-SQL conversion.

This module generates prompts for AI models to convert natural language queries
into SQL statements, including schema information, logical names, and business terminology.
"""

from typing import Optional, Dict, List, Any


class PromptGenerator:
    """
    Generates prompts for Text-to-SQL conversion.

    This class maintains database schema information, logical names, and business terminology,
    and generates structured prompts for AI models to convert natural language
    queries into SQL statements.
    """

    def __init__(
        self,
        schema: List[Dict[str, Any]],
        logical_names: Optional[Dict[str, str]] = None,
        business_terms: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """
        Initialize PromptGenerator with schema information and optional enhancements.

        Args:
            schema: Database schema information from DatabaseConnector.get_schema()
                   List of dicts with 'table_name' and 'columns' keys
            logical_names: Optional mapping from physical_name to logical_name
            business_terms: Optional list of business term definitions
                          Each dict has 'term' and 'definition' keys
        """
        self.schema = schema
        self.logical_names = logical_names or {}
        self.business_terms = business_terms or []

    def _build_schema_section(self) -> str:
        """
        Build schema section with logical names integration.

        Returns:
            Formatted schema information string
        """
        schema_lines = []

        for table in self.schema:
            table_name = table['table_name']
            columns = table['columns']

            # Build CREATE TABLE statement
            schema_lines.append(f"CREATE TABLE {table_name} (")

            column_defs = []
            for col in columns:
                col_name = col['column_name']
                col_type = col['data_type']
                is_pk = col['is_primary_key']

                # Add logical name if available
                logical_name = self.logical_names.get(col_name, "")
                if logical_name and logical_name != col_name:
                    col_def = f"    {col_name} {col_type}"  # 論理名: {logical_name}
                    if is_pk:
                        col_def += " PRIMARY KEY"
                    col_def += f"  -- {logical_name}"
                else:
                    col_def = f"    {col_name} {col_type}"
                    if is_pk:
                        col_def += " PRIMARY KEY"

                column_defs.append(col_def)

            schema_lines.append(",\n".join(column_defs))
            schema_lines.append(");\n")

        return "\n".join(schema_lines)

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
            >>> schema = [{'table_name': 'members', 'columns': [...]}]
            >>> logical_names = {'member_id': '会員ID'}
            >>> generator = PromptGenerator(schema, logical_names)
            >>> prompt = generator.generate("30代の会員は何人いますか？")
        """
        # System prompt
        system_prompt = """あなたはSQLエキスパートです。
自然言語の質問をSQLクエリに変換してください。

以下のデータベーススキーマを使用してください:"""

        # Schema section with logical names
        schema_section = "\n\n" + self._build_schema_section()

        # Business terms section
        business_section = ""
        if self.business_terms:
            business_section = "\n\n**ビジネス用語の定義:**\n"
            for term_dict in self.business_terms:
                term = term_dict.get('term', '')
                definition = term_dict.get('definition', '')
                if term and definition:
                    business_section += f"- {term}: {definition}\n"

        # User input section
        user_section = f"""

ユーザーの質問:
{user_input}

"""

        # Important constraints section
        constraints = """

**重要な制約:**
- データベースに無関係な質問（天気、ニュース、一般知識等）には、以下の形式で応答してください:
  ERROR: この質問はデータベースクエリに変換できません
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

        # Error context section
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
            + schema_section
            + business_section
            + constraints
            + user_section
            + error_section
            + output_format
        )

        return prompt
