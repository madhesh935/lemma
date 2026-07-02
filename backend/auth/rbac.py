"""
AEGIS-OS Role-Based Access Control.
Enforces permissions based on user roles across all resources.
"""
from typing import Dict, Any, List
from fastapi import HTTPException, status, Depends

from auth.jwt_handler import get_current_user
from database.models import UserRole


# ─── Role hierarchy ───────────────────────────────────────────────────────────
ROLE_HIERARCHY = {
    UserRole.admin: 4,
    UserRole.lead_investigator: 3,
    UserRole.investigator: 2,
    UserRole.viewer: 1,
}

# ─── Permission definitions ───────────────────────────────────────────────────
PERMISSIONS: Dict[str, List[str]] = {
    "pod:create": ["admin", "lead_investigator"],
    "pod:read": ["admin", "lead_investigator", "investigator", "viewer"],
    "pod:update": ["admin", "lead_investigator", "investigator"],
    "pod:delete": ["admin"],
    "pod:archive": ["admin", "lead_investigator"],

    "evidence:upload": ["admin", "lead_investigator", "investigator"],
    "evidence:read": ["admin", "lead_investigator", "investigator", "viewer"],
    "evidence:delete": ["admin", "lead_investigator"],

    "agent:invoke": ["admin", "lead_investigator", "investigator"],
    "workflow:start": ["admin", "lead_investigator"],
    "workflow:approve": ["admin", "lead_investigator"],

    "report:generate": ["admin", "lead_investigator", "investigator"],
    "report:approve": ["admin", "lead_investigator"],
    "report:read": ["admin", "lead_investigator", "investigator", "viewer"],

    "user:manage": ["admin"],
    "audit:read": ["admin", "lead_investigator"],
}


def check_permission(user: Dict[str, Any], permission: str) -> None:
    """Raise 403 if user lacks the required permission."""
    user_role = user.get("role", "viewer")
    allowed = PERMISSIONS.get(permission, [])
    if user_role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user_role}' does not have permission: {permission}",
        )


def require_role(*roles: str):
    """FastAPI dependency: require any of the given roles."""
    async def _check(current_user: Dict[str, Any] = Depends(get_current_user)):
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {list(roles)}",
            )
        return current_user
    return _check


def require_permission(permission: str):
    """FastAPI dependency: require a specific permission."""
    async def _check(current_user: Dict[str, Any] = Depends(get_current_user)):
        check_permission(current_user, permission)
        return current_user
    return _check


# ─── Convenience dependencies ─────────────────────────────────────────────────
require_admin = require_role("admin")
require_investigator = require_role("admin", "lead_investigator", "investigator")
require_lead = require_role("admin", "lead_investigator")
require_any = require_role("admin", "lead_investigator", "investigator", "viewer")
