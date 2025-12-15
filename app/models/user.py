"""
User model for authentication
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str


class UserCreate(UserBase):
    """User creation model"""
    password: str


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class User(UserBase):
    """User model"""
    id: Optional[int] = None
    role: Optional[str] = "user"
    created_at: Optional[str] = None  # Stored as ISO format string
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model"""
    email: Optional[str] = None

