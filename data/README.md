# natural2sql データセット仕様書

**レストラン予約サービス - サンプルデータセット**

## 📊 概要

このデータセットは、レストラン予約サービスのサンプルデータです。natural2sql Natural Language to SQLアプリケーションのデモンストレーション用に設計されています。

### データベース情報

| 項目 | 値 |
|------|-----|
| **形式** | SQLite 3.x |
| **ファイル名** | `restaurant.db` |
| **ファイルサイズ** | 4.6MB |
| **総レコード数** | 33,600件 |
| **テーブル数** | 6テーブル + 1システムテーブル |
| **生成日時** | 2025-10-01 |

## 🗂️ テーブル構成

### 1. members（会員マスタ）

会員の基本情報を格納するマスタテーブル。

| カラム名 | データ型 | 説明 | 例 |
|---------|---------|------|-----|
| member_id | INTEGER | 会員ID（主キー） | 1, 2, 3... |
| postal_code | TEXT | 郵便番号 | 123-4567 |
| gender | TEXT | 性別（M/F） | M, F |
| age | INTEGER | 年齢 | 25, 30, 35... |
| registration_date | TEXT | 登録日（ISO形式） | 2024-01-15T10:30:00 |

**レコード数**: 1,000件
**年齢分布**: 18-75歳（正規分布、平均35歳）
**性別比**: M:F = 1:1
**インデックス**: member_id（主キー）

### 2. restaurants（飲食店マスタ）

登録されている飲食店の基本情報。

| カラム名 | データ型 | 説明 | 例 |
|---------|---------|------|-----|
| restaurant_id | INTEGER | 店舗ID（主キー） | 1, 2, 3... |
| name | TEXT | 店舗名 | 田中寿司、ラーメン太郎 |
| genre | TEXT | ジャンル | 寿司・海鮮、ラーメン、イタリアン... |
| postal_code | TEXT | 郵便番号 | 123-4567 |
| registration_date | TEXT | 登録日（ISO形式） | 2024-01-15T10:30:00 |

**レコード数**: 200件
**ジャンル**: 寿司・海鮮、ラーメン、うどん・そば、天ぷら・とんかつ、焼き鳥・串焼き、鍋料理、粉もの、定食・食堂、懐石・料亭、イタリアン、フレンチ、ステーキ・ハンバーグ、焼肉、中華料理、韓国料理、エスニック、カフェ・喫茶店、居酒屋、バー、その他
**インデックス**: restaurant_id（主キー）

### 3. reservations（予約トランザクション）

会員の飲食店予約情報。

| カラム名 | データ型 | 説明 | 例 |
|---------|---------|------|-----|
| reservation_id | INTEGER | 予約ID（主キー） | 1, 2, 3... |
| member_id | INTEGER | 会員ID（外部キー） | 1, 2, 3... |
| restaurant_id | INTEGER | 店舗ID（外部キー） | 1, 2, 3... |
| reservation_date | TEXT | 予約日時（ISO形式） | 2024-01-15T10:30:00 |
| visit_date | TEXT | 来店日時（ISO形式、NULL可） | 2024-01-16T18:00:00 |

**レコード数**: 4,000件
**データ特性**:
- **パレート分布**: 上位20%の会員が80%の予約を占める
- **人気店舗**: 上位10%の店舗が50%の予約を占める
- **キャンセル率**: 10%（visit_date=NULL）
- **予約期間**: 過去2年間

**インデックス**:
- reservation_id（主キー）
- member_id（外部キー、インデックス）
- restaurant_id（外部キー、インデックス）

### 4. access_logs（アクセスログ）

店舗詳細ページへのアクセス履歴。

| カラム名 | データ型 | 説明 | 例 |
|---------|---------|------|-----|
| session_id | TEXT | セッションID（主キー、UUID） | 550e8400-e29b-41d4-a716-446655440000 |
| member_id | INTEGER | 会員ID（NULL可） | 1, 2, 3, NULL |
| restaurant_id | INTEGER | 店舗ID（外部キー） | 1, 2, 3... |
| access_date | TEXT | アクセス日時（ISO形式） | 2024-01-15T10:30:00 |

**レコード数**: 25,000件
**データ特性**:
- **非ログインユーザー**: 30%（member_id=NULL）
- **アクセス期間**: 過去2年間
- **セッションID**: UUID形式

**インデックス**:
- session_id（主キー）
- access_date（インデックス）

### 5. reviews（レビュー）

会員による飲食店評価。

| カラム名 | データ型 | 説明 | 例 |
|---------|---------|------|-----|
| review_id | INTEGER | レビューID（主キー） | 1, 2, 3... |
| member_id | INTEGER | 会員ID（外部キー） | 1, 2, 3... |
| restaurant_id | INTEGER | 店舗ID（外部キー） | 1, 2, 3... |
| rating | INTEGER | 評価（1-5点） | 1, 2, 3, 4, 5 |
| post_date | TEXT | 投稿日時（ISO形式） | 2024-01-15T10:30:00 |

**レコード数**: 400件
**データ特性**:
- **レビュー率**: 予約の10%がレビューに転換
- **評価分布**: 正規分布（平均4点、標準偏差1.0）
- **投稿期間**: 過去2年間

**インデックス**:
- review_id（主キー）
- restaurant_id（インデックス）

### 6. favorites（お気に入り）

会員の店舗お気に入り登録情報。

