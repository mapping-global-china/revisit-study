#!/usr/bin/env python3
"""Render a round's revision_notes.json into revision-notes.md, and update
the study's revision-notes-index.md.

Purely local rendering — no AI calls, no network access. Structure follows
references/report-structure.md.

Usage:
  python make_revision_report.py <revision_notes.json> --out <round-dir>/revision-notes.md \\
      --index <refinement-dir>/revision-notes-index.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}


def sort_key(note: dict) -> tuple:
    return (
        SEVERITY_ORDER.get(note.get("severity"), 9),
        CONFIDENCE_ORDER.get(note.get("confidence"), 9),
    )


def render_occurrences(occ: list[dict]) -> str:
    parts = []
    for o in occ:
        ts = o.get("timestamp", "?")
        ts_end = f"\u2013{o['timestamp_end']}" if o.get("timestamp_end") else ""
        task = o.get("task", "?")
        parts.append(f"{task} @ {ts}{ts_end}")
    return "; ".join(parts)


def render_code(code: dict | None) -> str:
    if not code:
        return "not performed"
    status = code.get("status", "?")
    if status == "not-correlated":
        return "not correlated"
    locs = code.get("locations", [])
    rendered = "; ".join(f"{l.get('file')}:{l.get('lines', '?')} \u2014 {l.get('why', '')}" for l in locs)
    return f"{rendered} (status: {status})"


def render_rehydration(rehydration: dict | None) -> list[str]:
    """Renders the optional 'Reconstructed state & actions' subsection when
    provenance-rehydration produced a result for this note. Empty list when
    unavailable — most notes won't have this."""
    if not rehydration or not rehydration.get("available"):
        return []
    lines = ["", "**Reconstructed state & actions** (via provenance-rehydration):", ""]
    lines.append(f"- Matched node `{rehydration.get('node_id')}` (event `{rehydration.get('event')}`) "
                 f"at +{rehydration.get('offset_from_task_start_s')}s into the task.")
    lines.append(f"- Timing confidence: **{rehydration.get('timing_confidence')}** — {rehydration.get('timing_note', '')}")
    sequence = rehydration.get("action_sequence") or []
    if sequence:
        lines.append("- Action sequence leading to this moment:")
        for step in sequence:
            lines.append(f"  - +{step.get('offset_s')}s `{step.get('event')}` ({step.get('label')})")
    if rehydration.get("repro_spec_path"):
        lines.append(f"- Generated repro spec: `{rehydration['repro_spec_path']}`")
    return lines


def render_note(note: dict, reviewer_name: str) -> str:
    lines = [
        f"### {note['id']}: {note['title']}",
        "",
        f"**Category**: {note['category']} \u00b7 **Severity**: {note['severity']} \u00b7 "
        f"**Confidence**: {note['confidence']} \u00b7 **Already documented**: {note.get('already_documented')}",
        "",
        f"**Observed**: {note.get('observed', '')}",
    ]
    if note.get("stated"):
        lines.append(f"**{reviewer_name} said**: {note['stated']}")
    if note.get("interpreted"):
        lines.append(f"**Interpreted**: {note['interpreted']}")
    if note.get("source_reference"):
        lines.append(f"**Should match**: {note['source_reference']}")
    lines.append("")
    lines.append(f"**Evidence**: {render_occurrences(note.get('occurrences', []))}")
    lines.append("")
    lines.append(f"**Code**: {render_code(note.get('code'))}")
    lines.extend(render_rehydration(note.get("rehydration")))
    lines.append("")
    lines.append(f"**Next action**: {note.get('next_action', '')}")
    if note.get("open_questions"):
        lines.append("**Open questions**:")
        for q in note["open_questions"]:
            lines.append(f"- {q}")
    lines.append("")
    return "\n".join(lines)


