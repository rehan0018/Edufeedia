# Edufeedia Minor Privacy & Consent Architecture 🔒

## 1. Principles of Child Data Protection

Edufeedia is designed with principles inspired by the **Indian Digital Personal Data Protection (DPDP) Act 2023** (Section 9: Processing of personal data of children) and the **United States Children's Online Privacy Protection Act (COPPA)**:

1. **Purpose Limitation**: Personal data is collected solely for curriculum personalization, spaced retention scheduling, and verified academic progress.
2. **Verifiable Parental Consent (VPC)**: Interactive learning and AI tutoring features require verifiable parental confirmation for students under 16/18.
3. **Data Minimization**: Peer leaderboards anonymize user identifiers and mask student names (`R*** S.`).
4. **Append-Oriented Audit Log**: Every consent grant, verification attempt, and revocation is recorded with timestamps, method, and client IP hash in `parental_consent_logs`.
5. **Guardian Right to Revoke**: Parents and school administrators can revoke consent at any time, immediately restricting interactive AI privileges without destroying verified academic records.

---

## 2. Consent State Lifecycle

```
[Google / Public Registration]
             │
             ▼
    PENDING_ONBOARDING
             │
             ▼ (Submit DOB, Grade, Board)
     ONBOARDING_COMPLETE
             │
             ▼ (Evaluate Student Age)
 ┌───────────────────────┴───────────────────────┐
 │ Student Age < 16                              │ Student Age >= 16
 ▼                                               ▼
CONSENT_PENDING (OTP sent to Parent)       CONSENT_EXEMPT (Adult Student)
 │                                               │
 ▼ (Parent Enters OTP)                           │
CONSENT_GRANTED                                  │
 └───────────────────────┬───────────────────────┘
                         │
                         ▼
                   ACTIVE ACCESS
                         │
       (Guardian Revokes via Portal)
                         │
                         ▼
                  CONSENT_REVOKED
            (Interactive AI Restricted)
```
