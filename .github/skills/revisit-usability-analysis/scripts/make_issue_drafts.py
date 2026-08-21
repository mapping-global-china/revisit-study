#!/usr/bin/env python3
"""Generate local Markdown issue drafts from findings.json.

Only findings with issue_ready: true produce drafts. Purely local — this
script never contacts GitHub. Redaction is enforced: drafts fail loudly if
they would contain raw participant ids, media URLs, or over-long quotations.

Usage: python make_issue_drafts.py <findings.json> --out <dir> [--github-target owner/repo]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAW_PID_RE = re.compile(
    r"\b[0-9a-f]{24}\b|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://\S+")
MAX_QUOTE = 140


def slugify(title: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", title.lower())).strip("-")[:60]


def redaction_errors(text: str, allowed_urls: bool = False) -> list[str]:
    errs = []
    if RAW_PID_RE.search(text):
        errs.append("contains a raw participant id (24-char hex or uuid)")
    if not allowed_urls and URL_RE.search(text):
        errs.append("contains a URL (media links are not allowed in drafts)")
    for quote in re.findall(r'"([^"]{%d,})"' % (MAX_QUOTE + 1), text):
        errs.append(f"quotation longer than {MAX_QUOTE} chars: \"{quote[:40]}...\"")
    return errs


def render(f: dict, run: dict, github_target: str | None) -> str:
    repo = run.get("code_repo") or {}
    commit = repo.get("commit")
    code = f.get("code") or {}
    lines = [
        f"# {f['title']}",
        "",
        f"Finding: {f['id']} · Severity: {f['severity']} · Confidence: {f['confidence']}",
        f"Target repo: {github_target or 'not specified'}",
        f"Analyzed at commit: {commit or 'no code correlation'}",
        "",
        "## Problem",
        f["observed"],
        "",
        "## Impact",
        f.get("impact") or f"Severity {f['severity']}: {f.get('intent') or 'see evidence below'}",
        "",
        "## Evidence",
    ]
    for o in f["occurrences"]:
        span = o["timestamp"] + (f"–{o['timestamp_end']}" if o.get("timestamp_end") else "")
        ctx = ", ".join(str(o[k]) for k in ("task", "condition") if o.get(k))
        lines.append(f"- {o['participant']} @ {span}" + (f" ({ctx})" if ctx else ""))
    if f.get("stated"):
        lines += ["", f"Participant (paraphrased): {f['stated']}"]

    lines += ["", "## Steps to reproduce"]
    steps = f.get("repro") or {}
    lines.append("Observed:")
    lines += [f"1. {s}" for s in steps.get("observed", ["(derive from evidence above)"])]
    if steps.get("inferred"):
        lines.append("Inferred (unverified):")
        lines += [f"1. {s}" for s in steps["inferred"]]

    if f.get("expected_vs_observed"):
        lines += ["", "## Expected vs observed", f["expected_vs_observed"]]

    if code.get("locations"):
        lines += ["", "## Relevant code", f"Status: {code.get('status')}"]
        for loc in code["locations"]:
            ref = loc["file"] + (f":{loc['lines']}" if loc.get("lines") else "")
            lines.append(f"- {ref}" + (f" — {loc['why']}" if loc.get("why") else ""))
        if f.get("hypothesis"):
            lines.append(f"Hypothesis: {f['hypothesis']}")
    elif f.get("hypothesis"):
        lines += ["", "## Hypothesis", f["hypothesis"]]

    lines += ["", "## Proposed approach", f["next_action"]]
    lines += ["", "## Acceptance criteria"]
    lines += [f"- [ ] {c}" for c in f.get("acceptance_criteria", ["Behavior matches expected outcome above"])]
    lines += ["", "## Validation plan",
              f.get("validation_plan") or (code.get("repro_path") or "Re-record the interaction and confirm the defect no longer occurs.")]
    if f.get("open_questions"):
        lines += ["", "## Open questions"]
        lines += [f"- {q}" for q in f["open_questions"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("findings", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--github-target", default=None)
    args = ap.parse_args()

    doc = json.loads(args.findings.read_text())
    run = doc.get("run", {})
    ready = [f for f in doc.get("findings", []) if f.get("issue_ready") is True]
    if not ready:
        print("no issue-ready findings — nothing to draft")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    failures = 0
    for f in ready:
        body = render(f, run, args.github_target)
        errs = redaction_errors(body)
        if errs:
            failures += 1
            print(f"{f['id']}: REFUSED — " + "; ".join(errs), file=sys.stderr)
            continue
        path = args.out / f"{f['id']}-{slugify(f['title'])}.md"
        path.write_text(body)
        print(f"wrote {path}")
    if failures:
        print(f"\n{failures} draft(s) refused for redaction violations — "
              "fix the finding text and re-run", file=sys.stderr)
        return 1
    print(f"\n{len(ready)} draft(s) written to {args.out} (local only — no GitHub issues were created)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
