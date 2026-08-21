---
name: revisit-usability-analysis
description: Analyze ReVISit screen recordings for usability findings — watch recordings of people testing a prototype or piloting a study, extract timestamped observations, classify them as GitHub issue candidates, needs-discussion items, or design opportunities, optionally correlate findings with a local code repository, and produce a Quarto report plus local issue drafts. Use when the user wants to "review the recordings", "find usability problems", "turn videos into issues", "preflight the study", "analyze pilot sessions", or asks what recordings reveal about bugs or confusing UX in this repo or another prototype.
---

You are running a usability analysis of screen recordings from a ReVISit study or prototype test. Recordings are the primary evidence; participant answers, provenance graphs, transcripts, and the study config are supporting context. Outputs extend the study's existing `analysis/<studyName>/` Quarto project (the `revisit-analysis` skill's layout). If that folder doesn't exist yet, run the `revisit-analysis` skill first to scaffold it — do not duplicate its instructions here.

When the prototype app source is in a separate non-ReVISit repository, run `revisit-multi-repo-context` first so `code_repo` is explicit and output paths stay anchored in the study repo.

**Inputs (accept via natural language, no rigid syntax):**

- `recordings` (required) — local video files, a directory, the study's `data/media/screenRecording/` (fetch with the study's `fetch_data.py --media` if absent), or a study name whose media the existing tooling can retrieve.
- `study_context` — what the prototype/study is, the participant task, intended behavior, priorities.
- `analysis_mode` — `prototype-usability`, `study-preflight`, `hybrid`, or `auto` (default). Under `auto`, infer: recordings of lab members taking a study before launch → preflight; recordings of target users on a tool → prototype-usability; both concerns → hybrid. State the inferred mode and let the user correct it.
- `code_repo` — optional repository path (`.`, relative, or absolute). `.` means this ReVISit repo. In split-repo iframe studies, set this to the external app repo captured by `revisit-multi-repo-context`.
- `video_model` — optional video-capable model/tool. Detect what's actually available (below); never assume a provider.
- `output_dir` — defaults to `analysis/<studyName>/`.
- `github_target` — repo where issue drafts would eventually belong (recorded in drafts only).
- `publish_issues` — **false by default; never create GitHub issues without the user explicitly authorizing it in this conversation.** This skill only writes local drafts.
- `privacy_constraints` — project-specific redaction or external-processing rules; ask if unstated and external AI processing is about to happen.

For mixed recordings that include both study scaffolding and app usage, classify observations by surface from the start:

- `study-scaffold`: intro/debrief copy, consent framing, questionnaire wording/scales, sequence flow, completion/redirect messaging.
- `app-product`: behavior inside the embedded app/stimulus.
- `cross-boundary`: friction when transitioning between scaffold and app contexts.

## 1. Establish context and provenance

1. **Inventory recordings**: run `scripts/video_inventory.py <media-dir> --participants <data/participants dir>` — it matches `{pid}_{taskId}` filenames against known participant ids, probes durations via ffprobe (honestly reporting `null` when ffprobe is unavailable), assigns pseudonyms (`P01`, `P02`, …), and emits a chunk plan for long videos. Use pseudonyms in all outputs; keep the pid↔pseudonym map only in `data/findings/inventory.json` (gitignored under `data/`).
2. **Join study metadata** where available: reuse the study's `study_context.py` (`media_index()`, `task_context()`, `llm_task_preamble()`) to attach task, instruction, trial order, and condition to each recording. For multi-condition studies, recover the condition per participant so findings can be marked all-conditions vs condition-specific.
3. **Validate `code_repo`** if given: confirm the path exists and is a git repo; record commit (`git rev-parse HEAD`), branch, remote, and dirty/clean status. **Read-only** — never modify, checkout, or clean it. If the path is invalid or not a repo, tell the user, set code correlation to "not performed", and continue video-only.
4. **Learn intended behavior before judging**: read the study `config.json` (instructions, response definitions, conditions), repo docs/specs/tests, and the user's context. In preflight mode, list the experimental manipulations up front so surprising-but-intentional behavior isn't misfiled as a bug.
5. Record run provenance: analysis date, model/tool used per artifact, repo commit, and which artifacts were sent to external services.
6. Create a quick surface map (`study-scaffold`/`app-product`/`cross-boundary`) for this run and keep it alongside the run notes; use it to avoid blending unrelated root causes.

