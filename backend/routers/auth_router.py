"""
AEGIS-OS Auth Router — JWT Login, Refresh, and User Management.
"""
from datetime import timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, EmailStr

from auth.jwt_handler import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user
)
from auth.audit import audit_logger
from config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Schemas ──────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class RefreshRequest(BaseModel):
    refresh_token: str

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = None
    role: str = "investigator"


# ─── In-memory user store (replace with DB in production) ─────────────────────
# Default accounts for development
_USERS: Dict[str, Dict] = {
    "admin@aegis.gov": {
        "id": "admin-001",
        "email": "admin@aegis.gov",
        "full_name": "AEGIS Administrator",
        "role": "admin",
        "department": "Forensics HQ",
        "badge_number": "ADM-001",
        "hashed_password": hash_password("Admin@aegis123"),
        "is_active": True,
    },

}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request = None):
    """Authenticate and return JWT tokens."""
    user = _USERS.get(request.email.lower())
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account deactivated.")

    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "full_name": user["full_name"],
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user["id"], "email": user["email"]})

    user_out = {k: v for k, v in user.items() if k != "hashed_password"}

    audit_logger.log_sync("LOGIN", "auth", user["id"], user["email"])
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user_out)


@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    """Refresh access token using refresh token."""
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type.")
    new_access = create_access_token({
        "sub": payload["sub"],
        "email": payload["email"],
        "role": payload.get("role", "viewer"),
    })
    return {"access_token": new_access, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    """Get current user profile."""
    user = _USERS.get(current_user.get("email", ""))
    if not user:
        return current_user
    return {k: v for k, v in user.items() if k != "hashed_password"}


@router.post("/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """Logout (client should discard token)."""
    audit_logger.log_sync("LOGOUT", "auth", current_user.get("sub"), current_user.get("email"))
    return {"message": "Logged out successfully."}


@router.post("/users", dependencies=[])
async def create_user(body: UserCreate):
    """Create a new user (admin only in production)."""
    import uuid
    if body.email in _USERS:
        raise HTTPException(status_code=409, detail="User already exists.")
    user = {
        "id": str(uuid.uuid4()),
        "email": body.email,
        "full_name": body.full_name,
        "role": body.role,
        "department": body.department,
        "badge_number": body.badge_number,
        "hashed_password": hash_password(body.password),
        "is_active": True,
    }
    _USERS[body.email] = user
    return {k: v for k, v in user.items() if k != "hashed_password"}


@router.get("/users")
async def list_users(current_user: Dict = Depends(get_current_user)):
    """List all users (admin/lead only)."""
    return [
        {k: v for k, v in u.items() if k != "hashed_password"}
        for u in _USERS.values()
    ]
