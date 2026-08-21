# Revision-notes schema (`data/revision_notes.json`)

Adapted from `revisit-usability-analysis`'s finding-schema.md for a different
kind of evidence: a **researcher or co-author reviewing the study's design**,
not a naive participant using the tool. The reviewer's comments are about
whether the study is faithful to its source design (a paper, a prior protocol,
a spec), not about software usability bugs — though software bugs can still
surface and are captured too.

Top-level object:

```json
{
  "schema_version": 1,
  "study": "forecast-charts",
  "run": {
    "round": 1,
    "date": "2026-08-03",
    "session_type": "researcher-review",
    "reviewer": {
      "name": "Lace Padilla",
      "role": "co-author / source-paper author"
    },
    "video_tool": "gemini-flash-latest",
    "video_tool_available": true,
    "fallback_evidence": [],
    "externally_processed": ["screenRecording/REVIEWER-lace-padilla_trial-median-near-1_0.webm -> Gemini Files API"],
    "grounded_in": {
      "config": "public/forecast-charts/config.json",
      "readme": "public/forecast-charts/README.md"
    },
    "code_repo": {
      "path": "/Users/x/proj",
      "commit": "abc1234",
      "branch": "main",
      "remote": "git@github.com:org/proj.git",
      "dirty": false
    }
  },
  "revision_notes": []
}
```

- Reviewer identity is **not anonymized** — this is collaborator/co-author
  design feedback, not confidential human-subjects data. Use the reviewer's
  real name and role in `run.reviewer`.
- `run.grounded_in` records which study documents were fed to the model
  alongside the recording, so a reader can tell what "known deviation" context
  the model had. When the study's README has an "Original vs. this
  replication" table (per the `study-from-paper` skill), always include it —
  it lets the model (and a human reviewer) distinguish an **already-documented
  deviation** from a **new fidelity concern** the reviewer is raising.
- `run.video_tool_available: false` means no video model processed the
  recording — every note must then use fallback evidence (`fallback_evidence`
  lists what: `transcripts`, `frames`, `event-logs`, `reviewer-notes`).
- `run.code_repo` is `null` when no repository was supplied or the path was
  invalid; also set `"code_correlation": "not-performed"` at top level then.
