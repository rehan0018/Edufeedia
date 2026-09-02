# Contributing to Edufeedia 🎓

Thank you for your interest in contributing to Edufeedia! We welcome contributions from developers, educators, researchers, and safety practitioners to improve educational intelligence, child-safety safeguards, curriculum discovery, and developer tooling.

---

## 📜 1. Contribution & Ownership Terms

Edufeedia is a **proprietary, source-available project** created and maintained by **Rehan Shaikh**. To protect the project's integrity and intellectual property while encouraging open collaboration, all contributions are subject to the following terms:

1. **Grant of Rights**: By submitting a pull request, patch, code snippet, documentation, design, or other contribution to this repository, you grant Rehan Shaikh and the Edufeedia project a perpetual, worldwide, irrevocable, non-exclusive, royalty-free, transferable, and sublicensable license to use, reproduce, modify, adapt, publish, translate, create derivative works from, distribute, perform, display, and commercially exploit your contribution as part of Edufeedia and related projects.
2. **Project Ownership**: Submitting a contribution does not grant you ownership, equity, copyright, trademark rights, or any proprietary interest in the Edufeedia project, brand, codebase, or intellectual property.
3. **Original Work Representation**: You represent that each contribution you submit is your original creation, or that you have the full legal right, title, and authorization to grant the rights described above without violating any third-party rights, patents, copyrights, or confidentiality obligations.
4. **Source-Available Nature**: You acknowledge that Edufeedia is source-available software under the terms of the project [LICENSE](LICENSE), and that your contributions will be distributed under that license.

---

## 🛠️ 2. Development & Code Quality Guidelines

Edufeedia is engineered specifically for students aged 10–17. As a child-facing educational platform, all contributions must uphold strict architectural and safety invariants:

### A. Child Safety & Privacy Invariants
- **Fail-Closed Safety**: Any AI or content pipeline modification must fail closed (i.e. block or safely filter rather than leaking uninspected outputs).
- **Zero PII Exposure**: Never log or expose personally identifiable information (PII), student email addresses, or unhashed IP addresses in log files, telemetry, or client responses.
- **Tenant & Role Isolation**: Ensure all database queries and administrative actions enforce strict multi-tenant school isolation and RBAC checks.
- **Purpose-Specific Consent**: New student-data processing features must map to explicit `ProcessingPurpose` definitions under the verifiable guardian consent engine.

### B. Engineering & Architecture Standards
- **Backend**: Python 3.10+ / FastAPI / SQLAlchemy / Pydantic. Maintain strict type annotations and docstrings.
- **Frontend**: React 18 / Vite / Tailwind CSS / Lucide Icons. Ensure accessible, responsive UI with clear loading and error states.
- **Testing**: Every new feature or bug fix MUST include automated unit and integration tests under `backend/tests/`. All tests must pass before submitting a PR.

---

## 🚀 3. How to Submit a Contribution

1. **Fork the Repository**: Create your own working branch from `main` (e.g. `feature/cbse-math-adapter` or `fix/socratic-timeout`).
2. **Set Up Local Environment**: Follow the [Local Development Quickstart](README.md#10-local-development-quickstart) in the README.
3. **Run the Test Suite**:
   ```bash
   # Run all backend tests
   python -m unittest discover -s backend/tests

   # Run frontend build check
   cd frontend && npm run build
   ```
4. **Commit with Clear Messages**: Write concise, descriptive commit messages outlining what was changed and why.
5. **Open a Pull Request**: Submit your pull request against the `main` branch with a clear description of the problem solved, architectural changes made, and verification steps performed.

---

## 🛡️ 4. Reporting Security Vulnerabilities

If you discover a potential security vulnerability, prompt injection bypass, or student privacy concern, please **do NOT create a public issue**. Instead, send a private report directly to **rehan.shaikh@edufeedia.com** with detailed steps to reproduce. We will review and address safety and security reports as high priority.

---

*Thank you for helping build safe, high-quality, personalized AI education for students!*
