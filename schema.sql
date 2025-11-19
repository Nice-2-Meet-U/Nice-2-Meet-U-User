CREATE DATABASE IF NOT EXISTS profile_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE profile_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS photos;
DROP TABLE IF EXISTS visibility;
DROP TABLE IF EXISTS profiles;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE profiles (
    profile_id      CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY DEFAULT (UUID()),
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL,
    phone           VARCHAR(50),
    birth_date      DATE,
    gender          VARCHAR(50),
    location        VARCHAR(255),
    bio             TEXT,
    created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_profiles_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE photos (
    photo_id        CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY DEFAULT (UUID()),
    profile_id      CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    url             VARCHAR(2048) NOT NULL,
    is_primary      TINYINT(1)  NOT NULL DEFAULT 0,
    uploaded_at     DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    description     TEXT,
    created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY idx_photos_profile (profile_id),
    CONSTRAINT fk_photos_profile FOREIGN KEY (profile_id) REFERENCES profiles(profile_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE visibility (
    visibility_id   CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY DEFAULT (UUID()),
    profile_id      CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    is_visible      TINYINT(1)  NOT NULL DEFAULT 1,
    visibility_scope ENUM('close', 'normal', 'wide') NOT NULL DEFAULT 'normal',
    last_toggled_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_visibility_profile (profile_id),
    CONSTRAINT fk_visibility_profile FOREIGN KEY (profile_id) REFERENCES profiles(profile_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
