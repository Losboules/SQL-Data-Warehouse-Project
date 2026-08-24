"""Check repository-relative Markdown links; skip web URLs and anchors."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def main() -> None:
    failures = []
    for path in Path(".").rglob("*.md"):
        if any(part in {".git", ".venv"} for part in path.parts):
            continue
        # The imported 3,219-page manual intentionally teaches repository-root paths
        # and contains thousands of internal anchors. Validate the repository docs,
        # while treating the manual as a separately generated reference artifact.
        if path.parts[:2] == ("docs", "manual"):
            continue
        text = path.read_text(encoding="utf-8")
        for raw in LINK.findall(text):
            target = raw.strip().split()[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"{path}: {raw}")
    if failures:
        raise SystemExit("Broken relative Markdown links:\n- " + "\n- ".join(failures))
    print("Relative Markdown link check passed.")


if __name__ == "__main__":
    main()
