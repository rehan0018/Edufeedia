# Edufeedia 🎓

> **An AI-powered safe, personalized learning and revision platform engineered specifically for students under 18.**  
> Curating curriculum-aligned educational materials from trusted sources, personalizing daily study feeds, orchestrating fail-closed Socratic AI tutoring, and driving long-term retention through active recall, adaptive quizzes, and SM-2 spaced repetition.

---

## 📑 Table of Contents

- [1. Executive Product Overview](#1-executive-product-overview)
- [2. Key Features & Capabilities](#2-key-features--capabilities)
- [3. High-Level Architecture Diagram](#3-high-level-architecture-diagram)
- [4. The End-to-End Content & AI Lifecycle](#4-the-end-to-end-content--ai-lifecycle)
- [5. AI & Socratic RAG Engine](#5-ai--socratic-rag-engine)
- [6. Zero-Trust Security & Multi-Category Safety](#6-zero-trust-security--multi-category-safety)
- [7. DPDP & COPPA Verifiable Parental Consent](#7-dpdp--coppa-verifiable-parental-consent)
- [8. Multi-Tenant Role-Based Access Control (RBAC)](#8-multi-tenant-role-based-access-control-rbac)
- [9. Technology Stack](#9-technology-stack)
- [10. Local Development Quickstart](#10-local-development-quickstart)
- [11. Environment Configuration Reference](#11-environment-configuration-reference)
- [12. Database Migrations (Alembic)](#12-database-migrations-alembic)
- [13. Comprehensive Automated Test Suite](#13-comprehensive-automated-test-suite)
- [14. Docker & CI/CD Deployment Architecture](#14-docker--cicd-deployment-architecture)
- [15. Observability & SRE Telemetry](#15-observability--sre-telemetry)
- [16. Product Roadmap](#16-product-roadmap)

---

## 1. Executive Product Overview

Traditional open internet search exposing K-12 students to toxic content, clickbait, and unvetted information. Generic AI chat interfaces frequently hallucinate answers or act as answer engines that short-circuit critical thinking.

**Edufeedia** solves these challenges with a **modular, fail-closed educational platform**:
1. **Verified Curriculum Discovery**: Ingests exclusively from whitelisted, verified educational authorities (CBSE, NCERT, ICSE, Khan Academy, MIT OpenCourseWare).
2. **Pedagogical AI Tutoring**: Socratic dialogue guides students step-by-step to arrive at conceptual solutions rather than spoon-feeding raw answers.
3. **Multi-Category Safety Shield**: Real-time content filtering rejects toxic material, dangerous activities, hate speech, and adversarial prompt injections.
4. **Adaptive Personalization**: Pointwise GBDT ranking and collaborative filtering adjust daily feeds based on dwell time, quiz accuracy, and subject mastery.
5. **Verifiable Parental Consent**: Cryptographic OTP guardian verification designed with the Indian Digital Personal Data Protection (DPDP) Act 2023 principles and US COPPA parental consent requirements in mind.

---

## 2. Key Features & Capabilities

- 🤖 **Multi-Provider Socratic AI Tutor**: Intelligent hybrid RAG (Dense Vector + Okapi BM25 + Reciprocal Rank Fusion) backed by OpenAI GPT-5/Responses API, Google Gemini, and a zero-latency local fallback.
- ⚡ **Anti-Answer Socratic Safeguards**: AI responses actively detect when a student is asking for homework answers and transform them into interactive guiding questions.
- 🧠 **SuperMemo SM-2 Spaced Repetition**: Dynamic interval scheduling automatically flags weak topics and queues personalized flashcards before memory decay occurs.
- 🛡️ **Fail-Closed AI Output Gate**: Every model token passes through real-time safety classification. If the safety auditor is unreachable, the system fails closed rather than leaking uninspected outputs.
- 📊 **Teacher & School Analytics**: Multi-tenant dashboards tracking class mastery, attendance engagement, weak topics, and assignment completion.
- 🔒 **Stateless JWT with Redis Blacklist**: Instant session revocation and token invalidation on logout.

---

## 3. High-Level Architecture Diagram

```mermaid
flowchart TD
    Client["React 18 + Vite Web Client\n(Tailwind CSS + Lucide Icons)"] -->|HTTPS / WSS| Gateway["FastAPI REST & Telemetry API Gateway"]

    subgraph Security Layer
        Gateway --> Auth["Auth & RBAC Middleware\n(Bcrypt + Stateless JWT)"]
        Auth --> Blacklist{"Redis Token Blacklist\n& Rate Limiter"}
        Blacklist --> PolicyEngine["Safety Policy Engine\n(Age Gating + Content Classifier)"]
    end

    subgraph Core Business Services
        PolicyEngine --> StudentSvc["Student Learning Service"]
        PolicyEngine --> QuizSvc["Quiz & Spaced Repetition Engine"]
        PolicyEngine --> RAGSvc["Hybrid RAG & Socratic Gateway"]
        PolicyEngine --> RecSvc["GBDT Recommendation Ranker"]
        PolicyEngine --> AdminSvc["Tenant-Scoped Admin & Audit Service"]
    end

    subgraph AI Model Gateway
        RAGSvc --> Embedder["384-Dim Semantic Embedder\n(SentenceTransformers)"]
        RAGSvc --> ModelRouter["Multi-Provider Gateway Router"]
        ModelRouter -->|Primary| OpenAI["OpenAI GPT API"]
        ModelRouter -->|Secondary| Gemini["Google Gemini API"]
        ModelRouter -->|Offline Fallback| LocalSocratic["Deterministic Socratic Engine"]
        ModelRouter --> OutputSafety["Fail-Closed Output Safety Auditor"]
    end

    subgraph Data & Storage Layer
        StudentSvc & QuizSvc & RecSvc --> Postgres["PostgreSQL / SQLite Database\n(SQLAlchemy ORM + Alembic Migrations)"]
        RAGSvc --> VectorStore["Curriculum Chunk Vector Index\n(pgvector / In-Memory Dense Store)"]
        Blacklist & ModelRouter --> RedisCluster["Redis Cluster\n(OTP TTL + Session Revocation)"]
        AdminSvc --> EmailDispatch["Transactional Email Service\n(Live SMTP / SES / STARTTLS)"]
    end
```

---

## 4. The End-to-End Content & AI Lifecycle

The core engineering strength of Edufeedia is its unidirectional 9-stage content intelligence and learning pipeline:

```
[1. Content Discovery] ──► [2. Source Verifier] ──► [3. Ingestion & Parser]
                                                            │
[6. Socratic Dialogue] ◄── [5. Hybrid RAG (Dense+BM25)] ◄── [4. Embedding Generation]
        │
        ▼
[7. Adaptive Quiz & Recall] ──► [8. SM-2 Spaced Repetition] ──► [9. GBDT Recommendation Ranker]
```

1. **Content Discovery**: Adapters poll verified educational channels (CBSE, NCERT, ICSE, Khan Academy, MIT OCW).
2. **Source Verifier**: Validates HTTPS certificates, domain reputation, and educational trust scoring before processing.
3. **Ingestion & Parser**: Cleanses raw HTML/Markdown, strips metadata, and chunks content into semantic sections.
4. **Embedding Generation**: Chunks are encoded into 384-dimensional dense semantic vector space via `SentenceTransformers`.
5. **Hybrid RAG Retrieval**: Intent classifier decouples queries; searches chunks using Dense Cosine Similarity + Okapi BM25 Lexical scoring; reranks via Reciprocal Rank Fusion (RRF, $k=60$).
6. **Socratic Dialogue**: Multi-provider AI Gateway produces pedagogical guidance that enforces concept mastery over answer extraction.
7. **Adaptive Quiz & Recall**: Synthesizes formative multiple-choice questions dynamically mapped to Bloom's taxonomy.
8. **SM-2 Spaced Repetition**: Student responses adjust easiness factors ($EF$) and repetition intervals to combat the Ebbinghaus forgetting curve.
9. **GBDT Recommendation Ranker**: Interaction weights (dwell time, completion, quiz accuracy) update feature vectors to re-rank the student's next daily feed.

---

## 5. AI & Socratic RAG Engine

### Intent-Aware Hybrid Retrieval

Unlike naive RAG systems that query only based on the open lesson, Edufeedia's `RAGEngine` runs **Intent Decoupling**:
- Evaluates whether the query is related to the active lesson or represents a new curriculum concept inquiry.
- Performs dense vector cosine similarity across curriculum chunks with persistent embedding caching (`_CHUNK_EMBEDDING_CACHE`).
- Calculates lexical Okapi BM25 scores:
  $$IDF(q_i) = \ln\left(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1\right)$$
- Merges candidate rankings using **Reciprocal Rank Fusion (RRF)**:
  $$RRF\_Score(d) = \sum_{m \in M} \frac{1}{60 + r_m(d)}$$

### Automated RAG Benchmark Results

Tested on our golden CBSE/ICSE curriculum evaluation dataset (`backend/app/ai/evaluator.py`):

| Evaluation Metric | Target Benchmark | Edufeedia Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **MRR@3 (Mean Reciprocal Rank)** | $\ge 0.75$ | **0.88** | 🟢 Exceeds Benchmark |
| **Precision@3** | $\ge 0.30$ | **0.33** | 🟢 Exceeds Benchmark |
| **Recall@3** | $\ge 0.75$ | **1.00** | 🟢 100% Corpus Coverage |
| **Safety Classification Accuracy** | $\ge 0.95$ | **1.00** | 🟢 100% Accurate |
| **Adversarial Injection Defense** | $\ge 0.95$ | **1.00** | 🟢 100% Blocked |
| **Groundedness Score** | $\ge 0.90$ | **0.94** | 🟢 Minimal Hallucination |

---

## 6. Zero-Trust Security & Multi-Category Safety

Because Edufeedia is designed for users under 18, safety is treated as a core architectural invariant rather than an afterthought:

- **Fail-Closed AI Gateway**: If the safety auditor encounters an error or network timeout, the request immediately fails closed with an error response instead of delivering unverified LLM output.
- **Multi-Category Classifier**: Scans text across 4 critical risk categories:
  1. `ADULT_EXPLICIT`: Sexually explicit and mature content.
  2. `DANGEROUS_ACTIVITIES`: Chemical synthesis, weapons, exploit crafting, firewall bypasses.
  3. `HATE_AND_HARASSMENT`: Hate speech, toxicity, and bullying.
  4. `PROMPT_INJECTION`: Jailbreak patterns (`DAN`, `ignore previous instructions`).
- **Strict CORS & Header Whitelisting**: Restricts HTTP methods (`GET, POST, PUT, PATCH, DELETE, OPTIONS`) and explicit origins (`http://localhost:3000`, `https://app.edufeedia.com`). Wildcards (`*`) are disallowed in production.

---

## 7. DPDP & COPPA Verifiable Parental Consent

Edufeedia implements a legally compliant 2-step verifiable parental consent protocol:

```
[Student Under 16 Registers] ──► [Account Inactive / Unverified]
                                           │
[Guardian Email Challenge] ◄───────────────┘
         │
         ▼
[6-Digit Cryptographic OTP Issued (Redis 15-min TTL)]
         │
         ▼
[Delivered via Live SMTP / SES Transactional Email]
         │
         ▼
[Parent Verifies OTP & Authorizes Scope] ──► [Immutable Audit Log Recorded] ──► [Account Activated]
```

- **IDOR Immunity**: Identity bindings prevent student accounts from verifying or claiming unlinked students.
- **Immutable Audit Logging**: Every consent grant and revocation is immutably logged with timestamp, consent scope, version (`2026.1-DPDP-COPPA`), and IP fingerprint.

---

## 8. Multi-Tenant Role-Based Access Control (RBAC)

Edufeedia isolates data boundaries strictly by tenant school IDs:

| Role | Registration Path | Permissions & Boundary Scope |
| :--- | :--- | :--- |
| **Student** | Public self-registration | Access personalized curriculum feed, Socratic tutor, quizzes, and personal analytics. Strictly cannot self-assign staff roles. |
| **Parent** | Linked via student invitation | Monitor linked child's progress, grant/revoke DPDP/COPPA consent, view mastery telemetry. Cross-child data strictly blocked. |
| **Teacher** | Staff invitation token only | Manage assigned classrooms, inspect student mastery, approve ingestion submissions, assign quizzes. |
| **School Admin** | Platform super-admin token | School-wide user management, teacher invitation, tenant analytics. Cross-school access strictly forbidden (403). |
| **System Admin** | Seed / Root configuration | Platform infrastructure monitoring, global curriculum corpus management. |

---

## 9. Technology Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) 0.111.0 (Async Python 3.11+)
- **Database ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) 2.0+ with [Alembic](https://alembic.sqlalchemy.org/) migrations
- **Relational Stores**: PostgreSQL 16 / SQLite (local dev)
- **Vector Search**: 384-dimensional dense semantic vectors with Cosine Similarity + BM25
- **ML / NLP**: [SentenceTransformers](https://www.sbert.net/), PyTorch, scikit-learn (GBDT Ranker)
- **Cache & Session**: [Redis](https://redis.io/) 5.0+ (OTP rate limiting, token revocation blacklist)
- **Email Delivery**: Python `smtplib` / AWS SES with TLS provider verification

### Frontend
- **Framework**: [React](https://react.dev/) 18 with [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **State Management**: Reactive Hooks with persistent authentication context

---

## 10. Local Development Quickstart

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **Redis** *(Optional for local dev, fallback in-process store enabled for offline testing)*

### Step 1: Clone Repository
```bash
git clone https://github.com/rehan0018/Edufeedia.git
cd Edufeedia
```

### Step 2: Set Up Python Backend Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Seed Database & Fixtures
```bash
python seed.py
```

### Step 4: Start Backend API Service
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
*API Swagger Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

### Step 5: Start Frontend Client
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
*Web Application will be accessible at: [http://localhost:3000](http://localhost:3000)*

---

## 11. Environment Configuration Reference

Create a `.env` file in the project root:

```ini
# Application Environment
ENVIRONMENT=development
PROJECT_NAME="Edufeedia API"
SECRET_KEY="your-32-character-random-secret-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database Configuration
DATABASE_URL="sqlite:///edufeedia.db"
# Production example: postgresql://user:password@rds-host:5432/edufeedia

# Cache & Session Store
REDIS_URL="redis://localhost:6379/0"

# CORS Allowed Origins (Comma-separated)
ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# AI Model Gateway
LLM_PROVIDER="auto"
OPENAI_API_KEY=""
OPENAI_MODEL="gpt-4o-mini"
GEMINI_API_KEY=""
GEMINI_MODEL="gemini-1.5-flash"

# Transactional Email Dispatch (SMTP / AWS SES)
SMTP_HOST="smtp.mailtrap.io"
SMTP_PORT=587
SMTP_USER=""
SMTP_PASSWORD=""
SMTP_FROM_EMAIL="noreply@edufeedia.com"
```

---

## 12. Database Migrations (Alembic)

Edufeedia uses Alembic for declarative schema versioning in production:

```bash
# Run latest database migrations
alembic upgrade head

# Generate a new migration revision
alembic revision --autogenerate -m "add_new_feature_column"

# Rollback last migration
alembic downgrade -1
```

---

## 13. Comprehensive Automated Test Suite

Edufeedia maintains an extensive test suite with **91 automated tests (100% passing)** covering authentication, security regression, AI safety, RAG benchmarks, spaced repetition, and tenant isolation:

```bash
# Run all test suites
python -m unittest discover -s backend/tests
```

```
...........................................................................................
----------------------------------------------------------------------
Ran 91 tests in 30.597s

OK
```

### Key Test Coverage Areas:
- 🧪 `test_security_regression.py`: Tenant-scoped admin records, Parental consent IDOR defense, Google OAuth audience validation, Redis production fail-fast.
- 🧪 `test_rag_evaluation.py`: MRR@3, Precision@K, Recall@K, Groundedness, Adversarial prompt injection defense.
- 🧪 `test_ai_model_gateway.py`: Multi-provider failover (OpenAI $\to$ Gemini $\to$ Local Socratic) and fail-closed safety gate.
- 🧪 `test_api.py` & `test_advanced_ai.py`: Student registration, SM-2 interval calculations, GBDT ranking, weak-topic detection.

---

## 14. Docker & CI/CD Deployment Architecture

### Multi-Stage Production Docker Build

The production Dockerfile utilizes a hardened, non-root user, slim runtime image:

```bash
# Build production Docker image
docker build -t edufeedia:latest .

# Run containerized service
docker run -d -p 8000:8000 --env-file .env edufeedia:latest
```

### GitHub Actions CI/CD Workflow (`.github/workflows/ci.yml`)

Every pull request and push to `main` automatically triggers:
1. Linting & syntax verification.
2. Redis service container initialization.
3. Full backend test suite execution (91 tests).
4. Frontend production asset build (`vite build`).
5. Multi-stage Docker container compilation and security smoke checks.

---

## 15. Observability & SRE Telemetry

Edufeedia includes built-in telemetry endpoints for Kubernetes and CloudWatch:
- **`GET /live`**: Process liveness probe for orchestrators.
- **`GET /ready`**: Real-time readiness probe inspecting PostgreSQL connection pools and Redis cluster status.
- **`GET /metrics`**: Operational metrics exposing request counts, HTTP 4xx/5xx error rates, uptime, and AI filter statistics.
- **Correlated Request Tracing**: Every HTTP response includes `X-Request-ID` and `X-Response-Time-MS` headers for end-to-end distributed tracing.

---

## 16. Product Roadmap

- [x] Multi-Provider AI Model Gateway (OpenAI / Gemini / Socratic Local)
- [x] Fail-Closed Output Safety Auditor & Adversarial Prompt Injection Defense
- [x] DPDP Act & COPPA Verifiable Parental Consent Flow with Transactional Email OTP
- [x] Anti-Farming XP Concurrency Idempotency & Leaderboards
- [x] Automated RAG Evaluation Framework (MRR@3, Precision@K, Groundedness)
- [x] Tenant-Scoped Multi-School Administration Dashboard
- [ ] Multimodal Visual Socratic Solver (Diagram & Geometry OCR analysis)
- [ ] Offline PWA Voice Socratic Study Assistant
- [ ] Automated NCERT/CBSE Question Bank Sync via Webhook

---

## 📄 License & Student Privacy Notice

Licensed under the **MIT License**. Engineered and designed with student data privacy, Indian DPDP Act principles, and US COPPA parental consent safeguards in mind.
