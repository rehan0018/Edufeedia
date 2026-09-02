# Edufeedia Third-Party Dependency and License Inventory

> This document provides a comprehensive inventory of open-source and third-party software dependencies utilized in Edufeedia, along with their respective license types and attribution details.

Third-party dependencies remain subject to their respective open-source licenses. The proprietary and source-available terms of Edufeedia apply to the project's original codebase and do not alter the underlying licenses of third-party dependencies.

---

## 1. Backend Core and Framework Dependencies (Python)

| Component | Version | Upstream License | Required Attribution | Commercial Permissibility |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI** | >= 0.111.0 | MIT License | Preserved in distribution | Permitted under MIT |
| **Starlette** | >= 0.37.2 | BSD-3-Clause | Preserved in distribution | Permitted under BSD-3 |
| **Uvicorn** | >= 0.30.0 | BSD-3-Clause | Preserved in distribution | Permitted under BSD-3 |
| **SQLAlchemy** | >= 2.0.0 | MIT License | Preserved in distribution | Permitted under MIT |
| **Alembic** | >= 1.13.0 | MIT License | Preserved in distribution | Permitted under MIT |
| **Pydantic** | >= 2.7.0 | MIT License | Preserved in distribution | Permitted under MIT |
| **Pydantic-Settings** | >= 2.3.0 | MIT License | Preserved in distribution | Permitted under MIT |
| **python-jose** | >= 3.3.0 | MIT License | Preserved in distribution | Permitted under MIT |
| **passlib** | >= 1.7.4 | BSD-3-Clause | Preserved in distribution | Permitted under BSD-3 |
| **redis-py** | >= 5.0.0 | MIT License | Preserved in distribution | Permitted under MIT |
| **psycopg2-binary** | >= 2.9.9 | LGPL with exception / BSD | Preserved in distribution | Permitted (Binary wrapper) |
| **httpx** | >= 0.27.0 | BSD-3-Clause | Preserved in distribution | Permitted under BSD-3 |
| **python-multipart** | >= 0.0.9 | Apache-2.0 | Preserved in distribution | Permitted under Apache-2.0 |

---

## 2. AI, Machine Learning, and Evaluation Dependencies (Python)

| Component | Version | Upstream License | Required Attribution | Commercial Permissibility |
| :--- | :--- | :--- | :--- | :--- |
| **SentenceTransformers** | >= 3.0.0 | Apache-2.0 | Preserved in distribution | Permitted under Apache-2.0 |
| **PyTorch (torch)** | >= 2.2.0 | BSD-3-Clause | Preserved in distribution | Permitted under BSD-3 |
| **scikit-learn** | >= 1.4.0 | BSD-3-Clause | Preserved in distribution | Permitted under BSD-3 |
| **numpy** | >= 1.26.0 | BSD-3-Clause | Preserved in distribution | Permitted under BSD-3 |
| **openai** | >= 1.30.0 | Apache-2.0 | Preserved in distribution | Permitted under Apache-2.0 |
| **google-generativeai** | >= 0.5.0 | Apache-2.0 | Preserved in distribution | Permitted under Apache-2.0 |

---

## 3. Frontend Dependencies (JavaScript / React / Vite)

| Component | Version | Upstream License | Required Attribution | Commercial Permissibility |
| :--- | :--- | :--- | :--- | :--- |
| **React** | ^18.3.1 | MIT License | Preserved in bundle | Permitted under MIT |
| **React-DOM** | ^18.3.1 | MIT License | Preserved in bundle | Permitted under MIT |
| **Lucide React** | ^0.460.0 | ISC License | Preserved in bundle | Permitted under ISC |
| **Canvas-Confetti** | ^1.9.3 | ISC License | Preserved in bundle | Permitted under ISC |
| **Vite** | ^5.4.11 | MIT License | Build-time tooling | Permitted under MIT |
| **@vitejs/plugin-react** | ^4.3.4 | MIT License | Build-time tooling | Permitted under MIT |

---

## 4. Infrastructure and Runtime Services

| Service | Runtime Context | Upstream License | Distribution Notes |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | Relational Database Engine | PostgreSQL License (BSD-like) | Network-accessed service |
| **Redis** | In-Memory Cache and Rate Limiter | BSD-3-Clause / RSALv2 / SSPL | Network-accessed service (redis-py client used) |
| **Docker** | Containerization Runtime | Apache-2.0 | Build and deployment orchestration |

---

## 5. License Attribution Compliance Statement

Edufeedia incorporates and builds upon the open-source community's foundational libraries. All included third-party notices, copyright headers, and dependency licenses are retained in accordance with their respective licensing obligations.
