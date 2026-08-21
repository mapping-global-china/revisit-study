# Findings schema (`data/findings/findings.json`)

Top-level object:

```json
{
  "schema_version": 1,
  "study": "nyc-commute",
  "analysis_mode": "study-preflight",
  "run": {
    "date": "2026-07-30",
    "video_tool": "gemini-flash-latest",
    "video_tool_available": true,
    "fallback_evidence": [],
    "externally_processed": ["screenRecording/P01_task-1_0.webm -> Gemini Files API"],
    "code_repo": {
      "path": "/Users/x/proj",
      "commit": "abc1234",
      "branch": "main",
      "remote": "git@github.com:org/proj.git",
      "dirty": false
    }
  },
  "findings": []
}
```

- `run.video_tool_available: false` means no video model processed the recordings — every finding must then use fallback evidence types, and `run.fallback_evidence` lists what was used (`transcripts`, `frames`, `event-logs`, `user-walkthrough`).
- `run.code_repo` is `null` when no repository was supplied or the path was invalid; also set `"code_correlation": "not-performed"` at top level in that case.
- `run.externally_processed` is the privacy ledger — one entry per artifact sent to an external service.

## Finding object

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Stable, `F-` + zero-padded number (`F-001`). Never renumber after review starts. |
| `title` | string | yes | Concise, describes the problem, not the participant. |
| `category` | enum | yes | `issue-candidate` \| `needs-discussion` \| `design-opportunity`. |
| `subtype` | enum | yes | See subtype list below. |
| `severity` | enum | yes | `critical` \| `high` \| `medium` \| `low`. Impact if unaddressed — independent of category. |
| `confidence` | enum | yes | `high` \| `medium` \| `low`. How sure the evidence is — independent of severity. |
| `nature` | enum | preflight/hybrid only | `software-defect` \| `wording` \| `stimulus-condition` \| `research-protocol` \| `intentional-manipulation` \| `investigator-review`. |
| `occurrences` | array | yes, ≥1 | Each: `{"participant": "P01", "session": "...", "task": "task-1", "trial": 0, "condition": "...", "timestamp": "04:12", "timestamp_end": "04:58"}`. `timestamp` is `mm:ss` or `h:mm:ss` in the original video timebase. `session`/`trial`/`condition` optional. |
| `observed` | string | yes | What visibly happened on screen. No interpretation. |
| `stated` | string \| null | — | Participant speech, paraphrased; short quotes only when wording is the evidence. |
| `interpreted` | string \| null | — | Model/analyst reading of the sequence. |
| `hypothesis` | string \| null | — | Causal guess, labeled as such. |
| `intent` | string \| null | — | Participant goal / task context, when known. |
| `expected_vs_observed` | string \| null | — | When applicable. |
| `alternatives` | array of string | — | Competing explanations that weren't ruled out. |
| `affects` | enum | — | `all-conditions` \| `specific-conditions` \| `single-trial` \| `unknown`. |
| `code` | object \| null | — | Correlation block, below. Required to be `null` or absent when code correlation was not performed. |
| `rehydration` | object \| null | — | Provenance-rehydration block, below. Optional — omitted or `{"available": false}` for the common case of no provenance on the flagged component. See the `provenance-rehydration` skill. |
| `suggested_owner` | enum | yes | `engineering` \| `research` \| `design` \| `content` \| `discussion`. |
| `next_action` | string | yes | One concrete recommended step. |
| `open_questions` | array of string | — | What's unknown / missing evidence. |
| `privacy_notes` | string \| null | — | Redaction needs for this finding's evidence. |
| `issue_ready` | boolean | yes | `true` only when reproducible enough to draft an issue. `needs-discussion` and `design-opportunity` findings are almost never issue-ready. |

### Mixed-surface runs (study scaffold + app)

When a session discusses both study scaffolding and app behavior, keep one findings file but make surface explicit in titles and correlation:

- Prefix `title` with `[study-scaffold]`, `[app-product]`, or `[cross-boundary]`.
- `study-scaffold`: correlate first to study-repo files.
- `app-product`: correlate first to external app-repo files (when `code_repo` points there).
- `cross-boundary`: include locations from both repos when the problem spans transitions.

This keeps categorization stable while making implementation ownership clear.

### Subtypes

`interaction-bug`, `rendering-bug`, `data-bug`, `crash`, `performance`, `wording`, `study-instrument`, `study-flow`, `usability-friction`, `accessibility`, `feature-request`, `workflow-gap`, `research-protocol`, `other`.

### Code correlation block (`code`)

```json
{
  "status": "suggests",
  "commit": "abc1234",
  "locations": [
    {"file": "src/components/Map.tsx", "symbol": "renderLegend", "lines": "120-140", "why": "legend visibility gated on this flag"}
  ],
  "alternative_locations": [],
  "tests": "no existing coverage for legend toggling",
  "repro_path": "load config with legend:false, toggle condition B"
}
```

- `status`: `confirms` (code demonstrably produces observed behavior) | `suggests` (plausible mechanism, unverified) | `contradicts` (code implies different behavior — revisit interpretation) | `not-correlated` (searched, no defensible connection; `locations` must be empty).
- `commit` must equal `run.code_repo.commit`.
- Never invent locations: if you didn't open the file at that commit, it doesn't go in `locations`.

### Provenance-rehydration block (`rehydration`)

Produced by the `provenance-rehydration` skill when the flagged component is
a `react-component` stimulus with a recorded trrack `provenanceGraph`. Read
`.github/skills/provenance-rehydration/references/rehydration-guide.md` for
the full mechanism (timing-anchor caveat, code correlation, degrade modes).

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

- `available: false` (or the whole block omitted) is the common case — most findings have no provenance (markdown/questionnaire/website components, or a react-component that didn't track state). Never treat its absence as an error.
- `timing_confidence`: `approximate` \| `low` — never `exact`; video and trrack clocks are aligned via an anchor, not natively synchronized.
- `repro_spec_path` is only set when the user confirmed generating a repro spec (Step 4 of the `provenance-rehydration` skill) — it's optional even when `available: true`.

## Rules enforced by `scripts/validate_findings.py`

- Required fields present; enums valid; ids unique and `F-\d+` shaped.
- Every finding has ≥1 occurrence with a valid `mm:ss`/`h:mm:ss` timestamp.
- `code.status != "not-correlated"` requires non-empty `locations` and a `commit` matching `run.code_repo.commit`; any `code` block requires `run.code_repo` to be present.
- `issue_ready: true` requires `category: issue-candidate` and `confidence != low`.
- `category: needs-discussion` requires at least one entry in `open_questions`.
- `severity`, `confidence`, `category` are independent — the validator never infers one from another.
- `rehydration`, when present, must have a boolean `available`; when `available: true`, `node_id`, `event`, and `timing_confidence` (one of `approximate`/`low`) are required.
