"""Shared email utilities — reusable across skills."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from agent.config import (
    GMAIL_APP_PASSWORD,
    GMAIL_RECIPIENT,
    GMAIL_SMTP_HOST,
    GMAIL_SMTP_PORT,
    GMAIL_USER,
)

logger = logging.getLogger(__name__)


def send_email(subject: str, html_body: str, recipient: str | None = None) -> bool:
    """Send an HTML email via Gmail SMTP.

    Args:
        subject: Email subject line.
        html_body: HTML content for the email body.
        recipient: Override recipient (defaults to config).

    Returns:
        True if sent successfully, False otherwise.
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.error("Gmail credentials not configured in .env file")
        return False

    to_addr = recipient or GMAIL_RECIPIENT or GMAIL_USER

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent to {to_addr}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
