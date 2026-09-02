# Edufeedia REST API Specification (`/api/v1`)

> **Architecture and Proprietary Notice**  
> This document describes proprietary Edufeedia architecture and implementation. It is provided for project transparency, technical review, and contribution purposes, and is subject to the project's [LICENSE](../LICENSE) and [TRADEMARKS.md](../TRADEMARKS.md).

---

All endpoints require JWT Bearer authentication unless explicitly marked **Public**.

---

## 1. Authentication & Session (`/auth`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Public | Public student registration. Strips client `school_id` to `None`. |
| `POST` | `/api/v1/auth/login` | Public | Authenticates via email/password. Checks `account_status == "ACTIVE"`. |
| `POST` | `/api/v1/auth/google` | Public | Validates Google ID token (`aud`, `iss`, `email_verified`). |
| `POST` | `/api/v1/auth/logout` | Authenticated | Revokes current JWT in Redis blacklist with TTL. |
| `GET` | `/api/v1/auth/me` | Authenticated | Returns current authenticated user and role profile. |

---

## 2. Student Learning & Analytics (`/students`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/students/profile` | Student | Retrieves self profile. |
| `PUT` | `/api/v1/students/profile` | Student | Updates board, interests, or learning preferences. |
| `POST` | `/api/v1/students/onboarding` | Student | Completes DOB collection and onboarding transition. |
| `GET` | `/api/v1/students/feed` | Student | Returns personalized daily learning plan with explanations. |
| `GET` | `/api/v1/students/analytics/mastery` | Student | Diagnostic topic mastery report (<60% weak topics). |
| `GET` | `/api/v1/students/analytics/learning-health` | Student | Composite Learning Health Score (0-100) and retention telemetry. |

---

## 3. Socratic AI Tutor & RAG (`/tutor`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/tutor/ask` | AI Gated Student / Staff | Socratic guidance with hybrid RAG, provenance citations, and output safety gate. |

---

## 4. Quizzes & SM-2 Spaced Repetition (`/quizzes`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/quizzes/{quiz_id}` | Student / Teacher | Role-aware schema. Students receive questions with **zero answer leakage**. |
| `POST` | `/api/v1/quizzes/submit` | Student | Submits answers, updates SM-2 schedule, awards first-attempt XP idempotently. |
| `POST` | `/api/v1/quizzes/custom` | Teacher / Admin | Publishes custom classroom assessment. |

---

## 5. Content Discovery & Reporting (`/content`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/content/explore` | Learning Access | Search catalog with age gating, subject, and grade filters. |
| `POST` | `/api/v1/content/progress` | Student | Tracks lesson completion (bounds 0-100%). |
| `POST` | `/api/v1/content/report` | Authenticated | Submits report for moderation (Unsafe, Incorrect, Inappropriate, Broken). |

---

## 6. Parent Portal & Verifiable Consent (`/parents`, `/privacy`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/parents/students` | Parent | List of verified linked children. |
| `GET` | `/api/v1/parents/student/{id}/progress` | Verified Parent | Single child progress, mastery metrics, and consent status. |
| `GET` | `/api/v1/parents/student/{id}/weekly-summary` | Verified Parent | Automated weekly digest reducing continuous manual monitoring. |
| `POST` | `/api/v1/privacy/request-parent-consent` | Student / Parent | Dispatches 6-digit cryptographic OTP to guardian email. |
| `POST` | `/api/v1/privacy/verify-parent-otp` | Parent / Student | Verifies OTP and activates consent in append-oriented audit log. |
| `POST` | `/api/v1/privacy/revoke-consent` | Parent / Admin | Revokes consent, instantly gating student AI tutor access. |

---

## 7. Teacher & Administration (`/teachers`, `/admin`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/teachers/classes` | Assigned Teacher | Roster of assigned classes. |
| `GET` | `/api/v1/teachers/classes/{id}/analytics` | Assigned Teacher | Class accuracy, attendance, and weak topics. |
| `GET` | `/api/v1/teachers/interventions` | Assigned Teacher | Automated alerts for students needing diagnostic help. |
| `GET` | `/api/v1/teachers/moderation-queue` | Staff | Pending content reports from students/guardians. |
| `POST` | `/api/v1/teachers/moderate-report` | Staff | Resolves or dismisses flagged content. |
| `GET` | `/api/v1/admin/records` | School Admin / Super | Multi-tenant scoped database roster inspection. |
| `POST` | `/api/v1/admin/invite-teacher` | School Admin | Tenant-isolated staff invitation. |
