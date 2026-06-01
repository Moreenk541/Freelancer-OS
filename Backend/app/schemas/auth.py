"""
Auth schemas.

RegisterSchema  — new account request body
LoginSchema     — login request body
TokenResponse   — single access token (register, refresh)
TokenPair       — access + refresh token pair (login)
RefreshRequest  — refresh token body
"""
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterSchema(BaseModel):
    name:     str      = Field(..., min_length=2,  max_length=120)
    email:    EmailStr
    password: str      = Field(..., min_length=8,  max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        return v


class LoginSchema(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    """Returned by /register and /refresh — access token only."""
    access_token: str
    token_type:   str = "bearer"


class TokenPair(BaseModel):
    """Returned by /login — both tokens."""
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str