| カラム名 | データ型 | 説明 | 例 |
|---------|---------|------|-----|
| member_id | INTEGER | 会員ID（複合主キー） | 1, 2, 3... |
| restaurant_id | INTEGER | 店舗ID（複合主キー） | 1, 2, 3... |
| registration_date | TEXT | 登録日時（ISO形式） | 2024-01-15T10:30:00 |

**レコード数**: 3,000件
**データ特性**:
- **お気に入り→予約転換率**: 30%
- **登録期間**: 過去2年間

**インデックス**:
- (member_id, restaurant_id)（複合主キー）
- restaurant_id（インデックス）

### 7. query_history（クエリ履歴 - システムテーブル）

natural2sqlアプリケーションのクエリ実行履歴を保存。

| カラム名 | データ型 | 説明 |
|---------|---------|------|
| id | INTEGER | 履歴ID（主キー、自動採番） |
| input_text | TEXT | 入力された自然言語クエリ |
| generated_sql | TEXT | 生成されたSQLクエリ |
| success | INTEGER | 成功フラグ（1=成功、0=失敗） |
| error_message | TEXT | エラーメッセージ（失敗時） |
| row_count | INTEGER | 結果行数 |
| created_at | TEXT | 実行日時（デフォルト: CURRENT_TIMESTAMP） |

**レコード数**: 動的（アプリ実行時に蓄積）

## 🔗 リレーション図

```
members (1,000)
  ├─→ reservations (4,000) [member_id]
  ├─→ access_logs (25,000) [member_id]
  ├─→ reviews (400) [member_id]
  └─→ favorites (3,000) [member_id]

restaurants (200)
  ├─→ reservations (4,000) [restaurant_id]
  ├─→ access_logs (25,000) [restaurant_id]
  ├─→ reviews (400) [restaurant_id]
  └─→ favorites (3,000) [restaurant_id]
```

## 📈 データ品質

### データ生成方法

- **会員**: Fakerライブラリによるランダム生成
- **飲食店**: パターンベース命名（例: 田中寿司、ラーメン太郎）
- **予約**: パレート分布による現実的な予約偏り
- **アクセスログ**: ランダム分布
- **レビュー**: 正規分布（平均4点）
- **お気に入り**: 予約の30%が転換

### データ整合性

- ✅ **参照整合性**: 全外部キーが参照先に存在
- ✅ **NULL値**: access_logs.member_id（30%）、reservations.visit_date（10%キャンセル）
- ✅ **データ型**: numpy型バイナリ保存問題を解決済（全てPythonネイティブ型）
- ✅ **日付整合性**: 予約日 < 来店日、登録日 < 予約日

## 💡 サンプルクエリ

### 基本クエリ

```sql
-- 30代の会員数
SELECT COUNT(*) FROM members WHERE age >= 30 AND age < 40;

-- 評価4以上のイタリアンレストラン
SELECT name, genre
FROM restaurants
WHERE genre LIKE '%イタリアン%'
  AND restaurant_id IN (
    SELECT restaurant_id FROM reviews WHERE rating >= 4
  );
```

### 集計クエリ

```sql
-- 予約数TOP5店舗
SELECT r.name, COUNT(*) as reservation_count
FROM restaurants r
JOIN reservations res ON r.restaurant_id = res.restaurant_id
GROUP BY r.restaurant_id
ORDER BY reservation_count DESC
LIMIT 5;

-- 休眠会員（90日以上予約なし）
SELECT COUNT(DISTINCT m.member_id)
FROM members m
WHERE NOT EXISTS (
  SELECT 1 FROM reservations r
  WHERE r.member_id = m.member_id
    AND r.reservation_date >= date('now', '-90 days')
);
```

### WITH句（CTE）クエリ

```sql
-- 評価4以上のレストランの予約数
WITH highly_rated AS (
  SELECT restaurant_id
  FROM reviews
  WHERE rating >= 4
  GROUP BY restaurant_id
)
SELECT res.name, COUNT(*) as reservation_count
FROM reservations r
JOIN highly_rated hr ON r.restaurant_id = hr.restaurant_id
JOIN restaurants res ON r.restaurant_id = res.restaurant_id
GROUP BY res.name
ORDER BY reservation_count DESC;
```

## 🔄 データ再生成

データセットを再生成する場合は、以下のコマンドを実行してください:

```bash
cd dataset
python3 generate_data.py
```

生成されたデータベースは`/home/nao/project/natural2sql/data/restaurant.db`に保存されます。

## 📝 注意事項

- このデータセットは**デモンストレーション用**です。実在の人物・店舗とは一切関係ありません。
- データは**ランダム生成**されており、統計的に現実的な分布を模倣していますが、実データではありません。
- **参照整合性は保証**されていますが、外部キー制約は設定されていません（READ ONLYモードでの接続のため）。

## 🛠️ 技術詳細

### 生成スクリプト

- **ファイル**: `dataset/generate_data.py`
- **依存ライブラリ**: Faker, numpy, tqdm
- **生成時間**: 約0.3秒
- **乱数シード**: 固定（再現性あり）

### バグ修正履歴

- **2025-10-01**: numpy型バイナリ保存問題を修正
  - 修正前: numpy.int64がバイナリとして保存され、JOINが失敗
  - 修正後: `.tolist()`によりPythonネイティブ型に変換

---

**最終更新**: 2025-10-01
**バージョン**: 1.0.0
**生成環境**: Python 3.10+, SQLite 3.x
