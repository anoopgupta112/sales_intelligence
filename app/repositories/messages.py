from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models import OutreachMessage

class OutreachMessageRepository(BaseRepository[OutreachMessage]):
    def __init__(self):
        super().__init__(OutreachMessage)

    async def get_by_lead_id(self, db: AsyncSession, lead_id: int) -> List[OutreachMessage]:
        """Fetch outreach messages by lead id."""
        query = select(self.model).where(self.model.lead_id == lead_id)
        result = await db.execute(query)
        return list(result.scalars().all())

message_repository = OutreachMessageRepository()
