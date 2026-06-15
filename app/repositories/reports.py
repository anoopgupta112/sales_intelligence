from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models import ResearchReport

class ResearchReportRepository(BaseRepository[ResearchReport]):
    def __init__(self):
        super().__init__(ResearchReport)

    async def get_by_lead_id(self, db: AsyncSession, lead_id: int) -> Optional[ResearchReport]:
        """Fetch research report by lead id."""
        query = select(self.model).where(self.model.lead_id == lead_id)
        result = await db.execute(query)
        return result.scalars().first()

report_repository = ResearchReportRepository()
