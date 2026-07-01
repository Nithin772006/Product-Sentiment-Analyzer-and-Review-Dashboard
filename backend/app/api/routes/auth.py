"""
app/api/routes/auth.py
───────────────────────
User authentication routes (register, login) and JWT security token handlers.
"""

from __future__ import annotations

import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, HTTPException, Depends, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.models.user import UserRegister, UserLogin, Token
from app.repositories.user_repository import UserRepository
from app.config.settings import get_settings
from app.utils.bson import format_response

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# Token Configuration
JWT_SECRET = get_settings().secret_key
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 600


# ── Password Hashing Helpers ──────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-SHA256."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_b64 = base64.b64encode(pwd_hash).decode("utf-8")
    return f"{salt_b64}:{hash_b64}"


def verify_password(password: str, hashed_str: str) -> bool:
    """Verify password against pbkdf2 hash."""
    try:
        salt_b64, hash_b64 = hashed_str.split(":")
        salt = base64.b64decode(salt_b64)
        expected_hash = base64.b64decode(hash_b64)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return pwd_hash == expected_hash
    except Exception:
        return False


# ── JWT Security Helpers ──────────────────────────────────────────────────────

def create_access_token(username: str, role: str) -> str:
    """Generate JWT Access Token."""
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(tz=timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Dependency: Extract and verify JWT token to identify current user."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims"
            )
        
        # Check database
        repo = UserRepository()
        user = await repo.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer exists"
            )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials token"
        )


def check_admin_role(user: dict = Depends(get_current_user)) -> dict:
    """Dependency: Restrict route to admins only."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )
    return user


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=dict)
async def register_user(
    payload: UserRegister = Body(...)
) -> dict:
    """
    Register a new user account.
    """
    repo = UserRepository()
    username = payload.username.strip()
    
    existing = await repo.get_by_username(username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash and save
    pwd_hash = hash_password(payload.password)
    role = payload.role if payload.role in ["admin", "user"] else "user"
    
    try:
        new_user = await repo.create_user(username, pwd_hash, role)
        return format_response(
            success=True,
            message="Registration successful",
            data={
                "username": new_user["username"],
                "role": new_user["role"],
                "created_at": new_user["created_at"]
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(exc)}")


@router.post("/login")
async def login_user(
    payload: UserLogin = Body(...)
) -> dict:
    """
    Log in with username and password to generate a JWT token.
    """
    repo = UserRepository()
    user = await repo.get_by_username(payload.username)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Generate token
    token = create_access_token(user["username"], user["role"])
    
    return format_response(
        success=True,
        message="Login successful",
        data={
            "access_token": token,
            "token_type": "bearer",
            "username": user["username"],
            "role": user["role"]
        }
    )
