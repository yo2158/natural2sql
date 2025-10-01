# 飲食店予約サイト テストデータ生成システム 基本設計書

**Version**: 1.0
**Date**: 2025-09-30
**Project**: Text-to-SQL Demo Dataset Generator

---

## 1. システム概要

### 1.1 目的
Text-to-SQLツールのデモンストレーション用に、飲食店予約サイトを模した実務的なテストデータセットを生成する。

### 1.2 成果物
- CSV形式のテストデータ（6テーブル、合計約280万件）
- MySQLデータベースへのインポート完了状態

---

## 2. アーキテクチャ設計

### 2.1 システム構成

```
┌─────────────────────────────────────┐
│   generate_data.py (Main Script)    │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐  │
│  │ DataGenerator クラス          │  │
│  ├───────────────────────────────┤  │
│  │ - MasterDataGenerator         │  │
│  │   • members                   │  │
│  │   • restaurants               │  │
│  │ - TransactionDataGenerator    │  │
│  │   • reservations              │  │
│  │   • access_logs               │  │
│  │   • reviews                   │  │
│  │   • favorites                 │  │
│  │ - MySQLImporter               │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
           ↓
    ┌─────────────┐
    │ CSV Files   │ (data/)
    └─────────────┘
           ↓
    ┌─────────────┐
    │ MySQL DB    │ (sandbox)
    └─────────────┘
```

### 2.2 技術スタック

| レイヤー | 技術 | 用途 |
|---------|------|------|
| データ生成 | Faker (ja_JP) | 日本語疑似データ生成 |
| データ処理 | pandas | DataFrame操作・CSV出力 |
| 確率分布 | numpy | パレート分布実装 |
| DB接続 | mysql-connector-python | MySQLインポート |
| 進捗表示 | tqdm | プログレスバー |
| ログ | logging | 実行ログ出力 |

---

## 3. データモデル設計

### 3.1 テーブル関連図

```
┌───────────────┐
│   members     │
│ (会員マスタ)  │
└───────┬───────┘
        │
        │ 1
        │
        │ *
    ┌───┴──────────────────────────┐
    │                              │
┌───▼────────┐              ┌──────▼──────┐
│ reservations│              │  reviews    │
│ (予約データ)│              │ (レビュー)  │
└───┬────────┘              └──────┬──────┘
    │                              │
    │ *                            │ *
    │                              │
    │ 1                            │ 1
┌───▼──────────┐            ┌──────▼──────┐
│ restaurants  │◄───────────┤ access_logs │
│ (店舗マスタ) │            │(アクセスログ)│
└──────┬───────┘            └─────────────┘
       │
       │ 1
       │
       │ *
   ┌───▼──────┐
   │ favorites│
   │(お気に入り)│
   └──────────┘
```

### 3.2 テーブル定義

#### 3.2.1 members（会員マスタ）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| member_id | INT | PK, AUTO_INCREMENT | 会員ID（1から連番） |
| postal_code | VARCHAR(8) | NOT NULL | 郵便番号（xxx-xxxx形式） |
| gender | CHAR(1) | NOT NULL | 性別（M/F） |
| age | INT | NOT NULL | 年齢（18-80） |
| registration_date | DATETIME | NOT NULL | 登録日時（過去10年以内） |

**INDEX**: `idx_registration_date`, `idx_age`

---

#### 3.2.2 restaurants（飲食店マスタ）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| restaurant_id | INT | PK, AUTO_INCREMENT | 店舗ID（1から連番） |
| name | VARCHAR(50) | NOT NULL | 店名（日本語） |
| genre | VARCHAR(20) | NOT NULL | ジャンル（18種類） |
| postal_code | VARCHAR(8) | NOT NULL | 郵便番号 |
| registration_date | DATETIME | NOT NULL | 登録日時（過去10年～1年前） |

**ジャンル一覧**:
```
寿司・海鮮, ラーメン, うどん・そば, 天ぷら・とんかつ, 焼き鳥・串焼き,
鍋料理, 粉もの, 定食・食堂, 懐石・料亭, イタリアン, フレンチ,
ステーキ・ハンバーグ, その他洋食, 中華料理, アジア・エスニック,
カレー, 居酒屋・バー, カフェ・スイーツ
```