## 2. Analyze recordings

**Capability detection first.** Check, in order: (a) a user-named `video_model`; (b) `GEMINI_API_KEY` + `google-genai` in the study venv (the `revisit-analysis` pipeline's default — upload, poll until not `PROCESSING`, `gemini-flash-latest`); (c) any other approved video-capable tool the user confirms. **Consent gate:** before uploading any recording, transcript, or frame to an external service, confirm the user approves that service for this project's data (ask once, remember the answer, honor `privacy_constraints`).

**If no video capability exists, say so plainly.** Never claim to have watched or verified a video you didn't process. Offer the truthful fallback ladder and label every resulting finding with its actual evidence source: cached Deepgram transcripts (`data/transcripts/`) → extracted frames (ffmpeg, if present) → provenance event logs → a user-supplied walkthrough. State the limitation in the report's scope section.

**Run analysis as an on-demand script, never at render time.** Add `analyze_usability.py` to the study folder following the `process_media.py` pattern exactly: per-file progress prints, skip-if-cached (cache raw model output in `data/findings/raw/{pseudonym}_{taskId}.json`), `--only`/`--force` flags, keys from env only. Prompt = `llm_task_preamble(component)` + a structured observation request covering:

- Errors, crashes, broken interactions, incorrect results, visual defects.
- Repeated attempts, backtracking, hesitation, long pauses, misclicks, recovery, abandonment.
- Confusing wording, ambiguous controls, unclear system state, weak feedback, expectation mismatches.
- Spoken bug reports, questions, feature ideas, workarounds, unmet needs.
- Divergence between what the participant says, does, and what the interface shows.

Require a `mm:ss` timestamp (or range) for every observation. Instruct the model to tag each observation as **observed** (visible on screen), **stated** (participant said it), or **interpreted** (model inference) — this distinction survives into findings.

**Long recordings**: follow the inventory's chunk plan (e.g. 10-min chunks, 30 s overlap). Always report timestamps in the *original* video timebase (add the chunk offset); reconcile duplicate observations in overlap windows instead of double-counting. **Spot-check** every high-severity finding against an extracted frame, transcript excerpt, or event-log entry before promoting it — model video analysis hallucinates UI details.

## 3. Create normalized findings

Write `data/findings/findings.json` following `references/finding-schema.md` — **read that file now** for the exact fields, enums, and rules. Core discipline:

- Stable ids `F-001, F-002, …`; category `issue-candidate` | `needs-discussion` | `design-opportunity`; a specific subtype; **severity and confidence are separate dimensions from category** — a high-impact confusing interaction with an unclear cause is high-severity `needs-discussion`, not a low-confidence issue.
- One finding per underlying problem: merge repeated instances into one finding with an `occurrences` list — but keep separate findings when contexts differ enough to have different causes.
- Prefix the finding title with the surface for scanability when mixed: `[study-scaffold]`, `[app-product]`, or `[cross-boundary]`.
- Preserve evidence types (observed / stated / interpreted / hypothesized / code-supported) in the description blocks; paraphrase participant speech, quoting only short fragments when the wording itself is the evidence.
- When uncertain between categories, choose `needs-discussion` and record the open questions — do not force ambiguous evidence into issue-candidate.
- Validate with `scripts/validate_findings.py data/findings/findings.json` and fix every error.

## 4. Correlate with code (only when `code_repo` is valid)

Search the repo read-only: source, styles, routes, schemas, study `config.json` wording/stimuli/conditions, tests, TODOs, docs. For each finding, either attach a correlation or mark it `not-correlated` — **never fabricate a location to make a finding look actionable.** For `study-scaffold` findings, prioritize study-repo files; for `app-product`, prioritize `code_repo`; for `cross-boundary`, cite both repos when warranted. Each correlation must cite the recorded commit, exact files (and symbols/lines when helpful), and a `relationship` of `confirms` (code demonstrably produces the observed behavior), `suggests` (plausible mechanism, unverified), or `contradicts` (code says the behavior should differ — revisit the interpretation). List alternative candidate locations when attribution is uncertain. Note existing or missing test coverage and a likely reproduction path. Do not modify the repo — implementation is a separate, explicit user request.

**Rehydrate provenance when available**: if a finding's flagged component is a `react-component` stimulus with a recorded trrack `provenanceGraph` on that answer, invoke the `provenance-rehydration` skill (read its SKILL.md) to attach a `rehydration` block — this reconstructs the exact application state and action sequence at that timestamp (via `analysis/primitives.py`, not a reimplementation) and can sharpen code correlation directly to the `registry.register(...)` call that produced the observed behavior. For `issue_ready` findings with `severity: high`/`critical`, offer (don't auto-run) generating a repro spec via that skill's Step 4 — this gives the engineer a colocated Vitest scaffold that mounts the real component with the reconstructed state, instead of prose repro steps.

