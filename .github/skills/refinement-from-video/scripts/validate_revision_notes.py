#!/usr/bin/env python3
"""Validate a revision_notes.json against the schema in references/finding-schema.md.

Usage: python validate_revision_notes.py <revision_notes.json>
Exit 0 = valid; exit 1 = errors (one per line on stderr). Stdlib only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CATEGORIES = {
    "fidelity-to-source", "task-wording", "flow-sequencing",
    "measurement-design", "stimulus-design", "technical-bug", "other",
}
SEVERITIES = {"critical", "high", "medium", "low"}
CONFIDENCES = {"high", "medium", "low"}
OWNERS = {"engineering", "research", "design", "content", "discussion"}
AFFECTS = {"all-conditions", "specific-conditions", "single-trial", "unknown"}
CODE_STATUSES = {"confirms", "suggests", "contradicts", "not-correlated"}
TIMING_CONFIDENCES = {"approximate", "low"}
TIMESTAMP_RE = re.compile(r"^(\d+:)?[0-5]?\d:[0-5]\d$")  # mm:ss or h:mm:ss
REQUIRED = [
    "id", "title", "category", "severity", "confidence", "occurrences",
    "observed", "already_documented", "suggested_owner", "next_action", "revision_ready",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    run = doc.get("run")
    if not isinstance(run, dict):
        errors.append("top-level: missing 'run' object")
        run = {}
    repo = run.get("code_repo")
    repo_commit = repo.get("commit") if isinstance(repo, dict) else None

    notes = doc.get("revision_notes")
    if not isinstance(notes, list):
        return errors + ["top-level: 'revision_notes' must be a list"]

    seen_ids: set[str] = set()
    for i, note in enumerate(notes):
        where = f"revision_notes[{i}]" + (f" ({note.get('id')})" if isinstance(note, dict) and note.get("id") else "")
        if not isinstance(note, dict):
            errors.append(f"{where}: not an object")
            continue
        for field in REQUIRED:
            if field not in note:
                errors.append(f"{where}: missing required field '{field}'")

        nid = note.get("id", "")
        if isinstance(nid, str) and nid:
            if not re.match(r"^RN-\d+$", nid):
                errors.append(f"{where}: id must match RN-<number>")
            if nid in seen_ids:
                errors.append(f"{where}: duplicate id")
            seen_ids.add(nid)

        for field, allowed in [
            ("category", CATEGORIES), ("severity", SEVERITIES),
            ("confidence", CONFIDENCES), ("suggested_owner", OWNERS),
        ]:
            if field in note and note[field] not in allowed:
                errors.append(f"{where}: {field} '{note[field]}' not in {sorted(allowed)}")
        if "affects" in note and note["affects"] is not None and note["affects"] not in AFFECTS:
            errors.append(f"{where}: affects '{note['affects']}' not in {sorted(AFFECTS)}")

        if "already_documented" in note and not isinstance(note["already_documented"], bool):
            errors.append(f"{where}: already_documented must be a boolean")

        occ = note.get("occurrences")
        if not isinstance(occ, list) or not occ:
            errors.append(f"{where}: occurrences must be a non-empty list")
        else:
            for j, o in enumerate(occ):
                if not isinstance(o, dict):
                    errors.append(f"{where}.occurrences[{j}]: not an object")
                    continue
                if not o.get("task"):
                    errors.append(f"{where}.occurrences[{j}]: missing task")
                ts = o.get("timestamp")
                if not isinstance(ts, str) or not TIMESTAMP_RE.match(ts):
                    errors.append(f"{where}.occurrences[{j}]: timestamp '{ts}' is not mm:ss or h:mm:ss")
                ts_end = o.get("timestamp_end")
                if ts_end is not None and not (isinstance(ts_end, str) and TIMESTAMP_RE.match(ts_end)):
                    errors.append(f"{where}.occurrences[{j}]: timestamp_end '{ts_end}' is not mm:ss or h:mm:ss")

        code = note.get("code")
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

        if note.get("revision_ready") is True and note.get("confidence") == "low":
            errors.append(f"{where}: revision_ready requires confidence better than 'low'")

        if note.get("already_documented") is True and not note.get("next_action"):
            errors.append(f"{where}: already_documented notes still require next_action")

        rehydration = note.get("rehydration")
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
        print("usage: validate_revision_notes.py <revision_notes.json>", file=sys.stderr)
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
        print("error: top-level document must be an object", file=sys.stderr)
        return 1

    errors = validate(doc)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        print(f"\n{len(errors)} error(s)", file=sys.stderr)
        return 1

    n = len(doc.get("revision_notes", []))
    print(f"valid — {n} revision note(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
