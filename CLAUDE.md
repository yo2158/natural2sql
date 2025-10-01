# Text-to-SQL プロジェクト記録

## ⚠️ プロジェクト最高原則（全行動に優先）
**目的**: AIを用いたシステム開発実績と記事作成によるエンジニア価値向上

**絶対禁止**: この目的に沿わない行動は一切禁止
- 技術のための技術
- 過剰な完璧主義
- 記事化できない複雑な実装
- ユーザー価値（記事執筆・実績作り）に繋がらない作業

## プロジェクト概要
自然言語からSQLクエリを自動生成するText-to-SQLシステムの構築
最終成果物: **技術記事（Qiita/Zenn）+ GitHub実装**

## Obsidian記録
- **プロジェクトディレクトリ**: `/mnt/obsidian/02_Projects/txt2sql/`
- **DB構築ノウハウ**: [dataset-db-troubleshooting.md](/mnt/obsidian/02_Projects/txt2sql/dataset-db-troubleshooting.md)

## プロジェクト進捗

### 完了: デモ用テストデータセット構築 ✅
- 飲食店予約サイトを模した280万件のテストデータ生成完了
- MySQL最適化（INDEX設計、外部キー制約削除）により高速インポート実現
- restaurant名を飲食店らしい名前に修正（居酒屋〇〇、レストラン〇〇、〇〇亭など）
- 最終実行時間: CSV生成21秒 + MySQLインポート30秒 = **合計51秒**
- 詳細: [dataset-db-troubleshooting.md](/mnt/obsidian/02_Projects/txt2sql/dataset-db-troubleshooting.md)

### 主要な技術的成果
1. **INDEX最適化**: access_logs PRIMARY KEY削除で200万件が21秒でインポート
2. **外部キー制約削除**: 参照専用データのため不要と判断
3. **店名生成ロジック**: Faker last_name()とパターン組み合わせで自然な飲食店名

## 次のステップ
1. Text-to-SQLエンジン実装
2. デモアプリケーション構築
3. 技術記事執筆（Qiita/Zenn想定）