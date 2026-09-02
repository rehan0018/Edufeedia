# Contributing to Edufeedia

Thank you for your interest in contributing to Edufeedia. We welcome contributions from developers, educators, researchers, and child-safety advocates to enhance our educational intelligence, curriculum adapters, safety filters, and developer tooling.

---

## 1. Contributor License Agreement (CLA)

Edufeedia is source-available software under the [PolyForm Shield License 1.0.0](LICENSE).

To ensure that the project can accept your code while protecting project ownership and long-term sustainability:
- **All contributors must review and agree to the [Edufeedia Contributor License Agreement (CLA.md)](CLA.md).**
- Submitting a Pull Request constitutes your agreement to the terms of CLA.md.
- Under the CLA, you retain copyright in your original contributions while granting Edufeedia a perpetual, worldwide, royalty-free, transferable license to include your contributions in the software.
- The project and brand remain the intellectual property of Rehan Shaikh.

---

## 2. Permitted and Restricted Actions

### Allowed without prior permission:
- Reading, cloning, and studying the source code
- Local development, debugging, and experimentation
- Writing bug fixes, test cases, and curriculum adapters
- Improving documentation and test coverage
- Submitting pull requests and participating in code review
- Private, non-commercial educational and research deployments

### Prohibited without express written permission:
- Commercial SaaS hosting or managed service offerings
- Reselling, bundling, or sublicensing the software
- Developing a competing commercial product based on the codebase
- Rebranding the software under a different commercial identity
- Removing proprietary notices or copyright attributions

---

## 3. Architectural and Child-Safety Invariants

Because Edufeedia is engineered specifically for students aged 10-17, all contributions must uphold these non-negotiable principles:

1. **Fail-Closed Safety**: Any AI or content classification pipeline modification must fail closed (i.e. block or safely filter rather than leaking uninspected outputs).
2. **Zero PII Leakage**: Never log, leak, or return student email addresses, full names, or unhashed IP addresses in log files, telemetry, or public API responses.
3. **Strict Multi-Tenant Scoping**: All database queries must enforce tenant isolation (e.g. User.school_id) to prevent cross-school IDOR vulnerabilities.
4. **Purpose-Specific Consent**: New student-data processing features must declare explicit ProcessingPurpose mappings under the guardian consent policy.

---

## 4. Development and Testing Workflow

### Step 1: Fork and Branch
Fork the repository and create a feature branch:
```bash
git checkout -b feature/cbse-math-adapter
```

### Step 2: Set Up Local Environment
Follow the [Local Development Quickstart](README.md#10-local-development-quickstart) in README.md.

### Step 3: Run the Test Suite
Ensure all automated unit and regression tests pass before submitting:
```bash
# Run backend test suite
python -m unittest discover -s backend/tests

# Run frontend build check
cd frontend && npm run build
```

### Step 4: Submit a Pull Request
1. Complete the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) requirements.
2. Ensure you have checked the CLA acceptance box.
3. Open a Pull Request against main.

---

## 5. Reporting Security Vulnerabilities

Please do NOT report security flaws via public GitHub issues. Refer to our [Security Policy (SECURITY.md)](SECURITY.md) for instructions on reporting vulnerabilities privately.

---

## 6. Trademarks and Branding

Usage of the Edufeedia name, logo, and brand assets is governed by [TRADEMARKS.md](TRADEMARKS.md). The software license does not grant trademark rights.
