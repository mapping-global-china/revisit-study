#!/usr/bin/env python3
"""Validate a findings.json against the schema in references/finding-schema.md.

Usage: python validate_findings.py <findings.json>
Exit 0 = valid; exit 1 = errors (one per line on stderr). Stdlib only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CATEGORIES = {"issue-candidate", "needs-discussion", "design-opportunity"}
SUBTYPES = {
    "interaction-bug", "rendering-bug", "data-bug", "crash", "performance",
    "wording", "study-instrument", "study-flow", "usability-friction",
    "accessibility", "feature-request", "workflow-gap", "research-protocol", "other",
}
SEVERITIES = {"critical", "high", "medium", "low"}
CONFIDENCES = {"high", "medium", "low"}
NATURES = {
    "software-defect", "wording", "stimulus-condition", "research-protocol",
    "intentional-manipulation", "investigator-review",
}
OWNERS = {"engineering", "research", "design", "content", "discussion"}
AFFECTS = {"all-conditions", "specific-conditions", "single-trial", "unknown"}
CODE_STATUSES = {"confirms", "suggests", "contradicts", "not-correlated"}
TIMING_CONFIDENCES = {"approximate", "low"}
TIMESTAMP_RE = re.compile(r"^(\d+:)?[0-5]?\d:[0-5]\d$")  # mm:ss or h:mm:ss
REQUIRED = ["id", "title", "category", "subtype", "severity", "confidence",
            "occurrences", "observed", "suggested_owner", "next_action", "issue_ready"]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    run = doc.get("run")
    if not isinstance(run, dict):
        errors.append("top-level: missing 'run' object")
        run = {}
    repo = run.get("code_repo")
    repo_commit = repo.get("commit") if isinstance(repo, dict) else None

    findings = doc.get("findings")
    if not isinstance(findings, list):
        return errors + ["top-level: 'findings' must be a list"]

    seen_ids: set[str] = set()
    for i, f in enumerate(findings):
        where = f"finding[{i}]" + (f" ({f.get('id')})" if isinstance(f, dict) and f.get("id") else "")
        if not isinstance(f, dict):
            errors.append(f"{where}: not an object")
            continue
        for field in REQUIRED:
            if field not in f:
                errors.append(f"{where}: missing required field '{field}'")

        fid = f.get("id", "")
        if isinstance(fid, str) and fid:
            if not re.match(r"^F-\d+$", fid):
                errors.append(f"{where}: id must match F-<number>")
            if fid in seen_ids:
                errors.append(f"{where}: duplicate id")
            seen_ids.add(fid)

        for field, allowed in [("category", CATEGORIES), ("subtype", SUBTYPES),
                               ("severity", SEVERITIES), ("confidence", CONFIDENCES),
                               ("suggested_owner", OWNERS)]:
            if field in f and f[field] not in allowed:
                errors.append(f"{where}: {field} '{f[field]}' not in {sorted(allowed)}")
        if "nature" in f and f["nature"] is not None and f["nature"] not in NATURES:
            errors.append(f"{where}: nature '{f['nature']}' not in {sorted(NATURES)}")
        if "affects" in f and f["affects"] is not None and f["affects"] not in AFFECTS:
            errors.append(f"{where}: affects '{f['affects']}' not in {sorted(AFFECTS)}")

        occ = f.get("occurrences")
        if not isinstance(occ, list) or not occ:
            errors.append(f"{where}: occurrences must be a non-empty list")
        else:
            for j, o in enumerate(occ):
                if not isinstance(o, dict):
                    errors.append(f"{where}.occurrences[{j}]: not an object")
                    continue
                if not o.get("participant"):
                    errors.append(f"{where}.occurrences[{j}]: missing participant")
                ts = o.get("timestamp")
                if not isinstance(ts, str) or not TIMESTAMP_RE.match(ts):
                    errors.append(f"{where}.occurrences[{j}]: timestamp '{ts}' is not mm:ss or h:mm:ss")
                ts_end = o.get("timestamp_end")
                if ts_end is not None and not (isinstance(ts_end, str) and TIMESTAMP_RE.match(ts_end)):
                    errors.append(f"{where}.occurrences[{j}]: timestamp_end '{ts_end}' is not mm:ss or h:mm:ss")

        code = f.get("code")
        if code is not None:
            if not isinstance(code, dict):
                errors.append(f"{where}: code must be an object or null")
            else:
                if repo_commit is None:
                    errors.append(f"{where}: code block present but run.code_repo is missing — "
                                  "code correlation requires a recorded repo")
                status = code.get("status")
                if status not in CODE_STATUSES:
                    errors.append(f"{where}: code.status '{status}' not in {sorted(CODE_STATUSES)}")
                locations = code.get("locations", [])
                if status == "not-correlated":
                    if locations:
                        errors.append(f"{where}: code.status 'not-correlated' must have empty locations")
                elif status in CODE_STATUSES:
                    if not locations:
                        errors.append(f"{where}: code.status '{status}' requires non-empty locations")
                    if repo_commit is not None and code.get("commit") != repo_commit:
                        errors.append(f"{where}: code.commit '{code.get('commit')}' does not match "
                                      f"run.code_repo.commit '{repo_commit}'")

        if f.get("issue_ready") is True:
            if f.get("category") != "issue-candidate":
                errors.append(f"{where}: issue_ready requires category 'issue-candidate'")
            if f.get("confidence") == "low":
                errors.append(f"{where}: issue_ready requires confidence better than 'low'")

        if f.get("category") == "needs-discussion" and not f.get("open_questions"):
            errors.append(f"{where}: needs-discussion findings must list open_questions")

        rehydration = f.get("rehydration")
        if rehydration is not None:
            if not isinstance(rehydration, dict):
                errors.append(f"{where}: rehydration must be an object or null")
            else:
                available = rehydration.get("available")
                if not isinstance(available, bool):
                    errors.append(f"{where}: rehydration.available must be a boolean")
                elif available:
                    for field in ("node_id", "event", "timing_confidence"):
                        if not rehydration.get(field):
                            errors.append(f"{where}: rehydration.available=true requires '{field}'")
                    tc = rehydration.get("timing_confidence")
                    if tc is not None and tc not in TIMING_CONFIDENCES:
                        errors.append(f"{where}: rehydration.timing_confidence '{tc}' not in {sorted(TIMING_CONFIDENCES)}")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_findings.py <findings.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 1
    if not isinstance(doc, dict):
        print("error: top level must be an object", file=sys.stderr)
        return 1
    errors = validate(doc)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        print(f"\n{len(errors)} error(s)", file=sys.stderr)
        return 1
    n = len(doc.get("findings", []))
    print(f"valid: {n} finding(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
