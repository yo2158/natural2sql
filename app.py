"""
txt2sql - Text-to-SQL Generator

A Streamlit application that converts natural language queries
into SQL statements using AI (Gemini/Ollama) and executes them safely.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional

from src.config import Config
from src.prompt_generator import PromptGenerator
from src.ai_connector import create_ai_connector
from src.sql_parser import SQLParser
from src.sql_executor import SQLExecutor
from src.error_handler import ErrorHandler


# Page configuration
st.set_page_config(
    page_title="txt2sql - Text to SQL",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def init_system() -> Dict[str, Any]:
    """
    Initialize system components with caching.

    Returns:
        Dictionary containing initialized components:
        - prompt_gen: PromptGenerator instance
        - sql_parser: SQLParser instance
        - sql_executor: SQLExecutor instance
        - error_handler: ErrorHandler instance

    Note:
        This function is cached by Streamlit to avoid re-initialization
        on every rerun. Config validation is performed here.
    """
    # Validate configuration
    Config.validate()

    # Initialize components
    prompt_gen = PromptGenerator()
    sql_parser = SQLParser()
    sql_executor = SQLExecutor(str(Config.DB_PATH))
    error_handler = ErrorHandler()

    return {
        "prompt_gen": prompt_gen,
        "sql_parser": sql_parser,
        "sql_executor": sql_executor,
        "error_handler": error_handler,
    }


def main():
    """Main application logic."""
    # Initialize system
    sys = init_system()

    # Sidebar UI (Task 28)
    st.sidebar.header("⚙️ 設定")

    # AI Provider selection
    provider = st.sidebar.radio("AIプロバイダ", ["Gemini", "Ollama"], index=0)

    # Model selection
    if provider == "Gemini":
        selected_model = st.sidebar.selectbox(
            "モデル",
            ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"],
            index=0,
        )
    else:  # Ollama
        selected_model = st.sidebar.selectbox(
            "モデル", ["gemma3:12b", "gemma3:27b", "gpt-oss:latest"], index=0
        )

    # History display toggle
    show_history = st.sidebar.checkbox("履歴表示", value=False)

    # Clear history button
    if st.sidebar.button("履歴クリア"):
        if "query_history" in st.session_state:
            st.session_state.query_history = []
            st.success("履歴をクリアしました")

    # Main area header and query input UI (Task 29)
    st.title("🔍 txt2sql - Text-to-SQL Generator")
    st.markdown("自然言語でデータベースに問い合わせできます")

    # Sample query selection
    sample_queries = [
        "",
        "30代の会員は何人いますか？",
        "評価4以上のイタリアンレストランを表示",
        "2025年1月に最も予約が多かった店舗TOP5",
        "休眠会員（90日以上予約なし）は何人？",
    ]
    selected_sample = st.selectbox("サンプル選択（任意）", sample_queries, index=0)

    # Text input area
    user_input = st.text_area(
        "自然言語でクエリを入力",
        value=selected_sample,
        max_chars=1000,
        height=100,
        placeholder="例: 30代の会員は何人いますか？",
    )

    # Execute button
    execute_button = st.button("🚀 SQL生成・実行", type="primary")

    # Execute query (Tasks 30-35)
    if execute_button:
        # Empty input check
        if not user_input.strip():
            st.error("❌ 質問を入力してください")
            return

        # Create AI connector (Task 30)
        try:
            if provider == "Gemini":
                ai_connector = create_ai_connector(
                    "gemini", api_key=Config.GEMINI_API_KEY, model=selected_model
                )
            else:  # Ollama
                ai_connector = create_ai_connector(
                    "ollama", host=Config.OLLAMA_HOST, model=selected_model
                )
        except Exception as e:
            st.error(f"❌ AI接続エラー: {str(e)}")
            return

        # Retry loop (Task 33)
        max_retries = Config.MAX_RETRIES
        error_context = None

        for attempt in range(max_retries):
            try:
                # Generate prompt (Task 30)
                prompt = sys["prompt_gen"].generate(user_input, error_context)

                # AI inference
                with st.spinner(f"🤖 AI推論中... ({attempt + 1}/{max_retries})"):
                    ai_response = ai_connector.generate(prompt)

                # SQL extraction (Task 31)
                parse_result = sys["sql_parser"].extract_sql(ai_response)

                # ERROR detection - TEST-F09 (Task 31)
                if (
                    not parse_result["success"]
                    and parse_result.get("error_type") == "invalid_question"
                ):
                    error_result = sys["error_handler"].handle_error(
                        "invalid_question", parse_result.get("error_message", "")
                    )
                    st.error(error_result["display_message"])
                    return

                # Extraction failed
                if not parse_result["success"]:
                    if attempt < max_retries - 1:
                        st.warning(
                            f"⚠️ SQL抽出失敗、リトライ中... ({attempt + 1}/{max_retries})"
                        )
                        error_context = {
                            "sql": None,
                            "error_message": parse_result.get(
                                "error_message", "SQL抽出失敗"
                            ),
                        }
                        continue
                    else:
                        st.error("❌ SQL抽出に失敗しました（リトライ上限）")
                        return

                # SQL execution (Task 32)
                sql = parse_result["sql"]
                st.code(sql, language="sql")

                with st.spinner("⚡ SQL実行中..."):
                    result = sys["sql_executor"].execute_query(sql)

                # Success (Task 34)
                if result["success"]:
                    # Display success message with row count
                    if result["row_count"] >= 1000:
                        st.success(f"✅ 成功 ({result['row_count']}件、最大1000件まで表示)")
                    else:
                        st.success(f"✅ 成功 ({result['row_count']}件)")

                    # Display results
                    if result["row_count"] > 0:
                        df = pd.DataFrame(result["data"])
                        st.dataframe(df, use_container_width=True)

                        # CSV download button
                        csv = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="📥 CSVダウンロード",
                            data=csv,
                            file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                        )

                        # Display executed SQL
                        with st.expander("実行されたSQL"):
                            st.code(result.get("sql_executed", sql), language="sql")
                    else:
                        st.info("📊 結果: 0件")

                    # Save to history (Task 35)
                    if "query_history" not in st.session_state:
                        st.session_state.query_history = []

                    st.session_state.query_history.insert(
                        0,
                        {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "question": user_input,
                            "sql": sql,
                            "row_count": result["row_count"],
                            "success": True,
                        },
                    )

                    # Success - break retry loop
                    break

                else:
                    # SQL execution failed (Task 33 retry logic)
                    if attempt < max_retries - 1:
                        # Determine if retry should be attempted
                        error_type = "syntax_error"  # Default
                        if "禁止操作" in result.get("error", ""):
                            error_type = "permission_error"
                        elif "no such column" in result.get("error", "").lower():
                            error_type = "column_error"
                        elif "no such table" in result.get("error", "").lower():
                            error_type = "table_error"

                        should_retry = sys["error_handler"].should_retry(error_type)

                        if should_retry:
                            st.warning(
                                f"🔄 SQL実行エラー、修正中... ({attempt + 1}/{max_retries})"
                            )
                            error_context = {
                                "sql": sql,
                                "error_message": result.get("error", "実行エラー"),
                            }
                            continue
                        else:
                            # Non-retryable error
                            error_result = sys["error_handler"].handle_error(
                                error_type, result.get("error", ""), sql
                            )
                            st.error(error_result["display_message"])
                            with st.expander("エラー詳細"):
                                st.text(error_result["error_context"])
                            return
                    else:
                        # Max retries reached
                        st.error("❌ SQL実行に失敗しました（リトライ上限）")
                        st.error(result.get("error", "不明なエラー"))
                        with st.expander("実行されたSQL"):
                            st.code(sql, language="sql")
                        return

            except Exception as e:
                st.error(f"❌ 予期しないエラー: {str(e)}")
                return

    # Display query history (Task 35)
    if show_history and "query_history" in st.session_state:
        st.markdown("---")
        st.subheader("📜 クエリ履歴")
        for i, record in enumerate(st.session_state.query_history[:10]):
            with st.expander(
                f"{record['timestamp']} - {record['question'][:50]}... ({record['row_count']}件)"
            ):
                st.markdown(f"**質問:** {record['question']}")
                st.code(record["sql"], language="sql")


if __name__ == "__main__":
    main()
