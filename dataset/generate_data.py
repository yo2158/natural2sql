#!/usr/bin/env python3
"""
テストデータ生成スクリプト - Text-to-SQL Demo Dataset Generator (SQLite版)

飲食店予約サイトを模したテストデータをSQLiteに直接生成します。
"""

import logging
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple
import uuid
import random
from pathlib import Path

import pandas as pd
import numpy as np
from faker import Faker
from tqdm import tqdm

import config


class SQLiteDataGenerator:
    """SQLiteデータ生成メインクラス"""

    def __init__(self):
        """初期化処理"""
        self.faker = Faker('ja_JP')
        Faker.seed(42)  # 再現性のためのシード固定
        np.random.seed(42)
        random.seed(42)

        self._setup_logging()
        self._create_directories()
        self._init_database()

        # 生成済みデータの保持（外部キー参照用）
        self.member_ids: List[int] = []
        self.restaurant_ids: List[int] = []
        self.reservations: List[Tuple[int, int, int]] = []  # (reservation_id, member_id, restaurant_id)

        self.logger.info("SQLiteデータ生成システム初期化完了")

    def _setup_logging(self):
        """ログ設定"""
        log_dir = config.OUTPUT_CONFIG['log_dir']
        os.makedirs(log_dir, exist_ok=True)
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
        db_path = Path(config.OUTPUT_CONFIG['db_path'])
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """SQLite データベース初期化"""
        db_path = config.OUTPUT_CONFIG['db_path']

        # 既存DBがあれば削除
        if os.path.exists(db_path):
            os.remove(db_path)
            self.logger.info(f"既存DB削除: {db_path}")

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        self._create_schema()
        self.logger.info(f"SQLite DB初期化完了: {db_path}")

    def _create_schema(self):
        """テーブルスキーマ作成"""
        schema_sql = """
        -- 会員マスタ
        CREATE TABLE members (
            member_id INTEGER PRIMARY KEY,
            postal_code TEXT,
            gender TEXT,
            age INTEGER,
            registration_date TEXT
        );

        -- 飲食店マスタ
        CREATE TABLE restaurants (
            restaurant_id INTEGER PRIMARY KEY,
            name TEXT,
            genre TEXT,
            postal_code TEXT,
            registration_date TEXT
        );

        -- 予約データ
        CREATE TABLE reservations (
            reservation_id INTEGER PRIMARY KEY,
            member_id INTEGER,
            restaurant_id INTEGER,
            reservation_date TEXT,
            visit_date TEXT
        );

        -- アクセスログ
        CREATE TABLE access_logs (
            session_id TEXT PRIMARY KEY,
            member_id INTEGER,
            restaurant_id INTEGER,
            access_date TEXT
        );

        -- レビュー
        CREATE TABLE reviews (
            review_id INTEGER PRIMARY KEY,
            member_id INTEGER,
            restaurant_id INTEGER,
            rating INTEGER,
            post_date TEXT
        );

        -- お気に入り
        CREATE TABLE favorites (
            member_id INTEGER,
            restaurant_id INTEGER,
            registration_date TEXT,
            PRIMARY KEY (member_id, restaurant_id)
        );

        -- クエリ履歴（システムテーブル）
        CREATE TABLE query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT,
            generated_sql TEXT,
            success INTEGER,
            error_message TEXT,
            row_count INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- インデックス作成
        CREATE INDEX idx_member_res ON reservations(member_id);
        CREATE INDEX idx_restaurant_res ON reservations(restaurant_id);
        CREATE INDEX idx_access_date ON access_logs(access_date);
        CREATE INDEX idx_review_restaurant ON reviews(restaurant_id);
        CREATE INDEX idx_favorite_restaurant ON favorites(restaurant_id);
        """

        self.cursor.executescript(schema_sql)
        self.conn.commit()
        self.logger.info("テーブルスキーマ作成完了")

    def generate_members(self):
        """会員マスタ生成"""
        self.logger.info(f"会員データ生成開始: {config.DATA_VOLUME['members']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['members']

        # データ生成
        member_ids = list(range(1, count + 1))
        postal_codes = [self.faker.postcode() for _ in tqdm(range(count), desc="郵便番号生成")]
        genders = np.random.choice(['M', 'F'], size=count)

        ages = np.random.normal(
            config.DISTRIBUTION_CONFIG['age_mean'],
            config.DISTRIBUTION_CONFIG['age_std'],
            count
        )
        ages = np.clip(ages, config.DISTRIBUTION_CONFIG['age_min'], config.DISTRIBUTION_CONFIG['age_max'])
        ages = ages.astype(int)

        now = datetime.now()
        years_ago = config.DATE_RANGES['members_registration_years']
        start_date = now - timedelta(days=years_ago * 365)

        registration_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=now).isoformat()
            for _ in tqdm(range(count), desc="登録日生成")
        ]

        # SQLite挿入
        data = list(zip(member_ids, postal_codes, genders, ages, registration_dates))
        self.cursor.executemany(
            "INSERT INTO members VALUES (?, ?, ?, ?, ?)",
            data
        )
        self.conn.commit()

        self.member_ids = member_ids

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"会員データ生成完了: {count}件 ({elapsed:.2f}秒)")

    def generate_restaurants(self):
        """飲食店マスタ生成"""
        self.logger.info(f"飲食店データ生成開始: {config.DATA_VOLUME['restaurants']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['restaurants']

        # データ生成
        restaurant_ids = list(range(1, count + 1))

        def generate_restaurant_name():
            patterns = [
                lambda: f"{self.faker.last_name()}{random.choice(['亭', '屋', '家', '処', '庵'])}",
                lambda: f"{random.choice(['居酒屋', 'レストラン', 'カフェ', 'ダイニング', 'バル'])}{self.faker.last_name()}",
                lambda: f"{self.faker.last_name()}{random.choice(['台所', '食卓', 'キッチン', '厨房'])}",
            ]
            pattern = random.choices(patterns, weights=[45, 35, 20])[0]
            return pattern()

        names = [generate_restaurant_name() for _ in tqdm(range(count), desc="店名生成")]
        genres = np.random.choice(config.RESTAURANT_GENRES, size=count)
        postal_codes = [self.faker.postcode() for _ in tqdm(range(count), desc="郵便番号生成")]

        now = datetime.now()
        years_ago = config.DATE_RANGES['restaurants_registration_years']
        min_years_ago = config.DATE_RANGES['restaurants_min_years_ago']
        start_date = now - timedelta(days=years_ago * 365)
        end_date = now - timedelta(days=min_years_ago * 365)

        registration_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=end_date).isoformat()
            for _ in tqdm(range(count), desc="登録日生成")
        ]

        # SQLite挿入
        data = list(zip(restaurant_ids, names, genres, postal_codes, registration_dates))
        self.cursor.executemany(
            "INSERT INTO restaurants VALUES (?, ?, ?, ?, ?)",
            data
        )
        self.conn.commit()

        self.restaurant_ids = restaurant_ids

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"飲食店データ生成完了: {count}件 ({elapsed:.2f}秒)")

    def generate_reservations(self):
        """予約データ生成（パレート分布適用）"""
        self.logger.info(f"予約データ生成開始: {config.DATA_VOLUME['reservations']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['reservations']

        # パレート分布設定
        member_active_count = int(len(self.member_ids) * config.PARETO_RATIOS['member_active_ratio'])
        restaurant_popular_count = int(len(self.restaurant_ids) * config.PARETO_RATIOS['restaurant_popular_ratio'])

        self.logger.info(f"パレート分布: 上位{member_active_count}会員、上位{restaurant_popular_count}店舗に偏重")

        # 重み付け
        member_weights = [10.0 if i < member_active_count else 1.0 for i in range(len(self.member_ids))]
        member_weights = np.array(member_weights) / np.sum(member_weights)

        restaurant_weights = [20.0 if i < restaurant_popular_count else 1.0 for i in range(len(self.restaurant_ids))]
        restaurant_weights = np.array(restaurant_weights) / np.sum(restaurant_weights)

        # データ生成
        reservation_ids = list(range(1, count + 1))
        member_ids_selected = np.random.choice(self.member_ids, size=count, p=member_weights)
        restaurant_ids_selected = np.random.choice(self.restaurant_ids, size=count, p=restaurant_weights)

        now = datetime.now()
        years_ago = config.DATE_RANGES['reservations_years']
        start_date = now - timedelta(days=years_ago * 365)

        reservation_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=now).isoformat()
            for _ in tqdm(range(count), desc="予約日生成")
        ]

        # visit_date（10%はNULL=キャンセル）
        visit_dates = []
        cancellation_rate = config.CANCELLATION_RATE

        for res_date_str in tqdm(reservation_dates, desc="来店日生成"):
            if random.random() < cancellation_rate:
                visit_dates.append(None)
            else:
                res_date = datetime.fromisoformat(res_date_str)
                days_ahead = random.randint(0, 30)
                visit_date = res_date + timedelta(days=days_ahead)
                visit_dates.append(visit_date.isoformat())

        # SQLite挿入
        data = list(zip(reservation_ids, member_ids_selected, restaurant_ids_selected, reservation_dates, visit_dates))
        self.cursor.executemany(
            "INSERT INTO reservations VALUES (?, ?, ?, ?, ?)",
            data
        )
        self.conn.commit()

        self.reservations = list(zip(reservation_ids, member_ids_selected, restaurant_ids_selected))

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"予約データ生成完了: {count}件 ({elapsed:.2f}秒)")

    def generate_access_logs(self):
        """アクセスログ生成（チャンク分割）"""
        self.logger.info(f"アクセスログ生成開始: {config.DATA_VOLUME['access_logs']}件")
        total_start = datetime.now()

        total_count = config.DATA_VOLUME['access_logs']
        chunk_size = config.CHUNK_SIZE
        num_chunks = (total_count + chunk_size - 1) // chunk_size

        now = datetime.now()
        months_ago = config.DATE_RANGES['access_logs_months']
        start_date = now - timedelta(days=months_ago * 30)

        for chunk_idx in range(num_chunks):
            chunk_start = datetime.now()
            current_chunk_size = min(chunk_size, total_count - chunk_idx * chunk_size)

            self.logger.info(f"チャンク {chunk_idx + 1}/{num_chunks} 生成中 ({current_chunk_size}件)")

            # データ生成
            session_ids = [str(uuid.uuid4()) for _ in range(current_chunk_size)]

            non_login_rate = config.NON_LOGIN_ACCESS_RATE
            member_ids_chunk = []
            for _ in range(current_chunk_size):
                if random.random() < non_login_rate:
                    member_ids_chunk.append(None)
                else:
                    member_ids_chunk.append(random.choice(self.member_ids))

            restaurant_ids_chunk = np.random.choice(self.restaurant_ids, size=current_chunk_size)

            access_dates = [
                self.faker.date_time_between(start_date=start_date, end_date=now).isoformat()
                for _ in range(current_chunk_size)
            ]

            # SQLite挿入
            data = list(zip(session_ids, member_ids_chunk, restaurant_ids_chunk, access_dates))
            self.cursor.executemany(
                "INSERT INTO access_logs VALUES (?, ?, ?, ?)",
                data
            )
            self.conn.commit()

            chunk_elapsed = (datetime.now() - chunk_start).total_seconds()
            self.logger.info(f"チャンク {chunk_idx + 1} 完了 ({chunk_elapsed:.2f}秒)")

        total_elapsed = (datetime.now() - total_start).total_seconds()
        self.logger.info(f"アクセスログ生成完了: {total_count}件 ({total_elapsed:.2f}秒)")

    def generate_reviews(self):
        """レビューデータ生成"""
        self.logger.info(f"レビューデータ生成開始: {config.DATA_VOLUME['reviews']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['reviews']

        # reservationsからサンプリング
        sampled_reservations = random.sample(self.reservations, count)

        review_ids = list(range(1, count + 1))
        member_ids = [res[1] for res in sampled_reservations]
        restaurant_ids = [res[2] for res in sampled_reservations]

        ratings = np.random.normal(
            config.DISTRIBUTION_CONFIG['rating_mean'],
            config.DISTRIBUTION_CONFIG['rating_std'],
            count
        )
        ratings = np.clip(ratings, config.DISTRIBUTION_CONFIG['rating_min'], config.DISTRIBUTION_CONFIG['rating_max'])
        ratings = np.round(ratings).astype(int)

        now = datetime.now()
        years_ago = config.DATE_RANGES['reviews_years']
        start_date = now - timedelta(days=years_ago * 365)

        post_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=now).isoformat()
            for _ in tqdm(range(count), desc="投稿日生成")
        ]

        # SQLite挿入
        data = list(zip(review_ids, member_ids, restaurant_ids, ratings, post_dates))
        self.cursor.executemany(
            "INSERT INTO reviews VALUES (?, ?, ?, ?, ?)",
            data
        )
        self.conn.commit()

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"レビューデータ生成完了: {count}件 ({elapsed:.2f}秒)")

    def generate_favorites(self):
        """お気に入り登録データ生成"""
        self.logger.info(f"お気に入りデータ生成開始: {config.DATA_VOLUME['favorites']}件")
        start_time = datetime.now()

        count = config.DATA_VOLUME['favorites']
        favorite_to_reservation_count = int(count * config.PARETO_RATIOS['favorite_to_reservation_rate'])

        self.logger.info(f"お気に入り→予約転換: {favorite_to_reservation_count}件 / {count}件")

        # 30%はreservationsから（重複除外）
        favorites_from_reservations = random.sample(self.reservations, min(favorite_to_reservation_count, len(self.reservations)))
        favorites_pairs_set = set()
        for res in favorites_from_reservations:
            pair = (res[1], res[2])  # (member_id, restaurant_id)
            favorites_pairs_set.add(pair)

        favorites_pairs = list(favorites_pairs_set)

        # 残り70%はランダム生成（重複回避）
        existing_pairs = set(favorites_pairs)
        max_attempts = count * 10  # 無限ループ防止
        attempts = 0

        while len(favorites_pairs) < count and attempts < max_attempts:
            member_id = random.choice(self.member_ids)
            restaurant_id = random.choice(self.restaurant_ids)
            pair = (member_id, restaurant_id)

            if pair not in existing_pairs:
                favorites_pairs.append(pair)
                existing_pairs.add(pair)
            attempts += 1

        if len(favorites_pairs) < count:
            self.logger.warning(f"お気に入り生成: 目標{count}件に対し{len(favorites_pairs)}件生成（重複回避制限）")

        member_ids = [pair[0] for pair in favorites_pairs]
        restaurant_ids = [pair[1] for pair in favorites_pairs]

        now = datetime.now()
        years_ago = config.DATE_RANGES['favorites_years']
        start_date = now - timedelta(days=years_ago * 365)

        registration_dates = [
            self.faker.date_time_between(start_date=start_date, end_date=now).isoformat()
            for _ in tqdm(range(count), desc="登録日生成")
        ]

        # SQLite挿入
        data = list(zip(member_ids, restaurant_ids, registration_dates))
        self.cursor.executemany(
            "INSERT INTO favorites VALUES (?, ?, ?)",
            data
        )
        self.conn.commit()

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"お気に入りデータ生成完了: {count}件 ({elapsed:.2f}秒)")

    def run(self):
        """メイン実行処理"""
        self.logger.info("=" * 60)
        self.logger.info("SQLiteテストデータ生成開始")
        self.logger.info("=" * 60)
        total_start = datetime.now()

        try:
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

            # DB統計情報
            self.cursor.execute("SELECT COUNT(*) FROM members")
            members_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM restaurants")
            restaurants_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM reservations")
            reservations_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM access_logs")
            access_logs_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM reviews")
            reviews_count = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM favorites")
            favorites_count = self.cursor.fetchone()[0]

            total_records = (members_count + restaurants_count + reservations_count +
                           access_logs_count + reviews_count + favorites_count)

            self.logger.info("=" * 60)
            self.logger.info(f"全データ生成完了 (総時間: {total_elapsed:.2f}秒)")
            self.logger.info(f"総レコード数: {total_records:,}件")
            self.logger.info("=" * 60)

            # DBファイルサイズ確認
            db_path = Path(config.OUTPUT_CONFIG['db_path'])
            if db_path.exists():
                size_mb = db_path.stat().st_size / 1024 / 1024
                self.logger.info(f"DBサイズ: {size_mb:.2f}MB")

        except Exception as e:
            self.logger.error(f"処理中にエラーが発生: {e}", exc_info=True)
            raise

        finally:
            if self.conn:
                self.conn.close()
                self.logger.info("SQLite接続クローズ")


def main():
    """エントリーポイント"""
    generator = SQLiteDataGenerator()
    generator.run()


if __name__ == '__main__':
    main()
