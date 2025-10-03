"""
natural2sql - Natural Language to SQL Generator

A Streamlit application that converts natural language queries
into SQL statements using AI (Gemini/Ollama) and executes them safely.
"""

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

from src.config import Config
from src.database_connector import create_database_connector
from src.logical_names_loader import LogicalNamesLoader
from src.business_terms_loader import BusinessTermsLoader
from src.prompt_generator import PromptGenerator
from src.ai_connector import create_ai_connector
from src.sql_parser import SQLParser
from src.error_handler import ErrorHandler
from src.schema_viewer import SchemaViewer


# Page configuration
st.set_page_config(
    page_title="natural2sql - Natural Language to SQL",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def check_ollama_available() -> bool:
    """
    Check if Ollama server is running.

    Returns:
        bool: True if Ollama is available, False otherwise
    """
    try:
        ollama_url = Config.OLLAMA_HOST
        response = requests.get(f"{ollama_url}/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def validate_config_on_startup() -> Tuple[Any, List[Dict[str, Any]], Optional[Dict[str, str]], Optional[List[Dict[str, str]]]]:
    """
    起動時設定検証とコンポーネント初期化

    Returns:
        Tuple containing:
        - connector: DatabaseConnector instance
        - schema: データベーススキーマ情報
        - logical_names: 論理名マッピング（オプション）
        - business_terms: ビジネス用語定義（オプション）

    Raises:
        ValueError: DB設定エラー
        Exception: DB接続・スキーマ取得失敗
    """
    # Config validation
    Config.validate()

    # DB_TYPE確認
    if Config.DB_TYPE not in ["sqlite", "mysql"]:
        st.error(f"❌ 未対応のDB_TYPE: {Config.DB_TYPE}")
        st.stop()

    # DatabaseConnector作成
    try:
        connector = create_database_connector()
    except ValueError as e:
        st.error(f"❌ DB設定エラー: {e}")
        st.stop()

    # 接続テスト
    try:
        connector.connect()
    except Exception as e:
        st.error(f"❌ DB接続失敗: {e}")
        st.stop()

    # スキーマ取得
    try:
        schema = connector.get_schema()
    except Exception as e:
        st.error(f"❌ スキーマ取得失敗: {e}")
        st.stop()

    # 論理名ロード（オプション）
    logical_names = None
    if Config.LOGICAL_NAMES_PATH:
        try:
            path = Config.resolve_path(Config.LOGICAL_NAMES_PATH)
            logical_names = LogicalNamesLoader.load(str(path))
        except (FileNotFoundError, ValueError, UnicodeDecodeError) as e:
            st.warning(f"⚠️ 論理名定義読み込み失敗: {e}。物理名のみで動作します。")

    # ビジネス用語ロード（オプション）
    business_terms = None
    if Config.BUSINESS_TERMS_PATH:
        try:
            path = Config.resolve_path(Config.BUSINESS_TERMS_PATH)
            business_terms = BusinessTermsLoader.load(str(path))
            if business_terms and len(business_terms) > 200:
                st.warning(f"⚠️ ビジネス用語は200件まで推奨（現在{len(business_terms)}件）")
        except (FileNotFoundError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
            st.warning(f"⚠️ ビジネス用語定義読み込み失敗: {e}。用語なしで動作します。")

    return connector, schema, logical_names, business_terms


@st.cache_resource
def init_system():
    """
    Initialize system components with caching.

    Returns:
        Dictionary containing initialized components:
        - connector: DatabaseConnector instance
        - schema: データベーススキーマ情報
        - logical_names: 論理名マッピング
        - business_terms: ビジネス用語定義
        - prompt_gen: PromptGenerator instance
        - sql_parser: SQLParser instance
        - error_handler: ErrorHandler instance

    Note:
        This function is cached by Streamlit to avoid re-initialization
        on every rerun. Config validation is performed here.
    """
    # 起動時検証とロード
    connector, schema, logical_names, business_terms = validate_config_on_startup()

    # Initialize components
    prompt_gen = PromptGenerator(schema, logical_names, business_terms)
    sql_parser = SQLParser()
    error_handler = ErrorHandler()

    return {
        "connector": connector,
        "schema": schema,
        "logical_names": logical_names,
        "business_terms": business_terms,
        "prompt_gen": prompt_gen,
        "sql_parser": sql_parser,
        "error_handler": error_handler,
    }


def start_execution():
    """Sets the execution flag in session state."""
    st.session_state.is_executing = True


def main():
    """Main application logic."""
    # Initialize execution state
    if "is_executing" not in st.session_state:
        st.session_state.is_executing = False

    # Initialize system
    try:
        sys = init_system()
    except (ValueError, FileNotFoundError) as e:
        st.error(f"❌ 設定エラー\n\n{str(e)}")
        st.stop()
        return

    # Sidebar UI
    # Schema viewer button (before settings)
    if st.sidebar.button("📊 スキーマ一覧を表示"):
        viewer = SchemaViewer(sys["schema"], sys["logical_names"])
        viewer.show()

    # DB connection info display
    if Config.DB_TYPE == "sqlite":
        db_info = f"**接続中:** SQLite (`{Config.DB_PATH.name}`)"
    else:  # mysql
        db_info = f"**接続中:** MySQL (`{Config.DB_NAME}`)"
    st.sidebar.info(db_info)

    st.sidebar.markdown("---")

    st.sidebar.header("⚙️ 設定")

    # Check Ollama availability
    ollama_available = check_ollama_available()

    # AI Provider selection
    if not ollama_available:
        st.sidebar.radio(
            "AIプロバイダ",
            ["Gemini"],
            index=0,
            help="Ollama: サーバーが起動していません",
        )
        provider = "Gemini"
    else:
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
    show_history = st.sidebar.checkbox(
        "履歴表示",
        value=False,
        help="このセッション中のクエリ履歴を表示（ブラウザを閉じると消去されます）",
    )

    # Clear history button
    if st.sidebar.button("履歴クリア"):
        if "query_history" in st.session_state:
            st.session_state.query_history = []
            st.success("履歴をクリアしました")

    # Main area header and query input UI (Task 29)
    st.title("🔍 natural2sql - Natural Language to SQL Generator")
    st.markdown("自然言語でデータベースに問い合わせできます")

    # Sample query selection (only for sample DB)
    is_sample_db = (
        Config.DB_TYPE == "sqlite" and
        Config.DB_PATH.name == "restaurant.db"
    )

    selected_sample = ""
    if is_sample_db:
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
    st.button(
        "🚀 SQL生成・実行",
        type="primary",
        on_click=start_execution,
        disabled=st.session_state.is_executing or not user_input.strip(),
    )

    # Execute query (Tasks 30-35)
    if st.session_state.is_executing:
        # Empty input check
        if not user_input.strip():
            st.error("❌ 質問を入力してください")
            st.session_state.is_executing = False
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
            st.session_state.is_executing = False
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
                    st.session_state.is_executing = False
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
                        st.session_state.is_executing = False
                        return

                # SQL execution
                sql = parse_result["sql"]
                st.code(sql, language="sql")

                with st.spinner("⚡ SQL実行中..."):
                    try:
                        df = sys["connector"].execute_query(sql)
                        row_count = len(df)

                        # Display success message with row count
                        if row_count >= 1000:
                            st.success(f"✅ 成功 ({row_count}件、最大1000件まで表示)")
                        else:
                            st.success(f"✅ 成功 ({row_count}件)")

                        # Display results
                        if row_count > 0:
                            st.dataframe(df, use_container_width=True)

                            # CSV download button
                            csv = df.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="📥 CSVダウンロード",
                                data=csv,
                                file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                            )

                            st.info("SQLは誤りを含む場合があります。内容はご確認ください。")
                        else:
                            st.info("📊 結果: 0件")

                        # Save to history
                        if "query_history" not in st.session_state:
                            st.session_state.query_history = []

                        st.session_state.query_history.insert(
                            0,
                            {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "question": user_input,
                                "sql": sql,
                                "row_count": row_count,
                                "success": True,
                            },
                        )

                        # Success - reset state and break retry loop
                        st.session_state.is_executing = False
                        break

                    except (ValueError, PermissionError, RuntimeError) as e:
                        # SQL execution failed (retry logic)
                        error_message = str(e)

                        if attempt < max_retries - 1:
                            # Determine if retry should be attempted
                            error_type = "syntax_error"  # Default
                            if "禁止操作" in error_message or "許可されていません" in error_message:
                                error_type = "permission_error"
                            elif "no such column" in error_message.lower():
                                error_type = "column_error"
                            elif "no such table" in error_message.lower():
                                error_type = "table_error"

                            should_retry = sys["error_handler"].should_retry(error_type)

                            if should_retry:
                                st.warning(
                                    f"🔄 SQL実行エラー、修正中... ({attempt + 1}/{max_retries})"
                                )
                                error_context = {
                                    "sql": sql,
                                    "error_message": error_message,
                                }
                                continue
                            else:
                                # Non-retryable error
                                error_result = sys["error_handler"].handle_error(
                                    error_type, error_message, sql
                                )
                                st.error(error_result["display_message"])
                                with st.expander("エラー詳細"):
                                    st.text(error_result["error_context"])
                                st.session_state.is_executing = False
                                return
                        else:
                            # Max retries reached
                            st.error("❌ SQL実行に失敗しました（リトライ上限）")
                            st.error(error_message)
                            with st.expander("実行されたSQL"):
                                st.code(sql, language="sql")
                            st.session_state.is_executing = False
                            return

            except Exception as e:
                st.error(f"❌ 予期しないエラー: {str(e)}")
                st.session_state.is_executing = False
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
