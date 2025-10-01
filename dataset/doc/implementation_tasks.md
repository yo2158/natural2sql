# テストデータ生成システム 実装タスクリスト

**プロジェクト**: Text-to-SQL Demo Dataset Generator
**作成日**: 2025-09-30
**基本設計**: tmp/basic_design.md

---

## タスク概要

| Phase | タスク数 | 推定時間 |
|-------|---------|---------|
| Phase 1: 環境構築 | 3 | 30分 |
| Phase 2: マスタデータ生成 | 3 | 60分 |
| Phase 3: トランザクションデータ生成 | 4 | 90分 |
| Phase 4: MySQL連携 | 2 | 45分 |
| Phase 5: 検証・完了 | 3 | 45分 |
| **合計** | **15** | **約4.5時間** |

---

## Phase 1: 環境構築

### Task 1.1: ディレクトリ構造作成
- [ ] `dataset/` ディレクトリ作成
- [ ] `dataset/data/` 作成（CSV出力先）
- [ ] `dataset/logs/` 作成（ログ出力先）
- [ ] `dataset/doc/` 作成（ドキュメント配置先）

**成果物**: ディレクトリ構造
**所要時間**: 5分

---

### Task 1.2: requirements.txt作成
- [ ] 依存パッケージリスト作成
  - faker==22.0.0
  - pandas==2.1.4
  - numpy==1.26.2
  - mysql-connector-python==8.2.0
  - tqdm==4.66.1

**成果物**: `dataset/requirements.txt`
**所要時間**: 5分

---

### Task 1.3: config.py作成
- [ ] データ量設定（DATA_VOLUME）
- [ ] チャンクサイズ設定（CHUNK_SIZE）
- [ ] パレート比率設定（PARETO_RATIOS）
- [ ] MySQL接続情報設定
- [ ] ジャンルリスト定義

**成果物**: `dataset/config.py`
**所要時間**: 20分

---

## Phase 2: マスタデータ生成実装

### Task 2.1: generate_data.py基本構造作成
- [ ] DataGeneratorクラス定義
- [ ] ログ初期化処理
- [ ] main()関数骨格
- [ ] 進捗バー設定（tqdm）

**成果物**: `dataset/generate_data.py`（骨格）
**所要時間**: 20分

---

### Task 2.2: members生成ロジック実装
- [ ] generate_members()メソッド実装
  - member_id（連番）
  - postal_code（Faker: ja_JP）
  - gender（M/F ランダム）
  - age（18-80 正規分布）
  - registration_date（過去10年以内）
- [ ] CSV出力処理
- [ ] ログ出力

**成果物**: members.csv生成機能
**所要時間**: 20分

---

### Task 2.3: restaurants生成ロジック実装
- [ ] generate_restaurants()メソッド実装
  - restaurant_id（連番）
  - name（Faker: company名をベース）
  - genre（config.pyから選択）
  - postal_code（Faker: ja_JP）
  - registration_date（過去10年～1年前）
- [ ] CSV出力処理
- [ ] ログ出力

**成果物**: restaurants.csv生成機能
**所要時間**: 20分

---

## Phase 3: トランザクションデータ生成実装

### Task 3.1: reservations生成（パレート分布）
- [ ] generate_reservations()メソッド実装
- [ ] パレート分布ロジック実装
  - 上位20%会員 → 80%予約の重み付け
  - 上位10%店舗 → 50%予約の重み付け
- [ ] reservation_date生成（過去10年以内）
- [ ] visit_date生成（reservation_date以降、10%はNULL）
- [ ] CSV出力処理
- [ ] ログ出力

**成果物**: reservations.csv生成機能
**所要時間**: 30分

---

### Task 3.2: access_logs生成（チャンク分割）
- [ ] generate_access_logs()メソッド実装
- [ ] チャンク分割処理（100,000件単位）
- [ ] session_id生成（UUID v4）
- [ ] member_id（30%はNULL=非ログイン）
- [ ] restaurant_id（ランダム選択）
- [ ] access_date生成（過去6ヶ月以内）
- [ ] CSV追記モード出力
- [ ] 進捗バー表示
- [ ] ログ出力

**成果物**: access_logs.csv生成機能（チャンク分割対応）
**所要時間**: 30分

---

### Task 3.3: reviews生成
- [ ] generate_reviews()メソッド実装
- [ ] reservationsから10%サンプリング（50,000件）
- [ ] rating生成（1-5、正規分布で平均3.5）
- [ ] post_date生成（過去5年以内）
- [ ] CSV出力処理
- [ ] ログ出力

**成果物**: reviews.csv生成機能
**所要時間**: 15分

---

### Task 3.4: favorites生成
- [ ] generate_favorites()メソッド実装
- [ ] member_id × restaurant_id ユニーク組み合わせ生成
- [ ] 30%がreservationsに繋がる設計
  - reservationsから45,000件の(member_id, restaurant_id)を抽出
  - 残り105,000件はランダム生成
- [ ] registration_date生成（過去5年以内）
- [ ] 重複チェック
- [ ] CSV出力処理
- [ ] ログ出力

**成果物**: favorites.csv生成機能
**所要時間**: 15分

---

## Phase 4: MySQL連携

