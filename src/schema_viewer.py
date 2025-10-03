"""
スキーマビューアー

データベーススキーマ情報をStreamlitモーダルダイアログで表示するモジュール。
論理名定義があれば併記する。
"""

import streamlit as st
from typing import List, Dict, Any, Optional


class SchemaViewer:
    """
    データベーススキーマビューアー

    スキーマ情報をStreamlitのモーダルダイアログで表示する。
    論理名定義があれば物理名の後に括弧付きで表示する。
    """

    def __init__(self, schema: List[Dict[str, Any]], logical_names: Optional[Dict[str, str]] = None):
        """
        SchemaViewerを初期化

        Args:
            schema: データベーススキーマ情報
                各要素は以下のキーを持つ辞書:
                - table_name: str - テーブル名
                - columns: List[Dict] - カラム情報のリスト
                    - column_name: str - カラム名
                    - data_type: str - データ型
                    - is_primary_key: bool - 主キーか否か
            logical_names: 物理名→論理名マッピング（オプション）
        """
        self.schema = schema
        self.logical_names = logical_names or {}

    def show(self) -> None:
        """
        スキーマ情報をモーダルダイアログで表示

        Streamlit 1.31.0以降の@st.dialogデコレーターを使用してモーダル表示。
        各テーブルはst.expander()で折りたたみ可能。
        カラム一覧はst.table()で表形式表示。
        論理名があれば「物理名 (論理名)」形式で表示。
        プライマリキーには🔑マークを付与。
        """
        @st.dialog("📊 データベーススキーマ一覧", width="large")
        def schema_dialog():
            for table in self.schema:
                # テーブル論理名を取得
                table_name = table['table_name']
                table_logical = self.logical_names.get(table_name, "")

                # テーブル表示名（論理名があれば併記）
                if table_logical and table_logical != table_name:
                    table_display = f"**{table_name}** ({table_logical})"
                else:
                    table_display = f"**{table_name}**"

                with st.expander(table_display):
                    # カラム一覧を4カラム形式で表示（物理名・論理名・データ型・PK）
                    columns_data = []
                    for col in table['columns']:
                        col_name = col['column_name']
                        logical = self.logical_names.get(col_name, "")

                        # 論理名は別カラムで表示（論理名定義がある場合のみ）
                        pk_mark = "🔑" if col['is_primary_key'] else ""

                        columns_data.append({
                            "物理名": col_name,
                            "論理名": logical,
                            "データ型": col['data_type'],
                            "PK": pk_mark
                        })

                    st.table(columns_data)

        schema_dialog()
