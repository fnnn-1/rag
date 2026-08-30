import re
from pathlib import Path
import subprocess
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
PREFIX_PATTERN = re.compile(r"sk-[A-Za-z0-9._-]{16,}")
LITERAL_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|secret[_-]?key)\s*=\s*['\"]([^'\"]{16,})['\"]"
)
SAFE_PLACEHOLDERS = ("change-me", "example", "replace", "your-", "your_", "placeholder")


def tracked_files() -> list[str]:
    output = subprocess.check_output(["git", "ls-files"], cwd=WORKSPACE, text=True, encoding="utf-8")
    return [line for line in output.splitlines() if line]


def contains_suspicious_secret(text: str) -> bool:
    if PREFIX_PATTERN.search(text):
        return True
    for match in LITERAL_PATTERN.finditer(text):
        value = match.group(1).strip().lower()
        if value and not any(placeholder in value for placeholder in SAFE_PLACEHOLDERS):
            return True
    return False


def scan_worktree() -> list[str]:
    findings = []
    for relative in tracked_files():
        path = WORKSPACE / relative
        if path.is_file() and contains_suspicious_secret(path.read_text(encoding="utf-8", errors="ignore")):
            findings.append(relative)
    return sorted(set(findings))


def scan_history() -> list[str]:
    commits = subprocess.check_output(
        ["git", "rev-list", "--all"], cwd=WORKSPACE, text=True, encoding="utf-8"
    ).splitlines()
    findings = set()
    expression = r"sk-[A-Za-z0-9._-]{16,}"
    for commit in commits:
        result = subprocess.run(
            ["git", "grep", "-I", "-l", "-E", expression, commit],
            cwd=WORKSPACE,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            _, _, path = line.partition(":")
            findings.add(path or line)
    return sorted(findings)


def main() -> int:
    worktree_findings = scan_worktree()
    history_findings = scan_history()
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", ".env"], cwd=WORKSPACE, check=False
    ).returncode == 0
    print(f"ENV_FILE_IGNORED={ignored}")
    print(f"TRACKED_SECRET_FINDINGS={len(worktree_findings)}")
    print(f"HISTORY_SECRET_FINDINGS={len(history_findings)}")
    if worktree_findings:
        print("TRACKED_FILES_REQUIRING_REVIEW=" + ",".join(worktree_findings))
    if history_findings:
        print("HISTORY_FILES_REQUIRING_REVIEW=" + ",".join(history_findings))
    clean = ignored and not worktree_findings and not history_findings
    print("SECURITY_SCAN=" + ("PASS" if clean else "FAIL"))
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