For website/iframe wrappers, provenance rehydration is often unavailable or partial. In that case, keep findings grounded in video evidence and correlate against the external `code_repo` where possible; do not force a provenance-derived explanation.

## 5. Issue drafts (local only)

For findings with `issue_ready: true`, run `scripts/make_issue_drafts.py data/findings/findings.json --out data/findings/issues/` to generate one Markdown draft per finding — structure in `references/report-and-issue-structure.md`. Drafts distinguish observed from inferred repro steps, cite the repo commit, and include acceptance criteria and a validation plan. **Redaction is enforced**: no participant names, raw pids, private video URLs, or long quotations; evidence is cited as `P03 @ 04:12`, never linked media, unless the project's privacy rules explicitly allow attachments. Review drafts with the user; creating actual GitHub issues stays a separate action the user must explicitly request (and only then use `github_target`).

## 6. Quarto report

Add `usability.qmd` to the study's Quarto site (register it in `_quarto.yml`'s navbar) — section-by-section structure in `references/report-and-issue-structure.md`, **read it before writing the page**. The page only *reads* caches (`findings.json`, raw model outputs, inventory) — no AI calls at render time. Verify `quarto render` succeeds. The machine-readable artifact is `findings.json` (no CSV — the existing workflow doesn't use one).

## Study-preflight safeguards

In preflight (or hybrid) mode, classify each finding's nature explicitly: software defect / wording-instruction problem / stimulus-condition problem / research-protocol concern / **intentional experimental manipulation** / needs-investigator-review. When a "bug" might be a manipulation (odd color scales, withheld legends, asymmetric conditions), check the config's conditions and any preregistration/design notes; if still unclear, file it as `needs-discussion` with `suggested_owner: research` — never as an issue-candidate with a proposed fix. Any change that could alter experimental validity (timing, wording, stimulus rendering, condition balance) routes to investigator discussion even when the code fix is trivial. Note whether each finding affects all conditions or specific trials/conditions.

## Research-data handling

Treat recordings as human-subject data: minimum necessary exposure, pseudonyms everywhere, no judgments about participants (describe interface/study behavior instead), keep raw media and the pid map inside gitignored `data/`, record in the report's methodology section exactly which artifacts were processed by which external service, and respect consent/retention rules the user states. When in doubt about whether something may leave the machine, ask first.

## Verify before finishing

1. `validate_findings.py` passes; every finding has timestamped evidence and a correct evidence-type label.
2. Issue drafts exist only for `issue_ready` findings and contain no identifying details.
3. `quarto render` succeeds and `usability.qmd` reads only caches.
4. Code correlations cite the recorded commit; anything unverified says so.
5. Report scope honestly states what was and wasn't actually watched/processed, and by which tool.

Report back: the findings count by category, the report path (`quarto preview` entry), the issue-draft folder, which recordings (if any) could not be analyzed and why, and open questions needing investigator or design discussion.

Also report counts by surface (`study-scaffold`, `app-product`, `cross-boundary`) when mixed-scope recordings were analyzed.