### Task 4.1: import.sql作成
- [ ] CREATE TABLE members
- [ ] CREATE TABLE restaurants
- [ ] CREATE TABLE reservations（外部キー制約）
- [ ] CREATE TABLE access_logs（外部キー制約）
- [ ] CREATE TABLE reviews（外部キー制約）
- [ ] CREATE TABLE favorites（外部キー制約、複合主キー）
- [ ] INDEX定義（全テーブル）

**成果物**: `dataset/import.sql`
**所要時間**: 25分

---

### Task 4.2: MySQLインポート処理実装
- [ ] MySQLImporterクラス実装
- [ ] DB接続処理（mysql-connector-python）
- [ ] CREATE TABLE実行
- [ ] LOAD DATA INFILE実行（6テーブル）
- [ ] エラーハンドリング（リトライ3回）
- [ ] 接続クローズ処理
- [ ] ログ出力

**成果物**: MySQLインポート機能
**所要時間**: 20分

---

## Phase 5: 検証・完了

### Task 5.1: データ検証スクリプト実装
- [ ] validate_data()関数実装
- [ ] 件数確認（6テーブル）
- [ ] 外部キー整合性チェック
  - reservations.member_id → members存在確認
  - reservations.restaurant_id → restaurants存在確認
  - 他テーブルも同様
- [ ] 日付論理性チェック
  - reservation_date <= visit_date
- [ ] パレート分布確認
  - 上位20%会員の予約比率
  - 上位10%店舗の予約比率
- [ ] 検証結果レポート出力

**成果物**: データ検証機能
**所要時間**: 20分

---

### Task 5.2: 動作確認・テスト実行
- [ ] `python generate_data.py` 実行
- [ ] 生成時間計測
- [ ] メモリ使用量確認
- [ ] CSV出力確認（6ファイル）
- [ ] MySQL接続確認
- [ ] データ検証実行
- [ ] エラー修正（必要に応じて）

**成果物**: 動作確認済みシステム
**所要時間**: 20分

---

### Task 5.3: ドキュメント移動・完了処理
- [ ] tmp/basic_design.md → dataset/doc/basic_design.md 移動
- [ ] tmp/implementation_tasks.md → dataset/doc/implementation_tasks.md 移動
- [ ] README.md作成（実行手順）
- [ ] 最終動作確認
- [ ] 完了ログ出力

**成果物**: 完成システム + ドキュメント
**所要時間**: 5分

---

## 成果物一覧

### スクリプト・設定ファイル
- [ ] `dataset/generate_data.py` - メインスクリプト
- [ ] `dataset/config.py` - 設定ファイル
- [ ] `dataset/requirements.txt` - 依存パッケージ
- [ ] `dataset/import.sql` - CREATE TABLE文

### データファイル
- [ ] `dataset/data/members.csv` (100,000件)
- [ ] `dataset/data/restaurants.csv` (5,000件)
- [ ] `dataset/data/reservations.csv` (500,000件)
- [ ] `dataset/data/access_logs.csv` (2,000,000件)
- [ ] `dataset/data/reviews.csv` (50,000件)
- [ ] `dataset/data/favorites.csv` (150,000件)

### ドキュメント
- [ ] `dataset/doc/basic_design.md` - 基本設計書
- [ ] `dataset/doc/implementation_tasks.md` - 本タスクリスト
- [ ] `dataset/README.md` - 実行手順書

### ログ
- [ ] `dataset/logs/generate_data.log` - 実行ログ

---

## 実装順序

```
Task 1.1 → Task 1.2 → Task 1.3
    ↓
Task 2.1 → Task 2.2 → Task 2.3
    ↓
Task 3.1 → Task 3.2 → Task 3.3 → Task 3.4
    ↓
Task 4.1 → Task 4.2
    ↓
Task 5.1 → Task 5.2 → Task 5.3
```

---

## 実装方針

### コーディング規約
- PEP 8準拠
- 型ヒント使用（Python 3.8+）
- docstring記載（Google Style）

### エラーハンドリング
- try-except-finally使用
- 適切なログ出力
- 異常終了時のクリーンアップ

### パフォーマンス
- メモリ効率優先（チャンク分割）
- 進捗可視化（tqdm）
- 不要なオブジェクト削減

---

## 進捗管理

| Phase | 開始日 | 完了日 | ステータス |
|-------|--------|--------|-----------|
| Phase 1 |  |  | 未着手 |
| Phase 2 |  |  | 未着手 |
| Phase 3 |  |  | 未着手 |
| Phase 4 |  |  | 未着手 |
| Phase 5 |  |  | 未着手 |

---

## リスク・課題管理

| リスク | 発生確率 | 対策 | 担当 | ステータス |
|-------|---------|------|------|-----------|
| メモリ不足 | 中 | チャンクサイズ調整 | - | - |
| 生成時間超過 | 低 | 並列化検討 | - | - |
| MySQL接続失敗 | 中 | リトライ機構 | - | - |
| データ不整合 | 低 | 検証フェーズ必須 | - | - |

---

## 完了条件

- [x] 基本設計書承認済み
- [ ] 全15タスク完了
- [ ] データ検証合格
- [ ] MySQL正常インポート確認
- [ ] ドキュメント完備

---

**作成者**: Claude Code
**最終更新**: 2025-09-30

---

END OF DOCUMENT