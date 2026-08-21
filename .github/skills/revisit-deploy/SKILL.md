---
name: revisit-deploy
description: Deploy a ReVISit study as a live, shareable site — provision participant-data storage (hosted Supabase), host any study-specific backend (Render), build and publish the frontend (Netlify), verify end-to-end, and generate a per-study redeploy script. Use when the user asks to "make a live version", "share the study", "deploy", or "provision" hosting for a study in this repo.
---

You are deploying an existing, locally-working ReVISit study from this repo so it can be shared with participants. The study should already pass its local click-through (if it doesn't, fix that first — deployment only amplifies local problems).

The user provides: a study name (must exist in `public/global.json`). Everything else is discovered or asked.

**Guiding principles:**

- **Detect, then offer — never auto-provision.** Deployment creates persistent external resources under the user's accounts. Check which CLIs are installed *and authenticated* before offering anything, and get explicit confirmation per resource before creating it.
- **Interactive logins are checkpoints, not errors.** Supabase login requires a browser verification code typed by the user; Render/Netlify logins open browser approvals; granting a GitHub App access to a private repo may require an org owner. When you hit one, tell the user exactly what to do, wait, and resume. Never ask the user to relay secrets (tokens, verification codes) through chat — they type those directly into the terminal/browser.
- **Patch `dist/`, never the source tree.** The deployed build intentionally differs from dev (storage engine, backend URLs, trimmed study list, redirects). Keep the repo pointing at localhost/dev values; apply deployment differences to the built output only.
- **End with a one-command redeploy script.** The deployment session wires things once; afterward the study designer redeploys without this skill.

## Phase 1 — Detect available tooling

Check each, capturing both presence and auth state:

- `netlify status` — frontend hosting (required for any deployment).
- `npx -y supabase@latest projects list` — participant-data storage. (`supabase` is usually not installed globally; use `npx`.)
- `render workspace current -o text` — backend hosting (only needed if the study calls its own backend).
- Fallbacks: if a tool is missing/unauthenticated, name it and let the user choose to log in (`netlify login`, `render login`, `npx -y supabase@latest login --agent no`) or skip that piece. The Supabase login prints a link and prompts for a verification code — the user must type it into the terminal themselves.

Also inspect the study to determine what's actually needed:

- Does any component's `parameters` contain a backend URL (e.g. `apiUrl` pointing at localhost)? Grep the study's `config.json`. If yes, a public backend is required — a static host cannot run it, and localhost breaks for participants.
- Current storage engine in `.env` (`VITE_STORAGE_ENGINE`) — deployment should use `supabase` (hosted) or `firebase`, not `localStorage`.

## Phase 2 — Confirm the deployment plan with the user

One ask-questions round covering:

1. **Backend hosting** (only if Phase 1 found a backend URL): Render (if available), an existing public URL the user provides, or skip (site deploys but the stimulus will show its backend-unavailable state for participants — say this plainly).
2. **Data storage**: create a new hosted Supabase project, reuse an existing one (user provides URL + anon key), or reuse credentials already in `.env`.
3. **Study list scope**: trim the deployed `configsList` to just this study (recommended for participant-facing links) or keep everything.
4. **Site/service names**: suggest `<studyName>-study` (Netlify) and `<studyName>-api` (Render); note the Netlify name becomes `<name>.netlify.app`.

Warn once about free-tier behavior so it lands in the decisions log: Render free instances spin down when idle (first request after a lull takes ~30–60s and the stimulus may briefly show a backend error), and free Supabase projects pause after ~a week of inactivity.

## Phase 3 — Provision Supabase (if confirmed)

Hosted supabase.com works with reVISit's Supabase engine (same `supabase-js` + anonymous sign-in as self-hosted; the revisit.dev docs describe self-hosting but the schema requirements are identical — https://revisit.dev/docs/data-and-deployment/supabase/setup/).

1. `npx -y supabase@latest orgs list` → pick/confirm org. Create the project with a generated DB password saved to a chmod-600 file in `$HOME` (tell the user where):
   ```
   npx -y supabase@latest projects create <name> --org-id <org> --region <region> --db-password "$(saved password)"
   ```
2. Fetch the anon key: `npx -y supabase@latest projects api-keys --project-ref <ref>` (use the legacy `anon` JWT — that's what `VITE_SUPABASE_ANON_KEY` expects).
3. Apply the schema via a migration (init a scratch dir under /tmp, `supabase link --project-ref <ref>`, write one migration, `supabase db push`). The migration must create:
   - Table `public.revisit`: `"createdAt" timestamptz default now()`, `"studyId" varchar`, `"docId" varchar`, `"data" jsonb`, composite PK `("studyId","docId")`; RLS enabled; one permissive `FOR ALL` policy for `anon, authenticated, service_role` with `USING (true)`.
   - Private storage bucket `revisit` (insert into `storage.buckets`, `public = false`).
   - Four `storage.objects` policies (select/insert/update/delete) for `anon, authenticated, service_role` scoped to `bucket_id = 'revisit'`.
4. **Enable anonymous sign-ins** — the engine calls `signInAnonymously()` and everything 401s without it: set `enable_anonymous_sign_ins = true` in the scratch `supabase/config.toml`, then `npx -y supabase@latest config push --yes`.
5. Verify with curl before moving on: anonymous signup (`POST /auth/v1/signup?grant_type=anonymous` with the anon key) returns an access token, and `GET /rest/v1/revisit?select=*&limit=1` with that token returns 200.

## Phase 4 — Deploy the backend (if confirmed, Render path)

1. The backend repo needs a git remote Render can fetch. For private repos, the Render GitHub App must have repo access; adding a repo to the app installation is org-owner-only, so if `render services create` fails with "repository URL is invalid or unfetchable", direct the user to their GitHub org's Settings → GitHub Apps → Render → add the repo, then retry.
2. Create the service (adapt runtime/build/start to the backend — for a uv-managed Flask app):
   ```
   render services create --name <name> --type web_service --repo <repo-url> --branch main \
     --runtime python --plan free --region <region> --num-instances 1 \
     --health-check-path <cheap-GET-endpoint> \
     --build-command "uv sync --locked" \
     --start-command "uv run --with gunicorn gunicorn <module>:app --bind 0.0.0.0:\$PORT --workers 2 --threads 8 --timeout 180 --graceful-timeout 30 --keep-alive 75" \
     --confirm -o json
   ```
   **The gunicorn flags are load-bearing for any backend that makes slow upstream calls (LLM proxies especially).** Default sync workers + 30s timeout = the arbiter SIGKILLs workers mid-request (500s to participants), and a blocked sync worker can't answer the health check, so Render marks the instance failed and restarts it — cascading failures under real participant load that never show up in solo testing. Threads provide concurrency during upstream waits; `--timeout` must exceed the app's own upstream timeout (e.g. 180 > 120).
3. Poll `render deploys list <service-id> -o text --confirm` until Live, then curl the health endpoint on the public `.onrender.com` URL.
4. Confirm the backend has permissive-enough CORS for the Netlify origin (reVISit backends typically use `flask_cors.CORS(app)` — wide open — but check).
5. Note for the README/decisions log: Render auto-deploys the backend on push to the tracked branch; no script needed for it.

## Phase 5 — Build, patch, and deploy the frontend (Netlify)

1. Build with deployment env inline — do not modify `.env`:
   ```
   VITE_BASE_PATH=/ VITE_STORAGE_ENGINE=supabase \
   VITE_SUPABASE_URL=<url> VITE_SUPABASE_ANON_KEY=<anon-key> yarn build
   ```
2. Patch `dist/` (never the source tree):
   - If trimming was confirmed: rewrite `dist/global.json`'s `configsList`/`configs` to just this study.
   - Rewrite any backend-URL parameters (e.g. `apiUrl`) in `dist/<studyName>/config.json` — both `baseComponents` and `components` — from localhost to the live backend URL.
   - Write `dist/_redirects` with `/*    /index.html   200` (SPA routing; the repo's `public/404.html` hack is for GitHub Pages, not Netlify).
3. `netlify sites:create --name <name>` (skip if it exists), then `netlify deploy --prod --dir=dist --no-build`.

## Phase 6 — Verify end-to-end on the live site

Open the live study URL in a browser and:

1. Step from the intro into (or jump via the study browser sidebar to) the main stimulus; confirm it renders and, if there's a backend, that real data comes back (not the backend-unavailable state).
2. Confirm participant data lands in Supabase: query the `revisit` table (expect `metadata` / `sequenceAssignment_*` rows for the deployed study) and list the storage bucket (expect `_sequenceArray` / `participants/` under the study prefix).
3. Known-benign console noise on a fresh project: a 406 from the user-management query (zero rows) and a 400 on a first-time participant file fetch. Don't chase these.

## Phase 7 — Generate the redeploy script and document

1. Create `scripts/deploy-<studyName>.sh` (chmod +x, `bash -n` to syntax-check) capturing exactly the Phase 5 build+patch+deploy with the real URLs/keys baked in, and add `"deploy:<studyName>": "bash scripts/deploy-<studyName>.sh"` to `package.json`. The Supabase anon key may be committed — it is a public client key that ships in the JS bundle; RLS protects the data. The DB password must NOT go in the script or repo.
2. Update the study's `public/<studyName>/README.md` with a **Live deployment** section: live URL, dashboard links (Netlify site, Render service, Supabase project), the redeploy command, free-tier caveats, and this warning stated plainly: **the Netlify site is not git-linked — pushing to the repo redeploys the backend (Render) but NOT the frontend; run `yarn deploy:<studyName>` for frontend changes.**
3. Report back: share link, what was provisioned where, where the DB password lives, and anything the user still owns (e.g. custom domain, upgrading plans for real data collection).

## Future hosting options

This skill currently implements Supabase + Render + Netlify because those CLIs are in use here. When adding another provider (Vercel, Cloudflare Pages, Fly.io, Firebase, GitHub Pages...), keep the same shape: detect+auth-check in Phase 1, offer in Phase 2, provider-specific provisioning in Phases 3–5, and the same Phase 6 verification and Phase 7 script/README contract. GitHub Pages specifically: use the repo's existing `public/404.html` SPA hack and set `VITE_BASE_PATH=/<repo-name>/` instead of `_redirects`.
