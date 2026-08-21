#!/usr/bin/env python3
"""Map a video timestamp to a provenance node, and reconstruct the exact
application state + action sequence leading up to it.

This is the core primitive both revisit-usability-analysis and
refinement-from-video build on when a finding/note has a timestamp AND the
flagged component used trrack (react-component with a provenanceGraph). It
turns "something looked wrong around 01:12" into "here is the literal state
and action sequence at that moment" instead of a prose guess.

Degrades honestly when provenance isn't available: the caller should check
`has_provenance()` first and only invoke this module when true, then always
report `timing_confidence` (see below) so nobody mistakes an approximate
timestamp match for ground truth.

Timing note: video/recording timestamps and trrack `createdOn` epoch-ms
values live in DIFFERENT clocks (browser recording start vs. epoch time).
This module aligns them using the task's `startTime`/`endTime` from the
participant's `answers[identifier]` (also epoch ms) as the anchor: video
00:00 for a task is assumed to correspond to that task's `startTime`. This is
an approximation — MediaRecorder start latency and dropped frames mean the
true offset can be off by up to ~1-2s in practice, so treat node matches near
timestamp boundaries with lower confidence (see `timing_confidence`).

Usage (as a library — import from an analysis script, or run standalone):
  python rehydrate_node.py <participantData.json> <identifier> <mm:ss>
    [--tolerance-s 2]

Prints the matched node, reconstructed state, and the ordered action
sequence from the component's root to that node, as JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# primitives.py lives at analysis/primitives.py (shared across studies).
# Search upward so this script works from any supported project skill folder.
try:
    from primitives import reconstruct_states
except ImportError:
    search_roots = [Path.cwd().resolve(), *Path(__file__).resolve().parents]
    analysis_dir = next(
        (root / "analysis" for root in search_roots if (root / "analysis" / "primitives.py").is_file()),
        None,
    )
    if analysis_dir is None:
        raise ImportError(
            "could not find analysis/primitives.py; run this command from a ReVISit "
            "repository containing the shared provenance primitives",
        )
    sys.path.insert(0, str(analysis_dir))
    from primitives import reconstruct_states  # noqa: E402


def has_provenance(answer: dict) -> bool:
    """True if this answer has a non-empty trrack provenance graph."""
    graph = (answer.get("provenanceGraph") or {}).get("stimulus")
    return bool(graph and graph.get("nodes"))


def parse_timestamp(ts: str) -> float:
    """'mm:ss' or 'h:mm:ss' -> seconds."""
    parts = [float(p) for p in ts.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


def ordered_nodes(answer: dict) -> list[dict]:
    graph = answer["provenanceGraph"]["stimulus"]
    nodes = list(graph["nodes"].values())
    return sorted(nodes, key=lambda n: n["createdOn"])


def rehydrate_at_timestamp(
    answer: dict,
    video_timestamp_s: float,
    tolerance_s: float = 2.0,
) -> dict:
    """Find the node active at video_timestamp_s (relative to this task's
    startTime) and return its reconstructed state + action sequence.

    Returns a dict with:
      matched: bool
      node_id, event, created_on_ms, offset_from_task_start_s
      state: reconstructed JSON application state at that node
      action_sequence: [{event, label, offset_s}, ...] from root to this node
      timing_confidence: "approximate" | "low" — see module docstring
      timing_note: human-readable caveat
    """
    if not has_provenance(answer):
        return {"matched": False, "reason": "no provenance graph on this answer"}

    task_start_ms = answer["startTime"]
    target_ms = task_start_ms + video_timestamp_s * 1000

    nodes = ordered_nodes(answer)
    resolved = reconstruct_states(nodes)

    # Find the last node whose createdOn <= target_ms (state was already
    # applied by then); if none, fall back to the first node.
    matched = None
    for node, state, change in resolved:
        if node["createdOn"] <= target_ms:
            matched = (node, state, change)
        else:
            break
    if matched is None:
        matched = resolved[0]

    node, state, _change = matched
    offset_s = (node["createdOn"] - task_start_ms) / 1000
    drift_s = abs(offset_s - video_timestamp_s)

    if drift_s <= tolerance_s:
        confidence = "approximate"
        note = (
            f"Matched within {drift_s:.1f}s of the requested timestamp "
            f"(tolerance {tolerance_s}s) — recording-start latency and dropped "
            "frames mean this is not frame-exact."
        )
    else:
        confidence = "low"
        note = (
            f"Nearest node is {drift_s:.1f}s away from the requested timestamp, "
            f"outside the {tolerance_s}s tolerance — video/provenance clocks may "
            "have drifted, or this task has sparse tracked interactions. Treat "
            "the state below as a rough approximation, not the exact moment."
        )

    action_sequence = [
        {
            "node_id": n["id"],
            "event": n["event"],
            "label": n.get("label", n["event"]),
            "offset_s": round((n["createdOn"] - task_start_ms) / 1000, 2),
        }
        for n, _s, _c in resolved
        if n["createdOn"] <= node["createdOn"]
    ]

    return {
        "matched": True,
        "node_id": node["id"],
        "event": node["event"],
        "created_on_ms": node["createdOn"],
        "offset_from_task_start_s": round(offset_s, 2),
        "state": state,
        "action_sequence": action_sequence,
        "timing_confidence": confidence,
        "timing_note": note,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("participant_data_json", help="path to a single ParticipantData JSON")
    parser.add_argument("identifier", help="answer identifier, e.g. 'trial-median-near-1_1'")
    parser.add_argument("timestamp", help="video timestamp, mm:ss or h:mm:ss")
    parser.add_argument("--tolerance-s", type=float, default=2.0)
    args = parser.parse_args()

    participant = json.loads(Path(args.participant_data_json).read_text())
    answer = participant.get("answers", {}).get(args.identifier)
    if not answer:
        sys.exit(f"no answer found for identifier {args.identifier!r}")

    result = rehydrate_at_timestamp(answer, parse_timestamp(args.timestamp), args.tolerance_s)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
