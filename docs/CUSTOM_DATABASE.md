# カスタムデータベース接続ガイド

natural2sqlは、サンプルDBだけでなく、あなた自身のSQLiteやMySQLデータベースにも接続できます。

---

## Step 1: データベース接続設定

### SQLiteの場合

`.env`ファイルを編集:

```bash
DB_TYPE=sqlite
DATABASE_PATH=path/to/your_database.db
```

**例**:
```bash
DB_TYPE=sqlite
DATABASE_PATH=/home/user/mydata/sales.db
```

### MySQLの場合

`.env`ファイルを編集:

```bash
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database_name
```

**例**:
```bash
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=analyst
DB_PASSWORD=secret123
DB_NAME=sales_db
```

### 接続確認

```bash
streamlit run app.py
```

左サイドバーの「📊 スキーマ一覧を表示」ボタンをクリック。
テーブル・カラムが表示されれば接続成功です。

---

## Step 2: 論理名定義の作成（オプション）

> **⚠️ 制約事項**
>
> 現在の論理名定義は、カラム名が複数テーブルで同名の場合に意味を区別できません。
> 例: `members.id`（会員ID）と `restaurants.id`（店舗ID）は区別されません。

### 2-1. スキーマ情報を抽出

**SQLiteの場合**:

```bash
sqlite3 path/to/your_database.db ".schema"
```

**MySQLの場合**:

```bash
mysql -u your_username -p your_database_name -e "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'your_database_name' ORDER BY TABLE_NAME, ORDINAL_POSITION;"
```

### 2-2. AIで論理名CSVに変換（オプション）

参考に抽出結果を以下のプロンプトに貼り付けて、ChatGPT/Geminiなどで変換する方法を紹介します。

> **⚠️ セキュリティ注意**
>
> 機密データベースのスキーマ情報を外部の生成AIサービスに入力する際は、組織のプライバシーポリシーを確認してください。
> テーブル名・カラム名から機密情報が推測される可能性があります。
> 以下は参考情報であり、利用結果について開発者は一切の責任を負いません。

**SQLite用プロンプト**:

```
以下のSQLiteスキーマ定義から、論理名定義CSVを作成してください。
テーブル名とカラム名の両方について、業務で使われる自然な日本語名を割り当ててください。

【出力形式】
physical_name,logical_name
(テーブル名またはカラム名),(論理名)

【スキーマ定義】
(ここに ".schema" の出力をそのまま貼り付け)

```

**MySQL用プロンプト**:

```
以下のMySQLスキーマ定義から、論理名定義CSVを作成してください。
テーブル名とカラム名の両方について、業務で使われる自然な日本語名を割り当ててください。

【出力形式】
physical_name,logical_name
(テーブル名またはカラム名),(論理名)

【スキーマ定義】
(ここに INFORMATION_SCHEMA.COLUMNS の出力をそのまま貼り付け)

```

### 2-3. CSVファイルを保存

AIが生成したCSVを `config/logical_names.csv` として保存。

**例**:
```csv
physical_name,logical_name
users,ユーザーマスタ
orders,注文トランザクション
user_id,ユーザーID
order_date,注文日
```

`.env`に以下を追加:

```bash
LOGICAL_NAMES_PATH=config/logical_names.csv
```

---

## Step 3: ビジネス用語定義の作成（オプション）

業務固有の用語や略語を定義します（最大200件推奨）。

### 3-1. 用語リストを作成

業務用語とその定義をリストアップします。

### 3-2. AIでJSONLに変換

以下のプロンプトをChatGPT/Geminiに貼り付け:

```
以下の業務用語に対して、ビジネス用語定義JSONLを作成してください。

【業務用語リスト】
- 新規会員（登録から30日以内の会員）
- リピーター（過去に2回以上予約した会員）
- 人気ジャンル（予約数上位3位以内のジャンル）

【出力形式】
{"term": "新規会員", "definition": "登録から30日以内の会員"}
{"term": "リピーター", "definition": "過去に2回以上予約した会員"}
{"term": "人気ジャンル", "definition": "予約数上位3位以内のジャンル"}
```

### 3-3. JSONLファイルを保存

AIが生成したJSONLを `config/business_terms.jsonl` として保存。

**例**:
```jsonl
{"term": "新規会員", "definition": "登録から30日以内の会員"}
{"term": "リピーター", "definition": "過去に2回以上予約した会員"}
{"term": "人気ジャンル", "definition": "予約数上位3位以内のジャンル"}
```

`.env`に以下を追加:

```bash
BUSINESS_TERMS_PATH=config/business_terms.jsonl
```

---

## Step 4: 動作確認

### 起動

```bash
streamlit run app.py
```

### 確認項目

1. **DB接続**: 左サイドバーに「接続中: SQLite (`your_database.db`)」または「接続中: MySQL (`your_database_name`)」が表示される
2. **スキーマ表示**: 「📊 スキーマ一覧を表示」で論理名が表示される
3. **クエリ実行**: 自然言語でクエリを入力し、正しく結果が返る

### トラブルシューティング

**エラー: "❌ DB接続失敗"**
- SQLite: `DATABASE_PATH`が正しいか確認
- MySQL: ホスト・ポート・ユーザー・パスワード・DB名を確認

**エラー: "⚠️ 論理名定義読み込み失敗"**
- CSVの形式を確認（ヘッダー: `physical_name,logical_name`）
- ファイルパスが正しいか確認
- 文字エンコーディングがUTF-8か確認

**エラー: "⚠️ ビジネス用語定義読み込み失敗"**
- JSONLの形式を確認（各行が`{"term": "...", "definition": "..."}`）
- ファイルパスが正しいか確認
- 200件以下に制限（推奨）

---

## セキュリティ保護

natural2sqlは5層のセキュリティ防御を実装しています:

1. **禁止パターン検出**: `DROP`, `DELETE`, `UPDATE`, `INSERT`などの破壊的操作を拒否
2. **READ ONLYモード**: 読み取り専用接続（SQLiteのみ）
3. **LIMIT注入**: 全クエリに`LIMIT 1000`を自動付与（大量データ取得防止）
4. **タイムアウト設定**: SQLite 30秒、MySQL 10秒（接続タイムアウト）
5. **禁止ワードチェック**: ビジネス用語定義に基づく追加制約

これにより、AIが生成したSQLでもデータ破壊のリスクを最小化します。

---

何かあれば、[GitHubリポジトリ](https://github.com/yo2158/natural2sql)のIssuesでご連絡ください。
