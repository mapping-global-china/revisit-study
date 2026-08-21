#!/usr/bin/env python3
"""Correlate a trrack node's `event` (registered action name) to the exact
`registry.register(...)` call that defines it, in a study's source.

Never invents a location: if the event string isn't found in any of the
candidate files, returns status "not-correlated" with an empty locations
list — same discipline as the code-correlation rules in both parent skills'
finding schemas.

Usage:
  python correlate_action.py <studyName> <eventName> [--repo-root <path>]

Searches, in order (first match wins per file, all matches reported):
  src/public/<studyName>/assets/trrack.ts
  src/public/<studyName>/assets/useProvenance.ts
  src/public/<studyName>/assets/SharedStateContext.tsx
  src/public/<studyName>/**/*.ts(x)   (fallback: any file under the study's
    src assets, in case the registration lives elsewhere)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Matches: registry.register('eventName', ... or registry.register("eventName", ...
REGISTER_RE_TEMPLATE = r"registry\.register\(\s*['\"]{event}['\"]"


def find_registrations(repo_root: Path, study_name: str, event_name: str) -> list[dict]:
    study_assets = repo_root / "src" / "public" / study_name
    if not study_assets.is_dir():
        return []

    pattern = re.compile(REGISTER_RE_TEMPLATE.format(event=re.escape(event_name)))
    candidates = [
        study_assets / "assets" / "trrack.ts",
        study_assets / "assets" / "useProvenance.ts",
        study_assets / "assets" / "SharedStateContext.tsx",
    ]
    # Fallback: scan all ts/tsx files under the study's assets if nothing
    # found in the expected locations.
    all_files = list(study_assets.rglob("*.ts")) + list(study_assets.rglob("*.tsx"))
    search_order = [f for f in candidates if f.is_file()] + [f for f in all_files if f not in candidates]

    matches = []
    seen = set()
    for f in search_order:
        if f in seen or not f.is_file():
            continue
        seen.add(f)
        text = f.read_text()
        lines = text.splitlines()
        # registry.register(...) calls are often multi-line (name on the
        # next line after the opening paren), so search the whole file text
        # rather than line-by-line, then map the match back to a line number.
        for m in pattern.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            snippet = "\n".join(lines[max(0, line_no - 1):min(len(lines), line_no + 4)])
            matches.append({
                "file": str(f.relative_to(repo_root)),
                "line": line_no,
                "snippet": snippet,
            })
    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("study_name", help="the study's folder name, e.g. forecast-charts")
    parser.add_argument("event_name", help="the trrack node's event string, e.g. 'bestGuess'")
    parser.add_argument("--repo-root", default=".", help="path to the repo root (default: cwd)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    matches = find_registrations(repo_root, args.study_name, args.event_name)

    if not matches:
        result = {"status": "not-correlated", "locations": []}
    else:
        result = {
            "status": "suggests",
            "locations": [{"file": m["file"], "lines": str(m["line"]), "why": f"registers event '{args.event_name}'"} for m in matches],
            "snippets": matches,
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
