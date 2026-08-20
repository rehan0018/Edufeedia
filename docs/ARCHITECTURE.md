# Edufeedia Technical Architecture & System Design 🏛️

## 1. Architectural Principles

Edufeedia is engineered around five fundamental design invariants:
1. **Minor Safety Fail-Closed**: Any anomaly, timeout, or ambiguity in safety evaluation defaults to immediate access restriction and pedagogical deflection.
2. **Tenant & Identity Isolation**: School districts, academies, teachers, parents, and students operate within strict cryptographically and relationally enforced boundaries.
3. **Decoupled Verification vs. Consent**: Identity confirmation ($\text{email\_verified}$, $\text{identity\_verified}$) is explicitly separated from legal guardian consent ($\text{parental\_consent\_status}$).
4. **Pedagogical Socratic Scaffolding**: Knowledge retrieval prioritizes step-by-step conceptual guidance over direct answer feeding.
5. **Active Recall & Spaced Retention**: Feed personalization optimizes for long-term retention via SuperMemo-2 (SM-2) scheduling rather than vanity engagement metrics.

---

## 2. Component Topology

```
+-------------------------------------------------------------------------------+
|                                  Client Tier                                  |
|     Next.js 14 / React SPA | Socratic AI Chat | Adaptive Feed | Portals       |
+---------------------------------------+---------------------------------------+
                                        | HTTPS / REST + SSE
+---------------------------------------v---------------------------------------+
|                               API Gateway Tier                                |
|  - Correlation ID Tracing (`X-Request-ID`, `X-Response-Time-MS`)              |
|  - Centralized Access Policy Engine (`app.core.access_policy`)                |
|  - Rate Limiting & Sliding Window Token Bucket                                |
|  - Multi-Tenant Role-Based Access Control (RBAC)                              |
+---------------------------------------+---------------------------------------+
                                        |
      +---------------------------------+--------------------------------+
      |                                 |                                |
+-----v---------------+       +---------v---------+            +---------v---------+
| Socratic AI Engine  |       | Recommendation    |            | Content Pipeline  |
| - Hybrid Dense+BM25 |       | - Hybrid Scoring  |            | - Verified Sources|
| - Model Gateway     |       | - SM-2 Spaced Rep |            | - SHA-256 Dedup   |
| - Safety Hard Gates |       | - Explainability  |            | - Educator Review |
+-----+---------------+       +---------+---------+            +---------+---------+
      |                                 |                                |
+-----v---------------------------------v--------------------------------v---------+
|                               Persistence Layer                               |
| - PostgreSQL 16 + pgvector (384-d semantic vectors)                           |
| - Redis 7 (Distributed sessions, OTP nonce storage, rate limit counters)      |
| - Append-Oriented Parental Consent Audit Trail                                |
+-------------------------------------------------------------------------------+
```

---

## 3. Database Schema & Data Integrity

All relational models enforce strict domain and relational integrity via database-level unique constraints:
- **`uq_school_class`**: Prevents duplicate class sections per academic year.
- **`uq_student_content_progress`**: Guarantees idempotent progress recording per student/content pair.
- **`uq_student_quiz_attempt`**: Enforces strict attempt number sequence and prevents XP duplication.
- **`uq_user_badge`**: Idempotent badge assignment preventing duplicate reward exploits.
- **`uq_parent_student_link`**: Verifiable single or multi-parent linkage.
