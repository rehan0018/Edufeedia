"""
Persistent Security & Access Audit Logging Service.
Logs all sensitive access, parent-child record views, authorization checks, and security rejections.
"""

import hashlib
import logging
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Request

from app.models.models import AuditEvent, User

logger = logging.getLogger("edufeedia.audit")


class AuditLogger:
    """
    Centralized service to record persistent, immutable audit events into the database.
    """

    @staticmethod
    def _hash_ip(ip_address: Optional[str]) -> Optional[str]:
        if not ip_address:
            return None
        return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def log(
        cls,
        db: Session,
        action: str,
        resource_type: str,
        actor: Optional[User] = None,
        resource_id: Optional[str] = None,
        school_id: Optional[str] = None,
        status: str = "SUCCESS",
        reason: Optional[str] = None,
        request: Optional[Request] = None
    ) -> AuditEvent:
        """
        Creates and persists an AuditEvent record.
        """
        ip_hash = None
        if request and request.client:
            client_ip = request.headers.get("X-Forwarded-For", request.client.host)
            ip_hash = cls._hash_ip(client_ip)

        resolved_school_id = school_id or (actor.school_id if actor else None)
        actor_id = actor.id if actor else None
        actor_role = actor.role if actor else None

        event = AuditEvent(
            actor_id=actor_id,
            actor_role=actor_role,
            school_id=resolved_school_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            reason=reason,
            ip_hash=ip_hash
        )
        try:
            db.add(event)
            db.commit()
            db.refresh(event)
        except Exception as e:
            logger.error(f"[AUDIT LOGGING FAILURE] Could not persist audit event: {e}")
            db.rollback()

        logger.info(
            f"[AUDIT] Action: {action} | Status: {status} | Actor: {actor_id} ({actor_role}) | "
            f"Resource: {resource_type}/{resource_id} | School: {resolved_school_id} | Reason: {reason or 'N/A'}"
        )
        return event