**INDEX**: `idx_genre`, `idx_registration_date`

---

#### 3.2.3 reservations（予約データ）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| reservation_id | INT | PK, AUTO_INCREMENT | 予約ID（1から連番） |
| member_id | INT | FK → members, NOT NULL | 会員ID |
| restaurant_id | INT | FK → restaurants, NOT NULL | 店舗ID |
| reservation_date | DATETIME | NOT NULL | 予約作成日時（過去10年以内） |
| visit_date | DATETIME | NULL | 来店予定日時（NULL=キャンセル） |

**制約**: `visit_date >= reservation_date` (NULL除く)

**INDEX**: `idx_member_id`, `idx_restaurant_id`, `idx_reservation_date`

---

#### 3.2.4 access_logs（アクセスログ）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| session_id | VARCHAR(36) | PK | セッションID（UUID v4形式） |
| member_id | INT | FK → members, NULL | 会員ID（非ログイン=NULL） |
| restaurant_id | INT | FK → restaurants, NOT NULL | 店舗ID |
| access_date | DATETIME | NOT NULL | アクセス日時（過去6ヶ月以内） |

**INDEX**: `idx_member_id`, `idx_restaurant_id`, `idx_access_date`

---

#### 3.2.5 reviews（レビューデータ）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| review_id | INT | PK, AUTO_INCREMENT | レビューID（1から連番） |
| member_id | INT | FK → members, NOT NULL | 会員ID |
| restaurant_id | INT | FK → restaurants, NOT NULL | 店舗ID |
| rating | INT | NOT NULL, CHECK (1 <= rating <= 5) | 評価（1-5） |
| post_date | DATETIME | NOT NULL | 投稿日時（過去5年以内） |

**INDEX**: `idx_member_id`, `idx_restaurant_id`, `idx_rating`

---

#### 3.2.6 favorites（お気に入り登録）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| member_id | INT | FK → members, PK | 会員ID |
| restaurant_id | INT | FK → restaurants, PK | 店舗ID |
| registration_date | DATETIME | NOT NULL | 登録日時（過去5年以内） |

**PRIMARY KEY**: `(member_id, restaurant_id)`

---

## 4. データ生成ロジック設計

### 4.1 生成順序

```
Phase 1: マスタデータ生成
  1. members (100,000件)
  2. restaurants (5,000件)

Phase 2: トランザクションデータ生成
  3. reservations (500,000件) ※パレート分布適用
  4. access_logs (2,000,000件) ※最大ボトルネック
  5. reviews (50,000件) ※予約の10%から生成
  6. favorites (150,000件) ※30%が予約に繋がる設計
```

### 4.2 パレート法則実装

#### 4.2.1 会員の予約分布（20/80ルール）

```python
# 上位20%の会員が80%の予約を占める
top_20_percent_members = member_ids[:20000]  # 100,000 * 0.2
other_members = member_ids[20000:]

# 予約500,000件の配分
high_activity_reservations = 400000  # 80%
low_activity_reservations = 100000   # 20%

# 重み付け抽選
weights_high = [8] * len(top_20_percent_members)  # 高頻度会員
weights_low = [1] * len(other_members)             # 低頻度会員
```

#### 4.2.2 店舗の予約分布（10/50ルール）

```python
# 上位10%の店舗に50%の予約が集中
popular_restaurants = restaurant_ids[:500]  # 5,000 * 0.1
other_restaurants = restaurant_ids[500:]

# 予約500,000件の配分
popular_reservations = 250000   # 50%
regular_reservations = 250000   # 50%

# 重み付け抽選
weights_popular = [50] * len(popular_restaurants)
weights_regular = [1] * len(other_restaurants)
```

#### 4.2.3 レビュー投稿率（10%）

```python
# 予約の10%がレビューに転換
# reservationsテーブルから50,000件をランダムサンプリング
reviewed_reservations = random.sample(reservations, 50000)
```

#### 4.2.4 お気に入り→予約転換（30%）

