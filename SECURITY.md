# Edufeedia Security Policy

Edufeedia is an educational intelligence and AI tutoring platform designed specifically for students aged 10-17. We take security, child safety, and student data privacy with the highest priority.

---

## 1. Supported Versions

Security patches and vulnerability updates are actively maintained for the following versions:

| Version or Branch | Supported | Notes |
| :--- | :--- | :--- |
| main (Latest) | Yes | Active development and continuous security patches |
| Release tags (>= 1.0.0) | Yes | Supported for critical CVEs and child-safety patches |
| Historical pre-1.0 tags | No | Please upgrade to the latest release |

---

## 2. Scope and Vulnerability Classifications

We prioritize security vulnerabilities across the following core areas:
- **Child Safety and Prompt Injection Bypasses**: Bypasses of the Socratic safety gate, jailbreaks extracting toxic content, or subversion of the content classifier.
- **Student Privacy and PII Leakage**: Unauthorized access to student learning records, parent email disclosure, or unmasked leaderboard data.
- **Tenant Isolation and IDOR**: Insecure Direct Object References allowing cross-school or cross-student data access.
- **Authentication and Session Security**: JWT forgery, replay attacks, or bypasses of the Redis token revocation blacklist.
- **Data Integrity**: Unauthorized tampering with audit log hash chains or quiz mastery scoring.

---

## 3. Reporting a Vulnerability

If you discover a security vulnerability or child-safety flaw, please do NOT report it via public GitHub issues or discussions.

Instead, please report it through one of the following private channels:

1. **GitHub Private Vulnerability Reporting**: Use the "Report a vulnerability" button under the repository's Security tab.
2. **Direct Email**: Send a report to:
   - **rehan.shaikh@edufeedia.com**
   - Subject: [SECURITY] Potential Vulnerability in Edufeedia: <Brief Description>

### Please include in your report:
- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Affected endpoints, modules, or file paths.
- Your recommended remediation or mitigation (if available).

---

## 4. Response Timeline and SLAs

- **Initial Acknowledgment**: Within 48 hours of report receipt.
- **Triage and Impact Assessment**: Within 5 business days.
- **Fix and Patch Deployment**: Critical child-safety and authentication vulnerabilities are patched as top-priority hotfixes.
- **Coordinated Disclosure**: We request that you give us 30 days to remediate the vulnerability before public disclosure.

---

## 5. Security Architecture Invariants

Edufeedia enforces the following defensive engineering principles:
- **Fail-Closed Safety Gate**: If real-time AI safety filters or content classifiers are unreachable, outputs are blocked rather than streamed uninspected.
- **Monotonic Cryptographic Audit Chains**: Administrative and consent actions are recorded in immutable SHA-256 hash chains.
- **Salted PII and IP Hashing**: Telemetry and audit logs store irreversibly salted hashes rather than raw student IP addresses.
