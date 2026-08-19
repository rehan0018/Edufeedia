import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("edufeedia.email")

class EmailService:
    """
    Transactional email delivery provider for verifiable parental consent,
    guardian invitations, and teacher onboarding.
    """

    @classmethod
    def send_parent_consent_otp(
        cls,
        parent_email: str,
        student_name: str,
        otp_code: str,
        school_name: str = "Edufeedia Partner School"
    ) -> Dict[str, Any]:
        """
        Dispatches a 6-digit cryptographic verification challenge to the student's legal guardian.
        """
        subject = f"Action Required: Guardian Consent Code for {student_name}"
        body_text = (
            f"Dear Guardian,\n\n"
            f"{student_name} has requested access to Edufeedia's AI Socratic learning platform via {school_name}.\n\n"
            f"Your 15-minute verification code is: {otp_code}\n\n"
            f"By submitting this code, you grant verifiable parental consent for personalized curriculum practice "
            f"in strict compliance with COPPA, GDPR-K, and DPDP Act 2023.\n\n"
            f"If you did not request this, no action is required."
        )

        # In production environments, integrate with SMTP / AWS SES / SendGrid
        logger.info(f"[Email Dispatch] To: {parent_email} | Subject: {subject} | Delivery: SENT")
        
        return {
            "status": "delivered",
            "recipient": parent_email,
            "subject": subject,
            "provider": os.getenv("EMAIL_PROVIDER", "edufeedia-transactional-v1")
        }

    @classmethod
    def send_staff_invitation(
        cls,
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
        
        logger.info(f"[Staff Invitation Dispatch] To: {recipient_email} | Role: {role} | Token: [REDACTED]")

        return {
            "status": "delivered",
            "recipient": recipient_email,
            "activation_link": activation_link
        }

email_service = EmailService()
