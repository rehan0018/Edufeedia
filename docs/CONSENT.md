# Parental Consent Architecture & Single Source of Truth

## 1. Overview & Statutory Requirements

Edufeedia implements verifiable parental consent designed in alignment with the **Digital Personal Data Protection Act (DPDP Act, India, 2023 §9)** and the **Children's Online Privacy Protection Act (COPPA)**.

For users under the age of 18, verifiable parental/guardian consent is mandatory before processing personal data or permitting access to interactive AI features (e.g., Socratic AI Tutor, voice input, or personalized analytics tracking).

---

## 2. Single Source of Truth: `ConsentService`

To prevent diverging or redundant consent verification pathways across the codebase, **`app.core.consent_service.ConsentService`** serves as the **sole authoritative subsystem** for evaluating, granting, and revoking consent.

All authorization enforcement policies (such as `AccessPolicy.has_consent` in `app.core.authorization`) delegate directly to `ConsentService.verify_consent()`.

### Core Architectural Principles:
1. **Delegation over Duplication**: No router or middleware should query `ParentalConsentLog` or `ConsentRecord` directly for access decisions. All checks must call `ConsentService.verify_consent(db, student_id, purpose)`.
2. **Fail-Closed Default**: If no active, verified consent record exists for the requested purpose, the request is denied (`403 Forbidden` / `consent_required`).
3. **Purpose-Specific Scoping**: Consent is granularly tracked by purpose:
   - `ProcessingPurpose.CURRICULUM_ACCESS`
   - `ProcessingPurpose.AI_SOCRATIC_TUTOR`
   - `ProcessingPurpose.ANALYTICS_TRACKING`
   - `ProcessingPurpose.VOICE_MULTIMODAL`
4. **Immediate Revocation Propagation**: When a guardian revokes consent via `/api/v1/privacy/revoke-consent`, `ConsentService.revoke_consent()` marks records revoked and clears any cached permissions, ensuring immediate downstream restriction.
5. **Audited Hash-Chained Logs**: Every consent grant and revocation writes an immutable audit record in `ParentalConsentLog` with verification metadata (OTP, timestamp, IP hash).

---

## 3. Usage Reference for Contributors

### Verifying Consent in Endpoints / Policies
```python
from app.core.consent_service import ConsentService
from app.core.age_policy import ProcessingPurpose

# Authoritative consent check
has_consent = ConsentService.verify_consent(
    db=db,
    student_id=student_user.id,
    purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR.value
)

if not has_consent:
    raise HTTPException(
        status_code=403,
        detail="Verifiable parental consent required for AI tutoring services."
    )
```

### Granting Consent via Verified Guardian OTP
```python
from app.core.consent_service import ConsentService

ConsentService.grant_consent(
    db=db,
    student_id=student_id,
    guardian_id=guardian_user_id,
    purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR.value,
    scope="ai_socratic_tutoring"
)
```
