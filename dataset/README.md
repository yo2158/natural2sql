# テストデータ生成システム

Text-to-SQLツールのデモ用テストデータ生成システム

## 概要

飲食店予約サイトを模した実務的なテストデータ（約280万件）を生成し、MySQLにインポートします。

### データセット構成

| テーブル | 件数 | 説明 |
|---------|------|------|
| members | 100,000 | 会員マスタ |
| restaurants | 5,000 | 飲食店マスタ |
| reservations | 500,000 | 予約データ |
| access_logs | 2,000,000 | アクセスログ |
| reviews | 50,000 | レビューデータ |
| favorites | 150,000 | お気に入り登録 |

### 特徴

- **パレート分布**: 会員20%が予約80%、店舗10%に予約50%集中
- **リアルな分布**: レビュー投稿率10%、お気に入り→予約転換30%
- **メモリ最適化**: チャンク分割による大量データ生成
- **日本語対応**: Faker (ja_JP) による日本語テストデータ

---

## セットアップ

### 1. 依存パッケージインストール

```bash
cd dataset
pip install -r requirements.txt
```

### 2. MySQL設定

`config.py` でMySQL接続情報を確認・変更してください。

```python
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'sandbox',
    'password': 'sandboxpass',
    'database': 'sandbox'
}
```

**必要な権限**:
```sql
GRANT SELECT, INSERT, CREATE, DROP, INDEX ON sandbox.* TO 'sandbox'@'localhost';
```

---

## 実行方法

### 基本実行

```bash
cd dataset
python generate_data.py
```

### 実行時間

- データ生成: 約10-20分
- MySQLインポート: 約5-10分
- **合計**: 約15-30分

### 出力先

- **CSVファイル**: `dataset/data/`
- **ログファイル**: `dataset/logs/generate_data.log`

---

## 生成データの確認

### 件数確認

```sql
SELECT 'members' AS table_name, COUNT(*) AS count FROM members
UNION ALL SELECT 'restaurants', COUNT(*) FROM restaurants
UNION ALL SELECT 'reservations', COUNT(*) FROM reservations
UNION ALL SELECT 'access_logs', COUNT(*) FROM access_logs
UNION ALL SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL SELECT 'favorites', COUNT(*) FROM favorites;
```

### パレート分布確認

**会員の予約分布（上位20%が80%を占めるか）**:

```sql
SELECT
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reservations) AS top_20_percent_ratio
FROM reservations
WHERE member_id IN (
    SELECT member_id FROM (
        SELECT member_id, COUNT(*) AS cnt
        FROM reservations
        GROUP BY member_id
        ORDER BY cnt DESC
        LIMIT 20000
    ) AS top_members
);
-- 期待値: 約80%
```

**店舗の予約分布（上位10%が50%を占めるか）**:

```sql
SELECT
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reservations) AS top_10_percent_ratio
FROM reservations
WHERE restaurant_id IN (
    SELECT restaurant_id FROM (
        SELECT restaurant_id, COUNT(*) AS cnt
        FROM reservations
        GROUP BY restaurant_id
        ORDER BY cnt DESC
        LIMIT 500
    ) AS popular_restaurants
);
-- 期待値: 約50%
```

---

## データ量調整

`config.py` の `DATA_VOLUME` を編集してください。

```python
DATA_VOLUME = {
    'members': 100000,
    'restaurants': 5000,
    'reservations': 500000,
    'access_logs': 2000000,
    'reviews': 50000,
    'favorites': 150000
}
```

---

## トラブルシューティング

### メモリ不足エラー

`config.py` の `CHUNK_SIZE` を小さくしてください。

```python
CHUNK_SIZE = 50000  # デフォルト: 100000
```

### MySQL接続エラー

1. MySQL接続情報を確認
2. データベース `sandbox` が存在するか確認
3. ユーザー権限を確認

```bash
mysql -u sandbox -p -e "SHOW GRANTS;"
```

### LOAD DATA INFILE エラー

スクリプトは自動的にfallback処理（INSERT文使用）に切り替わります。
ログを確認してください: `logs/generate_data.log`

---

## ディレクトリ構成

```
dataset/
├── generate_data.py        # メインスクリプト
├── config.py                # 設定ファイル
├── requirements.txt         # 依存パッケージ
├── import.sql               # CREATE TABLE文
├── README.md                # 本ファイル
├── doc/                     # ドキュメント
│   ├── basic_design.md      # 基本設計書
│   └── implementation_tasks.md  # タスクリスト
├── data/                    # CSV出力先（自動生成）
│   ├── members.csv
│   ├── restaurants.csv
│   ├── reservations.csv
│   ├── access_logs.csv
│   ├── reviews.csv
│   └── favorites.csv
└── logs/                    # ログ出力先（自動生成）
    └── generate_data.log
```

---

## Text-to-SQL クエリ例

生成したデータで以下のようなクエリを試せます:

### 人気店ランキング

```sql
SELECT r.name, COUNT(*) AS reservation_count
FROM reservations res
JOIN restaurants r ON res.restaurant_id = r.restaurant_id
GROUP BY r.restaurant_id
ORDER BY reservation_count DESC
LIMIT 10;
```

### 年齢層別のジャンル傾向

```sql
SELECT
    CASE
        WHEN m.age < 30 THEN '20代以下'
        WHEN m.age < 40 THEN '30代'
        WHEN m.age < 50 THEN '40代'
        ELSE '50代以上'
    END AS age_group,
    r.genre,
    COUNT(*) AS cnt
FROM reservations res
JOIN members m ON res.member_id = m.member_id
JOIN restaurants r ON res.restaurant_id = r.restaurant_id
GROUP BY age_group, r.genre
ORDER BY age_group, cnt DESC;
```

### お気に入り→予約転換率

```sql
SELECT
    COUNT(DISTINCT f.member_id) AS favorite_users,
    COUNT(DISTINCT res.member_id) AS reserved_users,
    COUNT(DISTINCT res.member_id) * 100.0 / COUNT(DISTINCT f.member_id) AS conversion_rate
FROM favorites f
LEFT JOIN reservations res
    ON f.member_id = res.member_id
    AND f.restaurant_id = res.restaurant_id;
```

---

## ライセンス

MIT License

---

## 作成者

Claude Code

---

## 関連ドキュメント

- [基本設計書](doc/basic_design.md)
- [実装タスクリスト](doc/implementation_tasks.md)