# Edufeedia Technical Architecture & System Design

> **Architecture and Proprietary Notice**  
> This document describes proprietary Edufeedia architecture and implementation. It is provided for project transparency, technical review, and contribution purposes, and is subject to the project's [LICENSE](../LICENSE) and [TRADEMARKS.md](../TRADEMARKS.md).

---

## 1. Architectural Principles

Edufeedia is engineered around fundamental design invariants:
1. **Minor Safety Fail-Closed**: Any anomaly, timeout, or ambiguity in safety evaluation defaults to immediate access restriction and pedagogical deflection.
2. **Tenant & Identity Isolation**: School districts, academies, teachers, parents, and students operate within strict cryptographically and relationally enforced boundaries.
3. **Decoupled Verification vs. Consent**: Identity confirmation (`email_verified`, `identity_verified`) is explicitly separated from legal guardian consent (`parental_consent_status`).
4. **Pedagogical Socratic Scaffolding**: Knowledge retrieval prioritizes step-by-step conceptual guidance over direct answer feeding.
5. **Active Recall & Spaced Retention**: Feed personalization optimizes for long-term retention via SuperMemo-2 (SM-2) scheduling rather than vanity engagement metrics.
6. **Anti-IDOR Server-Derived Identity**: The backend never accepts client-provided user IDs for student queries, progress tracking, or AI interactions—identity is strictly derived from verified JWT authentication tokens.

---

## 2. 3-Tier Access Hierarchy

Edufeedia operates on a strictly separated three-tier authorization and governance model:

```
+=================================================================================+
| LEVEL 3: INFRASTRUCTURE & CLOUD ADMIN |
| - AWS / RDS / CloudWatch / VPC / KMS / Docker Host Access |
| - Direct database administration, encryption keys, and backup management |
+=================================================================================+
 │
+=================================================================================+
| LEVEL 2: PLATFORM SUPER-ADMIN |
| - Cross-tenant system auditing & global curriculum management |
| - Platform-wide safety policy tuning & AI model failover controls |
| - Immutable audit log review (AccessPolicy.log_violation) |
+=================================================================================+
 │
+=================================================================================+
| LEVEL 1: END-USER APPLICATION ROLES |
| |
| ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌─────────┐ |
| │ School Admin │ │ Teacher │ │ Parent │ │ Student │ |
| │ (Single School │ │ (Assigned School │ │(Linked Children │ │(Private │ |
| │ Tenant Only) │ │ Classes Only) │ │ Records Only) │ │Data Only│ |
| └──────────────────┘ └──────────────────┘ └──────────────────┘ └─────────┘ |
+=================================================================================+
```

### Level 1: Application Roles & Scopes
- **Student**: Operates strictly within their own private scope (`User.id == current_user.id`). Can view their own dashboard, recommendations, progress, and AI tutor interactions. Cannot view peer students or access staff tools.
- **Parent**: Permitted access solely to verified linked children via the `parent_student_links` join table. Can grant/revoke consent, view child learning progress, and request data export or erasure.
- **Teacher**: Restricted to classes they are actively assigned to via the `teacher_classes` join table. Can create assignments, monitor class analytics, and view student progress within their assigned sections.
- **School Administrator**: Bound to their specific educational institution (`current_user.school_id`). Can invite teachers, manage school classes, and view aggregate school metrics. Strictly barred from cross-school tenant data.

### Level 2: Platform Super-Administrator
- Role-gated via `RoleChecker(["super_admin"])`.
- Authorized to inspect cross-tenant health, manage curriculum categories, and audit system-wide security logs.
- All super-admin administrative actions are written to immutable structured audit logs with actor identity and timestamp.

### Level 3: Infrastructure & Cloud Administrator
- Enforced at the cloud network and IAM policy level (AWS IAM, VPC security groups, database TLS/SSL connections, KMS encryption keys).
- Access to raw database storage, migration scripts, and Redis infrastructure.

---

## 3. Anti-IDOR & Server-Derived Identity Architecture

