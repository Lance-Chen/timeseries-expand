#!/usr/bin/env python3
"""Replace <your-username> placeholders in the timeseries-expand scaffold.

Usage:
    python replace_placeholders.py <your-github-username> [email]

Example:
    python replace_placeholders.py jiang [email protected]
"""
import re
import sys
from pathlib import Path

# RELEASE_CHECKLIST.md intentionally retains the placeholders as documentation
SKIP_FILES = {"RELEASE_CHECKLIST.md", "replace_placeholders.py"}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    username = sys.argv[1].strip()
    if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,38}[a-zA-Z0-9])?$", username):
        print(f"ERROR: '{username}' does not look like a valid GitHub username")
        return 1

    email = sys.argv[2] if len(sys.argv) > 2 else "[email protected]"
    root = Path(__file__).parent

    replacements = {
        "<your-username>": username,
        "your-security-contact@example.com": email,
    }

    total = 0
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if path.name in SKIP_FILES:
            continue
        if any(part.startswith(".git") for part in path.parts):
            continue
        if path.suffix not in {".md", ".toml", ".yml", ".yaml", ".py"}:
            continue

        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in replacements.items():
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            count = sum(original.count(k) for k in replacements)
            print(f"  updated {path.relative_to(root)}  ({count} replacements)")
            total += count

    print(f"\nTotal: {total} replacements")

    # Verify (excluding the doc-only RELEASE_CHECKLIST.md)
    import subprocess
    result = subprocess.run(
        ["grep", "-rn", "your-username",
         "--include=*.md", "--include=*.toml", "--include=*.yml",
         "--include=*.yaml", "--include=*.py", str(root)],
        capture_output=True, text=True,
    )
    remaining = [line for line in result.stdout.splitlines() if "RELEASE_CHECKLIST.md" not in line]
    if remaining:
        print("\nWARNING: placeholders remain:")
        for line in remaining:
            print(f"  {line}")
        return 1
    else:
        print("\nAll placeholders replaced (RELEASE_CHECKLIST.md intentionally retained).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
