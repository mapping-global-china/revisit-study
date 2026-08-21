---
name: provenance-rehydration
description: Combine a ReVISit screen recording with its trrack provenance graph to reconstruct the exact application state and action sequence at a flagged moment, correlate it to the specific code that produced it, and optionally scaffold a runnable repro test. This is a shared capability invoked as a step from revisit-usability-analysis or refinement-from-video's analysis phase — not a standalone workflow. Use when either of those skills has a timestamped finding on a react-component stimulus that tracks provenance, and a more precise repro than prose is possible.
---

You are attaching **ground-truth application state** to a video-timestamped observation, instead of relying on the video/transcript alone. This capability only applies when the flagged component is a `react-component` stimulus that recorded a trrack `provenanceGraph` — most markdown/questionnaire/website-type components have no provenance, and that's fine; degrade gracefully (see `references/rehydration-guide.md`, read it now).

**This skill is never invoked directly by a user.** It's a step inside `revisit-usability-analysis`'s or `refinement-from-video`'s analysis phase, called once per timestamped finding/note that has a candidate for rehydration.

## Inputs

- `participant_data_json` — the fetched `participantData.json` for the session being analyzed (both parent skills already fetch this).
- `identifier` — the answer identifier for the flagged component instance (e.g. `trial-median-near-1_1`).
- `video_timestamp` — the `mm:ss` timestamp from the finding's `occurrences`.
- `study_name` — for code correlation.
- `code_repo` — whether/where the repo is available (mirrors the parent skill's own `code_repo` input; don't re-ask if already confirmed there).

## Step 1 — Check provenance availability

Load the answer from `participant_data_json[answers][identifier]`. Call `scripts/rehydrate_node.py`'s `has_provenance(answer)` logic (or run the CLI) — if false, stop here: the finding gets no `rehydration` block (or `{"available": false}`), and this is the normal case, not a failure to report apologetically.

## Step 2 — Reconstruct state and action sequence

```
python3 .github/skills/provenance-rehydration/scripts/rehydrate_node.py \
  <participantData.json> <identifier> <mm:ss> [--tolerance-s 2]
```

This anchors the video timestamp to the task's `startTime`, finds the nearest trrack node, and returns the reconstructed state (via `analysis/primitives.py`'s `reconstruct_states` — don't reimplement this), the ordered action sequence from the task's start to that node, and a `timing_confidence`/`timing_note` pair. **Always carry the timing caveat into the finding** — never present the state as frame-exact.

## Step 3 — Correlate to code (only if `code_repo` confirmed)

```
python3 .github/skills/provenance-rehydration/scripts/correlate_action.py \
  <study_name> <event_name> --repo-root <repo_root>
```

`event_name` is the matched node's `event` field from Step 2's output. This greps the study's `trrack.ts`/`useProvenance.ts`/`SharedStateContext.tsx` for the exact `registry.register('<event_name>', ...)` call. Use the result to fill or upgrade the finding's `code` block (`status: "suggests"` with the found location, or `"not-correlated"` if nothing matched — never invent a location).

## Step 4 — Offer a repro spec (only for high-value findings, only with confirmation)

If the finding is `issue_ready`/`revision_ready` and severity is `high`/`critical`, **ask the user** before scaffolding a test — this writes a new file into `src/public/**`:

```
python3 .github/skills/provenance-rehydration/scripts/generate_repro_spec.py \
  <study>/config.json <componentInstanceName> <state.json> --repo-root <repo_root>
```

Write the reconstructed `state` from Step 2 to a temp JSON file first (the script reads it from disk). The generated spec follows this repo's existing pattern (`renderToStaticMarkup`, no jsdom) and only asserts the component renders — it leaves the actual bug assertion as a `// TODO` for the engineer. Record the written path back in the finding's `rehydration.repro_spec_path`.

## Attaching results to the parent skill's schema

Both `revisit-usability-analysis` and `refinement-from-video` define an **optional** `rehydration` block on their finding/note objects:

```json
"rehydration": {
  "available": true,
  "node_id": "n042",
  "event": "bestGuess",
  "offset_from_task_start_s": 12.4,
  "timing_confidence": "approximate",
  "timing_note": "Matched within 0.8s of the requested timestamp...",
  "action_sequence": [{"node_id": "n040", "event": "Root", "label": "Root", "offset_s": 0.0}, "..."],
  "repro_spec_path": "src/public/forecast-charts/assets/MfvTrial.repro.spec.tsx"
}
```

Omit the block entirely (or set `available: false` with no other fields) when Step 1 found no provenance — this must remain optional; most findings won't have it.

## Common pitfalls

- **Treating rehydrated state as exact.** It's an approximation anchored to task `startTime` — always propagate `timing_confidence`/`timing_note`, never round it off to "the state at that exact moment."
- **Reimplementing state reconstruction.** `analysis/primitives.py`'s `reconstruct_states` is the one source of truth for trrack checkpoint/patch replay — import it, don't rewrite it.
- **Generating a repro spec that claims to test the bug.** It only proves the component renders with the given state; the actual bug assertion is a human `// TODO`, since the script has no way to know what "correct" behavior looks like.
- **Inventing code correlations.** If `correlate_action.py` finds nothing, report `not-correlated` — don't guess a plausible-looking file.
- **Running this on components without provenance.** Check availability first every time; don't assume every finding can be rehydrated.
