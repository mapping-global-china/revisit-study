#!/usr/bin/env python3
"""On-demand design-review analysis of a researcher's screen recording(s).

Distinct from revisit-usability-analysis's analyze_usability.py: this prompt
asks the model to evaluate DESIGN FIDELITY (does the study match its source
paper/protocol, is the wording/flow/measurement right) rather than naive-user
usability friction. The reviewer is assumed to be a researcher/co-author, and
their spoken commentary is the primary signal, not a symptom to interpret.

Grounds the prompt in the task's config.json instruction AND, when present,
the study's README "Original vs. this replication" table, so the model can
flag whether a concern is already a documented deviation or a new one.

This script only produces RAW model output per recording — it does not write
revision_notes.json itself. Read the raw output and hand-write
revision_notes.json following references/finding-schema.md (same division of
labor as revisit-usability-analysis: the agent synthesizes findings, scripts
only fetch/cache/validate/render).

Usage:
  export GEMINI_API_KEY=...
  python analyze_refinement.py <session-dir> --config public/<study>/config.json \\
      [--readme public/<study>/README.md] --out <round-dir>/data/raw

Instead of exporting the key every session, put it once in a gitignored
analysis/<studyName>/.env file (KEY=value, one per line — same convention as
analysis/chart-assistant/.gitignore's `.env` entry). This script loads that
file automatically (without overwriting a shell-exported value) before
checking for the key — never commit this file, and never put the key
anywhere else in the repo.

Cache (delete a file to regenerate):
  <out>/{taskIdentifier}.json   # raw Gemini observation list per recording
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path


def load_dotenv(session_dir: Path) -> None:
    """Load KEY=VALUE lines from analysis/<studyName>/.env into os.environ,
    without overwriting a variable already exported in the shell. Stdlib
    only (no python-dotenv dependency) — matches this repo's convention of
    keeping analysis secrets in a gitignored per-study .env file (see
    analysis/chart-assistant/.gitignore) rather than committing them or
    requiring `export` every session.

    session_dir is the fetched session folder (.../refinement/rounds/<n>/data/session);
    the .env is looked up at analysis/<studyName>/.env, two levels above
    the 'rounds' folder.
    """
    # session_dir: analysis/<study>/refinement/rounds/<n>/data/session
    # study root:  analysis/<study>/
    study_dir = session_dir.resolve()
    for _ in range(6):
        if study_dir.name == "refinement":
            study_dir = study_dir.parent
            break
        study_dir = study_dir.parent
    env_path = study_dir / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def component_name(identifier: str) -> str:
    return re.sub(r"_\d+$", "", identifier)


def task_instruction(config: dict, component: str) -> str:
    comps = config.get("components", {})
    base_comps = config.get("baseComponents", {})
    comp = dict(base_comps.get(comps.get(component, {}).get("baseComponent", ""), {}))
    comp.update(comps.get(component, {}))
    return comp.get("instruction", "") or comp.get("description", "")


def extract_readme_table(readme_text: str) -> str:
    """Best-effort: pull the 'Original vs. this replication' section, else empty."""
    marker = "Original vs. this replication"
    idx = readme_text.find(marker)
    if idx == -1:
        return ""
    rest = readme_text[idx:]
    next_heading = re.search(r"\n## ", rest[1:])
    return rest[: next_heading.start() + 1] if next_heading else rest


OBSERVATION_PROMPT_TEMPLATE = """
You are helping analyze a recording of a RESEARCHER (not a naive study
participant) reviewing a research study's design by taking it themselves and
narrating their reactions. Their comments are meta-commentary about whether
the study is faithful to its intended design (a source paper, protocol, or
spec), not reports of confusion as an end user.

Task being reviewed ('{component}'):
  "{instruction}"

{grounding_section}

Watch and listen carefully. Report every meaningful sequence involving:
- the reviewer comparing what they see/do to what they expected from the
  source design (wording, sequencing, measurement, stimulus rendering)
- explicit statements that something should be built differently, with their
  stated reasoning
- genuine software defects (crashes, broken interactions) distinct from
  design-fidelity commentary
- open questions or uncertainty the reviewer voices about the design

Respond with ONLY a JSON array. Each element:
{{
  "timestamp": "mm:ss",
  "timestamp_end": "mm:ss",
  "observed": "...",
  "stated": "...",
  "interpreted": "...",
  "category_guess": "fidelity-to-source | task-wording | flow-sequencing | measurement-design | stimulus-design | technical-bug | other"
}}

Be precise about timestamps. Do not invent UI details you did not see. If the
recording is too short or content-free to assess, return [].
""".strip()


def build_prompt(component: str, instruction: str, grounding: str) -> str:
    grounding_section = ""
    if grounding:
        grounding_section = (
            "Here is the study's documented replication/design contract, so you "
            "can tell an ALREADY-DOCUMENTED deviation apart from a NEW concern "
            "the reviewer raises:\n\n" + grounding
        )
    return OBSERVATION_PROMPT_TEMPLATE.format(
        component=component, instruction=instruction, grounding_section=grounding_section,
    )


def analyze(rows: list[Path], config: dict, grounding: str, out: Path, force: bool) -> None:
    key = __import__("os").environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY not set")
    from google import genai  # pip install google-genai

    client = genai.Client(api_key=key)
    out.mkdir(parents=True, exist_ok=True)
    for i, path in enumerate(rows, 1):
        identifier = path.stem
        component = component_name(identifier)
        cache = out / f"{identifier}.json"
        label = f"[{i}/{len(rows)}] {path.name}"
        if cache.exists() and not force:
            print(f"{label} — cached, skipping", flush=True)
            continue
        print(f"{label} — uploading...", flush=True)
        video = client.files.upload(file=path)
        while video.state and video.state.name == "PROCESSING":
            time.sleep(2)
            video = client.files.get(name=video.name)
        print(f"{label} — analyzing...", flush=True)
        instruction = task_instruction(config, component)
        prompt = build_prompt(component, instruction, grounding)
        response = client.models.generate_content(
            model="gemini-flash-latest", contents=[video, prompt],
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        try:
            observations = json.loads(text)
        except json.JSONDecodeError:
            observations = {"parse_error": True, "raw_text": response.text}
        cache.write_text(json.dumps({
            "video": path.name,
            "component": component,
            "model": "gemini-flash-latest",
            "observations": observations,
        }, indent=2))
        n = len(observations) if isinstance(observations, list) else "PARSE ERROR"
        print(f"    {n} observations", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_dir", help="directory from fetch_reviewer_session.py (contains screenRecording/)")
    parser.add_argument("--config", required=True, help="path to public/<study>/config.json")
    parser.add_argument("--readme", help="path to public/<study>/README.md (optional grounding)")
    parser.add_argument("--out", required=True, help="output directory for raw analysis cache")
    parser.add_argument("--force", action="store_true", help="reprocess even if cached")
    args = parser.parse_args()

    session = Path(args.session_dir)
    load_dotenv(session)
    recordings_dir = session / "screenRecording"
    if not recordings_dir.is_dir():
        sys.exit(f"no screenRecording/ under {session}")
    rows = sorted(recordings_dir.glob("*.webm"))
    if not rows:
        sys.exit(f"no .webm files under {recordings_dir}")

    config = json.loads(Path(args.config).read_text())
    grounding = ""
    if args.readme:
        readme_path = Path(args.readme)
        if readme_path.is_file():
            grounding = extract_readme_table(readme_path.read_text())

    analyze(rows, config, grounding, Path(args.out), args.force)


if __name__ == "__main__":
    main()
