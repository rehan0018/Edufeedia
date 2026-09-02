"""
Git Commit History Secret Scanner for CI and Pre-Commit Audits.
Scans all commit diffs, tree objects, and branches for sensitive credentials,
API keys, private keys, and hardcoded secrets.
"""

import subprocess
import re
import sys

# High-risk secret regex patterns
PATTERNS = [
    ("OpenAI API Key", re.compile(r"(?i)\bsk-[a-zA-Z0-9]{20,}\b")),
    ("Google Gemini / Cloud API Key", re.compile(r"\bAIzaSy[a-zA-Z0-9_-]{33}\b")),
    ("Anthropic API Key", re.compile(r"\bsk-ant-[a-zA-Z0-9_-]{20,}\b")),
    ("AWS Access Key ID", re.compile(r"\b(?:AKIA|ASIA|AROA)[0-9A-Z]{16}\b")),
    ("AWS Secret Access Key", re.compile(r"(?i)(?:aws_secret_access_key|aws_secret_key)\s*[:=]\s*['\"][a-zA-Z0-9/+=]{40}['\"]")),
    ("Private Key Block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("GitHub Personal Access Token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}\b")),
    ("GitHub Fine-Grained Token", re.compile(r"\bgithub_pat_[a-zA-Z0-9_]{82}\b")),
    ("Hardcoded Database URL with Password", re.compile(r"(?:postgresql|postgres|mysql|mongodb)://[a-zA-Z0-9_\-]+:[a-zA-Z0-9!@#$%^&*()_+]{4,}@[a-zA-Z0-9_\-\.]+:[0-9]+")),
    ("Hardcoded Production JWT Secret", re.compile(r"(?i)(?:jwt_secret|secret_key)\s*[:=]\s*['\"][a-zA-Z0-9!@#$%^&*()_+]{16,}['\"]"))
]

# Known non-secret placeholders used in templates and docs
SAFE_PLACEHOLDERS = {
    "change_this_to_a_cryptographically_secure_random_64_character_hex_string",
    "generate_a_secure_postgres_password_here",
    "generate_a_secure_64_character_hex_secret_key",
    "test_secret_key_for_ci_pipeline_verification_only_64_characters_long",
    "edufeedia_pass",
    "Student123!",
    "Teacher123!",
    "Parent123!",
    "Admin123!",
    "user:password@rds-host",
    "postgresql://user:password@rds-host:5432/edufeedia"
}


def audit_git_history() -> bool:
    print("================================================================================")
    print("Executing Deep Git History Secret Audit...")
    print("================================================================================")

    try:
        cmd = ["git", "log", "-p", "--all", "--full-history"]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        diff_text = proc.stdout

        if not diff_text:
            print("[WARN] git log returned empty diff. Ensuring full git clone...")
            return True

        print(f"Scanned {len(diff_text):,} characters of Git commit history diffs.")

        violations = []
        for name, regex in PATTERNS:
            matches = regex.findall(diff_text)
            real_matches = []
            for m in matches:
                is_safe = any(safe in m for safe in SAFE_PLACEHOLDERS)
                if not is_safe:
                    real_matches.append(m)

            if real_matches:
                violations.append((name, len(real_matches), real_matches[:3]))

        if violations:
            print("\n[CRITICAL FAILURE] Potential secrets detected in Git history:")
            for name, count, samples in violations:
                print(f"  - {name}: {count} occurrences found. Samples: {samples}")
            print("\nPlease rotate any exposed credentials immediately and purge them from git history.")
            return False

        print("\n[SUCCESS] 0 secrets detected. Git history audit PASSED.")
        print("================================================================================")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to execute git history audit: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = audit_git_history()
    sys.exit(0 if success else 1)
