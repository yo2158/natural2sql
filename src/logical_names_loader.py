"""
論理名定義ローダー

物理名（カラム名）から論理名（日本語表示名）へのマッピングを
CSVファイルから読み込むモジュール。
"""

import pandas as pd
from typing import Dict, Optional
from pathlib import Path


class LogicalNamesLoader:
    """
    論理名定義ローダー

    CSVファイルから物理名→論理名のマッピングを読み込む。
    プロンプトインジェクション防止のため禁止ワード検証を実施。
    """

    # 禁止ワードリスト（プロンプトインジェクション防止）
    PROHIBITED_WORDS = [
        "無視", "ignore", "指示", "重要", "システム",
        "プロンプト", "以下", "上記", "破棄", "削除",
        "あなたの役割", "代わりに", "最優先"
    ]

    @staticmethod
    def load(file_path: str) -> Optional[Dict[str, str]]:
        """
        CSVファイルから論理名定義を読み込む

        Args:
            file_path: CSVファイルパス

        Returns:
            物理名→論理名のマッピング辞書（エラー時はNone）

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: フォーマット不正、禁止ワード検出時

        CSV形式:
            physical_name,logical_name
            member_id,会員ID
            name,氏名
        """
        try:
            # ファイル存在確認
            if not Path(file_path).exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

            # CSV読み込み（UTF-8）
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                raise ValueError(
                    f"ファイルの文字エンコーディングが正しくありません: {file_path}\n"
                    "UTF-8形式で保存してください。"
                )

            # ヘッダー検証
            required_cols = {"physical_name", "logical_name"}
            if not required_cols.issubset(df.columns):
                raise ValueError(
                    f"必須カラム不足: {required_cols}\n"
                    f"現在のカラム: {set(df.columns)}"
                )

            # NULL/空値処理 & 禁止ワード検証
            mapping = {}
            for _, row in df.iterrows():
                physical = str(row["physical_name"]).strip()
                logical = str(row["logical_name"]).strip()

                # physical_nameが空の行はスキップ
                if not physical or physical == "nan":
                    continue

                # logical_nameが空またはnanの場合、physical_nameで代替
                if not logical or logical == "nan":
                    logical = physical

                # 禁止ワード検証（セキュリティ対策: プロンプトインジェクション防止）
                if any(word.lower() in logical.lower() for word in LogicalNamesLoader.PROHIBITED_WORDS):
                    raise ValueError(
                        f"論理名に禁止ワードが含まれています: {physical} -> {logical}\n"
                        f"禁止ワード: {', '.join(LogicalNamesLoader.PROHIBITED_WORDS)}"
                    )

                mapping[physical] = logical

            return mapping

        except FileNotFoundError:
            # ファイル不存在エラーはそのまま再スロー（呼び出し側で警告表示）
            raise

        except ValueError:
            # フォーマット不正、禁止ワードエラーはそのまま再スロー
            raise

        except Exception as e:
            # 予期しないエラーはValueErrorに変換
            raise ValueError(f"論理名定義ファイルの読み込みに失敗しました: {str(e)}")
