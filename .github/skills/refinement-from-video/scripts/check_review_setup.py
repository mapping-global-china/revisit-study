#!/usr/bin/env python3
"""Check whether a study's config.json is ready for a researcher review recording.

Verifies three things needed for refinement-from-video to work:
  1. Screen recording is enabled (uiConfig.recordScreen + "screen-recording" in
     importedLibraries + the permission component present in the sequence).
  2. Audio (think-aloud) recording is enabled (uiConfig.recordAudio) — this is
     NOT implied by recordScreen; the point of a researcher review is spoken
     design-fidelity commentary, so audio is required, not optional, for this
     skill. Screen recording alone captures video with no narration.
  3. There is a shortText response field the reviewer can use to tag their
     session with a marker string (e.g. "REVIEWER-lace-padilla") instead of a
     real participant/Prolific ID.

Never edits the config. Prints a plain-language report and, if something is
missing, a concrete proposed diff for a human to review and apply.

Usage: python check_review_setup.py <path-to-config.json>
Exit 0 = ready; exit 1 = missing something (see stdout for proposed fixes).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def find_marker_field(config: dict) -> tuple[str, str] | None:
    """Return (componentName, responseId) of the first shortText field with a
    paramCapture, or any shortText field on the introduction component."""
    components = config.get("components", {})
    intro = components.get("introduction", {})
    for r in intro.get("response", []):
        if r.get("type") == "shortText":
            return "introduction", r.get("id", "")
    return None


def has_screen_recording(config: dict) -> tuple[bool, list[str]]:
    reasons = []
    ui = config.get("uiConfig", {})
    libs = config.get("importedLibraries", [])
    ok = True

    if not ui.get("recordScreen"):
        ok = False
        reasons.append("uiConfig.recordScreen is not true")
    if "screen-recording" not in libs:
        ok = False
        reasons.append('"screen-recording" not in importedLibraries')

    sequence_str = json.dumps(config.get("sequence", {}))
    if "$screen-recording.components.screenRecordingPermission" not in sequence_str:
        ok = False
        reasons.append("screenRecordingPermission component not found in sequence")

    return ok, reasons


def has_audio_recording(config: dict) -> tuple[bool, list[str]]:
    """Think-aloud audio is a separate flag from screen recording — recordScreen
    does NOT imply recordAudio. A researcher review without audio only captures
    video with no narration, defeating the point of this skill."""
    ui = config.get("uiConfig", {})
    if ui.get("recordAudio"):
        return True, []
    return False, ["uiConfig.recordAudio is not true (think-aloud commentary will not be recorded)"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_path", help="path to public/<studyName>/config.json")
    args = parser.parse_args()

    path = Path(args.config_path)
    if not path.is_file():
        sys.exit(f"not found: {path}")
    config = json.loads(path.read_text())

    recording_ok, recording_reasons = has_screen_recording(config)
    audio_ok, audio_reasons = has_audio_recording(config)
    marker = find_marker_field(config)

    print(f"Study config: {path}")
    print(f"Screen recording ready: {recording_ok}")
    for reason in recording_reasons:
        print(f"  - missing: {reason}")
    print(f"Audio (think-aloud) recording ready: {audio_ok}")
    for reason in audio_reasons:
        print(f"  - missing: {reason}")

    if marker:
        print(f"Marker field found: components.{marker[0]}.response[id={marker[1]!r}]")
        print(f'  Tell the reviewer to type e.g. "REVIEWER-<name>" into this field instead of a real id.')
    else:
        print("Marker field: none found on introduction (no shortText response).")

    if recording_ok and audio_ok and marker:
        print("\nReady — no config changes needed.")
        sys.exit(0)

    print("\nProposed changes (apply manually after reviewing):")
    if not recording_ok or not audio_ok:
        print("""
  uiConfig:
    + "recordAudio": true
    + "recordScreen": true
    + "recordScreenFPS": 30

  importedLibraries:
    + "screen-recording"

  sequence.components: insert before the first recorded component:
    + "$screen-recording.components.screenRecordingPermission"
""")
    if not marker:
        print("""
  components.introduction.response: append:
    + {
    +   "id": "reviewerId",
    +   "prompt": "Reviewer name/marker (e.g. REVIEWER-lace-padilla)",
    +   "location": "belowStimulus",
    +   "type": "shortText",
    +   "placeholder": "REVIEWER-<name>",
    +   "required": false
    + }
""")
    sys.exit(1)


if __name__ == "__main__":
    main()
