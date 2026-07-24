-- Monk Play Login Events MySQL Workbench File
-- Open this file in MySQL Workbench and click the lightning/run button.
-- This file creates the login_events table and safe views for checking user login history.
-- It does not store plain-text passwords. User passwords stay hashed in users.password.

CREATE DATABASE IF NOT EXISTS flask_crud
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE flask_crud;

-- =========================================================
-- REQUIRED USERS TABLE
-- The login_events table links to users.id when the email belongs to a real user.
-- Passwords must remain hashed in this table.
-- =========================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    google_id VARCHAR(255) UNIQUE NULL,
    avatar_url VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_role (role),
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- LOGIN EVENTS
-- Records successful and failed login attempts.
-- Never insert the submitted password into this table.
-- =========================================================
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

-- =========================================================
-- SAFE LOGIN EVENT VIEW
-- Shows login details without exposing passwords or password hashes.
-- =========================================================
CREATE OR REPLACE VIEW login_event_details AS
SELECT
    login_events.id,
    login_events.user_id,
    COALESCE(users.name, 'Unknown user') AS user_name,
    login_events.email,
    COALESCE(users.role, 'guest') AS user_role,
    login_events.status,
    login_events.password_storage_status,
    login_events.ip_address,
    login_events.user_agent,
    login_events.created_at
FROM login_events
LEFT JOIN users
    ON users.id = login_events.user_id;

-- =========================================================
-- PASSWORD HASH CHECK VIEW
-- Confirms users.password stores hashed values without exposing the full hash.
-- =========================================================
CREATE OR REPLACE VIEW user_password_hash_check AS
SELECT
    id,
    name,
    email,
    role,
    LEFT(password, 18) AS password_hash_prefix,
    CASE
        WHEN password LIKE 'pbkdf2:%'
            OR password LIKE 'scrypt:%'
            OR password LIKE 'argon2:%'
        THEN 'OK - hashed'
        ELSE 'Warning - reset password'
    END AS password_check,
    updated_at
FROM users;

-- =========================================================
-- MYSQL WORKBENCH CHECKING QUERIES
-- Rerun these queries after users log in.
-- =========================================================

-- 1. Confirm the login_events table exists.
SHOW TABLES LIKE 'login_events';

-- 2. See newest login details.
SELECT *
FROM login_event_details
ORDER BY created_at DESC, id DESC;

-- 3. See successful, failed, and incomplete login counts.
SELECT
    status,
    COUNT(*) AS event_count,
    MAX(created_at) AS latest_event
FROM login_events
GROUP BY status
ORDER BY latest_event DESC;

-- 4. See login history grouped by email.
SELECT
    email,
    COUNT(*) AS total_attempts,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_logins,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_logins,
    MAX(created_at) AS latest_attempt
FROM login_events
GROUP BY email
ORDER BY latest_attempt DESC;

-- 5. Confirm user passwords are stored as hashes.
SELECT *
FROM user_password_hash_check
ORDER BY updated_at DESC, id DESC;
