from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from sqlalchemy import text

from models.profile import ProfileCreate, ProfileRead, ProfileUpdate


class ProfileRepository:
    """Profile persistence with MySQL or in-memory fallback."""

    def __init__(self, engine=None):
        self.engine = engine
        self._memory: Dict[str, Dict] = {}
        if self.engine:
            self._ensure_table()

    def _ensure_table(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id CHAR(36) NOT NULL PRIMARY KEY,
            user_id CHAR(36) NOT NULL UNIQUE,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            birth_date DATE,
            gender VARCHAR(50),
            location VARCHAR(255),
            bio TEXT,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_profiles_user_id (user_id),
            CONSTRAINT uc_profiles_user UNIQUE (user_id)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        """
        with self.engine.begin() as conn:
            conn.execute(text(ddl))

    def _row_to_profile(self, row: Dict) -> ProfileRead:
        return ProfileRead(
            id=row["profile_id"],
            user_id=row["user_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row.get("phone"),
            birth_date=row.get("birth_date"),
            gender=row.get("gender"),
            location=row.get("location"),
            bio=row.get("bio"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_by_user_id(self, user_id: str) -> Optional[ProfileRead]:
        if not self.engine:
            for record in self._memory.values():
                if record["user_id"] == user_id:
                    return self._row_to_profile(record)
            return None

        with self.engine.begin() as conn:
            row = conn.execute(
                text("SELECT * FROM profiles WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).mappings().first()
            return self._row_to_profile(row) if row else None

    def get_by_id(self, profile_id: str) -> Optional[ProfileRead]:
        if not self.engine:
            record = self._memory.get(profile_id)
            return self._row_to_profile(record) if record else None

        with self.engine.begin() as conn:
            row = conn.execute(
                text("SELECT * FROM profiles WHERE profile_id = :profile_id"),
                {"profile_id": profile_id},
            ).mappings().first()
            return self._row_to_profile(row) if row else None

    def create_profile(self, *, user_id: str, payload: ProfileCreate) -> ProfileRead:
        now = datetime.utcnow()
        profile_id = str(uuid4())
        record = {
            "profile_id": profile_id,
            "user_id": user_id,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "email": payload.email,
            "phone": payload.phone,
            "birth_date": payload.birth_date,
            "gender": payload.gender,
            "location": payload.location,
            "bio": payload.bio,
            "created_at": now,
            "updated_at": now,
        }

        if not self.engine:
            self._memory[profile_id] = record
            return self._row_to_profile(record)

        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO profiles (
                        profile_id, user_id, first_name, last_name, email, phone,
                        birth_date, gender, location, bio, created_at, updated_at
                    ) VALUES (
                        :profile_id, :user_id, :first_name, :last_name, :email, :phone,
                        :birth_date, :gender, :location, :bio, :created_at, :updated_at
                    )
                    """
                ),
                record,
            )
            row = conn.execute(
                text("SELECT * FROM profiles WHERE profile_id = :profile_id"),
                {"profile_id": profile_id},
            ).mappings().first()
            return self._row_to_profile(row)

    def update_profile(
        self,
        *,
        profile_id: str,
        user_id: str,
        update: ProfileUpdate,
    ) -> Optional[ProfileRead]:
        now = datetime.utcnow()
        if not self.engine:
            existing = self._memory.get(profile_id)
            if not existing or existing["user_id"] != user_id:
                return None
            for field, value in update.model_dump(exclude_unset=True).items():
                existing[field] = value
            existing["updated_at"] = now
            return self._row_to_profile(existing)

        with self.engine.begin() as conn:
            owned = conn.execute(
                text(
                    "SELECT * FROM profiles WHERE profile_id = :profile_id AND user_id = :user_id"
                ),
                {"profile_id": profile_id, "user_id": user_id},
            ).mappings().first()
            if not owned:
                return None

            set_clauses = []
            params = {"profile_id": profile_id, "user_id": user_id, "updated_at": now}
            for field, value in update.model_dump(exclude_unset=True).items():
                set_clauses.append(f"{field} = :{field}")
                params[field] = value

            if set_clauses:
                set_sql = ", ".join(set_clauses + ["updated_at = :updated_at"])
                conn.execute(
                    text(
                        f"UPDATE profiles SET {set_sql} WHERE profile_id = :profile_id AND user_id = :user_id"
                    ),
                    params,
                )

            row = conn.execute(
                text("SELECT * FROM profiles WHERE profile_id = :profile_id"),
                {"profile_id": profile_id},
            ).mappings().first()
            return self._row_to_profile(row) if row else None

    def delete_profile(self, *, profile_id: str, user_id: str) -> bool:
        if not self.engine:
            existing = self._memory.get(profile_id)
            if not existing or existing["user_id"] != user_id:
                return False
            self._memory.pop(profile_id)
            return True

        with self.engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM profiles WHERE profile_id = :profile_id AND user_id = :user_id"),
                {"profile_id": profile_id, "user_id": user_id},
            )
            return result.rowcount > 0
