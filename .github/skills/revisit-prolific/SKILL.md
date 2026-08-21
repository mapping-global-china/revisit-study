---
name: revisit-prolific
description: Connect a deployed ReVISit study to Prolific for participant recruitment — wire PROLIFIC_PID capture and completion redirect into the study config, then create a draft Prolific study via the Prolific API pointing at the live study URL. Use when the user wants to "run the study on Prolific", "recruit participants", "set up Prolific", or create/manage Prolific studies from this repo.
---

You are connecting an already-deployed ReVISit study (live, shareable URL — see the `revisit-deploy` skill) to Prolific so real participants can be recruited and paid. There are two halves: (1) config changes in this repo so reVISit captures the Prolific ID and redirects participants back, and (2) creating the study on Prolific via their API.

**Money-safety principle (most important rule in this skill):** Creating a study via `POST /api/v1/studies/` only makes an **UNPUBLISHED draft** — free, harmless, fully editable in the Prolific dashboard. **Publishing** (the `/transition/` endpoint with `{"action": "PUBLISH"}`) starts real recruitment and spends real money. NEVER publish without the user explicitly confirming in that moment — creating the draft and stopping is the correct default ending for this skill. Point them to the dashboard for final review and publish.

## Phase 1 — Prerequisites and authentication

1. The study must already be deployed with a public URL (frontend + any backend + cloud storage). If not, offer the `revisit-deploy` skill first — a localhost URL in a Prolific study is a guaranteed failure.
2. **API token**: check `[[ -n "$PROLIFIC_TOKEN" ]]` or a token file at `~/.prolific_token` (chmod 600). If absent, ask the user to create a Researcher token at https://app.prolific.com/researcher/tokens/ and either `export PROLIFIC_TOKEN=...` in the terminal themselves or save it to `~/.prolific_token` — the token is a secret: never ask for it in chat, never echo it, always reference it as `$PROLIFIC_TOKEN` / `$(cat ~/.prolific_token)`.
3. Verify auth and discover context (also confirms which account/workspace):
   ```
   curl -s https://api.prolific.com/api/v1/users/me/ -H "Authorization: Token $PROLIFIC_TOKEN"
   curl -s https://api.prolific.com/api/v1/workspaces/ -H "Authorization: Token $PROLIFIC_TOKEN"
   ```
   (The Go-based Prolific CLI exists — `go install github.com/prolific-oss/cli/cmd/prolific@latest`, auth via the same `PROLIFIC_TOKEN` — but don't require it; curl covers everything this skill needs.)

## Phase 2 — Wire the reVISit side (per https://revisit.dev/docs/data-and-deployment/connecting-to-external-platform/)

Edit the study's `public/<studyName>/config.json`:

1. `uiConfig.urlParticipantIdParam: "PROLIFIC_PID"` — reVISit stores the ID Prolific appends to the study URL, so the same participant can resume across devices and their data is keyed to their Prolific ID.
2. Optionally display/record the ID explicitly: add a `shortText` response with `"paramCapture": "PROLIFIC_PID"` to an early component (auto-filled, non-editable).
3. Completion redirect — generate a completion code now (e.g. 6–8 uppercase alphanumerics, `openssl rand`), you'll register the same code with Prolific in Phase 3:
   - `uiConfig.studyEndMsg`: "Thank you! Return to Prolific to register your completion: [https://app.prolific.com/submissions/complete?cc=<CODE>](...)"
   - Optionally `studyEndAutoRedirectURL: "https://app.prolific.com/submissions/complete?cc=<CODE>"` (+ `studyEndAutoRedirectDelay`).
4. **Redeploy the frontend** so the live site has these changes (run the study's `scripts/deploy-<studyName>.sh` — remember the Netlify site is not git-linked). Verify the live config actually serves the new fields before creating the Prolific study.

## Phase 3 — Confirm study parameters, then create the draft

**One ask-questions round** (these directly determine cost — don't guess any of them):

- Study name + description shown to participants (description supports basic HTML). **For think-aloud studies, make compliance a visible condition of approval**: put "Think-aloud Study" in the study name and a bolded line in the description like *"Participants who do not speak aloud will not be approved. Your verbal thoughts are very important for this analysis!"* — silent recordings are the top rejection cause for think-aloud protocols, and stating the requirement up front both filters willing participants and makes later rejections defensible.
- Number of participants (`total_available_places`).
- Estimated completion time in minutes (be honest — Prolific derives `maximum_allowed_time` and flags misestimates). Base it on actual pilot timings when available, not the config's advertised duration.
- Reward in **cents** of the account currency (`reward`). Prolific's guidance: minimum £6.00/$8.00 per hour, recommended £9.00/$12.00+ per hour. Always compute and surface the implied hourly rate (`reward / minutes × 60`) and refuse to default below the minimum — underpaid studies get flagged, recruit slowly, and attract low-effort participants. Suggest the recommended rate as the default.
- Device restrictions (`device_compatibility`, e.g. `["desktop"]` — recommend desktop-only for map/visualization stimuli or anything with `deviceRestriction` in the reVISit config).
- Peripheral requirements (`peripheral_requirements`, e.g. `["audio", "microphone"]` if the study records think-aloud; add `"camera"`/`"download"` as applicable).
- Approval mode: `MANUALLY_REVIEW` (recommended default) vs `AUTOMATICALLY_APPROVE`.
- Screening filters. **Defaults to propose** (user can override): country of residence = United States, approval rate ≥ 95, fluent in English. In the API these are `filters` entries, e.g.:
  ```json
  "filters": [
    {"filter_id": "current-country-of-residence", "selected_values": ["1"]},
    {"filter_id": "approval_rate", "selected_range": {"lower": 95, "upper": 100}}
  ]
  ```
  (Verified 2026-07: `current-country-of-residence` is a select filter whose value `"1"` = United States; `approval_rate` (underscore) is a range filter. Re-verify against `GET /api/v1/filters/` before sending — vocabularies change.) Ask about additional screening (age range, previous-studies blocklist, vision, ...); filters can also be refined later in the dashboard.
- **Follow-up batches**: a COMPLETED Prolific study can't be reopened — create a new study. To exclude earlier participants use `{"filter_id": "previous_studies_blocklist", "selected_values": ["<earlier-study-id>"]}` (verified 2026-07; there is no filter named `previous_studies`). Reusing the same completion code across batches is fine. Suggest the user set a reVISit **stage** (study Manage tab) before publishing a new batch so its data is segmented; the active stage is stamped on each participant at session start.
- Which Prolific workspace/project, if the account has several (`project` field).

Then create the **draft**:

```
curl -s -X POST https://api.prolific.com/api/v1/studies/ \
  -H "Authorization: Token $PROLIFIC_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "name": "<participant-facing name>",
    "description": "<participant-facing description>",
    "external_study_url": "https://<live-study-url>?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}",
    "prolific_id_option": "url_parameters",
    "total_available_places": <N>,
    "estimated_completion_time": <minutes>,
    "reward": <cents>,
    "completion_codes": [
      {"code": "<CODE from Phase 2>", "code_type": "COMPLETED", "actions": [{"action": "MANUALLY_REVIEW"}]}
    ],
    "device_compatibility": [...],
    "peripheral_requirements": [...],
    "filters": [...],
    "submissions_config": {"max_submissions_per_participant": 1}
  }'
```

Notes:
- `{{%PROLIFIC_PID%}}` etc. are Prolific template placeholders — send them literally; Prolific substitutes per participant.
- The ReVISit study URL is the direct study path (e.g. `https://<site>/<studyName>`); reVISit reads `PROLIFIC_PID` from the querystring via `urlParticipantIdParam`.
- Response contains `id` and `"status": "UNPUBLISHED"` — confirm both. Record the study `id`.

## Phase 4 — Verify the draft end-to-end (still free)

0. **reVISit mode safety check (do this every time, and re-check right before any publish).** A study left in development/sharing mode leaks the study navigator and the full analytics interface (including all participant data) to anyone with the URL. The modes live in the study's storage: Supabase table `revisit`, row `studyId = {prod|dev}-<studyName>`, `docId = 'metadata'`, fields `developmentModeEnabled`, `dataSharingEnabled`, `dataCollectionEnabled`. Check programmatically (anon auth flow as in `revisit-analysis`):
   ```
   GET {SUPABASE_URL}/rest/v1/revisit?select=data&studyId=eq.prod-<studyName>&docId=eq.metadata
   ```
   For recruitment the required state is: `dataCollectionEnabled: true`, `developmentModeEnabled: false`, `dataSharingEnabled: false`. If wrong, fix via PATCH on the same row (merge the corrected flags into `data`) or point the user at the study's Manage tab (`/analysis/stats/<studyName>/manage`), then re-verify with a fresh GET. Also spot-check behaviorally: load the live study URL in a private window — the Study Browser sidebar must NOT appear, and `/analysis/stats/<studyName>` must not show data without login.
1. `GET /api/v1/studies/<id>/` — check `external_study_url`, reward, places, and `is_ready_to_publish`.
2. Open the study's own URL with fake Prolific params in a browser: `https://<live-study-url>?PROLIFIC_PID=TEST123&STUDY_ID=test&SESSION_ID=test` — confirm the study loads, the participant ID is captured (visible in the paramCapture response if added, or in the stored participant data), and the end-of-study screen shows the Prolific return link with the right code.
3. Optionally direct the user to the Prolific dashboard preview for the draft.

## Phase 5 — Hand off for publishing (do NOT do this yourself by default)

Report to the user:
- Draft study ID + dashboard link (`https://app.prolific.com/researcher/workspaces/studies/<id>`).
- Total cost estimate: places × reward + Prolific's service fee (shown in the dashboard), and the implied hourly rate.
- What publishing does: study goes live to matching participants and reserved funds are committed. Publishing requires available workspace balance.
- How to publish — dashboard button (recommended: gives a final cost/summary screen), or if the user explicitly asks you to do it:
  ```
  curl -s -X POST https://api.prolific.com/api/v1/studies/<id>/transition/ \
    -H "Authorization: Token $PROLIFIC_TOKEN" -H "Content-Type: application/json" \
    -d '{"action": "PUBLISH"}'
  ```
  Only run this after a fresh, explicit "yes, publish now" from the user in the current conversation — never as part of the initial setup flow. **Immediately before publishing, rerun the Phase 4 step-0 mode check** — modes may have been flipped back on for debugging since the draft was created.

Also update the study's `public/<studyName>/README.md` with a **Prolific** section: draft study ID, dashboard link, completion code, where the config wiring lives (`urlParticipantIdParam`, `studyEndMsg`), and the reminder that config changes require a frontend redeploy before more participants run.

## Useful management endpoints (all read-only or draft-safe)

- List studies: `GET /api/v1/studies/`
- Study detail: `GET /api/v1/studies/<id>/`
- Update a draft: `PATCH /api/v1/studies/<id>/` (same fields as create)
- Submissions (once running): `GET /api/v1/studies/<id>/submissions/`
- Pause/stop a live study: `POST /api/v1/studies/<id>/transition/` with `{"action": "PAUSE"}` / `{"action": "STOP"}` — pausing is safe and reversible; stopping is final.
