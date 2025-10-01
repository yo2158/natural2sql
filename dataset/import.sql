-- テストデータ生成システム - MySQL CREATE TABLE文
-- Database: sandbox

-- 高速クリーンアップ: 外部キー無視してDROP
SET FOREIGN_KEY_CHECKS = 0;

-- テーブル削除
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS access_logs;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS restaurants;
DROP TABLE IF EXISTS members;

-- 会員マスタ
CREATE TABLE members (
    member_id INT PRIMARY KEY AUTO_INCREMENT,
    postal_code VARCHAR(8) NOT NULL COMMENT '郵便番号',
    gender CHAR(1) NOT NULL COMMENT '性別（M/F）',
    age INT NOT NULL COMMENT '年齢',
    registration_date DATETIME NOT NULL COMMENT '登録日時'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会員マスタ';

-- 飲食店マスタ
CREATE TABLE restaurants (
    restaurant_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL COMMENT '店名',
    genre VARCHAR(20) NOT NULL COMMENT 'ジャンル',
    postal_code VARCHAR(8) NOT NULL COMMENT '郵便番号',
    registration_date DATETIME NOT NULL COMMENT '登録日時',
    INDEX idx_genre (genre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='飲食店マスタ';

-- 予約データ
CREATE TABLE reservations (
    reservation_id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT NOT NULL COMMENT '会員ID',
    restaurant_id INT NOT NULL COMMENT '店舗ID',
    reservation_date DATETIME NOT NULL COMMENT '予約作成日時',
    visit_date DATETIME COMMENT '来店予定日時（NULL=キャンセル）',
    INDEX idx_member_id (member_id),
    INDEX idx_restaurant_id (restaurant_id),
    INDEX idx_reservation_date (reservation_date),
    INDEX idx_visit_date (visit_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='予約データ';

-- アクセスログ
CREATE TABLE access_logs (
    session_id VARCHAR(36) COMMENT 'セッションID（UUID）',
    member_id INT COMMENT '会員ID（NULL=非ログイン）',
    restaurant_id INT NOT NULL COMMENT '店舗ID',
    access_date DATETIME NOT NULL COMMENT 'アクセス日時',
    INDEX idx_access_date (access_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='アクセスログ';

-- レビューデータ
CREATE TABLE reviews (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT NOT NULL COMMENT '会員ID',
    restaurant_id INT NOT NULL COMMENT '店舗ID',
    rating INT NOT NULL COMMENT '評価（1-5）',
    post_date DATETIME NOT NULL COMMENT '投稿日時',
    CHECK (rating BETWEEN 1 AND 5),
    INDEX idx_restaurant_id (restaurant_id),
    INDEX idx_rating (rating),
    INDEX idx_post_date (post_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='レビューデータ';

-- お気に入り登録
CREATE TABLE favorites (
    member_id INT NOT NULL COMMENT '会員ID',
    restaurant_id INT NOT NULL COMMENT '店舗ID',
    registration_date DATETIME NOT NULL COMMENT '登録日時',
    PRIMARY KEY (member_id, restaurant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='お気に入り登録';