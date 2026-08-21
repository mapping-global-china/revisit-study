#!/usr/bin/env python3
"""Fetch one reviewer's session (participantData + screen recording) from Supabase.

ONLY works when the study's VITE_STORAGE_ENGINE is "supabase" (or the study
was deployed with hosted Supabase). If the study runs locally with
VITE_STORAGE_ENGINE="localStorage", the session data lives in the browser's
IndexedDB, not any cloud bucket — use import_local_export.py instead.

Standalone — does not require the study's full analysis/<studyName>/ Quarto
project to exist. Finds the reviewer's session by matching either:
  - the universal `participantId` (a UUID auto-generated for every session,
    visible in the Analyze & Manage UI's "ID" column with a copy button,
    regardless of storage engine or whether Prolific is involved) via --pid
  - a marker string (e.g. "REVIEWER-lace-padilla") typed into the study's
    existing id-capture field (e.g. the Prolific ID field) via --marker —
    useful when you don't want to look up the UUID by hand

Usage:
  export SUPABASE_URL=...        # from the study's own analysis/<study>/fetch_data.py
  export SUPABASE_ANON_KEY=...   # or the study's deploy script
  python fetch_reviewer_session.py <studyName> --marker REVIEWER-lace-padilla \\
      --out analysis/<studyName>/refinement/rounds/1/data/session --dev
  # or, if you already copied the participant ID from Analyze & Manage:
  python fetch_reviewer_session.py <studyName> --pid <uuid> --out ... --dev

Resulting layout (under --out):
  participantData.json
  screenRecording/{taskIdentifier}.webm
  audio/{taskIdentifier}.webm            (only if present)
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.request
from pathlib import Path

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # fall back to system certs
    _SSL_CONTEXT = ssl.create_default_context()

BUCKET = "revisit"


def _request(url: str, key: str, token: str | None = None, body: dict | None = None) -> bytes:
    req = urllib.request.Request(url, method="POST" if body is not None else "GET")
    req.add_header("apikey", key)
    req.add_header("Authorization", f"Bearer {token or key}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(body).encode()
    with urllib.request.urlopen(req, context=_SSL_CONTEXT) as resp:
        return resp.read()


def _anon_token(base: str, key: str) -> str:
    raw = _request(f"{base}/auth/v1/signup?grant_type=anonymous", key, body={})
    return json.loads(raw)["access_token"]


def _list_objects(base: str, key: str, token: str, prefix: str) -> list[str]:
    names, offset = [], 0
    while True:
        raw = _request(
            f"{base}/storage/v1/object/list/{BUCKET}",
            key, token,
            {"prefix": prefix, "limit": 100, "offset": offset},
        )
        batch = json.loads(raw)
        names.extend(o["name"] for o in batch if o.get("id"))
        if len(batch) < 100:
            return names
        offset += 100


def _download(base: str, key: str, token: str, path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(
        _request(f"{base}/storage/v1/object/{BUCKET}/{path}?cb={int(time.time())}", key, token),
    )


def _find_marker_value(participant: dict) -> str | None:
    """Best-effort: look for the marker string in any shortText answer on
    the introduction component (field id varies: reviewerId, prolificId, ...)."""
    for identifier, answer in participant.get("answers", {}).items():
        if not identifier.startswith("introduction"):
            continue
        for value in (answer.get("answer") or {}).values():
            if isinstance(value, str) and value:
                return value
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study_name", help="the study's folder name, e.g. forecast-charts")
    parser.add_argument("--marker", help="marker string typed into the intro id field, e.g. REVIEWER-lace-padilla")
    parser.add_argument("--pid", help="the universal participantId (UUID) from the Analyze & Manage UI's ID column — skips marker matching")
    parser.add_argument("--dev", action="store_true", help="use dev-<studyName> prefix instead of prod-<studyName>")
    parser.add_argument("--out", required=True, help="output directory for this round's session data")
    parser.add_argument("--limit", type=int, default=50, help="max participants to scan when matching by marker")
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        sys.exit(
            "SUPABASE_URL / SUPABASE_ANON_KEY not set.\n"
            "Find these in the study's own analysis/<studyName>/fetch_data.py "
            "(DEFAULT_URL / DEFAULT_ANON_KEY) or its deploy script, then export them."
        )
    url = url.rstrip("/")

    prefix = f"{'dev' if args.dev else 'prod'}-{args.study_name}"
    token = _anon_token(url, key)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    pid = args.pid
    if not pid:
        if not args.marker:
            sys.exit("pass --marker <string> or --pid <participantId>")
        names = _list_objects(url, key, token, f"{prefix}/participants")
        candidates = [n.removesuffix("_participantData") for n in names if n.endswith("_participantData")]
        candidates = candidates[: args.limit]
        print(f"scanning {len(candidates)} participant(s) for marker {args.marker!r}...")
        for candidate in candidates:
            raw = _request(f"{url}/storage/v1/object/{BUCKET}/{prefix}/participants/{candidate}_participantData?cb={int(time.time())}", key, token)
            participant = json.loads(raw)
            value = _find_marker_value(participant)
            if value and args.marker in value:
                pid = candidate
                (out / "participantData.json").write_text(json.dumps(participant, indent=2))
                print(f"matched participant {pid} (marker field = {value!r})")
                break
        if not pid:
            sys.exit(f"no participant found with marker {args.marker!r} among {len(candidates)} scanned — try --pid or increase --limit")
    else:
        _download(url, key, token, f"{prefix}/participants/{pid}_participantData", out / "participantData.json")
        print(f"fetched participant {pid}")

    for kind in ("audio", "screenRecording"):
        names = _list_objects(url, key, token, f"{prefix}/{kind}")
        matches = [n for n in names if n.startswith(f"{pid}_")]
        if not matches:
            continue
        print(f"{kind}: {len(matches)} file(s)")
        for name in matches:
            identifier = name.removeprefix(f"{pid}_")
            dest = out / kind / f"{identifier}.webm"
            _download(url, key, token, f"{prefix}/{kind}/{name}", dest)
            print(f"  {dest}")

    print(f"\nDone. Session data in {out}")


if __name__ == "__main__":
    main()
