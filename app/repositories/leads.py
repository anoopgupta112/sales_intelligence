from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models import Lead

class LeadRepository(BaseRepository[Lead]):
    def __init__(self):
        super().__init__(Lead)

    async def get_by_company_name(self, db: AsyncSession, company_name: str) -> Optional[Lead]:
        """Fetch a lead by company name."""
        query = select(self.model).where(self.model.company_name == company_name)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_status(self, db: AsyncSession, status: str) -> List[Lead]:
        """Fetch leads filtered by status."""
        query = select(self.model).where(self.model.status == status)
        result = await db.execute(query)
        return list(result.scalars().all())

lead_repository = LeadRepository()
