import pymysql

import config


def get_connection():
    try:
        connection = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
        return connection
    except pymysql.MySQLError:
        return None


def ensure_column(cursor, table_name, column_name, definition):
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (config.MYSQL_DATABASE, table_name, column_name),
    )
    result = cursor.fetchone()

    if result and result["count"] == 0:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def create_tables():
    connection = get_connection()
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            google_id VARCHAR(255) UNIQUE NULL,
            avatar_url VARCHAR(255) NULL
        )
        """
    )
    ensure_column(cursor, "users", "google_id", "VARCHAR(255) NULL UNIQUE")
    ensure_column(cursor, "users", "avatar_url", "VARCHAR(255) NULL")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS imported_playlists (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            spotify_playlist_id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT NULL,
            owner_name VARCHAR(255) NULL,
            image_url VARCHAR(500) NULL,
            spotify_url VARCHAR(500) NULL,
            track_count INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_playlist (user_id, spotify_playlist_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS imported_playlist_tracks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            imported_playlist_id INT NOT NULL,
            spotify_track_id VARCHAR(255) NULL,
            track_name VARCHAR(255) NOT NULL,
            artist_names VARCHAR(255) NULL,
            album_name VARCHAR(255) NULL,
            spotify_url VARCHAR(500) NULL,
            local_file_url VARCHAR(500) NULL,
            source_type VARCHAR(30) NOT NULL DEFAULT 'spotify',
            duration_ms INT NOT NULL DEFAULT 0,
            track_position INT NOT NULL,
            FOREIGN KEY (imported_playlist_id) REFERENCES imported_playlists(id) ON DELETE CASCADE
        )
        """
    )
    ensure_column(cursor, "imported_playlist_tracks", "local_file_url", "VARCHAR(500) NULL")
    ensure_column(cursor, "imported_playlist_tracks", "source_type", "VARCHAR(30) NOT NULL DEFAULT 'spotify'")

    connection.commit()
    cursor.close()
    connection.close()
