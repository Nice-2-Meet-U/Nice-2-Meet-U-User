from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from passlib.hash import bcrypt
from sqlalchemy import text

from models.user import UserPublic


class UserRepository:
    """Repository for persisting users with DB-first or in-memory fallback."""

    def __init__(self, engine=None):
        self.engine = engine
        self._memory: Dict[str, Dict] = {}
        if self.engine:
            self._ensure_table()

    def _ensure_table(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS users (
            user_id CHAR(36) NOT NULL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(255),
            provider VARCHAR(20) NOT NULL,
            google_sub VARCHAR(255) UNIQUE,
            picture VARCHAR(2048),
            password_hash VARCHAR(255),
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            last_login DATETIME(6)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        """
        with self.engine.begin() as conn:
            conn.execute(text(ddl))

    def _row_to_public(self, row: Dict) -> UserPublic:
        return UserPublic(
            id=row["user_id"],
            email=row["email"],
            name=row.get("name"),
            provider=row.get("provider", "local"),
            picture=row.get("picture"),
            last_login=row.get("last_login"),
        )

    def upsert_google_user(
        self,
        *,
        email: str,
        name: Optional[str],
        google_sub: str,
        picture: Optional[str],
    ) -> UserPublic:
        now = datetime.utcnow()
        if not self.engine:
            existing = self._get_memory_by_email(email)
            if existing:
                existing.update(
                    {
                        "name": name or existing.get("name"),
                        "google_sub": google_sub,
                        "picture": picture or existing.get("picture"),
                        "provider": "google",
                        "last_login": now,
                        "updated_at": now,
                    }
                )
                return self._row_to_public(existing)
            user_id = str(uuid4())
            record = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "provider": "google",
                "google_sub": google_sub,
                "picture": picture,
                "created_at": now,
                "updated_at": now,
                "last_login": now,
            }
            self._memory[user_id] = record
            return self._row_to_public(record)

        insert_sql = text(
            """
            INSERT INTO users (user_id, email, name, provider, google_sub, picture, created_at, updated_at, last_login)
            VALUES (:user_id, :email, :name, 'google', :google_sub, :picture, :created_at, :updated_at, :last_login)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                google_sub = VALUES(google_sub),
                picture = VALUES(picture),
                provider = 'google',
                updated_at = VALUES(updated_at),
                last_login = VALUES(last_login)
            """
        )
        user_id = str(uuid4())
        params = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "google_sub": google_sub,
            "picture": picture,
            "created_at": now,
            "updated_at": now,
            "last_login": now,
        }
        with self.engine.begin() as conn:
            conn.execute(insert_sql, params)
            row = conn.execute(
                text("SELECT * FROM users WHERE email = :email"), {"email": email}
            ).mappings().first()
            return self._row_to_public(row)

    def create_local_user(self, *, email: str, password: str, name: Optional[str]) -> UserPublic:
        now = datetime.utcnow()
        password_hash = bcrypt.hash(password)
        if not self.engine:
            if self._get_memory_by_email(email):
                raise ValueError("User already exists.")
            user_id = str(uuid4())
            record = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "provider": "local",
                "password_hash": password_hash,
                "created_at": now,
                "updated_at": now,
                "last_login": now,
            }
            self._memory[user_id] = record
            return self._row_to_public(record)

        with self.engine.begin() as conn:
            existing = conn.execute(
                text("SELECT user_id FROM users WHERE email = :email"), {"email": email}
            ).first()
            if existing:
                raise ValueError("User already exists.")

            user_id = str(uuid4())
            conn.execute(
                text(
                    """
                    INSERT INTO users (user_id, email, name, provider, password_hash, created_at, updated_at, last_login)
                    VALUES (:user_id, :email, :name, 'local', :password_hash, :created_at, :updated_at, :last_login)
                    """
                ),
                {
                    "user_id": user_id,
                    "email": email,
                    "name": name,
                    "password_hash": password_hash,
                    "created_at": now,
                    "updated_at": now,
                    "last_login": now,
                },
            )
            row = conn.execute(
                text("SELECT * FROM users WHERE user_id = :user_id"), {"user_id": user_id}
            ).mappings().first()
            return self._row_to_public(row)

    def verify_local_credentials(self, *, email: str, password: str) -> Optional[UserPublic]:
        now = datetime.utcnow()
        if not self.engine:
            record = self._get_memory_by_email(email)
            if record and record.get("password_hash") and bcrypt.verify(password, record["password_hash"]):
                record.update({"last_login": now, "updated_at": now})
                return self._row_to_public(record)
            return None

        with self.engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT * FROM users WHERE email = :email AND provider = 'local'"
                ),
                {"email": email},
            ).mappings().first()
            if row and row.get("password_hash") and bcrypt.verify(password, row["password_hash"]):
                conn.execute(
                    text(
                        "UPDATE users SET last_login = :last_login, updated_at = :updated_at WHERE user_id = :user_id"
                    ),
                    {
                        "last_login": now,
                        "updated_at": now,
                        "user_id": row["user_id"],
                    },
                )
                refreshed = conn.execute(
                    text("SELECT * FROM users WHERE user_id = :user_id"),
                    {"user_id": row["user_id"]},
                ).mappings().first()
                return self._row_to_public(refreshed)
            return None

    def get_user_by_id(self, user_id: str) -> Optional[UserPublic]:
        if not self.engine:
            record = self._memory.get(user_id)
            return self._row_to_public(record) if record else None

        with self.engine.begin() as conn:
            row = conn.execute(
                text("SELECT * FROM users WHERE user_id = :user_id"), {"user_id": user_id}
            ).mappings().first()
            return self._row_to_public(row) if row else None

    def _get_memory_by_email(self, email: str) -> Optional[Dict]:
        for record in self._memory.values():
            if record["email"] == email:
                return record
        return None
