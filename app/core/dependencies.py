from typing import Annotated
from fastapi import Depends, Header, Cookie
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.core.exceptions import AuthenticationError, AuthorizationError

def get_token_from_header_or_cookie(
    authorization: str | None = Header(default=None),
    session_token: str | None = Cookie(default=None)
) -> str:
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    if session_token:
        return session_token
    raise AuthenticationError("Not authenticated")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header_or_cookie)
) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing user identity")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("Inactive user")
    return user

def require_role(*roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AuthorizationError(f"Access forbidden for role '{current_user.role.value}'")
        return current_user
    return role_checker
