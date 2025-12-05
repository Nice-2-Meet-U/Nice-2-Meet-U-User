from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import text

from models.photos import PhotoCreate, PhotoRead, PhotoUpdate


class PhotoRepository:
    """Photo persistence with MySQL or in-memory fallback."""

    def __init__(self, engine=None):
        self.engine = engine
        self._memory: Dict[str, Dict] = {}
        if self.engine:
            self._ensure_table()

    def _ensure_table(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS photos (
            photo_id CHAR(36) NOT NULL PRIMARY KEY,
            profile_id CHAR(36) NOT NULL,
            url VARCHAR(2048) NOT NULL,
            is_primary BOOLEAN NOT NULL DEFAULT FALSE,
            uploaded_at DATETIME(6) NOT NULL,
            description TEXT,
            created_at DATETIME(6) NOT NULL,
            updated_at DATETIME(6) NOT NULL,
            INDEX idx_photos_profile_id (profile_id)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        """
        with self.engine.begin() as conn:
            conn.execute(text(ddl))

    def _row_to_photo(self, row: Dict) -> PhotoRead:
        return PhotoRead(
            photo_id=row["photo_id"],
            profile_id=row["profile_id"],
            url=row["url"],
            is_primary=bool(row["is_primary"]),
            uploaded_at=row["uploaded_at"],
            description=row.get("description"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ----------------------------
    # Queries
    # ----------------------------
    def list_by_profile(self, profile_id: str) -> List[PhotoRead]:
        if not self.engine:
            return [
                self._row_to_photo(record)
                for record in self._memory.values()
                if record["profile_id"] == profile_id
            ]

        with self.engine.begin() as conn:
            rows = conn.execute(
                text("SELECT * FROM photos WHERE profile_id = :profile_id ORDER BY created_at ASC"),
                {"profile_id": profile_id},
            ).mappings().all()
            return [self._row_to_photo(row) for row in rows]

    def get(self, photo_id: str) -> Optional[PhotoRead]:
        if not self.engine:
            record = self._memory.get(photo_id)
            return self._row_to_photo(record) if record else None

        with self.engine.begin() as conn:
            row = conn.execute(
                text("SELECT * FROM photos WHERE photo_id = :photo_id"),
                {"photo_id": photo_id},
            ).mappings().first()
            return self._row_to_photo(row) if row else None

    # ----------------------------
    # Mutations
    # ----------------------------
    def create(self, payload: PhotoCreate) -> PhotoRead:
        now = datetime.utcnow()
        photo_id = str(uuid4())
        record = {
            "photo_id": photo_id,
            "profile_id": str(payload.profile_id),
            "url": payload.url,
            "is_primary": bool(payload.is_primary),
            "uploaded_at": payload.uploaded_at or now,
            "description": payload.description,
            "created_at": now,
            "updated_at": now,
        }

        if not self.engine:
            # enforce single primary per profile in memory
            if record["is_primary"]:
                for r in self._memory.values():
                    if r["profile_id"] == record["profile_id"]:
                        r["is_primary"] = False
            self._memory[photo_id] = record
            return self._row_to_photo(record)

        with self.engine.begin() as conn:
            if record["is_primary"]:
                conn.execute(
                    text("UPDATE photos SET is_primary = FALSE WHERE profile_id = :pid"),
                    {"pid": record["profile_id"]},
                )
            conn.execute(
                text(
                    """
                    INSERT INTO photos (
                        photo_id, profile_id, url, is_primary, uploaded_at, description, created_at, updated_at
                    ) VALUES (
                        :photo_id, :profile_id, :url, :is_primary, :uploaded_at, :description, :created_at, :updated_at
                    )
                    """
                ),
                record,
            )
            row = conn.execute(
                text("SELECT * FROM photos WHERE photo_id = :photo_id"),
                {"photo_id": photo_id},
            ).mappings().first()
            return self._row_to_photo(row)

    def update(self, photo_id: str, update: PhotoUpdate) -> Optional[PhotoRead]:
        now = datetime.utcnow()
        if not self.engine:
            record = self._memory.get(photo_id)
            if not record:
                return None
            data = update.model_dump(exclude_unset=True)
            if not data:
                return self._row_to_photo(record)
            if data.get("is_primary"):
                # clear other primaries
                for r in self._memory.values():
                    if r["profile_id"] == record["profile_id"]:
                        r["is_primary"] = False
            for field, value in data.items():
                record[field] = value
            record["updated_at"] = now
            return self._row_to_photo(record)

        data = update.model_dump(exclude_unset=True)
        if not data:
            return self.get(photo_id)

        with self.engine.begin() as conn:
            if data.get("is_primary"):
                # unset other primary photos for this profile
                conn.execute(
                    text(
                        "UPDATE photos SET is_primary = FALSE WHERE profile_id = (SELECT profile_id FROM photos WHERE photo_id = :pid)"
                    ),
                    {"pid": photo_id},
                )

            set_clauses = [f"{field} = :{field}" for field in data.keys()]
            set_clauses.append("updated_at = :updated_at")
            params = {**data, "photo_id": photo_id, "updated_at": now}

            conn.execute(
                text(f"UPDATE photos SET {', '.join(set_clauses)} WHERE photo_id = :photo_id"),
                params,
            )
            row = conn.execute(
                text("SELECT * FROM photos WHERE photo_id = :photo_id"),
                {"photo_id": photo_id},
            ).mappings().first()
            return self._row_to_photo(row) if row else None

    def delete(self, photo_id: str) -> bool:
        if not self.engine:
            if photo_id in self._memory:
                self._memory.pop(photo_id)
                return True
            return False

        with self.engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM photos WHERE photo_id = :photo_id"),
                {"photo_id": photo_id},
            )
            return result.rowcount > 0
