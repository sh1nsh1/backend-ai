from fastapi import APIRouter, Request

from logger import get_logger
from rate_limiter import limiter
from schemas import ContactRequest
from services.ai_service import AIServiceDep
from services.email_service import EmailServiceDep
from services.metrics_service import MetricsServiceDep

logger = get_logger(__name__)

router = APIRouter(prefix="/api")


@router.get("/health")
async def health_check():
    logger.info("Health check")
    return {"healthy": True}


@router.get("/metrics")
async def metrics(metrics_service: MetricsServiceDep):
    logger.info("Metrics requested")
    return await metrics_service.get_metrics()


@router.post("/contact")
@limiter.limit("3/minute")
async def contact(
    request: Request,
    contact_request: ContactRequest,
    email_service: EmailServiceDep,
    ai_service: AIServiceDep,
    metrics_service: MetricsServiceDep,
):
    logger.info(f"Received contact request from {contact_request.email}")

    ai_analysis = await ai_service.analyze_contact(
        name=contact_request.name,
        email=contact_request.email,
        message=contact_request.message,
    )
    logger.info(
        "AI analysis: %s / %s", ai_analysis["category"], ai_analysis["sentiment"]
    )

    await email_service.send_email(
        name=contact_request.name,
        phone=contact_request.phone,
        email=contact_request.email,
        comment=contact_request.message,
        ai_analysis=ai_analysis,
    )

    await metrics_service.track_request("contact")
    return {
        "message": "Contact request sent successfully",
        "analysis": ai_analysis,
    }
