"""
ビジネス用語定義ローダー

業務特有の用語（「休眠会員」「人気店舗」等）の定義を
JSON Linesファイルから読み込むモジュール。
"""

import json
from typing import List, Dict, Optional
from pathlib import Path


class BusinessTermsLoader:
    """
    ビジネス用語定義ローダー

    JSON Linesファイルからビジネス用語定義を読み込む。
    プロンプトインジェクション防止のため禁止ワード検証を実施。
    """

    # 禁止ワードリスト（プロンプトインジェクション防止）
    PROHIBITED_WORDS = [
        "無視", "ignore", "指示", "重要", "システム",
        "プロンプト", "以下", "上記", "破棄", "削除",
        "あなたの役割", "代わりに", "最優先"
    ]

    # 最大用語数（パフォーマンス保護）
    MAX_TERMS = 200

    @staticmethod
    def load(file_path: str) -> Optional[List[Dict[str, str]]]:
        """
        JSON Linesファイルからビジネス用語定義を読み込む

        Args:
            file_path: JSON Linesファイルパス

        Returns:
            ビジネス用語定義のリスト（エラー時はNone）
            各要素は以下のキーを持つ辞書:
            - term: 用語名
            - definition: 定義

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: フォーマット不正、必須キー不足時

        JSON Lines形式:
            {"term": "休眠会員", "definition": "90日以上予約していない会員"}
            {"term": "人気店舗", "definition": "月間予約数が平均の2倍以上の店舗"}
        """
        try:
            # ファイル存在確認
            if not Path(file_path).exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

            terms = []

            # JSON Lines読み込み（UTF-8）
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, start=1):
                        line = line.strip()

                        # 空行スキップ
                        if not line:
                            continue

                        # JSON解析
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError as e:
                            raise ValueError(
                                f"{line_num}行目: JSON解析エラー: {e}\n"
                                "各行が正しいJSON形式か確認してください。"
                            )

                        # 必須キー検証
                        if "term" not in data or "definition" not in data:
                            raise ValueError(
                                f"{line_num}行目: 必須キー不足 (term, definition)\n"
                                f"現在のキー: {set(data.keys())}"
                            )

                        term_text = str(data["term"]).strip()
                        definition_text = str(data["definition"]).strip()

                        # 空値チェック
                        if not term_text or not definition_text:
                            # 空値の行はスキップ（警告なし）
                            continue

                        # 禁止ワード検証（セキュリティ対策: プロンプトインジェクション防止）
                        has_prohibited = False
                        for word in BusinessTermsLoader.PROHIBITED_WORDS:
                            if word.lower() in term_text.lower() or word.lower() in definition_text.lower():
                                # 禁止ワード検出時は行をスキップ（警告はStreamlit側で表示）
                                has_prohibited = True
                                break

                        if has_prohibited:
                            continue

                        terms.append({
                            "term": term_text,
                            "definition": definition_text
                        })

            except UnicodeDecodeError:
                raise ValueError(
                    f"ファイルの文字エンコーディングが正しくありません: {file_path}\n"
                    "UTF-8形式で保存してください。"
                )

            # 200件上限チェック（警告のみ、エラーにしない）
            if len(terms) > BusinessTermsLoader.MAX_TERMS:
                # 最初の200件のみ使用（Streamlit側で警告表示）
                terms = terms[:BusinessTermsLoader.MAX_TERMS]

            return terms

        except FileNotFoundError:
            # ファイル不存在エラーはそのまま再スロー（呼び出し側で警告表示）
            raise

        except ValueError:
            # フォーマット不正、必須キー不足エラーはそのまま再スロー
            raise

        except Exception as e:
            # 予期しないエラーはValueErrorに変換
            raise ValueError(f"ビジネス用語定義ファイルの読み込みに失敗しました: {str(e)}")
