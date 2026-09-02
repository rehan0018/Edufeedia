# Edufeedia Minor Privacy & Consent Architecture

> **Architecture and Proprietary Notice**  
> This document describes proprietary Edufeedia architecture and implementation. It is provided for project transparency, technical review, and contribution purposes, and is subject to the project's [LICENSE](../LICENSE) and [TRADEMARKS.md](../TRADEMARKS.md).

---

## 1. Principles of Child Data Protection

Edufeedia is designed with principles inspired by the **Indian Digital Personal Data Protection (DPDP) Act 2023** (Section 9: Processing of personal data of children) and the **United States Children's Online Privacy Protection Act (COPPA)**:

1. **Purpose-Specific Consent**: Data processing activities are decoupled by `ProcessingPurpose` (AI Tutoring, Personalized Recommendations, Formative Tracking, Safety Monitoring, School Administration). Guardian consent requirements are evaluated per purpose rather than applying a single monolithic rule.
2. **Statutory Child Definition Alignment**: Under the DPDP framework, students under 18 years of age require verifiable guardian consent for interactive AI tutoring and non-essential algorithmic processing.
3. **Data Minimization**: Peer leaderboards anonymize user identifiers and mask student names (`R*** S.`).
4. **Append-Oriented Audit Log**: Every consent grant, verification attempt, purpose scope change, and revocation is recorded with timestamps, method, and hashed client IP fingerprint in `parental_consent_logs` / `audit_events`.
5. **Guardian Right to Revoke**: Parents and school administrators can revoke consent at any time, immediately invalidating cached recommendation sessions and restricting interactive AI privileges without destroying verified academic transcripts.

---

## 2. Purpose-Specific Consent Lifecycle

```
[Student Registration (Ages 10-17)]
             │
             ▼
    PENDING_ONBOARDING
             │
             ▼ (Submit DOB, Grade Level, School)
    ONBOARDING_COMPLETE
             │
             ▼ (Evaluate Purpose-Specific Legal Basis)
 ┌───────────────────────────────────────────────────────────┐
 │ Interactive AI Tutoring / Algorithmic Personalization     │
 └─────────────────────────────┬─────────────────────────────┘
                               │
                               ▼ (Minor Under 18)
                 CONSENT_PENDING_VERIFICATION
                 (Cryptographic OTP to Guardian Email)
                               │
                               ▼ (Guardian Submits OTP)
                        CONSENT_GRANTED
                               │
                               ▼
                         ACTIVE ACCESS
                               │
                 (Guardian Revokes via Portal)
                               │
                               ▼
                        CONSENT_REVOKED
                 (Interactive AI Restricted;
                  Essential School Tasks Preserved)
```

---

## 3. Student Privacy Notice and Legal Disclaimer

Edufeedia is designed with student-data privacy as a core engineering principle. The platform is developed with consideration for applicable privacy and child-safety requirements, including principles of India's Digital Personal Data Protection (DPDP) framework and parental-consent safeguards relevant to the US Children's Online Privacy Protection Act (COPPA).

This technical specification describes the project's design principles and technical safeguards. It does not by itself constitute a legal determination or formal certification of statutory compliance under any specific jurisdiction's legal framework. Production deployments targeting minors should be validated by qualified legal counsel.
