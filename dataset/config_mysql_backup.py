"""
テストデータ生成システム 設定ファイル
"""

# データ量設定
DATA_VOLUME = {
    'members': 100000,
    'restaurants': 5000,
    'reservations': 500000,
    'access_logs': 2000000,
    'reviews': 50000,
    'favorites': 150000
}

# チャンク分割サイズ（大量データ生成時のメモリ最適化）
CHUNK_SIZE = 100000

# パレート法則の比率設定
PARETO_RATIOS = {
    'member_active_ratio': 0.2,           # 上位アクティブ会員の割合（20%）
    'member_reservation_ratio': 0.8,      # 上位会員が占める予約の割合（80%）
    'restaurant_popular_ratio': 0.1,      # 人気店舗の割合（10%）
    'restaurant_reservation_ratio': 0.5,  # 人気店が占める予約の割合（50%）
    'review_rate': 0.1,                   # 予約からレビュー投稿への転換率（10%）
    'favorite_to_reservation_rate': 0.3   # お気に入りから予約への転換率（30%）
}

# MySQL接続情報
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'sandbox',
    'password': 'sandboxpass',
    'database': 'sandbox'
}

# レストランジャンルリスト
RESTAURANT_GENRES = [
    '寿司・海鮮',
    'ラーメン',
    'うどん・そば',
    '天ぷら・とんかつ',
    '焼き鳥・串焼き',
    '鍋料理',
    '粉もの',
    '定食・食堂',
    '懐石・料亭',
    'イタリアン',
    'フレンチ',
    'ステーキ・ハンバーグ',
    'その他洋食',
    '中華料理',
    'アジア・エスニック',
    'カレー',
    '居酒屋・バー',
    'カフェ・スイーツ'
]

# 日付範囲設定
DATE_RANGES = {
    'members_registration_years': 10,      # 会員登録: 過去10年以内
    'restaurants_registration_years': 10,  # 店舗登録: 過去10年以内
    'restaurants_min_years_ago': 1,        # 店舗登録: 最低1年前
    'reservations_years': 10,              # 予約データ: 過去10年以内
    'access_logs_months': 6,               # アクセスログ: 過去6ヶ月以内
    'reviews_years': 5,                    # レビュー: 過去5年以内
    'favorites_years': 5                   # お気に入り: 過去5年以内
}

# 年齢・評価の分布設定
DISTRIBUTION_CONFIG = {
    'age_min': 18,
    'age_max': 80,
    'age_mean': 40,
    'age_std': 15,
    'rating_min': 1,
    'rating_max': 5,
    'rating_mean': 3.5,
    'rating_std': 0.8
}

# キャンセル率（visit_dateがNULLになる割合）
CANCELLATION_RATE = 0.1

# 非ログインアクセス率（access_logsのmember_idがNULLになる割合）
NON_LOGIN_ACCESS_RATE = 0.3

# 出力設定
OUTPUT_CONFIG = {
    'data_dir': 'data',
    'log_dir': 'logs',
    'log_file': 'generate_data.log',
    'csv_encoding': 'utf-8',
    'csv_index': False  # CSVにインデックス列を含めない
}

# ログレベル
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL