---
name: revisit-analysis
description: Scaffold a Quarto analysis project for a deployed ReVISit study — fetch participant data and media from cloud storage, analyze questionnaire responses, run on-demand AI processing (transcription, video summaries) grounded in each task's config.json instruction, and compute provenance-graph behavioral metrics. Use when the user wants to "analyze study data", "set up analysis", "process recordings/transcripts", or build reports for a study in this repo.
---

You are scaffolding `analysis/<studyName>/` — a Quarto website project for analyzing one deployed ReVISit study. The user provides the study name (must exist in `public/global.json`, with participant data already collected). Reference implementations: `analysis/nyc-commute/` and `analysis/chart-assistant/` — mirror their structure, adapting study-specific parts.

**Multi-study layout.** `analysis/` holds one folder per study plus shared code at the top level: `analysis/primitives.py` (generic trrack state reconstruction + metrics — never study-specific) is imported by every study via `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))`. Each study folder is fully self-contained otherwise (own `.venv`, `data/`, `_quarto.yml`). Never put study-specific files loose in `analysis/` — if you find any (early projects did this), move them into a study folder and fix their imports.

**Architecture principles (learned the hard way — keep these):**

- **AI processing is on-demand, never at render time.** Renders must stay fast; long API work (transcription, video summaries) lives in a separate `process_media.py` with per-file progress prints and skip-if-cached behavior. The `.qmd`s only *read* caches.
- **Everything is cached under `data/`** (gitignored): raw AI responses in `data/transcripts/`, summaries in `data/summaries/`, combined bundles in `data/clips/`. Delete a file to regenerate it.
- **Task context flows into every AI prompt.** Media filenames encode participant × task; the study `config.json` defines what each task asked (`instruction`). `llm_task_preamble()` joins them so an LLM analyzing a clip knows what the participant was trying to do.
- **The Quarto project is a website** (`type: website` + navbar + `index.qmd`) so `quarto preview` gives a single browsable entry point, not loose HTML files.

## Files to create (template: analysis/nyc-commute/)

| File | Adaptation needed |
| --- | --- |
| `_quarto.yml` | Website project, navbar: Home / Responses / Media / Provenance. Retitle. |
| `.gitignore` | `data/`, `_output/`, `.quarto/`, `.venv/`, `.env` — copy as-is. |
| `index.qmd` | Landing page: section links, workflow commands, data/cache status counts. |
| `fetch_data.py` | Set `STUDY_PREFIX` (`prod-<studyName>` — or `dev-` for dev-mode data) and the storage credentials (below). Copy the pagination, cache-busting, and folder-vs-file handling as-is. |
| `study_context.py` | Update `CONFIG_PATH` to the study's config. The rest (config join, answer access, provenance extraction, media index) is study-agnostic — copy. |
| `<study>_metrics.py` | Study-specific — follow the `provenance-analysis` skill: sample real event types first, then write named metrics over `../primitives.py`. |
| `quality.qmd` | **Data-quality gate — always include for Prolific studies.** Session-validity table (see Prolific-ID filter below), think-aloud/compliance flags, and a copy-paste review list + suggested kind rejection message. Analysts review this page before approving/rejecting Prolific submissions. |
| `responses.qmd` | Study-specific — map the study's components/response ids into a tidy DataFrame; Likert/questionnaire summaries as applicable. Split by condition for multi-condition studies (recover condition from which task component appears in `answers`). |
| `media.qmd` | Mostly copy: media index, cached-transcript/summary display, per-clip JSON export. Read-only w.r.t. AI. |
| `process_media.py` | Mostly copy: set `DEFAULT_COMPONENTS` to the study's recorded stimulus tasks. Deepgram + Gemini sections optional per what the study recorded. |
| `provenance.qmd` | Study-specific metrics tables + interaction timelines. |
| `README.md` | Data routes, workflow, flag documentation. |

## Data access facts (Supabase storage engine)

- Bucket `revisit`, all paths under `{prod|dev}-<studyName>/`:
  - `participants/{pid}_participantData` — full ParticipantData JSON (answers, provenance graphs, timings)
  - `audio/{pid}_{taskIdentifier}` and `screenRecording/{pid}_{taskIdentifier}` — webm blobs
