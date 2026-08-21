---
name: revisit-multi-repo-context
description: Prepare and persist run context when a ReVISit study repo and an external app repo are separate, including multi-root workspace setup, code-repo targeting, and iframe-specific analysis expectations. Use before refinement-from-video or revisit-usability-analysis whenever recordings come from a website/iframe study whose source lives in another repository.
---

You are preparing a repeatable run context for video-analysis skills when the study and the app under review live in different repositories.

Use this skill before `refinement-from-video` or `revisit-usability-analysis` when either of these is true:

- The study stimulus is a `website`/iframe wrapper.
- The app source code is in a non-ReVISit repository.
- The user wants findings to be written in the study repo but correlated to a different code repo.

## Inputs

Accept naturally in chat:

- `study_repo_root` — the ReVISit repository where study config, recordings, and analysis outputs live.
- `app_repo_root` — the external application repository to correlate findings against.
- `study_name` — optional now, required later by the analysis skill.
- `recording_source` — Supabase/local-export location details as usual.
- `analysis_mode` — `refinement` or `usability`.

## Step 1 — Confirm workspace shape

1. Ensure both repositories are open in the same VS Code workspace (multi-root is preferred).
2. Confirm `study_repo_root` has `public/global.json` and expected study files.
3. Confirm `app_repo_root` is a valid git repo and capture commit/branch/remote/dirty status.
4. Record paths exactly; do not assume `.` means the app repo in this setup.

## Step 2 — Set run defaults

For downstream invocation:

- `code_repo` should be set to `app_repo_root` (not the study repo) when the user asks for cross-repo correlation.
- Output paths remain in `study_repo_root` (`analysis/<studyName>/...`).
- Repo edits are read-only unless the user explicitly asks for implementation after findings.

Also set a `surface_map` for this run so mixed recordings are handled explicitly:

- `study-scaffold`: intro/debrief copy, consent text, questionnaires, sequencing, response wiring, study config behavior.
- `app-product`: behavior inside the embedded app (iframe/website or integrated stimulus app).
- `cross-boundary`: transitions and handoff friction between scaffold and app (launch/open-tab instructions, return flow, completion messaging).

## Step 3 — Iframe expectations

If the flagged study components are website/iframe wrappers:

- Primary evidence is video + narration (+ transcripts if available).
- Provenance rehydration may be unavailable or partial.
- This is normal; findings should explicitly note provenance availability instead of forcing rehydration.
- Code correlation should focus on `app_repo_root` source, with `not-correlated` used when evidence is insufficient.

## Step 4 — Persist a context artifact

Write or update:

`analysis/<studyName>/refinement/multi-repo-context.md` (or `analysis/<studyName>/usability/multi-repo-context.md` for usability mode)

Template:

```markdown
# Multi-Repo Analysis Context

- Date: <YYYY-MM-DD>
- Mode: refinement | usability
- Study repo: <absolute path>
- App repo (code_repo): <absolute path>
- Study name: <name>

## Repo State (App)
- Commit: <hash>
- Branch: <branch>
- Remote: <remote>
- Dirty: true|false

## Evidence Expectations
- Stimulus type: website/iframe | react-component | mixed
- Provenance rehydration: available | partial | unavailable
- Primary evidence: video, narration, transcripts, event logs

## Surface Map
- study-scaffold: <what counts>
- app-product: <what counts>
- cross-boundary: <what counts>

## Correlation Defaults
- study-scaffold notes correlate to study repo files first (config, intro/questionnaire assets, routing/sequence wiring)
- app-product notes correlate to app repo files first
- cross-boundary notes may cite both repos in one note/finding when needed

## Invocation Defaults
- Run refinement/usability from the study repo
- Pass `code_repo=<app_repo_root>`
- Keep outputs under `analysis/<studyName>/...` in the study repo
```

## Step 5 — Hand-off to the analysis skill

When this setup is complete, invoke the requested downstream skill with explicit context:

- For design-fidelity reviews: `refinement-from-video`
- For participant usability: `revisit-usability-analysis`

State the chosen `code_repo` path and provenance expectations at the top of that run so there is no ambiguity.

## Common pitfalls

- Treating `.` as the app repo when current working directory is the study repo.
- Writing outputs into the app repo instead of the study repo.
- Assuming iframe studies always have rehydratable provenance.
- Mixing implementation changes into the analysis run without explicit user request.