```python
# favorites 150,000件のうち30%（45,000件）が予約に繋がる
# ※ reservationsテーブル生成時に45,000件分をfavoritesから選択
favorite_based_reservations = 45000
```

### 4.3 メモリ最適化戦略

#### チャンク分割生成

```python
CHUNK_SIZE = 100000  # 10万件単位

# access_logs (200万件) の場合
for chunk_num in range(20):
    chunk_data = generate_access_logs_chunk(CHUNK_SIZE)
    chunk_data.to_csv('data/access_logs.csv', mode='a', header=(chunk_num==0))
    del chunk_data  # 明示的なメモリ解放
```

---

## 5. 処理フロー設計

### 5.1 メイン処理フロー

```
START
  │
  ├─ ログ初期化
  ├─ 出力ディレクトリ作成 (data/)
  │
  ├─ [Phase 1] マスタデータ生成
  │   ├─ members生成 (100,000件)
  │   └─ restaurants生成 (5,000件)
  │
  ├─ [Phase 2] トランザクションデータ生成
  │   ├─ reservations生成 (500,000件) ※パレート適用
  │   ├─ access_logs生成 (2,000,000件) ※チャンク分割
  │   ├─ reviews生成 (50,000件)
  │   └─ favorites生成 (150,000件)
  │
  ├─ [Phase 3] データ検証
  │   ├─ 外部キー整合性チェック
  │   ├─ 日付論理性チェック
  │   └─ 件数確認
  │
  ├─ [Phase 4] MySQLインポート
  │   ├─ データベース接続
  │   ├─ CREATE TABLE実行
  │   ├─ LOAD DATA INFILE (CSV→MySQL)
  │   └─ INDEX作成
  │
  └─ 終了ログ出力
END
```

### 5.2 エラーハンドリング

| エラー種別 | 検出箇所 | 対応 |
|-----------|---------|------|
| メモリ不足 | データ生成中 | チャンクサイズ縮小・警告ログ |
| 外部キー違反 | 検証フェーズ | エラーログ出力・処理中断 |
| MySQL接続失敗 | インポート開始時 | リトライ3回・失敗時中断 |
| CSV書き込み失敗 | ファイル出力時 | 例外スロー・処理中断 |

---

## 6. 出力仕様

### 6.1 CSVファイル仕様

- **文字コード**: UTF-8 (BOM無し)
- **改行コード**: LF
- **区切り文字**: カンマ
- **囲み文字**: ダブルクォート（必要時のみ）
- **ヘッダー**: 有り（1行目）
- **NULL表現**: 空文字列

### 6.2 ファイル出力先

```
data/
├── members.csv          (~10 MB)
├── restaurants.csv      (~500 KB)
├── reservations.csv     (~50 MB)
├── access_logs.csv      (~200 MB) ← 最大
├── reviews.csv          (~5 MB)
└── favorites.csv        (~15 MB)
```

### 6.3 ログ出力仕様

**ファイル**: `logs/generate_data.log`

**フォーマット**:
```
[2025-09-30 10:00:00] INFO - データ生成開始
[2025-09-30 10:02:15] INFO - members: 100,000件生成完了 (2.5分)
[2025-09-30 10:03:30] INFO - restaurants: 5,000件生成完了 (1.2分)
...
[2025-09-30 10:20:00] INFO - 全データ生成完了 (20分)
[2025-09-30 10:25:00] INFO - MySQLインポート完了
```

---

## 7. 性能要件

| 項目 | 目標値 | 許容値 |
|------|--------|--------|
| 総生成時間 | 15分以内 | 30分以内 |
| メモリ使用量 | 50MB以下 | 200MB以下 |
| CSV出力サイズ | 280MB | 350MB |
| MySQLインポート時間 | 5分以内 | 10分以内 |

---

## 8. 環境設定

### 8.1 依存パッケージ

**requirements.txt**:
```
faker==22.0.0
pandas==2.1.4
numpy==1.26.2
mysql-connector-python==8.2.0
tqdm==4.66.1
```

### 8.2 MySQL設定

