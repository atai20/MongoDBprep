from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=24)
    password: str = Field(min_length=8, max_length=128)
    rating: int | None = None

    @field_validator("username")
    @classmethod
    def username_charset(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.replace("_", "").isalnum():
            raise ValueError("username may contain letters, numbers and underscores only")
        return cleaned


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=24)
    password: str = Field(min_length=1, max_length=128)


class RatingUpdateRequest(BaseModel):
    rating: int = Field(ge=1, le=10000)


class CreateLobbyRequest(BaseModel):
    name: str = Field(min_length=3, max_length=40)
    capacity: int = Field(default=4, ge=2, le=8)
