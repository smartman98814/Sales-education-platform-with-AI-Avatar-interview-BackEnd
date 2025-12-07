"""
Authentication schemas
"""
from pydantic import BaseModel, EmailStr


class SignUpRequest(BaseModel):
    """Sign up request schema"""
    email: EmailStr
    username: str
    password: str


class SignInRequest(BaseModel):
    """Sign in request schema"""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response schema"""
    access_token: str
    token_type: str = "bearer"
    user: dict