```sql
-- データベース: sandbox
-- 接続情報
HOST: localhost
PORT: 3306
USER: sandbox
PASSWORD: sandboxpass
DATABASE: sandbox

-- 必要権限
GRANT SELECT, INSERT, CREATE, DROP, INDEX ON sandbox.* TO 'sandbox'@'localhost';
```

### 8.3 CREATE TABLE SQL

```sql
CREATE TABLE members (
    member_id INT PRIMARY KEY AUTO_INCREMENT,
    postal_code VARCHAR(8) NOT NULL,
    gender CHAR(1) NOT NULL,
    age INT NOT NULL,
    registration_date DATETIME NOT NULL,
    INDEX idx_registration_date (registration_date),
    INDEX idx_age (age)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurants (
    restaurant_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    genre VARCHAR(20) NOT NULL,
    postal_code VARCHAR(8) NOT NULL,
    registration_date DATETIME NOT NULL,
    INDEX idx_genre (genre),
    INDEX idx_registration_date (registration_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE reservations (
    reservation_id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    reservation_date DATETIME NOT NULL,
    visit_date DATETIME,
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id),
    INDEX idx_member_id (member_id),
    INDEX idx_restaurant_id (restaurant_id),
    INDEX idx_reservation_date (reservation_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE access_logs (
    session_id VARCHAR(36) PRIMARY KEY,
    member_id INT,
    restaurant_id INT NOT NULL,
    access_date DATETIME NOT NULL,
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id),
    INDEX idx_member_id (member_id),
    INDEX idx_restaurant_id (restaurant_id),
    INDEX idx_access_date (access_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE reviews (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    post_date DATETIME NOT NULL,
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id),
    INDEX idx_member_id (member_id),
    INDEX idx_restaurant_id (restaurant_id),
    INDEX idx_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE favorites (
    member_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    registration_date DATETIME NOT NULL,
    PRIMARY KEY (member_id, restaurant_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 9. テスト計画

### 9.1 単体テスト

| テスト項目 | 検証内容 | 合格基準 |
|-----------|---------|---------|
| データ件数 | 各テーブルの生成件数 | 仕様通りの件数 |
| データ型 | 各カラムの型・形式 | スキーマ準拠 |
| NULL制約 | NOT NULL制約 | 違反なし |
| 範囲制約 | age, rating等の範囲 | 仕様範囲内 |
| 日付形式 | DATETIME形式 | MySQL互換 |

### 9.2 統合テスト

| テスト項目 | 検証内容 | 合格基準 |
|-----------|---------|---------|
| 外部キー整合性 | FK参照先の存在確認 | 全件存在 |
| 日付論理性 | reservation_date <= visit_date | 違反なし |
| パレート分布 | 予約の偏り確認 | 20/80, 10/50達成 |
| CSV読み込み | MySQLへのインポート | エラーなし |

### 9.3 検証SQL

```sql
-- 件数確認
SELECT 'members' AS table_name, COUNT(*) FROM members
UNION ALL
SELECT 'restaurants', COUNT(*) FROM restaurants
UNION ALL
SELECT 'reservations', COUNT(*) FROM reservations
UNION ALL
SELECT 'access_logs', COUNT(*) FROM access_logs
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'favorites', COUNT(*) FROM favorites;

-- 外部キー整合性
SELECT COUNT(*) FROM reservations r
LEFT JOIN members m ON r.member_id = m.member_id
WHERE m.member_id IS NULL;  -- 0であること

