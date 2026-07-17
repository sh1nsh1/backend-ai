from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated, Optional

import aiosmtplib
from fastapi import Depends, HTTPException, status

from config import config
from logger import get_logger

logger = get_logger(__name__)


class EmailService:
    def __init__(self):
        self.SMTP_HOST = config.email.smtp_host
        self.SMTP_PORT = config.email.smtp_port
        self.SMTP_USER = config.email.smtp_user
        self.SMTP_PASSWORD = config.email.smtp_password

    async def _build_message(
        self,
        subject: str,
        text: str,
        from_email: str,
        to_email: str,
    ) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(text, "plain", "utf-8"))
        return msg

    async def send_email(
        self,
        name: str,
        phone: str,
        email: str,
        comment: str,
        ai_analysis: Optional[dict] = None,
    ) -> None:
        logger.info("send_email")
        msg_text = f"Name: {name}\nPhone: {phone}\nEmail: {email}\nComment: {comment}\n"

        if ai_analysis:
            msg_text += (
                f"\n--- AI Analysis ---\n"
                f"Category: {ai_analysis.get('category', 'N/A')}\n"
                f"Sentiment: {ai_analysis.get('sentiment', 'N/A')}\n"
                f"Suggested Reply: {ai_analysis.get('suggested_reply', 'N/A')}\n"
            )

        msg_to_owner = await self._build_message(
            subject=f"Contact ({ai_analysis.get('category', 'New')})"
            if ai_analysis
            else "Contact",
            text=msg_text,
            from_email=self.SMTP_USER,
            to_email=self.SMTP_USER,
        )

        reply = ai_analysis.get("suggested_reply", "") if ai_analysis else ""
        user_text = (
            f"Thank you for your message!\n\n"
            f"We have received your inquiry and will get back to you shortly.\n\n"
            f"---\n"
            f"{reply}"
            if reply
            else (
                "Thank you for your message!\n\n"
                "We have received your inquiry and will get back to you shortly."
            )
        )
        msg_to_sender = await self._build_message(
            subject="We received your message",
            text=user_text,
            from_email=self.SMTP_USER,
            to_email=email,
        )

        try:
            async with aiosmtplib.SMTP(
                hostname=self.SMTP_HOST,
                port=self.SMTP_PORT,
                timeout=15,
                use_tls=True,
            ) as smtp:
                logger.debug("logging in")
                await smtp.login(self.SMTP_USER, self.SMTP_PASSWORD)
                logger.debug("sending to owner")
                await smtp.send_message(msg_to_owner)
                logger.debug("sending to sender")
                await smtp.send_message(msg_to_sender)

        except aiosmtplib.SMTPException as e:
            logger.exception("SMTP error while sending email")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="SMTP error"
            )

        except Exception as e:
            logger.exception("Unexpected error while sending email")
            raise HTTPException(status_code=500, detail="Unexpected error")


EmailServiceDep = Annotated[EmailService, Depends(EmailService)]
