#!/usr/bin/env python3
"""Inventory screen recordings for usability analysis.

Scans a media directory for video files, matches ReVISit `{pid}_{taskId}`
filenames against known participant ids, assigns pseudonyms (P01, P02, ...),
probes durations with ffprobe when available (honest `null` otherwise), and
emits a chunk plan for long recordings.

Usage:
  python video_inventory.py <media-dir> [--participants <dir-of-pid-jsons>]
      [--chunk-minutes 10] [--overlap-seconds 30] [--out inventory.json]

Output (stdout or --out): JSON with `ffprobe_available`, `videos` (path,
pseudonym, participant id, task, trial, duration_seconds, chunks), and the
pid->pseudonym `pseudonym_map`. Keep the output inside gitignored data/.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_EXTS = {".webm", ".mp4", ".mov", ".mkv", ".avi"}


def known_pids(participants_dir: Path | None) -> list[str]:
    """Participant ids from data/participants/ filenames ({pid}.json or {pid}_participantData)."""
    if not participants_dir or not participants_dir.is_dir():
        return []
    pids = set()
    for f in participants_dir.iterdir():
        if f.is_file():
            pids.add(f.name.split("_")[0].removesuffix(".json"))
    return sorted(pids, key=len, reverse=True)  # longest first for prefix matching


def split_name(stem: str, pids: list[str]) -> tuple[str | None, str | None, int | None]:
    """Return (pid, task, trial) from '{pid}_{task}_{trial}' or '{pid}_{task}'.

    Prefers matching a known pid prefix (pid formats vary: uuid4, 24-char hex,
    arbitrary test strings), falling back to first-underscore split.
    """
    for pid in pids:
        if stem == pid:
            return pid, None, None
        if stem.startswith(pid + "_"):
            rest = stem[len(pid) + 1:]
            m = re.match(r"^(.*)_(\d+)$", rest)
            if m:
                return pid, m.group(1), int(m.group(2))
            return pid, rest, None
    if "_" in stem:
        pid, rest = stem.split("_", 1)
        m = re.match(r"^(.*)_(\d+)$", rest)
        if m:
            return pid, m.group(1), int(m.group(2))
        return pid, rest, None
    return None, None, None


def probe_duration(path: Path) -> float | None:
    """Duration in seconds via ffprobe, or None if unavailable/unparseable.

    MediaRecorder webms (ReVISit screen recordings) often lack a duration
    header, so when ffprobe reports N/A we fall back to decoding the file
    with ffmpeg and parsing the final progress timestamp.
    """
    if not shutil.which("ffprobe"):
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=60, check=True,
        ).stdout.strip()
        if out and out != "N/A":
            return float(out)
    except (subprocess.SubprocessError, ValueError, OSError):
        return None
    if not shutil.which("ffmpeg"):
        return None
    try:
        err = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "quiet", "-stats",
             "-i", str(path), "-f", "null", "-"],
            capture_output=True, text=True, timeout=300,
        ).stderr
        times = re.findall(r"time=(\d+):(\d\d):(\d\d(?:\.\d+)?)", err)
        if times:
            h, m, s = times[-1]
            return int(h) * 3600 + int(m) * 60 + float(s)
    except (subprocess.SubprocessError, ValueError, OSError):
        pass
    return None


def chunk_plan(duration: float | None, chunk_s: int, overlap_s: int) -> list[dict] | None:
    """Chunks in the ORIGINAL timebase, overlapping so events at boundaries aren't lost."""
    if duration is None:
        return None
    if duration <= chunk_s:
        return [{"start_seconds": 0.0, "end_seconds": round(duration, 1)}]
    chunks, start = [], 0.0
    while start < duration:
        end = min(start + chunk_s, duration)
        chunks.append({"start_seconds": round(start, 1), "end_seconds": round(end, 1)})
        if end >= duration:
            break
        start = end - overlap_s
    return chunks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("media_dir", type=Path)
    ap.add_argument("--participants", type=Path, default=None)
    ap.add_argument("--chunk-minutes", type=int, default=10)
    ap.add_argument("--overlap-seconds", type=int, default=30)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if not args.media_dir.is_dir():
        print(f"error: media dir not found: {args.media_dir}", file=sys.stderr)
        return 1

    pids = known_pids(args.participants)
    ffprobe_ok = shutil.which("ffprobe") is not None
    files = sorted(p for p in args.media_dir.rglob("*")
                   if p.is_file() and p.suffix.lower() in VIDEO_EXTS)

    pseudonyms: dict[str, str] = {}
    videos = []
    for f in files:
        pid, task, trial = split_name(f.stem, pids)
        if pid is not None and pid not in pseudonyms:
            pseudonyms[pid] = f"P{len(pseudonyms) + 1:02d}"
        dur = probe_duration(f)
        videos.append({
            "path": str(f),
            "participant_id": pid,
            "pseudonym": pseudonyms.get(pid) if pid else None,
            "task": task,
            "trial": trial,
            "duration_seconds": dur,
            "chunks": chunk_plan(dur, args.chunk_minutes * 60, args.overlap_seconds),
        })

    result = {
        "ffprobe_available": ffprobe_ok,
        "note": None if ffprobe_ok else
            "ffprobe not found — durations and chunk plans are null; install ffmpeg or supply durations manually",
        "video_count": len(videos),
        "pseudonym_map": pseudonyms,
        "videos": videos,
    }
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"wrote {args.out} ({len(videos)} videos, ffprobe={'yes' if ffprobe_ok else 'NO'})")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
