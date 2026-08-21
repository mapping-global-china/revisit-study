---
name: refinement-from-video
description: Turn a researcher's own screen-recorded review of a ReVISit study into a categorized list of study-design revision notes — have a collaborator (e.g. a source-paper author) take the study as a "reviewer" narrating design-fidelity feedback, fetch that recording via reVISit's own storage, analyze it against the study's config and replication-contract README, and produce timestamped, code-correlated revision notes for the next design round. Use when the user wants to "get Lace's feedback into something actionable", "process a researcher's walkthrough recording", "turn reviewer comments into revision notes", or asks for a design-fidelity review distinct from participant usability testing.
---

You are turning a **researcher/collaborator review recording** of a ReVISit study into structured revision notes — not participant usability data. The reviewer (e.g. a paper's original author) takes the study themselves and **narrates spoken commentary (think-aloud)** about whether the study matches its intended design: fidelity to a source paper/protocol, task wording, flow/sequencing, and measurement choices. Audio is the primary evidence here, not an optional add-on to the screen recording — a review with video but no narration defeats the point of this skill. This is a sibling skill to `revisit-usability-analysis` (which handles naive-participant usability bugs) — keep them separate; don't merge outputs or reuse its finding-schema.json as-is.

**This is invoked repeatedly, once per review round**, and typically runs *before* the study has any real participant data or `analysis/<studyName>/` Quarto project — don't require that project to exist.

When the app under review lives in a separate non-ReVISit repository, run `revisit-multi-repo-context` first so the run explicitly captures `study_repo_root`, `app_repo_root`, and `code_repo` targeting.

Read `references/finding-schema.md` and `references/report-structure.md` now — they define the exact schema and report layout used below.

**Inputs (accept via natural language):**

- `study_name` (required) — must exist in `public/global.json`.
- `reviewer` — name and role (e.g. "Lace Padilla, co-author / source-paper author"). Ask if not given; this is not anonymized (collaborator feedback, not participant data).
- `round` — defaults to the next unused round number under `analysis/<studyName>/refinement/rounds/`.
- Session identifier — **two ways to point at a specific recording, both work regardless of storage engine**:
  - `pid` — the universal `participantId` (a UUID auto-generated for every session), visible in the Analyze & Manage UI's "ID" column with a copy button. Always present, whether or not Prolific is involved.
  - `marker` — a string the reviewer types into the study's existing id-capture field (e.g. `REVIEWER-lace-padilla` into the Prolific ID field) instead of a real Prolific ID, so the session is identifiable without looking up the UUID by hand.
- `storage_engine` — check the repo's `.env` (`VITE_STORAGE_ENGINE`): `supabase` → use `fetch_reviewer_session.py`; `firebase` → use `fetch_firebase_reviewer_session.mjs` with a local read-only service-account credential and the bucket that actually holds the recording; `localStorage` / local-export → use `import_local_export.py` with files the user exports by hand from Analyze & Manage's download buttons instead. If local and deployed runs are mixed across rounds, resolve and record this value per round.
- `firebase_service_account` — required for direct Firebase retrieval: a local path to an untracked service-account JSON with Storage Object Viewer and Firestore read access to the project that holds the session. Never request its contents in chat or place it in either repository.
- `firebase_storage_bucket` — required for direct Firebase retrieval. Do not assume `<project>.appspot.com`; confirm the bucket containing the study prefix and pass it explicitly.
- `code_repo` — defaults to `.` (this repo). In split-repo setups, set this explicitly to the external app repo path captured by `revisit-multi-repo-context`. Read-only correlation, same discipline as `revisit-usability-analysis`.
- `privacy_constraints` — ask if unstated and external AI processing (Gemini) is about to happen; reviewer identity itself does not need redaction, but confirm before uploading any recording externally.

When recordings discuss both the study scaffold and the app itself, classify each observation into one of three surfaces before synthesis:

- `study-scaffold`: intro text, consent framing, questionnaire wording/scales, sequence flow, completion/redirect messaging.
- `app-product`: behavior inside the embedded app/stimulus.
- `cross-boundary`: handoff friction between scaffold and app (instructions for opening/returning, context switches, completion transitions).

## Phase 1 — Confirm the study is ready for a review recording

1. Run `scripts/check_review_setup.py public/<study_name>/config.json`. This checks **three** things: screen recording (`uiConfig.recordScreen` + the `screen-recording` library + its permission component in the sequence), **audio/think-aloud recording (`uiConfig.recordAudio`)**, and a marker-capable id field. `recordScreen` does **not** imply `recordAudio` — they are independent flags, and both are required for this skill.
2. If it reports ready (screen + audio recording enabled + a marker-capable id field exists), tell the user the study's local/live URL and the marker-string convention (`REVIEWER-<name>`) to type into that field.
3. If not ready, show the exact proposed diff the script printed and **ask the user to confirm before editing** `config.json` — never silently mutate a shared study config. Apply only the pieces the user approves.
4. Tell the user: have the reviewer open the study, grant both microphone and screen-recording permissions when prompted, enter the marker string, **narrate their reactions out loud** while working through it, and let recording run to the end (or at least through the components under review).

## Phase 2 — Fetch the reviewer's session

Check which storage engine the study actually uses (`VITE_STORAGE_ENGINE` in the repo's `.env`, or the deployed study's env if it's live) — the paths below are not interchangeable. If the team switches between local and remote environments, do this check fresh for each round instead of reusing previous assumptions.

**Supabase path** (`VITE_STORAGE_ENGINE=supabase`, or a deployed study using hosted Supabase):
1. Determine the Supabase URL/anon key the study actually uses — check the study's own `analysis/<studyName>/fetch_data.py` (if it exists) for `DEFAULT_URL`/`DEFAULT_ANON_KEY`, or its deploy script/README. Export as `SUPABASE_URL`/`SUPABASE_ANON_KEY`.
2. Run:
   ```
   python3 .github/skills/refinement-from-video/scripts/fetch_reviewer_session.py \
     <study_name> --marker <marker> \
     --out analysis/<study_name>/refinement/rounds/<round>/data/session [--dev]
   ```
   Use `--pid <participantId>` instead of `--marker` if the user already copied the UUID from Analyze & Manage's "ID" column. Use `--dev` if the review happened against a dev-mode deployment.

**Firebase path** (`VITE_STORAGE_ENGINE=firebase`): Firebase is a remote storage backend. For local analysis, authenticate with a dedicated read-only service account, not a browser API key or an anonymous user session. The service account reads `participants/<pid>_participantData`, `screenRecording/<pid>_*`, and `audio/<pid>_*` under the study's `dev-` or `prod-` prefix, and writes the matching Firestore sequence assignment when present.
1. Create or reuse a service account with `Cloud Storage Object Viewer` and Firestore read access for the project that actually holds the study data. Keep its JSON outside the workspace, for example `~/.config/revisit/firebase/<project>-analysis-reader.json`, with mode `600`.
2. Confirm the bucket has the expected `dev-<studyName>/` or `prod-<studyName>/` objects before fetching. A Firebase project may use `<project>.firebasestorage.app`, a legacy `<project>.appspot.com`, or a separately configured bucket.
3. Run from the ReVISit repository:
  ```
  node .github/skills/refinement-from-video/scripts/fetch_firebase_reviewer_session.mjs \
    <study_name> --pid <participantId> \
    --out analysis/<study_name>/refinement/rounds/<round>/data/session \
    --credentials ~/.config/revisit/firebase/<project>-analysis-reader.json \
    --bucket <actual-storage-bucket> [--dev]
  ```
  Use `--dev` when the recording was made by a Vite development build; omit it for production. The script writes the same `session/` layout as the Supabase fetcher.
4. Do not copy service-account JSON or credentials into analysis artifacts or chat. If the bucket/prefix does not contain the participant object, report the exact project, bucket, and prefix checked without reporting private data; obtain access to the project/bucket that actually holds the session rather than weakening production security controls.

**Local-export path** (`VITE_STORAGE_ENGINE=localStorage`, or a Firebase deployment that does not permit the authenticated fetcher): session data lives in the browser's IndexedDB or must be exported through the app's own UI.
1. Tell the user to open **Analyze & Manage** for the study, find the reviewer's row (by the marker string in the "Name" column, or the `participantId` in the "ID" column), select it, and use the download buttons to save the participant JSON and the screen-recording (and audio, if applicable) zip — usually to `~/Downloads`.
2. Run:
   ```
   python3 .github/skills/refinement-from-video/scripts/import_local_export.py \
     --json <downloaded.json> \
     --screen-recording-zip <downloaded_screenRecording.zip> \
     --pid <participantId-or-marker-substring> \
     --out analysis/<study_name>/refinement/rounds/<round>/data/session
   ```

Either path produces the same `session/` layout, so Phase 3 works identically afterward. Confirm at least one `screenRecording/*.webm` landed in the output before continuing.

## Phase 3 — Analyze the recording(s)

1. **Consent gate**: before uploading to Gemini, confirm the user is fine sending this recording to that external service for this project (ask once per project, remember the answer, honor any stated privacy constraints).
2. Get the key into place: either `export GEMINI_API_KEY=...` for this session, or (preferred for repeat use) put it once in a gitignored `analysis/<study_name>/.env` file (`GEMINI_API_KEY=...`, one `KEY=value` per line) — `analyze_refinement.py` loads that file automatically without overwriting a shell-exported value. Confirm the study's `analysis/<study_name>/.gitignore` has a `.env` entry before creating the file (create the `.gitignore` first if the folder is new — see `analysis/chart-assistant/.gitignore` for the pattern). **Never** put the key in `config.json`, the repo-root `.env`, or anywhere that isn't gitignored.
3. Run:
   ```
   python3 .github/skills/refinement-from-video/scripts/analyze_refinement.py \
     analysis/<study_name>/refinement/rounds/<round>/data/session \
     --config public/<study_name>/config.json \
     --readme public/<study_name>/README.md \
     --out analysis/<study_name>/refinement/rounds/<round>/data/raw
   ```
   Omit `--readme` if the study has none yet. If `GEMINI_API_KEY` isn't available, say so plainly and fall back to whatever evidence exists (cached transcript via a separate Deepgram pass, or ask the user to describe what the reviewer said) — never claim to have watched a recording you didn't process.
4. **You (the agent) synthesize `revision_notes.json` from the raw per-recording output** — the scripts only fetch/cache/render/validate, they never write the normalized notes themselves (same division of labor as `revisit-usability-analysis`). For each raw observation:
  - Assign a surface label (`study-scaffold` | `app-product` | `cross-boundary`) in your working notes before writing the final JSON.
  - Keep separate notes when the same symptom has different root causes across surfaces.
   - Merge near-duplicate observations about the same underlying concern into one note with multiple `occurrences`.
   - Assign `category` (using the model's `category_guess` as a starting point, but verify against the schema's category guidance).
   - Set `already_documented`: check the study's README "Original vs. this replication" table (if any) — if the concern matches a listed deviation, set `true` and still include a `next_action` (per the schema, these are never silently dropped).
   - Fill `source_reference` with what the reviewer says the study *should* match, when stated.
  - **Correlate code**: search the repo read-only for the component/file responsible. For `study-scaffold`, prioritize study-repo config/assets/wiring. For `app-product`, prioritize `code_repo` (external app repo in split setups). For `cross-boundary`, include both when warranted. Cite exact files, never fabricate a location — mark `status: "not-correlated"` with empty `locations` if you didn't verify one.
   - **Rehydrate provenance when available**: if the flagged component is a `react-component` stimulus with a recorded trrack `provenanceGraph` on that answer, invoke the `provenance-rehydration` skill (read its SKILL.md) to attach a `rehydration` block — the reconstructed state and action sequence at that timestamp often pin down a design-fidelity concern precisely (e.g. confirming a single-page vs. multi-page elicitation flow from the actual tracked steps, not just what's visible in the video). This also strengthens code correlation: `correlate_action.py` maps a node's `event` directly to its `registry.register(...)` call. For a `revision_ready` note with `severity: high`/`critical`, offer (don't auto-run) generating a repro spec via that skill's Step 4.
  - In the note title, prefix the surface for scanability, e.g. `[study-scaffold] ...`, `[app-product] ...`, `[cross-boundary] ...`.
  - Write the file to `analysis/<study_name>/refinement/rounds/<round>/data/revision_notes.json` per `references/finding-schema.md`.
5. Validate: `python3 .github/skills/refinement-from-video/scripts/validate_revision_notes.py analysis/<study_name>/refinement/rounds/<round>/data/revision_notes.json` — fix every error before continuing.

## Phase 4 — Report

1. Run:
   ```
   python3 .github/skills/refinement-from-video/scripts/make_revision_report.py \
     analysis/<study_name>/refinement/rounds/<round>/data/revision_notes.json \
     --out analysis/<study_name>/refinement/rounds/<round>/revision-notes.md \
     --index analysis/<study_name>/refinement/revision-notes-index.md
   ```
2. Ensure `analysis/<study_name>/refinement/rounds/*/data/` is gitignored (add an entry if the study has no `.gitignore` covering it).

## Phase 5 — Report back

State: round number, note counts by category/severity, note counts by surface (`study-scaffold`/`app-product`/`cross-boundary`), the report path, which notes are `revision_ready` vs need discussion, and which (if any) are `already_documented` deviations the reviewer re-raised — call those out specifically since they signal the README may be underselling the concern. **Do not implement any revision note's fix** — that's a separate, explicit follow-up request, same as `revisit-usability-analysis`'s issue-draft stance.

## Common pitfalls

- **Conflating this with participant usability testing.** The reviewer is not a naive user; don't file "confusion" as `usability-friction` the way `revisit-usability-analysis` would — the reviewer's job here is judging fidelity to intended design, and their commentary should be taken as an expert claim to evaluate, not a symptom to interpret.
- **Assuming iframe studies always support provenance rehydration.** Website/iframe wrappers often have no rehydratable trrack graph in the study repo. Treat this as normal, note provenance availability explicitly, and rely on video evidence + app-repo code correlation.
- **Dropping already-documented deviations.** If a reviewer re-raises something already listed in the README's replication-contract table, don't discard it as redundant — a researcher flagging a known deviation as a bigger deal than expected is itself useful signal (schema requires `next_action` even when `already_documented: true`).
- **Silent config edits.** Never enable screen recording or add an id-capture field without showing the diff and getting confirmation first — this is a shared study config.
- **Skipping grounding.** Always pass the study's README to `analyze_refinement.py` when one exists — without it the model can't distinguish a new concern from something already scoped as a deliberate deviation.
