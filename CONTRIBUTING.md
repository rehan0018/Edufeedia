# Contributing to Edufeedia 🎓

Thank you for your interest in contributing to Edufeedia! We welcome contributions from developers, educators, researchers, and child-safety advocates to enhance our educational intelligence, curriculum adapters, safety filters, and developer tooling.

---

## 📜 1. Contributor License Agreement (CLA)

Edufeedia is source-available software under the [PolyForm Shield License 1.0.0](LICENSE).

To ensure that the project can accept your code while protecting project ownership and long-term sustainability:
- **All contributors must review and agree to the [Edufeedia Contributor License Agreement (CLA.md)](CLA.md).**
- Submitting a Pull Request constitutes your agreement to the terms of `CLA.md`.
- Under the CLA, you retain copyright in your original contributions while granting Edufeedia a perpetual, worldwide, royalty-free, transferable license to include your contributions in the software.
- The project and brand remain the intellectual property of Rehan Shaikh.

---

## 🛡️ 2. Architectural & Child-Safety Invariants

Because Edufeedia is engineered specifically for students aged 10–17, all contributions must uphold these non-negotiable principles:

1. **Fail-Closed Safety**: Any AI or content classification pipeline modification must fail closed (i.e. block or safely filter rather than leaking uninspected outputs).
2. **Zero PII Leakage**: Never log, leak, or return student email addresses, full names, or unhashed IP addresses in log files, telemetry, or public API responses.
3. **Strict Multi-Tenant Scoping**: All database queries must enforce tenant isolation (e.g. `User.school_id`) to prevent cross-school IDOR vulnerabilities.
4. **Purpose-Specific Consent**: New student-data processing features must declare explicit `ProcessingPurpose` mappings under the guardian consent policy.

---

## 🛠️ 3. Development & Testing Workflow

### Step 1: Fork & Branch
Fork the repository and create a feature branch:
```bash
git checkout -b feature/cbse-math-adapter
```

### Step 2: Set Up Local Environment
Follow the [Local Development Quickstart](README.md#10-local-development-quickstart) in `README.md`.

### Step 3: Run the Test Suite
Ensure all automated unit and regression tests pass before submitting:
```bash
# Run backend test suite
python -m unittest discover -s backend/tests

# Run frontend build check
cd frontend && npm run build
```

### Step 4: Submit a Pull Request
1. Write clear, concise commit messages following standard conventional commit formats.
2. Open a Pull Request against `main`.
3. Verify that all automated CI workflow checks pass.

---

## 🔒 4. Reporting Security Vulnerabilities

Please **do NOT report security flaws via public GitHub issues**. Refer to our [Security Policy (SECURITY.md)](SECURITY.md) for instructions on reporting vulnerabilities privately.

---

## 🏷️ 5. Trademarks & Branding

Usage of the Edufeedia name, logo, and brand assets is governed by [TRADEMARKS.md](TRADEMARKS.md). The software license does not grant trademark rights.

---

*Thank you for contributing to safe, transparent, and personalized AI education for students!*
