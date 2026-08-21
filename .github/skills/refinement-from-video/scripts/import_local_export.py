#!/usr/bin/env python3
"""Import a reviewer session that was manually exported from a LOCAL
(VITE_STORAGE_ENGINE="localStorage") study instance.

Use this instead of fetch_reviewer_session.py when the study is not backed by
Supabase, so there is no cloud bucket to fetch from. localStorage sessions
live in the browser's IndexedDB and can only be gotten out via the app's own
download UI.

Manual export steps (before running this script):
  1. Open the study, go to Analyze & Manage (top-right menu) for this study.
  2. Find the reviewer's session in the participant table \u2014 identify it by
     the marker string typed into the id field (shown in the "Name" column
     when the study config has uiConfig.participantNameField set), or by the
     universal `participantId` UUID shown in the "ID" column (works
     regardless of storage engine or Prolific involvement).
  3. Select that row and use the download buttons to save:
       - the participant JSON (single-participant or "download selected")
       - the screen recording zip (IconDeviceDesktopDown button)
       - the audio zip, if separately recorded
  4. Note where your browser saved these files (usually ~/Downloads).

Usage:
  python import_local_export.py --json ~/Downloads/forecast-charts_all.json \\
      --screen-recording-zip ~/Downloads/forecast-charts_screenRecording.zip \\
      --pid <participantId-or-marker-substring> \\
      --out analysis/<studyName>/refinement/rounds/1/data/session

Resulting layout (under --out), matching fetch_reviewer_session.py's output
so downstream scripts (analyze_refinement.py) work identically either way:
  participantData.json
  screenRecording/{taskIdentifier}.webm
  audio/{taskIdentifier}.webm            (only if provided)
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


def find_marker_value(participant: dict) -> str | None:
    for identifier, answer in participant.get("answers", {}).items():
        if not identifier.startswith("introduction"):
            continue
        for value in (answer.get("answer") or {}).values():
            if isinstance(value, str) and value:
                return value
    return None


def find_participant(doc, match: str) -> dict | None:
    """doc may be a single ParticipantData object or a list (from a
    multi-participant JSON download). Match against participantId or the
    marker value found on the introduction component."""
    participants = doc if isinstance(doc, list) else [doc]
    for p in participants:
        if p.get("participantId") == match:
            return p
        marker = find_marker_value(p)
        if marker and match in marker:
            return p
    return None


def extract_zip_for_pid(zip_path: Path, pid: str, out_dir: Path) -> int:
    """Extract entries for this participant into out_dir, stripping the
    filename down to {taskIdentifier}.webm.

    The app's download buttons (handleDownloadFiles.ts) name files
    '{namePrefix}_{participantId}_{identifier}.webm', where namePrefix
    defaults to the studyId — NOT '{participantId}_{identifier}.webm'. Match
    on '_{pid}_' occurring anywhere in the name (namePrefix may itself
    contain underscores, e.g. 'forecast-charts') and take everything after it
    as the identifier.
    """
    count = 0
    marker = f"_{pid}_"
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            base = Path(name).name
            idx = base.find(marker)
            if idx == -1:
                continue
            identifier = base[idx + len(marker):]
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / identifier).write_bytes(zf.read(name))
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", required=True, help="path to the exported participant JSON (single participant or array)")
    parser.add_argument("--screen-recording-zip", help="path to the exported screen recording zip")
    parser.add_argument("--audio-zip", help="path to the exported audio zip, if applicable")
    parser.add_argument("--pid", required=True, help="participantId (UUID) or a marker substring to identify the session within the JSON")
    parser.add_argument("--out", required=True, help="output directory for this round's session data")
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.is_file():
        sys.exit(f"not found: {json_path}")
    doc = json.loads(json_path.read_text())
    participant = find_participant(doc, args.pid)
    if not participant:
        sys.exit(f"no participant matching {args.pid!r} found in {json_path}")

    pid = participant["participantId"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "participantData.json").write_text(json.dumps(participant, indent=2))
    print(f"matched participant {pid} -> {out / 'participantData.json'}")

    if args.screen_recording_zip:
        n = extract_zip_for_pid(Path(args.screen_recording_zip), pid, out / "screenRecording")
        print(f"screenRecording: extracted {n} file(s)")
    if args.audio_zip:
        n = extract_zip_for_pid(Path(args.audio_zip), pid, out / "audio")
        print(f"audio: extracted {n} file(s)")

    if not args.screen_recording_zip and not args.audio_zip:
        print("no media zips provided \u2014 only participantData.json was imported")

    print(f"\nDone. Session data in {out}")


if __name__ == "__main__":
    main()
