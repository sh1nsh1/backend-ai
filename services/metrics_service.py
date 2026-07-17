from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from logger import get_logger
from repositories.metrics_repository import MetricsRepository

logger = get_logger(__name__)


class MetricsService:
    def __init__(self, db: AsyncSession):
        self.repo = MetricsRepository(db)

    async def track_request(self, endpoint: str) -> None:
        await self.repo.log_request(endpoint)
        logger.debug("Tracked request for %s", endpoint)

    async def get_metrics(self) -> dict:
        return await self.repo.get_metrics()


async def _get_metrics_service(db: AsyncSession = Depends(get_db)) -> MetricsService:
    return MetricsService(db)


MetricsServiceDep = Annotated[MetricsService, Depends(_get_metrics_service)]
