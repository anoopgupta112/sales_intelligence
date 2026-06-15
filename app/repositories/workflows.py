from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models import WorkflowRun

class WorkflowRunRepository(BaseRepository[WorkflowRun]):
    def __init__(self):
        super().__init__(WorkflowRun)

    async def get_active_runs(self, db: AsyncSession) -> list[WorkflowRun]:
        """Fetch all running or paused workflows."""
        query = select(self.model).where(self.model.status.in_(["RUNNING", "AWAITING_REVIEW"]))
        result = await db.execute(query)
        return list(result.scalars().all())

workflow_run_repository = WorkflowRunRepository()
