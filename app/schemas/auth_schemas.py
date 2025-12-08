"""
Authentication schemas
"""
from pydantic import BaseModel, EmailStr, Field, field_validator


class SignUpRequest(BaseModel):
    """Sign up request schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        if len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v.strip()) > 50:
            raise ValueError('Username must be at most 50 characters')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 72:
            raise ValueError('Password must be at most 72 characters')
        return v


class SignInRequest(BaseModel):
    """Sign in request schema"""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


class AuthResponse(BaseModel):
    """Authentication response schema"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UpdateProfileRequest(BaseModel):
    """Update profile request"""
    username: str | None = Field(None, min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    current_password: str | None = Field(None, min_length=1, max_length=72)
    new_password: str | None = Field(None, min_length=6, max_length=72)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Username cannot be empty')
        if len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v.strip()) > 50:
            raise ValueError('Username must be at most 50 characters')
        return v.strip()

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if v is None:
            return v
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters')
        if len(v) > 72:
            raise ValueError('New password must be at most 72 characters')
        return v


class DeleteAccountRequest(BaseModel):
    """Delete account request"""
    current_password: str = Field(..., min_length=1, max_length=72)

