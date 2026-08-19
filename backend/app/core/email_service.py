import os
import smtplib
import socket
import logging
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

logger = logging.getLogger("edufeedia.email")

class EmailService:
    """
    Production transactional email delivery engine.
    Supports real SMTP/STARTTLS/SSL (Amazon SES, SendGrid SMTP, Mailgun, Postmark)
    with structured fallback and provider acceptance tracking.
    """

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
        self.use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ("true", "1", "yes")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "no-reply@edufeedia.com")
        self.from_name = os.getenv("SMTP_FROM_NAME", "Edufeedia Safe Learning Platform")
        self.is_live_configured = bool(self.smtp_host and self.smtp_user and self.smtp_password)

    def _send_real_smtp_email(
        self,
        recipient_email: str,
        subject: str,
        plain_body: str,
        html_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes real socket connection to the upstream SMTP provider (e.g. AWS SES / SendGrid).
        """
        message_id = f"<{uuid.uuid4()}@edufeedia.com>"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = recipient_email
        msg["Message-ID"] = message_id

        part_plain = MIMEText(plain_body, "plain", "utf-8")
        msg.attach(part_plain)

        if html_body:
            part_html = MIMEText(html_body, "html", "utf-8")
            msg.attach(part_html)

        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                if self.use_tls:
                    server.starttls()

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.send_message(msg)
            server.quit()

            logger.info(f"[Live SMTP Delivery Success] To: {recipient_email} | MsgID: {message_id}")
            return {
                "status": "accepted_by_provider",
                "recipient": recipient_email,
                "message_id": message_id,
                "provider": "smtp_live",
                "host": self.smtp_host
            }
        except (smtplib.SMTPException, socket.timeout, socket.error, ConnectionError) as e:
            logger.error(f"[Live SMTP Delivery Failure] To: {recipient_email} | Error: {e}")
            return {
                "status": "delivery_failed",
                "recipient": recipient_email,
                "error": str(e),
                "provider": "smtp_live"
            }

    def send_parent_consent_otp(
        self,
        parent_email: str,
        student_name: str,
        otp_code: str,
        school_name: str = "Edufeedia Partner School"
    ) -> Dict[str, Any]:
        """
        Dispatches a 6-digit cryptographic verification challenge to the legal guardian.
        Uses real SMTP if configured; otherwise explicitly records simulated delivery mode.
        """
        subject = f"Action Required: Guardian Consent Code for {student_name}"
        plain_body = (
            f"Dear Guardian,\n\n"
            f"{student_name} has requested access to Edufeedia's AI Socratic learning platform via {school_name}.\n\n"
            f"Your 15-minute verification code is: {otp_code}\n\n"
            f"By submitting this code, you grant verifiable parental consent for personalized curriculum practice "
            f"in strict compliance with COPPA, GDPR-K, and DPDP Act 2023.\n\n"
            f"If you did not request this, no action is required."
        )

        html_body = (
            f"<div style='font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;'>"
            f"<h2 style='color: #4338ca;'>Edufeedia Safe Learning Platform</h2>"
            f"<p>Dear Guardian,</p>"
            f"<p><strong>{student_name}</strong> has requested access to Edufeedia's AI Socratic learning platform via <strong>{school_name}</strong>.</p>"
            f"<div style='background-color: #f1f5f9; padding: 15px; border-radius: 6px; text-align: center; margin: 20px 0;'>"
            f"<span style='font-size: 28px; font-weight: bold; letter-spacing: 6px; color: #1e293b;'>{otp_code}</span>"
            f"</div>"
            f"<p style='color: #64748b; font-size: 13px;'>This code is valid for 15 minutes. Submitting it provides verifiable consent under COPPA and DPDP Act 2023.</p>"
            f"</div>"
        )

        if self.is_live_configured:
            return self._send_real_smtp_email(parent_email, subject, plain_body, html_body)

        # Explicitly declare development mode simulation
        logger.info(f"[Email Dispatch (Dev Mode)] To: {parent_email} | Subject: {subject} | Mode: simulated_local_dev")
        return {
            "status": "simulated_local_dev",
            "recipient": parent_email,
            "subject": subject,
            "provider": "development_mock",
            "info": "SMTP_HOST not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD for live network delivery."
        }

    def send_staff_invitation(
        self,
        recipient_email: str,
        role: str,
        invitation_token: str,
        school_name: str
    ) -> Dict[str, Any]:
        """
        Dispatches an invitation link for a teacher or school administrator to activate their account.
        """
        activation_link = f"https://edufeedia.com/activate?token={invitation_token}"
        subject = f"Invitation to join {school_name} on Edufeedia ({role.replace('_', ' ').title()})"
        plain_body = (
            f"Hello,\n\n"
            f"You have been invited to join {school_name} on Edufeedia as a {role.replace('_', ' ').title()}.\n\n"
            f"To activate your account and establish your secure credentials, click the link below:\n"
            f"{activation_link}\n\n"
            f"This link expires in 7 days."
        )

        if self.is_live_configured:
            return self._send_real_smtp_email(recipient_email, subject, plain_body)

        logger.info(f"[Staff Invitation Dispatch (Dev Mode)] To: {recipient_email} | Role: {role} | Mode: simulated_local_dev")
        return {
            "status": "simulated_local_dev",
            "recipient": recipient_email,
            "activation_link": activation_link,
            "provider": "development_mock"
        }

email_service = EmailService()
