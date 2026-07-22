"""
app/api/deps.py
───────────────
Shared FastAPI dependencies:
  - get_current_user(): validates JWT and returns user payload
  - get_db(): re-exported from database module
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings
from app.database import get_db  # re-export for convenience

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


class UserPayload:
    """Minimal user object extracted from the JWT."""

    def __init__(self, user_id: str, email: str | None = None):
        self.user_id = user_id
        self.email = email


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserPayload:
    """
    Validate JWT Bearer token and return the user payload.

    MVP note: For development, if JWT_SECRET is still 'change-me',
    a hardcoded demo user is returned so the frontend can work without auth.
    """
    # ── Dev bypass: allow working without a real token ────────────────────────
    if settings.jwt_secret == "change-me":
        return UserPayload(user_id="demo_user_001", email="demo@mindmap.local")

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Authorization header missing"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise ValueError("Missing 'sub' in token")
        return UserPayload(user_id=user_id, email=payload.get("email"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Invalid or expired token"},
        )


# Re-export for cleaner imports in route files
__all__ = ["get_current_user", "get_db", "UserPayload"]