To eliminate Insecure Direct Object Reference (IDOR) vulnerabilities:

```
Client Request
 │
 ▼
[ 1. JWT Authentication Layer ]
 │ Extracts Bearer Token -> Decodes & validates signature -> Resolves current_user
 ▼
[ 2. Identity Binding ]
 │ NEVER accepts ?student_id= or { "student_id": ... } in student-facing endpoints.
 │ student_user_id is HARDCODED to current_user.id on the server.
 ▼
[ 3. Access Policy Engine (app.core.access_policy) ]
 │ - Student: Is caller modifying their own data? (Yes -> Allow)
 │ - Parent: Is student linked in parent_student_links? (Yes -> Allow, No -> 403)
 │ - Teacher: Is class assigned in teacher_classes? (Yes -> Allow, No -> 403)
 │ - School Admin: Does class/student match caller school_id? (Yes -> Allow, No -> 403)
 ▼
[ 4. Scoped Database Query & Minimum Data Return ]
```

---

## 4. Environment-Segregated Seeding Architecture

Edufeedia strictly separates production curriculum bootstrapping from local mock demo data:

| Script Path | Target Environment | Data Seeded | Fake Users / Progress Seeded? |
| :--- | :--- | :--- | :--- |
| `backend/scripts/seed_curriculum.py` | **Production & Staging** | NCERT/CBSE educational items, dense 384-d semantic embeddings, flashcards, standard quizzes | **Zero fake users or student progress** |
| `backend/scripts/seed_demo_data.py` | **Local Dev & CI Tests** | Full mock ecosystem: Apex International School, Classes 10A/10B, sample students (Rahul, Priya), teachers, parents, mock quiz attempts | Seeded for local test coverage |
| `backend/scripts/create_admin.py` | **Production Bootstrap** | Interactive/CLI utility to securely provision the initial Super Admin or School Admin account with bcrypt hashing | Non-synthetic verified admin |

---

## 5. Component Topology

```
+-------------------------------------------------------------------------------+
| Client Tier |
| Next.js 14 / React SPA | Socratic AI Chat | Adaptive Feed | Portals |
+---------------------------------------+---------------------------------------+
 | HTTPS / REST + SSE
+---------------------------------------v---------------------------------------+
| API Gateway Tier |
| - Correlation ID Tracing (`X-Request-ID`, `X-Response-Time-MS`) |
| - Centralized Access Policy Engine (`app.core.access_policy`) |
| - Rate Limiting & Sliding Window Token Bucket |
| - Multi-Tenant Role-Based Access Control (RBAC) |
+---------------------------------------+---------------------------------------+
 |
 +---------------------------------+--------------------------------+
 | | |
+-----v---------------+ +---------v---------+ +---------v---------+
| Socratic AI Engine | | Recommendation | | Content Pipeline |
| - Hybrid Dense+BM25 | | - Hybrid Scoring | | - Verified Sources|
| - Model Gateway | | - SM-2 Spaced Rep | | - SHA-256 Dedup |
| - Safety Hard Gates | | - Explainability | | - Educator Review |
+-----+---------------+ +---------+---------+ +---------+---------+
 | | |
+-----v---------------------------------v--------------------------------v---------+
| Persistence Layer |
| - PostgreSQL 16 + pgvector (384-d semantic vectors) |
| - Redis 7 (Distributed sessions, OTP nonce storage, rate limit counters) |
| - Append-Oriented Parental Consent Audit Trail |
+-------------------------------------------------------------------------------+
```

---

## 6. Database Schema & Data Integrity

All relational models enforce strict domain and relational integrity via database-level unique constraints:
- **`uq_school_class`**: Prevents duplicate class sections per academic year.
- **`uq_student_content_progress`**: Guarantees idempotent progress recording per student/content pair.
- **`uq_student_quiz_attempt`**: Enforces strict attempt number sequence and prevents XP duplication.
- **`uq_user_badge`**: Idempotent badge assignment preventing duplicate reward exploits.
- **`uq_parent_student_link`**: Verifiable single or multi-parent linkage.