def render_report(doc: dict) -> str:
    run = doc.get("run", {})
    notes = sorted(doc.get("revision_notes", []), key=sort_key)
    reviewer = run.get("reviewer", {})
    reviewer_name = reviewer.get("name", "reviewer")

    by_category: dict[str, int] = {}
    for n in notes:
        by_category[n.get("category", "other")] = by_category.get(n.get("category", "other"), 0) + 1

    lines = [
        f"# Revision notes \u2014 round {run.get('round', '?')}",
        "",
        f"**Reviewer**: {reviewer_name} ({reviewer.get('role', 'reviewer')}) \u00b7 "
        f"**Date**: {run.get('date', '?')} \u00b7 **Tool**: {run.get('video_tool', 'n/a')}",
        "",
        "## Round summary",
        "",
        f"{len(notes)} note(s). By category: " + ", ".join(f"{k}={v}" for k, v in sorted(by_category.items())),
        "",
        "## Scope and grounding",
        "",
    ]
    grounded = run.get("grounded_in", {})
    if grounded:
        lines.append(f"Grounded in: config `{grounded.get('config', 'n/a')}`" +
                      (f", README `{grounded.get('readme')}`" if grounded.get("readme") else ""))
    if not run.get("video_tool_available", True):
        lines.append(f"**No video tool available.** Fallback evidence used: {run.get('fallback_evidence', [])}")
    lines.append("")

    lines.append("## Prioritized notes")
    lines.append("")
    lines.append("| id | title | category | severity | confidence | already documented | owner |")
    lines.append("|---|---|---|---|---|---|---|")
    for n in notes:
        lines.append(
            f"| {n['id']} | {n['title']} | {n['category']} | {n['severity']} | "
            f"{n['confidence']} | {n.get('already_documented')} | {n.get('suggested_owner', '')} |"
        )
    lines.append("")

    lines.append("## Note details")
    lines.append("")
    for n in notes:
        lines.append(render_note(n, reviewer_name))

    already = [n for n in notes if n.get("already_documented") is True]
    lines.append("## Already-documented deviations re-raised")
    lines.append("")
    if already:
        for n in already:
            lines.append(f"- **{n['id']}**: {n['title']} \u2014 {n.get('next_action', '')}")
    else:
        lines.append("None.")
    lines.append("")

    new_fidelity = [n for n in notes if n.get("category") == "fidelity-to-source" and not n.get("already_documented")]
    lines.append("## New fidelity concerns")
    lines.append("")
    if new_fidelity:
        for n in new_fidelity:
            lines.append(f"- **{n['id']}**: {n['title']}")
    else:
        lines.append("None.")
    lines.append("")

    repo = run.get("code_repo")
    lines.append("## Code correlation summary")
    lines.append("")
    if repo:
        lines.append(f"Repo `{repo.get('path')}` @ `{repo.get('commit')}` (branch `{repo.get('branch')}`, "
                      f"dirty={repo.get('dirty')})")
        statuses: dict[str, int] = {}
        for n in notes:
            code = n.get("code")
            if code:
                statuses[code.get("status", "?")] = statuses.get(code.get("status", "?"), 0) + 1
        lines.append(", ".join(f"{k}={v}" for k, v in sorted(statuses.items())) or "no code blocks")
    else:
        lines.append("Not performed \u2014 no repo supplied.")
    lines.append("")

    lines.append("## Open questions / discussion agenda")
    lines.append("")
    any_open = False
    for n in notes:
        if n.get("open_questions"):
            any_open = True
            lines.append(f"- **{n['id']}** ({n['title']}): " + "; ".join(n["open_questions"]))
    if not any_open:
        lines.append("None.")
    lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append(f"Model/tool: {run.get('video_tool', 'n/a')} \u00b7 Run date: {run.get('date', '?')}")
    if run.get("externally_processed"):
        lines.append("External processing:")
        for item in run["externally_processed"]:
            lines.append(f"- {item}")
    if repo:
        lines.append(f"Repo commit: {repo.get('commit')}")
    lines.append("")

    return "\n".join(lines)


def update_index(index_path: Path, doc: dict, report_rel_path: str) -> None:
    run = doc.get("run", {})
    notes = doc.get("revision_notes", [])
    new_fidelity_count = sum(
        1 for n in notes if n.get("category") == "fidelity-to-source" and not n.get("already_documented")
    )
    reviewer = run.get("reviewer", {}).get("name", "reviewer")
    round_num = str(run.get("round", "?"))
    row = (
        f"| {round_num} | {run.get('date', '?')} | {reviewer} | "
        f"{len(notes)} | {new_fidelity_count} | [{report_rel_path}]({report_rel_path}) |"
    )

    header = (
        "# Revision notes index\n\n"
        "| Round | Date | Reviewer | Notes | Fidelity concerns (new) | Report |\n"
        "|---|---|---|---|---|---|\n"
    )
    existing_rows: list[str] = []
    if index_path.exists():
        for line in index_path.read_text().splitlines():
            if not line.startswith("|") or line.startswith("| Round") or line.startswith("|---"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0] == round_num:
                continue  # replaced by the new row for this round, below
            existing_rows.append(line)

    text = header + "\n".join(existing_rows + [row]) + "\n"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision_notes_json", help="path to a round's revision_notes.json")
    parser.add_argument("--out", required=True, help="output path for revision-notes.md")
    parser.add_argument("--index", help="path to revision-notes-index.md to append a row to")
    args = parser.parse_args()

    doc = json.loads(Path(args.revision_notes_json).read_text())
    report = render_report(doc)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(f"wrote {out_path}")

    if args.index:
        index_path = Path(args.index)
        try:
            report_rel = str(out_path.relative_to(index_path.parent))
        except ValueError:
            report_rel = str(out_path)
        update_index(index_path, doc, report_rel)
        print(f"updated {index_path}")


if __name__ == "__main__":
    main()
