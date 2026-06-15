from typing import List
from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.exceptions import CredentialsException, ForbiddenException
from app.core.security import decode_access_token
from app.db.models import User
from app.repositories.user import user_repository

# OAuth2 Password Bearer definition
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to retrieve and validate the current authenticated user."""
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise CredentialsException()
    
    email = payload["sub"]
    user = await user_repository.get_by_email(db, email)
    if not user:
        raise CredentialsException()
    return user

class RoleChecker:
    """Dependency class to verify users have specific roles (RBAC)."""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenException(f"Role '{current_user.role}' does not have permission for this resource.")
        return current_user