- `run.externally_processed` is the privacy ledger — one entry per artifact
  sent to an external service (kept for consistency even though this data
  isn't participant-sensitive).

## Revision note object

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Stable, `RN-` + zero-padded number (`RN-001`). Never renumber after review starts. |
| `title` | string | yes | Concise, describes the design concern, not the reviewer. |
| `category` | enum | yes | `fidelity-to-source` \| `task-wording` \| `flow-sequencing` \| `measurement-design` \| `stimulus-design` \| `technical-bug` \| `other`. |
| `severity` | enum | yes | `critical` \| `high` \| `medium` \| `low`. Impact on the study's validity/results if unaddressed — independent of category. |
| `confidence` | enum | yes | `high` \| `medium` \| `low`. How sure the evidence is — independent of severity. |
| `occurrences` | array | yes, ≥1 | Each: `{"task": "trial-median-near-1", "timestamp": "01:12", "timestamp_end": "01:40"}`. `timestamp` is `mm:ss` or `h:mm:ss` in the original video timebase. `trial`/`condition` optional. |
| `observed` | string | yes | What visibly happened on screen. No interpretation. |
| `stated` | string \| null | — | Reviewer speech, paraphrased; short quotes only when wording is the evidence (real name attribution is fine here, unlike participant data). |
| `interpreted` | string \| null | — | Model/analyst reading of the sequence. |
| `hypothesis` | string \| null | — | Causal guess, labeled as such. |
| `source_reference` | string \| null | — | What the reviewer says the study *should* match (e.g. "paper's 4-step elicitation, Section 3.2: best guess on one page, then low/high on the next"). |
| `already_documented` | boolean | yes | `true` if this concern is already listed as a stated deviation in the study's README replication-contract table. If `true`, the note records that the reviewer re-raised it anyway (e.g. they think it matters more than the README implies) — it does not get silently dropped. |
| `alternatives` | array of string | — | Competing explanations that weren't ruled out. |
| `affects` | enum | — | `all-conditions` \| `specific-conditions` \| `single-trial` \| `unknown`. |
| `code` | object \| null | — | Correlation block, below. Required to be `null` or absent when code correlation was not performed. Code correlation is **important** for this skill — most revision notes should resolve to a specific file/component. |
| `rehydration` | object \| null | — | Provenance-rehydration block, below. Optional — omitted or `{"available": false}` when the flagged component has no trrack provenance. See the `provenance-rehydration` skill. |
| `suggested_owner` | enum | yes | `engineering` \| `research` \| `design` \| `content` \| `discussion`. |
| `next_action` | string | yes | One concrete recommended step. |
| `open_questions` | array of string | — | What's unknown / missing evidence. |
| `revision_ready` | boolean | yes | `true` only when specific and reproducible enough to act on directly in the next revision round (analogous to `issue_ready` in the usability schema, but scoped to design-revision work, not GitHub issues). |

### Mixed-surface runs (study scaffold + app)

When one recording contains concerns about both the study scaffold and the app itself, keep one schema but make surface explicit in note titles and code mapping:

- Prefix `title` with `[study-scaffold]`, `[app-product]`, or `[cross-boundary]`.
- `study-scaffold`: correlate first to study-repo config/assets/wiring.
- `app-product`: correlate first to external app repo paths.
- `cross-boundary`: use one note with locations from both repos when the issue spans handoff points.

This avoids creating a second schema while preserving triage clarity.

### Category guidance

- `fidelity-to-source` — the study deviates from what the source paper/protocol specified (e.g. combined-page elicitation vs. the paper's two-page elicitation).
- `task-wording` — instructions, prompts, or response labels are unclear, ambiguous, or don't match the source language.
- `flow-sequencing` — component/trial ordering, pacing, or step-by-step flow doesn't match the intended design.
- `measurement-design` — the response type, scale, or elicitation mechanism doesn't capture what the design intends to measure.
- `stimulus-design` — the visual/interactive stimulus itself doesn't match the intended manipulation or is rendered incorrectly.
- `technical-bug` — a genuine software defect unrelated to design fidelity (crashes, broken interactions).
- `other` — anything not covered above.

### Code correlation block (`code`)

Same shape as `revisit-usability-analysis`'s:

```json
{
  "status": "suggests",
  "commit": "abc1234",
  "locations": [
    {"file": "src/public/forecast-charts/assets/MfvTrial.tsx", "symbol": "MfvTrial", "lines": "1-40", "why": "single component renders all four elicitation steps on one page"}
  ],
  "alternative_locations": [],
  "tests": "no existing coverage for step pagination",
  "repro_path": "load any mfvTrial component and observe all steps in one view"
}
```

- `status`: `confirms` | `suggests` | `contradicts` | `not-correlated`.
- `commit` must equal `run.code_repo.commit`.
- Never invent locations: if you didn't open the file at that commit, it doesn't go in `locations`.

### Provenance-rehydration block (`rehydration`)

Produced by the `provenance-rehydration` skill when the flagged component is
a `react-component` stimulus with a recorded trrack `provenanceGraph` — this
is especially valuable here since a design-fidelity concern (e.g. "this
should be two pages, not one") often maps directly onto the exact state/step
the reviewer was at. Read
`.github/skills/provenance-rehydration/references/rehydration-guide.md` for
the full mechanism.

```json
{
  "available": true,
  "node_id": "n042",
  "event": "bestGuess",
  "offset_from_task_start_s": 12.4,
  "timing_confidence": "approximate",
  "timing_note": "Matched within 0.8s of the requested timestamp (tolerance 2.0s) — recording-start latency and dropped frames mean this is not frame-exact.",
  "action_sequence": [
    {"node_id": "n040", "event": "Root", "label": "Root", "offset_s": 0.0}
  ],
  "repro_spec_path": "src/public/forecast-charts/assets/MfvTrial.repro.spec.tsx"
}
```

- `available: false` (or the whole block omitted) is the common case for
  non-react-component stimuli (markdown/questionnaire/website) or ones that
  didn't track state.
- `timing_confidence`: `approximate` \| `low` — never `exact`.
- `repro_spec_path` is only set when the user confirmed generating a repro
  spec — optional even when `available: true`.

## Rules enforced by `scripts/validate_revision_notes.py`

- Required fields present; enums valid; ids unique and `RN-\d+` shaped.
- Every note has ≥1 occurrence with a valid `mm:ss`/`h:mm:ss` timestamp.
- `code.status != "not-correlated"` requires non-empty `locations` and a `commit` matching `run.code_repo.commit`; any `code` block requires `run.code_repo` to be present.
- `revision_ready: true` requires `confidence != low`.
- `category: fidelity-to-source` with `already_documented: true` still requires `next_action` (re-raised concerns aren't dropped just because they're known).
- `severity`, `confidence`, `category` are independent — the validator never infers one from another.
- `rehydration`, when present, must have a boolean `available`; when `available: true`, `node_id`, `event`, and `timing_confidence` (one of `approximate`/`low`) are required.
