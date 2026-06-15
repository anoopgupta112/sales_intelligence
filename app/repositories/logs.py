from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models import AgentLog

class AgentLogRepository(BaseRepository[AgentLog]):
    def __init__(self):
        super().__init__(AgentLog)

    async def get_by_workflow_run_id(self, db: AsyncSession, run_id: str) -> List[AgentLog]:
        """Fetch all logs associated with a workflow run."""
        query = select(self.model).where(self.model.workflow_run_id == run_id)
        result = await db.execute(query)
        return list(result.scalars().all())

agent_log_repository = AgentLogRepository()
