CREATE TABLE members (
            member_id INTEGER PRIMARY KEY,
            postal_code TEXT,
            gender TEXT,
            age INTEGER,
            registration_date TEXT
        );
CREATE TABLE restaurants (
            restaurant_id INTEGER PRIMARY KEY,
            name TEXT,
            genre TEXT,
            postal_code TEXT,
            registration_date TEXT
        );
CREATE TABLE reservations (
            reservation_id INTEGER PRIMARY KEY,
            member_id INTEGER,
            restaurant_id INTEGER,
            reservation_date TEXT,
            visit_date TEXT
        );
CREATE TABLE access_logs (
            session_id TEXT PRIMARY KEY,
            member_id INTEGER,
            restaurant_id INTEGER,
            access_date TEXT
        );
CREATE TABLE reviews (
            review_id INTEGER PRIMARY KEY,
            member_id INTEGER,
            restaurant_id INTEGER,
            rating INTEGER,
            post_date TEXT
        );
CREATE TABLE favorites (
            member_id INTEGER,
            restaurant_id INTEGER,
            registration_date TEXT,
            PRIMARY KEY (member_id, restaurant_id)
        );
CREATE TABLE query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT,
            generated_sql TEXT,
            success INTEGER,
            error_message TEXT,
            row_count INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_member_res ON reservations(member_id);
CREATE INDEX idx_restaurant_res ON reservations(restaurant_id);
CREATE INDEX idx_access_date ON access_logs(access_date);
CREATE INDEX idx_review_restaurant ON reviews(restaurant_id);
CREATE INDEX idx_favorite_restaurant ON favorites(restaurant_id);
