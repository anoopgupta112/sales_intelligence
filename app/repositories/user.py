from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models import User

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Fetch user by email."""
        query = select(self.model).where(self.model.email == email)
        result = await db.execute(query)
        return result.scalars().first()

user_repository = UserRepository()
