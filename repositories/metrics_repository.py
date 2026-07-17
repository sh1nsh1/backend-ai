from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import RequestLog


class MetricsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_request(self, endpoint: str) -> None:
        log = RequestLog(endpoint=endpoint, requested_at=datetime.now())
        self.session.add(log)
        await self.session.commit()

    async def get_metrics(self) -> dict:
        total = await self._scalar(select(func.count(RequestLog.id)))

        started_at = await self._scalar(select(func.min(RequestLog.requested_at)))

        last_at = await self._scalar(select(func.max(RequestLog.requested_at)))

        endpoints_result = await self.session.execute(
            select(
                RequestLog.endpoint,
                func.count(RequestLog.id),
                func.max(RequestLog.requested_at),
            ).group_by(RequestLog.endpoint)
        )

        endpoints = {}
        for row in endpoints_result.all():
            endpoints[row[0]] = {
                "count": row[1],
                "last_at": row[2].isoformat() if row[2] else None,
            }

        return {
            "total_requests": total or 0,
            "endpoints": endpoints,
            "started_at": started_at.isoformat() if started_at else None,
            "last_request_at": last_at.isoformat() if last_at else None,
        }

    async def _scalar(self, stmt):
        result = await self.session.execute(stmt)
        return result.scalar()
