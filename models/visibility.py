from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional


class VisibilityBase(BaseModel):
    """Shared attributes for all visibility models."""
    is_visible: bool = Field(
        True,
        description="Indicates whether the profile is currently visible.",
        json_schema_extra={"example": True},
    )
    visibility_scope: Optional[str] = Field(
        "normal",
        description="Visibility level (e.g., close, normal, wide).",
        json_schema_extra={"example": "normal"},
    )
    last_toggled_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of when visibility was last updated (UTC).",
        json_schema_extra={"example": "2025-10-18T17:45:23Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_visible": True,
                    "visibility_scope": "normal",
                    "last_toggled_at": "2025-10-18T17:45:23Z",
                }
            ]
        }
    }


class VisibilityCreate(VisibilityBase):
    """Creation payload for visibility record."""
    profile_id: UUID = Field(
        ...,
        description="Profile ID this visibility record belongs to.",
        json_schema_extra={"example": "660e8400-e29b-41d4-a716-446655440000"},
    )


class VisibilityUpdate(BaseModel):
    """Partial update for visibility fields."""
    is_visible: Optional[bool] = Field(
        None,
        description="Set to true/false to toggle visibility.",
        json_schema_extra={"example": False},
    )
    visibility_scope: Optional[str] = Field(
        None,
        description="Update visibility level (e.g., close, normal, wide).",
        json_schema_extra={"example": "close"},
    )
    last_toggled_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Updated automatically on toggle (UTC).",
        json_schema_extra={"example": "2025-10-18T17:45:23Z"},
    )


class VisibilityRead(VisibilityBase):
    """Returned representation of a visibility record."""
    visibility_id: UUID = Field(
        default_factory=uuid4,
        description="Server-generated unique visibility record ID.",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    profile_id: UUID = Field(
        ...,
        description="Profile ID this visibility record belongs to.",
        json_schema_extra={"example": "660e8400-e29b-41d4-a716-446655440000"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "visibility_id": "550e8400-e29b-41d4-a716-446655440000",
                    "profile_id": "660e8400-e29b-41d4-a716-446655440000",
                    "is_visible": True,
                    "visibility_scope": "normal",
                    "last_toggled_at": "2025-10-18T17:45:23Z",
                }
            ]
        }
    }