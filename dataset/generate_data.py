#!/usr/bin/env python3
"""
テストデータ生成スクリプト - Text-to-SQL Demo Dataset Generator

飲食店予約サイトを模したテストデータを生成します。
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Tuple
import uuid
import random

import pandas as pd
import numpy as np
from faker import Faker
from tqdm import tqdm
import mysql.connector
from mysql.connector import Error

import config


class DataGenerator:
    """データ生成メインクラス"""

    def __init__(self):
        """初期化処理"""
        self.faker = Faker('ja_JP')
        Faker.seed(42)  # 再現性のためのシード固定
        np.random.seed(42)
        random.seed(42)

        self._setup_logging()
        self._create_directories()

        # 生成済みデータの保持（外部キー参照用）
        self.member_ids: List[int] = []
        self.restaurant_ids: List[int] = []
        self.reservations: List[Tuple[int, int, int]] = []  # (reservation_id, member_id, restaurant_id)

        self.logger.info("データ生成システム初期化完了")

    def _setup_logging(self):
        """ログ設定"""
        log_dir = config.OUTPUT_CONFIG['log_dir']
        log_file = os.path.join(log_dir, config.OUTPUT_CONFIG['log_file'])

        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='[%(asctime)s] %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _create_directories(self):
        """出力ディレクトリ作成"""
        os.makedirs(config.OUTPUT_CONFIG['data_dir'], exist_ok=True)
        os.makedirs(config.OUTPUT_CONFIG['log_dir'], exist_ok=True)

    def _get_output_path(self, filename: str) -> str:
        """CSV出力パス取得"""
        return os.path.join(config.OUTPUT_CONFIG['data_dir'], filename)

    def generate_members(self) -> pd.DataFrame:
        """
        会員マスタ生成

        Returns:
            members DataFrame
        """
        self.logger.info(f"会員データ生成開始: {config.DATA_VOLUME['members']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['members']

        # member_id（連番）
        member_ids = list(range(1, count + 1))

        # postal_code（日本の郵便番号形式）
        postal_codes = [self.faker.postcode() for _ in tqdm(range(count), desc="郵便番号生成")]

        # gender（M/F）
        genders = np.random.choice(['M', 'F'], size=count)

        # age（18-80、正規分布）
        ages = np.random.normal(
            config.DISTRIBUTION_CONFIG['age_mean'],
            config.DISTRIBUTION_CONFIG['age_std'],
            count
        )
        ages = np.clip(ages, config.DISTRIBUTION_CONFIG['age_min'], config.DISTRIBUTION_CONFIG['age_max'])
        ages = ages.astype(int)

        # registration_date（過去10年以内）
        now = datetime.now()
        years_ago = config.DATE_RANGES['members_registration_years']
        start_date = now - timedelta(days=years_ago * 365)

        registration_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=now)
            for _ in tqdm(range(count), desc="登録日生成")
        ]

        df = pd.DataFrame({
            'member_id': member_ids,
            'postal_code': postal_codes,
            'gender': genders,
            'age': ages,
            'registration_date': registration_dates
        })

        # CSV出力
        output_path = self._get_output_path('members.csv')
        df.to_csv(output_path, index=config.OUTPUT_CONFIG['csv_index'], encoding=config.OUTPUT_CONFIG['csv_encoding'])

        # member_ids保存（後続処理で使用）
        self.member_ids = member_ids

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"会員データ生成完了: {len(df)}件 ({elapsed:.2f}秒)")

        return df

    def generate_restaurants(self) -> pd.DataFrame:
        """
        飲食店マスタ生成

        Returns:
            restaurants DataFrame
        """
        self.logger.info(f"飲食店データ生成開始: {config.DATA_VOLUME['restaurants']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['restaurants']

        # restaurant_id（連番）
        restaurant_ids = list(range(1, count + 1))

        # name（店名）- 飲食店らしい名前生成
        def generate_restaurant_name():
            patterns = [
                lambda: f"{self.faker.last_name()}{random.choice(['亭', '屋', '家', '処', '庵'])}",  # 45%
                lambda: f"{random.choice(['居酒屋', 'レストラン', 'カフェ', 'ダイニング', 'バル'])}{self.faker.last_name()}",  # 35%
                lambda: f"{self.faker.last_name()}{random.choice(['台所', '食卓', 'キッチン', '厨房'])}",  # 20%
            ]
            pattern = random.choices(patterns, weights=[45, 35, 20])[0]
            return pattern()

        names = [generate_restaurant_name() for _ in tqdm(range(count), desc="店名生成")]

        # genre（ジャンル）
        genres = np.random.choice(config.RESTAURANT_GENRES, size=count)

        # postal_code
        postal_codes = [self.faker.postcode() for _ in tqdm(range(count), desc="郵便番号生成")]

        # registration_date（過去10年～1年前）
        now = datetime.now()
        years_ago = config.DATE_RANGES['restaurants_registration_years']
        min_years_ago = config.DATE_RANGES['restaurants_min_years_ago']
        start_date = now - timedelta(days=years_ago * 365)
        end_date = now - timedelta(days=min_years_ago * 365)

        registration_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=end_date)
            for _ in tqdm(range(count), desc="登録日生成")
        ]

        df = pd.DataFrame({
            'restaurant_id': restaurant_ids,
            'name': names,
            'genre': genres,
            'postal_code': postal_codes,
            'registration_date': registration_dates
        })

        # CSV出力
        output_path = self._get_output_path('restaurants.csv')
        df.to_csv(output_path, index=config.OUTPUT_CONFIG['csv_index'], encoding=config.OUTPUT_CONFIG['csv_encoding'])

        # restaurant_ids保存
        self.restaurant_ids = restaurant_ids

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"飲食店データ生成完了: {len(df)}件 ({elapsed:.2f}秒)")

        return df

    def generate_reservations(self) -> pd.DataFrame:
        """
        予約データ生成（パレート分布適用）

        Returns:
            reservations DataFrame
        """
        self.logger.info(f"予約データ生成開始: {config.DATA_VOLUME['reservations']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['reservations']

        # パレート分布設定
        member_active_count = int(len(self.member_ids) * config.PARETO_RATIOS['member_active_ratio'])
        member_active_reservations = int(count * config.PARETO_RATIOS['member_reservation_ratio'])

        restaurant_popular_count = int(len(self.restaurant_ids) * config.PARETO_RATIOS['restaurant_popular_ratio'])
        restaurant_popular_reservations = int(count * config.PARETO_RATIOS['restaurant_reservation_ratio'])

        self.logger.info(f"パレート分布: 上位{member_active_count}会員が{member_active_reservations}予約")
        self.logger.info(f"パレート分布: 上位{restaurant_popular_count}店舗が{restaurant_popular_reservations}予約")

        # 会員の重み付け（上位20%に高い重み）
        member_weights = [10.0 if i < member_active_count else 1.0 for i in range(len(self.member_ids))]
        member_weights = np.array(member_weights)
        member_weights = member_weights / member_weights.sum()

        # 店舗の重み付け（上位10%に高い重み）
        restaurant_weights = [20.0 if i < restaurant_popular_count else 1.0 for i in range(len(self.restaurant_ids))]
        restaurant_weights = np.array(restaurant_weights)
        restaurant_weights = restaurant_weights / restaurant_weights.sum()

        # reservation_id（連番）
        reservation_ids = list(range(1, count + 1))

        # member_id（重み付けランダム選択）
        member_ids_selected = np.random.choice(
            self.member_ids,
            size=count,
            p=member_weights
        )

        # restaurant_id（重み付けランダム選択）
        restaurant_ids_selected = np.random.choice(
            self.restaurant_ids,
            size=count,
            p=restaurant_weights
        )

        # reservation_date（過去10年以内）
        now = datetime.now()
        years_ago = config.DATE_RANGES['reservations_years']
        start_date = now - timedelta(days=years_ago * 365)

        reservation_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=now)
            for _ in tqdm(range(count), desc="予約日生成")
        ]

        # visit_date（reservation_date以降、10%はNULL=キャンセル）
        visit_dates = []
        cancellation_rate = config.CANCELLATION_RATE

        for res_date in tqdm(reservation_dates, desc="来店日生成"):
            if random.random() < cancellation_rate:
                visit_dates.append(None)  # キャンセル
            else:
                # 予約日から30日以内の来店日
                days_ahead = random.randint(0, 30)
                visit_date = res_date + timedelta(days=days_ahead)
                visit_dates.append(visit_date)

        df = pd.DataFrame({
            'reservation_id': reservation_ids,
            'member_id': member_ids_selected,
            'restaurant_id': restaurant_ids_selected,
            'reservation_date': reservation_dates,
            'visit_date': visit_dates
        })

        # CSV出力
        output_path = self._get_output_path('reservations.csv')
        df.to_csv(output_path, index=config.OUTPUT_CONFIG['csv_index'], encoding=config.OUTPUT_CONFIG['csv_encoding'])

        # reservations保存（reviews生成で使用）
        self.reservations = list(zip(reservation_ids, member_ids_selected, restaurant_ids_selected))

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"予約データ生成完了: {len(df)}件 ({elapsed:.2f}秒)")

        return df

    def generate_access_logs(self) -> pd.DataFrame:
        """
        アクセスログ生成（チャンク分割）

        Returns:
            access_logs DataFrame（最終チャンク）
        """
        self.logger.info(f"アクセスログ生成開始: {config.DATA_VOLUME['access_logs']}件（チャンク分割）")
        total_start = datetime.now()

        total_count = config.DATA_VOLUME['access_logs']
        chunk_size = config.CHUNK_SIZE
        num_chunks = (total_count + chunk_size - 1) // chunk_size

        output_path = self._get_output_path('access_logs.csv')

        # 日付範囲
        now = datetime.now()
        months_ago = config.DATE_RANGES['access_logs_months']
        start_date = now - timedelta(days=months_ago * 30)

        for chunk_idx in range(num_chunks):
            chunk_start = datetime.now()
            current_chunk_size = min(chunk_size, total_count - chunk_idx * chunk_size)

            self.logger.info(f"チャンク {chunk_idx + 1}/{num_chunks} 生成中 ({current_chunk_size}件)")

            # session_id（UUID v4）
            session_ids = [str(uuid.uuid4()) for _ in range(current_chunk_size)]

            # member_id（30%はNULL=非ログイン）
            non_login_rate = config.NON_LOGIN_ACCESS_RATE
            member_ids_chunk = []
            for _ in range(current_chunk_size):
                if random.random() < non_login_rate:
                    member_ids_chunk.append(None)
                else:
                    member_ids_chunk.append(random.choice(self.member_ids))

            # restaurant_id（ランダム選択）
            restaurant_ids_chunk = np.random.choice(self.restaurant_ids, size=current_chunk_size)

            # access_date（過去6ヶ月以内）
            access_dates = [
                self.faker.date_time_between(start_date=start_date, end_date=now)
                for _ in range(current_chunk_size)
            ]

            chunk_df = pd.DataFrame({
                'session_id': session_ids,
                'member_id': member_ids_chunk,
                'restaurant_id': restaurant_ids_chunk,
                'access_date': access_dates
            })

            # CSV出力（追記モード）
            mode = 'w' if chunk_idx == 0 else 'a'
            header = (chunk_idx == 0)
            chunk_df.to_csv(
                output_path,
                mode=mode,
                header=header,
                index=config.OUTPUT_CONFIG['csv_index'],
                encoding=config.OUTPUT_CONFIG['csv_encoding']
            )

            chunk_elapsed = (datetime.now() - chunk_start).total_seconds()
            self.logger.info(f"チャンク {chunk_idx + 1} 完了 ({chunk_elapsed:.2f}秒)")

        total_elapsed = (datetime.now() - total_start).total_seconds()
        self.logger.info(f"アクセスログ生成完了: {total_count}件 ({total_elapsed:.2f}秒)")

        return chunk_df  # 最終チャンクを返す

    def generate_reviews(self) -> pd.DataFrame:
        """
        レビューデータ生成（予約の10%）

        Returns:
            reviews DataFrame
        """
        self.logger.info(f"レビューデータ生成開始: {config.DATA_VOLUME['reviews']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['reviews']

        # reservationsから10%サンプリング
        sampled_reservations = random.sample(self.reservations, count)

        # review_id（連番）
        review_ids = list(range(1, count + 1))

        # member_id, restaurant_id（reservationsから取得）
        member_ids = [res[1] for res in sampled_reservations]
        restaurant_ids = [res[2] for res in sampled_reservations]

        # rating（1-5、正規分布で平均3.5）
        ratings = np.random.normal(
            config.DISTRIBUTION_CONFIG['rating_mean'],
            config.DISTRIBUTION_CONFIG['rating_std'],
            count
        )
        ratings = np.clip(ratings, config.DISTRIBUTION_CONFIG['rating_min'], config.DISTRIBUTION_CONFIG['rating_max'])
        ratings = np.round(ratings).astype(int)

        # post_date（過去5年以内）
        now = datetime.now()
        years_ago = config.DATE_RANGES['reviews_years']
        start_date = now - timedelta(days=years_ago * 365)

        post_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=now)
            for _ in tqdm(range(count), desc="投稿日生成")
        ]

        df = pd.DataFrame({
            'review_id': review_ids,
            'member_id': member_ids,
            'restaurant_id': restaurant_ids,
            'rating': ratings,
            'post_date': post_dates
        })

        # CSV出力
        output_path = self._get_output_path('reviews.csv')
        df.to_csv(output_path, index=config.OUTPUT_CONFIG['csv_index'], encoding=config.OUTPUT_CONFIG['csv_encoding'])

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"レビューデータ生成完了: {len(df)}件 ({elapsed:.2f}秒)")

        return df

    def generate_favorites(self) -> pd.DataFrame:
        """
        お気に入り登録データ生成（30%が予約に繋がる設計）

        Returns:
            favorites DataFrame
        """
        self.logger.info(f"お気に入りデータ生成開始: {config.DATA_VOLUME['favorites']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['favorites']
        favorite_to_reservation_count = int(count * config.PARETO_RATIOS['favorite_to_reservation_rate'])

        self.logger.info(f"お気に入り→予約転換: {favorite_to_reservation_count}件 / {count}件")

        # 30%はreservationsから取得
        favorites_from_reservations = random.sample(self.reservations, favorite_to_reservation_count)
        favorites_pairs = [(res[1], res[2]) for res in favorites_from_reservations]  # (member_id, restaurant_id)

        # 残り70%はランダム生成（重複チェック）
        remaining_count = count - favorite_to_reservation_count
        existing_pairs = set(favorites_pairs)

        while len(favorites_pairs) < count:
            member_id = random.choice(self.member_ids)
            restaurant_id = random.choice(self.restaurant_ids)
            pair = (member_id, restaurant_id)

            if pair not in existing_pairs:
                favorites_pairs.append(pair)
                existing_pairs.add(pair)

        # member_id, restaurant_id分離
        member_ids = [pair[0] for pair in favorites_pairs]
        restaurant_ids = [pair[1] for pair in favorites_pairs]

        # registration_date（過去5年以内）
        now = datetime.now()
        years_ago = config.DATE_RANGES['favorites_years']
        start_date = now - timedelta(days=years_ago * 365)

        registration_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=now)
            for _ in tqdm(range(count), desc="登録日生成")
        ]

        df = pd.DataFrame({
            'member_id': member_ids,
            'restaurant_id': restaurant_ids,
            'registration_date': registration_dates
        })

        # CSV出力
        output_path = self._get_output_path('favorites.csv')
        df.to_csv(output_path, index=config.OUTPUT_CONFIG['csv_index'], encoding=config.OUTPUT_CONFIG['csv_encoding'])

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"お気に入りデータ生成完了: {len(df)}件 ({elapsed:.2f}秒)")

        return df

    def import_to_mysql(self):
        """MySQLへのデータインポート"""
        self.logger.info("=" * 60)
        self.logger.info("MySQLインポート開始")
        self.logger.info("=" * 60)
        start_time = datetime.now()

        connection = None

        try:
            # MySQL接続
            self.logger.info("MySQL接続中...")
            connection = mysql.connector.connect(
                host=config.MYSQL_CONFIG['host'],
                port=config.MYSQL_CONFIG['port'],
                user=config.MYSQL_CONFIG['user'],
                password=config.MYSQL_CONFIG['password'],
                database=config.MYSQL_CONFIG['database'],
                allow_local_infile=True  # LOAD DATA LOCAL INFILE有効化
            )

            if connection.is_connected():
                self.logger.info("MySQL接続成功")
                cursor = connection.cursor()

                # CREATE TABLE実行
                self.logger.info("CREATE TABLE実行中...")
                with open('import.sql', 'r', encoding='utf-8') as f:
                    sql_script = f.read()

                # 複数のSQL文を分割して実行
                for statement in sql_script.split(';'):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)

                connection.commit()
                self.logger.info("CREATE TABLE完了")

                # CSVインポート（LOAD DATA LOCAL INFILE）
                tables = [
                    ('members', 'members.csv'),
                    ('restaurants', 'restaurants.csv'),
                    ('reservations', 'reservations.csv'),
                    ('access_logs', 'access_logs.csv'),
                    ('reviews', 'reviews.csv'),
                    ('favorites', 'favorites.csv')
                ]

                for table_name, csv_file in tables:
                    self.logger.info(f"{table_name} インポート中...")
                    csv_path = self._get_output_path(csv_file)
                    abs_csv_path = os.path.abspath(csv_path)

                    load_sql = f"""
                    LOAD DATA LOCAL INFILE '{abs_csv_path}'
                    INTO TABLE {table_name}
                    FIELDS TERMINATED BY ','
                    ENCLOSED BY '\"'
                    LINES TERMINATED BY '\\n'
                    IGNORE 1 ROWS
                    """

                    try:
                        cursor.execute(load_sql)
                        connection.commit()
                        row_count = cursor.rowcount
                        self.logger.info(f"{table_name} インポート完了: {row_count}件")
                    except Error as e:
                        self.logger.warning(f"{table_name} LOAD DATA INFILE失敗（fallback処理へ）: {e}")
                        # Fallback: pandasでCSVを読んでINSERT
                        self._import_csv_fallback(cursor, connection, table_name, csv_path)

                cursor.close()

                elapsed = (datetime.now() - start_time).total_seconds()
                self.logger.info("=" * 60)
                self.logger.info(f"MySQLインポート完了 ({elapsed:.2f}秒)")
                self.logger.info("=" * 60)

        except Error as e:
            self.logger.error(f"MySQLエラー: {e}", exc_info=True)
            raise

        finally:
            if connection and connection.is_connected():
                connection.close()
                self.logger.info("MySQL接続クローズ")

    def _import_csv_fallback(self, cursor, connection, table_name: str, csv_path: str):
        """CSVインポートのfallback処理（INSERT文使用）"""
        self.logger.info(f"{table_name} fallback処理（INSERT）開始...")

        df = pd.read_csv(csv_path)
        columns = ','.join(df.columns)
        placeholders = ','.join(['%s'] * len(df.columns))
        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # バッチインサート（1000件ずつ）
        batch_size = 1000
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            data = [tuple(row) for row in batch.values]
            cursor.executemany(insert_sql, data)
            connection.commit()

        self.logger.info(f"{table_name} fallback処理完了: {len(df)}件")

    def run(self, skip_csv_generation=False):
        """メイン実行処理"""
        self.logger.info("=" * 60)
        self.logger.info("テストデータ生成開始")
        self.logger.info("=" * 60)
        total_start = datetime.now()

        try:
            if not skip_csv_generation:
                # Phase 1: マスタデータ生成
                self.logger.info("Phase 1: マスタデータ生成")
                self.generate_members()
                self.generate_restaurants()

                # Phase 2: トランザクションデータ生成
                self.logger.info("Phase 2: トランザクションデータ生成")
                self.generate_reservations()
                self.generate_access_logs()
                self.generate_reviews()
                self.generate_favorites()

                total_elapsed = (datetime.now() - total_start).total_seconds()
                self.logger.info("=" * 60)
                self.logger.info(f"全データ生成完了 (総時間: {total_elapsed:.2f}秒)")
                self.logger.info("=" * 60)
            else:
                self.logger.info("CSV生成スキップ（既存ファイル使用）")

            # Phase 3: MySQLインポート
            self.import_to_mysql()

        except Exception as e:
            self.logger.error(f"処理中にエラーが発生: {e}", exc_info=True)
            raise


def main():
    """エントリーポイント"""
    import sys
    skip_csv = '--skip-csv' in sys.argv
    generator = DataGenerator()
    generator.run(skip_csv_generation=skip_csv)


if __name__ == '__main__':
    main()