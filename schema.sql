CREATE DATABASE IF NOT EXISTS flask_crud
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE flask_crud;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    google_id VARCHAR(255) UNIQUE NULL,
    avatar_url VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS login_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    email VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,
    password_storage_status VARCHAR(80) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_login_events_user_id (user_id),
    INDEX idx_login_events_email (email),
    INDEX idx_login_events_status (status),
    INDEX idx_login_events_created_at (created_at),
    CONSTRAINT fk_login_events_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    CONSTRAINT fk_imported_playlists_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS imported_playlist_tracks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    imported_playlist_id INT NOT NULL,
    spotify_track_id VARCHAR(255) NULL,
    track_name VARCHAR(255) NOT NULL,
    artist_names VARCHAR(255) NULL,
    album_name VARCHAR(255) NULL,
    track_description TEXT NULL,
    spotify_url VARCHAR(500) NULL,
    local_file_url VARCHAR(500) NULL,
    source_type VARCHAR(30) NOT NULL DEFAULT 'spotify',
    duration_ms INT NOT NULL DEFAULT 0,
    track_position INT NOT NULL,
    CONSTRAINT fk_imported_playlist_tracks_playlist
        FOREIGN KEY (imported_playlist_id) REFERENCES imported_playlists(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
