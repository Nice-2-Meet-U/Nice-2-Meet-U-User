from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class PhotoBase(BaseModel):
    photo_id: UUID = Field(
        default_factory=uuid4,
        description="Persistent Photo ID (server-generated).",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    profile_id: UUID = Field(
        ...,
        description="Persistent Profile ID this photo is associated with.",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    url: str = Field(
        ...,
        description="Location of the photo (URL).",
        json_schema_extra={"example": "https://example.com/photos/550e8400-e29b-41d4-a716-446655440000.jpg"},
    )
    is_primary: bool = Field(
        ...,
        description="Indicates if this is the primary photo for the profile.",
        json_schema_extra={"example": "true"},
    )
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the photo was uploaded (UTC).",
        json_schema_extra={"example": "2025-10-18T17:45:23Z"},
    )
    description: Optional[str] = Field(
        None,
        description="Optional description or caption for the photo.",
        json_schema_extra={"example": "A beautiful sunset at the beach."},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "photo_id": "550e8400-e29b-41d4-a716-446655440000",
                    "profile_id": "660e8400-e29b-41d4-a716-446655440000",
                    "url": "https://example.com/photos/550e8400-e29b-41d4-a716-446655440000.jpg",
                    "is_primary": True,
                    "uploaded_at": "2025-10-18T17:45:23Z",
                    "description": "A beautiful sunset at the beach."
                }
            ]
        }
    }


class PhotoCreate(PhotoBase):
    """Creation payload; ID is generated server-side but present in the base model."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "profile_id": "660e8400-e29b-41d4-a716-446655440000",
                    "url": "https://example.com/photos/550e8400-e29b-41d4-a716-446655440000.jpg",
                    "is_primary": True,
                    "description": "A beautiful sunset at the beach."
                }
            ]
        }
    }


class PhotoUpdate(BaseModel):
    """Partial update for a Photo; supply only fields to change."""
    url: Optional[str] = Field(None, json_schema_extra={"example": "https://example.com/photos/new_photo.jpg"})
    is_primary: Optional[bool] = Field(None, json_schema_extra={"example": "false"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "An updated description."})

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"url": "https://example.com/photos/updated_photo.jpg"},
                {"is_primary": False},
                {"description": "An updated description for the photo."}
            ]
        }
    }
    

class PhotoRead(PhotoBase):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC).",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-01-16T12:00:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "photo_id": "550e8400-e29b-41d4-a716-446655440000",
                    "profile_id": "660e8400-e29b-41d4-a716-446655440000",
                    "url": "https://example.com/photos/550e8400-e29b-41d4-a716-446655440000.jpg",
                    "is_primary": True,
                    "uploaded_at": "2025-10-18T17:45:23Z",
                    "description": "A beautiful sunset at the beach.",
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }
