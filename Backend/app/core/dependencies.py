"""
app.core.dependencies — FastAPI auth & RBAC dependencies.

─────────────────────────────────────────────────────────────────────────────
AUTHENTICATION
─────────────────────────────────────────────────────────────────────────────
get_current_user  → decodes JWT, loads User from DB, raises 401/404 on failure

─────────────────────────────────────────────────────────────────────────────
ROLE-BASED ACCESS CONTROL (RBAC)
─────────────────────────────────────────────────────────────────────────────
The multi-role system means a user can hold more than one role simultaneously.
Access is granted if the user holds ANY of the required roles.

role_required(*roles)  → dependency factory, use for custom combos

Shortcut aliases (pre-built for the three standard roles):
  admin_required        → "admin" only
  freelancer_required   → "freelancer" OR "admin"
  client_or_above       → "client" OR "freelancer" OR "admin"

─────────────────────────────────────────────────────────────────────────────
USAGE IN ROUTE FILES
─────────────────────────────────────────────────────────────────────────────

    from app.core.dependencies import (
        get_current_user,
        role_required,
        admin_required,
        freelancer_required,
        client_or_above,
    )

    # Any authenticated user
    @router.get("/profile")
    def profile(user = Depends(get_current_user)):
        return user

    # Freelancer or admin only
    @router.post("/projects")
    def create(user = Depends(freelancer_required)):
        ...

    # Custom combo
    @router.get("/report")
    def report(user = Depends(role_required("admin", "freelancer"))):
        ...
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.database import get_db
from app.models.user import User

# Points Swagger UI to the login endpoint for the "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Core authentication ───────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the Bearer JWT and return the authenticated User ORM object.

    Flow:
      1. Extract the token from the Authorization header
      2. Decode and validate the JWT signature and expiry
      3. Confirm token type is 'access' (not 'refresh')
      4. Load the user from the database
      5. Confirm the user account is active

    Raises:
      401 — token is missing, malformed, expired, or is a refresh token
      404 — user ID in the token no longer exists in the database
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload    = decode_token(token)
        user_id    = payload.get("sub")
        token_type = payload.get("type")

        # Reject missing subject or wrong token type
        if user_id is None:
            raise credentials_exception
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use an access token, not a refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == int(user_id), User.is_active == True)   # noqa: E712
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found or has been deactivated.",
        )

    return user


# ── RBAC — dependency factory ─────────────────────────────────────────────────

def role_required(*role_names: str):
    """
    Dependency factory — restrict a route to users who hold
    ANY of the specified role names.

    Because users can hold multiple roles simultaneously, this check
    passes as long as there is at least one overlap between the user's
    roles and the required roles.

    Args:
        *role_names: One or more role name strings.
                     Valid values: "admin", "freelancer", "client"

    Returns:
        A FastAPI dependency function that yields the authenticated user
        if the role check passes, or raises HTTP 403 if it fails.

    Example:
        Depends(role_required("admin"))
        Depends(role_required("freelancer", "admin"))
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_role(*role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. "
                    f"Your roles {current_user.role_names} do not include "
                    f"any of the required roles: {list(role_names)}."
                ),
            )
        return current_user

    # Give the inner function a readable name for FastAPI's dependency graph
    _check.__name__ = f"require_{'_or_'.join(role_names)}"
    return _check


# ── Convenience shortcuts ─────────────────────────────────────────────────────
# Import these in route files instead of calling role_required() directly.
# Each one is a valid FastAPI dependency — use with Depends().

def admin_required(
    current_user: User = Depends(role_required("admin")),
) -> User:
    """
    Restrict to **admin** role only.
    Use for platform management endpoints (user list, role assignment, etc.)
    """
    return current_user


def freelancer_required(
    current_user: User = Depends(role_required("freelancer", "admin")),
) -> User:
    """
    Restrict to **freelancer** or **admin** roles.
    Admins are included so they can perform all freelancer actions.
    Use for: creating clients, projects, tasks, invoices, time entries.
    """
    return current_user


def client_or_above(
    current_user: User = Depends(role_required("client", "freelancer", "admin")),
) -> User:
    """
    Allow any authenticated role.
    Equivalent to get_current_user() but with explicit role documentation.
    Use for read-heavy endpoints that all roles can access.
    """
    return current_user