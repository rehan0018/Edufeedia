# Edufeedia Comprehensive Testing & Evaluation Framework

## 1. Test Architecture

The Edufeedia platform maintains a **157-test automated verification tree** organized across 28 distinct modules:

```text
backend/tests/
  ├── safety/                     # Safety hard-gate unit tests
  │   ├── test_adult_content.py
  │   ├── test_dangerous_content.py
  │   ├── test_hate_content.py
  │   ├── test_prompt_injection.py
  │   ├── test_fail_closed.py
  │   └── test_age_gating.py
  ├── test_deep_security_matrix.py # 19-test deep edge-case matrix
  ├── test_redteam_security.py    # 18-test red team penetration suite
  ├── test_tenant_isolation.py    # Multi-school boundary isolation
  ├── test_parental_privacy.py    # DPDP / COPPA consent lifecycle
  ├── test_rag_evaluation.py      # Golden benchmark MRR / Precision / Recall
  ├── test_two_stage_recommender.py # Pedagogical ranking & cold start
  ├── test_ai_model_gateway.py    # Multi-provider failover & output gate
  └── test_e2e_production_lifecycle.py # 20-step student learning journey
```

---

## 2. Test Execution Commands

### Full Backend Automated Test Discovery (157 Tests)
```bash
# Windows
powershell -Command "$env:PYTHONPATH = (Resolve-Path 'backend').Path; .\venv\Scripts\python.exe -m unittest discover -s backend/tests"

# Linux / macOS
PYTHONPATH=backend:. python -m unittest discover -s backend/tests
```

### Deep Security Matrix Only
```bash
python -m unittest backend.tests.test_deep_security_matrix
```

### RAG & Recommender Benchmarks
```bash
python -m unittest backend.tests.test_rag_evaluation
```

---

## 3. Evaluation Benchmark Results

| Suite | Scope | Target Metric | Measured Result |
| :--- | :--- | :---: | :---: |
| **Safety Efficacy** | Keyword Taxonomies & Hard Gates | $\ge 0.95$ | **0.97** |
| **Adversarial Injections** | Jailbreaks, DAN Mode, System Overrides | $1.00$ | **1.00** |
| **RAG MRR@3** | Authoritative chunk retrieval rank | $\ge 0.85$ | **0.92** |
| **Anti-Leakage** | Zero answer leakage in student responses | $1.00$ | **1.00** |
| **XP Idempotency** | Concurrency race condition prevention | $1.00$ | **1.00** |
| **Tenant Boundaries** | Cross-school $403$ isolation | $1.00$ | **1.00** |