-- パレート分布確認（上位20%会員の予約比率）
SELECT
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reservations) AS percentage
FROM reservations
WHERE member_id IN (
    SELECT member_id FROM (
        SELECT member_id, COUNT(*) AS cnt
        FROM reservations
        GROUP BY member_id
        ORDER BY cnt DESC
        LIMIT 20000
    ) AS top_members
);  -- 約80%であること
```

---

## 10. 運用・保守

### 10.1 再生成手順

```bash
# 1. 既存データ削除
rm -rf data/*.csv logs/*.log

# 2. データ生成実行
python generate_data.py

# 3. MySQLインポート（スクリプト内で自動実行）
# または手動実行:
# mysql -u sandbox -p sandbox < import.sql
```

### 10.2 データ量変更時の調整

**config.py** (設定ファイル化推奨):
```python
DATA_VOLUME = {
    'members': 100000,
    'restaurants': 5000,
    'reservations': 500000,
    'access_logs': 2000000,
    'reviews': 50000,
    'favorites': 150000
}

CHUNK_SIZE = 100000  # チャンクサイズ
PARETO_RATIOS = {
    'member_active_ratio': 0.2,  # 上位20%
    'member_reservation_ratio': 0.8,  # 予約80%
    'restaurant_popular_ratio': 0.1,  # 上位10%
    'restaurant_reservation_ratio': 0.5  # 予約50%
}
```

---

## 11. リスク管理

| リスク | 影響度 | 対策 |
|-------|-------|------|
| メモリ不足 | 中 | チャンク分割・進捗監視 |
| 生成時間超過 | 低 | Faker事前生成・並列化検討 |
| MySQL接続失敗 | 中 | リトライ機構・接続確認 |
| データ不整合 | 高 | 検証フェーズ必須実行 |

---

## 12. 今後の拡張性

### 12.1 将来的な拡張候補

- [ ] ジャンル別予約傾向の実装（ラーメン→若年層多など）
- [ ] 季節性の考慮（予約数の季節変動）
- [ ] 地域別分布（郵便番号の地域偏り）
- [ ] 複数回予約の考慮（リピーター分析）

### 12.2 Text-to-SQL連携

生成データは以下のクエリパターンに対応:

```sql
-- 例1: 人気店ランキング
SELECT r.name, COUNT(*) AS reservation_count
FROM reservations res
JOIN restaurants r ON res.restaurant_id = r.restaurant_id
GROUP BY r.restaurant_id
ORDER BY reservation_count DESC
LIMIT 10;

-- 例2: 年齢層別のジャンル傾向
SELECT m.age, r.genre, COUNT(*) AS cnt
FROM reservations res
JOIN members m ON res.member_id = m.member_id
JOIN restaurants r ON res.restaurant_id = r.restaurant_id
GROUP BY m.age, r.genre;

-- 例3: お気に入り→予約転換率
SELECT
    COUNT(DISTINCT f.member_id) AS favorite_users,
    COUNT(DISTINCT res.member_id) AS reserved_users,
    COUNT(DISTINCT res.member_id) * 100.0 / COUNT(DISTINCT f.member_id) AS conversion_rate
FROM favorites f
LEFT JOIN reservations res ON f.member_id = res.member_id AND f.restaurant_id = res.restaurant_id;
```

---

## 付録A: ディレクトリ構成

```
txt2sql/
├── dataset/
│   ├── generate_data.py      # メインスクリプト
│   ├── config.py              # 設定ファイル
│   ├── requirements.txt       # 依存パッケージ
│   ├── import.sql             # CREATE TABLE文
│   ├── doc/                   # ドキュメント
│   │   └── basic_design.md   # 本設計書（最終配置先）
│   ├── data/                  # CSV出力先
│   │   ├── members.csv
│   │   ├── restaurants.csv
│   │   ├── reservations.csv
│   │   ├── access_logs.csv
│   │   ├── reviews.csv
│   │   └── favorites.csv
│   └── logs/                  # ログ出力先
│       └── generate_data.log
```

**注記**: 本設計書は実装完了後に `dataset/doc/basic_design.md` に配置されます。

---

## 付録B: 用語集

| 用語 | 説明 |
|------|------|
| パレート法則 | 80/20の法則。上位20%が全体の80%を占める分布 |
| チャンク分割 | 大量データを小分割して処理する手法 |
| Text-to-SQL | 自然言語の質問をSQLクエリに自動変換する技術 |
| Faker | テストデータ生成ライブラリ |
| LOAD DATA INFILE | MySQLの高速CSVインポート機能 |

---

**承認欄**

| 役割 | 氏名 | 承認日 | サイン |
|------|------|--------|--------|
| 設計者 | Claude Code |  |  |
| 承認者 |  |  |  |

---

**変更履歴**

| Version | 日付 | 変更者 | 変更内容 |
|---------|------|--------|---------|
| 1.0 | 2025-09-30 | Claude Code | 初版作成 |

---

END OF DOCUMENT