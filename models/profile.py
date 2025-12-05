from __future__ import annotations

from typing import Optional, List, Annotated
from uuid import UUID, uuid4
from datetime import date, datetime
from pydantic import BaseModel, Field, EmailStr, StringConstraints


class ProfileBase(BaseModel):
    first_name: str = Field(
        ...,
        description="Given name.",
        json_schema_extra={"example": "Ada"},
    )
    last_name: str = Field(
        ...,
        description="Family name.",
        json_schema_extra={"example": "Lovelace"},
    )
    email: EmailStr = Field(
        ...,
        description="Primary email address.",
        json_schema_extra={"example": "ada@example.com"},
    )
    phone: Optional[str] = Field(
        None,
        description="Contact phone number in any reasonable format.",
        json_schema_extra={"example": "+1-212-555-0199"},
    )
    birth_date: Optional[date] = Field(
        None,
        description="Date of birth (YYYY-MM-DD).",
        json_schema_extra={"example": "1815-12-10"},
    )
    gender: Optional[str] = Field(
        None,
        description="Gender identity.",
        json_schema_extra={"example": "Male"},
    )
    location: Optional[str] = Field(
        None,
        description="General location (city, state, country).",
        json_schema_extra={"example": "New York, NY"},
    )
    bio: Optional[str] = Field(
        None,
        description="Short biography or description.",
        json_schema_extra={"example": "Student at Columbia University studying art history. New to the city and looking for friends!"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "email": "ada@example.com",
                    "phone": "+1-212-555-0199",
                    "birth_date": "1815-12-10",
                    "gender": "female", 
                    "location": "London, UK",
                    "bio": "Dog lover and mathematician."
                }
            ]
        }
    }


class ProfileCreate(ProfileBase):
    """Creation payload for a Profile."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "first_name": "Grace",
                    "last_name": "Hopper",
                    "email": "grace.hopper@navy.mil",
                    "phone": "+1-202-555-0101",
                    "birth_date": "1906-12-09"
                }
            ]
        }
    }


class ProfileUpdate(BaseModel):
    """Partial update for a Profile; supply only fields to change."""
    first_name: Optional[str] = Field(None, json_schema_extra={"example": "Augusta"})
    last_name: Optional[str] = Field(None, json_schema_extra={"example": "King"})
    email: Optional[EmailStr] = Field(None, json_schema_extra={"example": "ada@newmail.com"})
    phone: Optional[str] = Field(None, json_schema_extra={"example": "+44 20 7946 0958"})
    birth_date: Optional[date] = Field(None, json_schema_extra={"example": "1815-12-10"})
    gender: Optional[str] = Field(None, json_schema_extra={"example": "female"})
    location: Optional[str] = Field(None, json_schema_extra={"example": "London, UK"})
    bio: Optional[str] = Field(None, json_schema_extra={"example": "Aspiring founder."})

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"first_name": "Ada", "last_name": "Byron"},
                {"phone": "+1-415-555-0199"},
                {"bio": "Loves hiking and outdoor adventures."}
            ]
        }
    }


class ProfileRead(ProfileBase):
    """Server representation returned to clients."""
    id: UUID = Field(
        default_factory=uuid4,
        description="Server-generated Profile ID.",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    user_id: UUID = Field(
        default_factory=uuid4,
        description="User owner ID for this profile.",
        json_schema_extra={"example": "11111111-2222-4333-8444-555555555555"},
    )
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
                    "id": "99999999-9999-4999-8999-999999999999",
                    "user_id": "11111111-2222-4333-8444-555555555555",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "email": "ada@example.com",
                    "phone": "+1-212-555-0199",
                    "birth_date": "1815-12-10",
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }
