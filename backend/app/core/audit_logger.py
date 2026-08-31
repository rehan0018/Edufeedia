"""
Persistent Security & Access Audit Logging Service.
Logs all sensitive access, parent-child record views, authorization checks, and security rejections.
Enforces cryptographic hash chaining to guarantee tamper-evident audit trails.
"""

import hashlib
import logging
import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import Request

from app.models.models import AuditEvent, User

logger = logging.getLogger("edufeedia.audit")

GENESIS_HASH = "0" * 64


class AuditLogger:
    """
    Centralized service to record persistent, tamper-evident audit events into the database.
    Each event mathematically commits to the SHA-256 hash of the preceding event.
    """

    @staticmethod
    def _extract_safe_ip(request: Optional[Request]) -> Optional[str]:
        """Safely extracts client IP address without naively trusting spoofed forward headers."""
        if not request:
            return None
        # In standard local/dev environment, rely directly on connection socket
        if request.client and request.client.host:
            raw_ip = request.client.host
            return raw_ip
        return None

    @staticmethod
    def _hash_ip(ip_address: Optional[str]) -> Optional[str]:
        if not ip_address:
            return None
        return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _format_timestamp_utc(dt: Optional[datetime.datetime]) -> str:
        if not dt:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def compute_event_hash(
        cls,
        previous_hash: str,
        sequence_number: int,
        actor_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        status: str,
        timestamp_iso: str
    ) -> str:
        """Computes deterministic SHA-256 digest over sequence number, event payload, and parent hash."""
        payload = f"{previous_hash}|{sequence_number}|{actor_id or ''}|{action}|{resource_type}|{resource_id or ''}|{status}|{timestamp_iso}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

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
        Creates and persists an AuditEvent record chained to the last recorded event with sequential ordering.
        """
        raw_ip = cls._extract_safe_ip(request)
        ip_hash = cls._hash_ip(raw_ip)

        resolved_school_id = school_id or (actor.school_id if actor else None)
        actor_id = actor.id if actor else None
        actor_role = actor.role if actor else None
        now = datetime.datetime.now(datetime.timezone.utc)
        now_ts = cls._format_timestamp_utc(now)

        # Retrieve previous event for sequence and block chaining
        last_event = db.query(AuditEvent).order_by(AuditEvent.sequence_number.desc(), AuditEvent.id.desc()).first()
        prev_hash = last_event.event_hash if (last_event and last_event.event_hash) else GENESIS_HASH
        seq_num = (last_event.sequence_number + 1) if (last_event and last_event.sequence_number) else 1

        event_hash = cls.compute_event_hash(
            previous_hash=prev_hash,
            sequence_number=seq_num,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            timestamp_iso=now_ts
        )

        event = AuditEvent(
            sequence_number=seq_num,
            previous_event_hash=prev_hash,
            event_hash=event_hash,
            actor_id=actor_id,
            actor_role=actor_role,
            school_id=resolved_school_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            reason=reason,
            ip_hash=ip_hash,
            timestamp=now
        )
        try:
            db.add(event)
            db.commit()
            db.refresh(event)
        except Exception as e:
            logger.error(f"[AUDIT LOGGING FAILURE] Could not persist audit event: {e}")
            db.rollback()

        logger.info(
            f"[AUDIT] Seq: {seq_num} | Action: {action} | Status: {status} | Actor: {actor_id} ({actor_role}) | "
            f"Resource: {resource_type}/{resource_id} | Hash: {event_hash[:12]}..."
        )
        return event

    @classmethod
    def verify_chain_integrity(cls, db: Session) -> Dict[str, Any]:
        """
        Validates the entire chronological audit trail. Returns True if all cryptographic hashes match.
        """
        events = db.query(AuditEvent).order_by(AuditEvent.sequence_number.asc(), AuditEvent.id.asc()).all()
        if not events:
            return {"is_valid": True, "total_events_checked": 0, "violations": []}

        expected_prev_hash = GENESIS_HASH
        expected_seq = 1
        violations = []

        for idx, ev in enumerate(events):
            if ev.previous_event_hash != expected_prev_hash:
                violations.append({
                    "event_id": ev.id,
                    "sequence_number": ev.sequence_number,
                    "index": idx,
                    "error": "PREVIOUS_HASH_MISMATCH",
                    "stored_prev": ev.previous_event_hash,
                    "expected_prev": expected_prev_hash
                })

            ts_iso = cls._format_timestamp_utc(ev.timestamp)
            recomputed_hash = cls.compute_event_hash(
                previous_hash=ev.previous_event_hash or GENESIS_HASH,
                sequence_number=ev.sequence_number or (idx + 1),
                actor_id=ev.actor_id,
                action=ev.action,
                resource_type=ev.resource_type,
                resource_id=ev.resource_id,
                status=ev.status,
                timestamp_iso=ts_iso
            )
            if ev.event_hash != recomputed_hash:
                violations.append({
                    "event_id": ev.id,
                    "sequence_number": ev.sequence_number,
                    "index": idx,
                    "error": "EVENT_HASH_CORRUPTED",
                    "stored_hash": ev.event_hash,
                    "recomputed_hash": recomputed_hash
                })

            expected_prev_hash = ev.event_hash
            expected_seq += 1

        return {
            "is_valid": len(violations) == 0,
            "total_events_checked": len(events),
            "violations": violations
        }
