"""Simple educational secret-pattern scanner; not a replacement for enterprise tooling."""
from __future__ import annotations

import re
from pathlib import Path

PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Databricks token-like": re.compile(r"\bdapi[a-zA-Z0-9]{20,}\b"),
    "GitHub token-like": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "password assignment": re.compile(r"(?i)\b(password|pwd)\s*[=:]\s*['\"][^<'\"]{8,}['\"]"),
}
SKIP = {".git", ".venv", "datasets", "logs", "run_artifacts"}
EXTENSIONS = {".py", ".ps1", ".sql", ".md", ".yml", ".yaml", ".json", ".dax", ".txt"}


def main() -> None:
    findings = []
    for path in Path(".").rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS or any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path}: {label}")
    if findings:
        raise SystemExit("Possible secrets found; review and rotate real credentials:\n- " + "\n- ".join(findings))
    print("Secret-pattern scan passed.")


if __name__ == "__main__":
    main()