- Auth: anonymous sign-in with the project's anon key (`POST /auth/v1/signup?grant_type=anonymous`), then bearer token for `storage/v1/object/list/` (paginate, skip folder rows with null `id`) and `storage/v1/object/revisit/{path}`.
- **Cache-bust downloads** (`?cb=<timestamp>`) — reVISit sets 1-year CDN cache headers on participant files; without it you get stale early-session snapshots.
- **Beware the repo root `.env`** — it may point at a different Supabase than the study's deployment. Confirm the study's actual project URL/anon key (see the study's deploy script or README) and default to those in `fetch_data.py`.
- Transcripts are NOT stored server-side on the Supabase engine (Firebase-only feature) — generate them locally.
- Alternative data routes (support both): analytics-page JSON downloads dropped into `data/participants/`, and manual Supabase dashboard browsing.

## Participant data facts

- Answer identifiers are `{componentName}_{trialOrder}` (e.g. `task-1_2`); library components keep their `$lib.components.name` prefix. Strip the trailing `_N` to get the component.
- There is **no `completed` flag** — treat a participant as complete if they answered the final sequence component (e.g. debrief) and `rejected` is falsy.
- Participant id formats vary (uuid4 and 24-char hex) — when parsing media filenames, match against known pids from `data/participants/` rather than assuming a fixed length.
- **Prolific-ID validity filter**: real Prolific IDs are 24-char hex (Mongo ObjectId). Researcher tests, direct-link pilots, and previews produce uuids/arbitrary strings/empty in the `paramCapture` response — give `load_participants()` a `prolific_only=True` flag matching `^[0-9a-f]{24}$` against the captured ID, and use it in all analysis pages. Show the excluded sessions in quality.qmd so tests are visible, not silently dropped.
- **Compliance flags from transcripts**: for think-aloud studies, compute per-participant speech stats from cached Deepgram word timings (word count, summed word durations) and flag `no_speech` / `low_speech` with tunable thresholds in quality.qmd. Silent recordings are rejection candidates — include a suggested kind rejection message.
- **Sampling while collecting**: give `fetch_data.py` `--limit N` and `--only <pidPrefix>` flags so the pipeline can be built and verified on a few participants before the study finishes.
- Trrack node `event` fields hold the **registered action name** (e.g. `setDestination`), not the human-readable `trrack.apply` label — check real data before writing metrics (the `provenance-analysis` skill's sampling step).
- Extra payload fields recorded in tracked state (e.g. latency measurements) are read from the reconstructed `state`, not the label.

## AI processing facts

- **Deepgram** (audio → transcript): `POST https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true&filler_words=true`, header `Authorization: Token $DEEPGRAM_API_KEY`, body = raw webm bytes. Cache the full JSON response.
- **Gemini** (video → summary): `google-genai` package; `client.files.upload(file=...)`, then **poll until `file.state != "PROCESSING"`** (generate_content rejects non-ACTIVE files), then `generate_content`. Use the **`gemini-flash-latest` alias** — pinned versions get retired and 404 for new users.
- Keys come from env vars only (`DEEPGRAM_API_KEY`, `GEMINI_API_KEY`); never write them into files. The user exports them in their own terminal.
- Prompt template: `llm_task_preamble(component)` (task instruction + think-aloud note) + the analysis ask (steps taken / hesitation / completion).

## Workflow to verify before finishing

```sh
cd analysis/<studyName>
python3 -m venv .venv && ./.venv/bin/pip install pandas matplotlib jsonpatch certifi jupyter google-genai
source .venv/bin/activate          # activate — QUARTO_PYTHON alone is not enough
python fetch_data.py --media
python process_media.py --transcribe --summarize   # only if keys provided
quarto render                       # all pages must succeed
```

Then sanity-check with real data (not just a clean render): responses populate the DataFrame, provenance metrics return non-trivial values for at least one participant, `media_index()` rows join to instructions. If provenance events come back empty, re-sample the event names — that's the most common mismatch.

Report back: the folder path, `quarto preview` as the entry command, which AI parts are wired, and any study-specific metrics the user should review.
