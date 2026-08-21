---
name: study-from-link
description: Turn a link to an already-running external tool/system (or, if no link exists yet, a description of one anticipated soon) into a new ReVISit study built around screen recording + think-aloud exploration followed by researcher-authored post-task questionnaire(s) — brainstorm the intro-page framing and questionnaire content with the study designer, wrap the live tool as a website stimulus (or scaffold a swappable placeholder if there's no link yet), and register the study.
---

You are turning a link to an external, already-running system — or, if no link exists yet, a plain-language description of one the study designer anticipates getting soon — into a runnable ReVISit study. Unlike `study-from-repo`, **you have no source code to read**: the tool is a black box reached over the network (or doesn't exist as a reachable thing yet). That changes what's possible. There is no Trrack/provenance state instrumentation option here — you can't add tracking code to someone else's running system. The entire behavioral signal this study can capture is **screen recording + think-aloud audio**, plus whatever the participant reports afterward in a questionnaire. Say this plainly to the study designer early — don't let them assume click-by-click interaction logs will exist.

The user provides: a study name, and either (a) a URL to the running system, or (b) no URL yet plus a plain-language description of the anticipated tool. Normalize the study name per `public/README.md`'s convention (periods/spaces/slashes → underscores) before using it as a folder name.

**Keep a running decisions log as you go**, the same way `study-from-repo` does — the mode chosen (live-link vs. no-link), the goal-scoping conversation from Phase B, the intro-page framing from Phase C, and the questionnaire selection from Phase D. It becomes the "Decisions made" section of the README in Phase F.

## Phase A — Gather inputs and pick a mode

1. Ask for the study name and the link. Two modes:
   - **Live-link mode**: a real, reachable URL exists now.
   - **No-link mode**: no URL yet — the study designer anticipates getting one soon, but wants to brainstorm and scaffold the study (intro framing, questionnaire content, sequence) ahead of time so they can move fast once the link arrives. Ask for a short plain-language description of the tool instead: what it does, who it's for, roughly what kind of interface it presents (a dashboard, a chat assistant, a map, a form, etc.) — enough to ground the intro/questionnaire brainstorming in Phases C–D.
2. **Live-link mode only** — do two quick checks before committing to an iframe wrap:
   - Optionally fetch the page (`fetch_webpage`) to understand the tool's purpose/domain if the study designer's description is thin — this only informs your brainstorming in Phases C–D, don't over-invest here.
   - Check embeddability risk: run `curl -sI <url>` in the terminal and look for `X-Frame-Options` (e.g. `DENY`, `SAMEORIGIN`) or a `Content-Security-Policy` with `frame-ancestors` that would block the site from rendering inside ReVISit's iframe (`src/controllers/IframeController.tsx` renders the `website` component as a plain `<iframe>`, no bypass exists). If either header suggests blocking, tell the user now and propose the fallback in step 3.
3. **If iframe embedding looks blocked (or the user prefers it anyway)**: the fallback is to *not* embed the tool at all. Instead, the intro/task page gives participants the link to open in a new tab, and screen recording is still captured for the ReVISit browser tab — but the participant must choose "entire screen" (not "this tab") when the browser's screen-share picker (`getDisplayMedia`, see `src/store/hooks/useRecording.ts`) appears, so their tab-switch to the external tool is actually captured. Confirm with the user which approach to use (iframe wrap vs. new-tab-plus-entire-screen) and note the choice in the decisions log — the intro copy in Phase C differs depending on which one is picked.
4. **No-link mode**: note explicitly in the decisions log that a placeholder stimulus stands in for the real tool, to be swapped in once the link exists (see Phase E step 2 and the re-entry note at the end of Phase E).

## Phase B — Scope what this study can and can't capture, then confirm the goal

1. State the constraint up front, in plain language: because there's no code access, there's no interaction-by-interaction tracking (no Trrack) — only screen recording (what participants literally did on screen), think-aloud audio (why, as they narrate it), and whatever they answer in a questionnaire afterward. If the study designer needs fine-grained click/state logs, that's out of scope here — say so rather than implying the recording covers it.
2. Ask, in plain language, what they want to learn about how people use the tool — same spirit as `study-from-repo` Phase B step 1, but frame the answer as "what to watch for on the recording" and "what to ask about afterward" rather than "what to track." Prompt with concrete examples if they're unsure: "where do people get stuck or confused?", "do they discover feature X on their own?", "how do they react out loud to results?", "how do they rate it afterward on ease of use / trust / satisfaction?"
3. If the goal uses a fuzzy term ("intuitive," "useful," "trustworthy"), don't silently resolve it — ask a concrete follow-up with 2–3 grounded options, same as `study-from-repo` Phase B step 3. This determines what to listen/watch for during screen recording vs. what needs its own questionnaire item, so getting it right here avoids a data-doesn't-answer-the-question problem later. If the goal is really about naming what kind of decision the tool supports (e.g. "help people pick the best X" vs. "help people find any X that qualifies"), consider running `decision-task-abstraction` first — it classifies the decision as CHOOSE/ACTIVATE/CREATE and writes a spec to `public/<studyName>/design/decision-abstraction.md` that the intro/questionnaire drafting in Phases C–D can then reference.
4. Confirm think-aloud audio is wanted (it almost always is for this study shape, since it's the only source of *why*) — but still ask, don't assume; a purely observational screen-recording-only study is valid if the designer prefers not to burden participants with narrating.

## Phase C — Brainstorm the intro-page framing (before the recorded exploration)

Work with the user to draft `assets/introduction.md` collaboratively — don't invent study-specific copy unilaterally. Cover:

1. **Task framing**: free exploration vs. one or more directed tasks (e.g. "find X," "try to accomplish Y"). Directed tasks make "did they complete it" and duration easy to reason about later; free exploration surfaces more organic reactions but is harder to compare across participants. Ask which fits the goal from Phase B.
2. **Recording disclosure**: plain-language notice that microphone audio and screen will be recorded during the exploration, used only for research, stored securely — matches the tone of `public/nyc-commute/assets/introduction.md` and `public/chart-assistant/assets/introduction.md`.
3. **Think-aloud instruction**, if confirmed in Phase B: "please think aloud while you work — say what you're looking at, trying to do, and anything that surprises or confuses you."
4. **If using the new-tab-plus-entire-screen fallback** (Phase A step 3): explicit instructions to open the link in a new tab, and — critically — to choose "Entire Screen" (not "This Tab") when the browser prompts for what to share, or their activity on the external tool won't be captured at all. Call this out clearly and consider bolding it; it's the single most likely failure mode for this approach.
5. **If no-link mode**: the intro can still be drafted now against the anticipated tool's description — it just won't be pointed at anything real until Phase E step 2's placeholder is swapped for the live link.
6. Draft expected duration and any consent-style language if this will run on Prolific (mention the `revisit-prolific` skill exists for the recruitment side; don't invoke it here).

## Phase D — Brainstorm the post-exploration questionnaire(s)

1. Ask what aspects of the experience matter enough to measure right after the exploration. Point to what's already available under `public/libraries/` as off-the-shelf options rather than reinventing them:
   - **General usability/UX**: `sus` (System Usability Scale), `umux-lite` / `umux`, `tam2` (Technology Acceptance Model), `ues` (User Engagement Scale).
   - **Workload**: `nasa-tlx`.
   - **Affect**: `sam` (Self-Assessment Manikin).
   - **Detailed multi-dimension satisfaction**: `quis`.
   - **Perceived effort**: `smeq`.
   - Custom Likert/open-ended items (a `questionnaire`-type component) for anything specific to the stated goal from Phase B (e.g. "I felt confident I could accomplish my task with this tool," or an open text box: "What, if anything, confused you?").
2. If more than one questionnaire makes sense (e.g. a standard scale plus a custom reflection block, or one per distinct task if there are several directed tasks), confirm the count and order with the user.
3. Confirm the final list and exact wording of any custom items before scaffolding — don't invent survey copy the user hasn't seen.

## Phase E — Scaffold the study

1. Create `public/<studyName>/config.json`, modeled on `public/demo-screen-recording/config.json` (the canonical external-website-plus-recording pattern) for the stimulus, and on the relevant `public/library-*/config.json` files (e.g. `library-sus`, `library-umux-lite`) for the `$libraryName.components.x` / `$libraryName.sequences.x` questionnaire syntax:
   - `uiConfig`: `recordAudio: true` (if think-aloud confirmed), `recordScreen: true`, `recordScreenFPS: 30`, `helpTextPath`, `withSidebar`, etc.
   - `importedLibraries`: `["screen-recording", ...any questionnaire libraries chosen in Phase D]`.
   - `components`:
     - `introduction` — `type: "markdown"`, from Phase C's draft. Optionally include a `prolificId` short-text response with `paramCapture: "PROLIFIC_PID"` if this will run on Prolific (see `public/nyc-commute/config.json` for the pattern) — ask first.
     - `$screen-recording.components.screenRecordingPermission` goes into `sequence`, not `components`, right before the first recorded stimulus.
     - The tool stimulus itself — `type: "website"`:
       - **Live-link, iframe wrap**: `"path": "<the confirmed URL>"`.
       - **Live-link, new-tab fallback**: still a `website` component, but its `instruction` text carries the "open in new tab, share Entire Screen" guidance from Phase C, and the embedded `path` can point at a small local landing asset (or the same URL, accepting it may render blank) — confirm which the user prefers.
       - **No-link mode**: `"path": "<studyName>/assets/placeholder-tool.html"` — see step 2 below.
     - One `questionnaire`-type (or library) component per questionnaire confirmed in Phase D, placed after the tool stimulus in the sequence.
     - `debrief` — `type: "markdown"`, `recordAudio`/`recordScreen: false`.
   - `sequence.components`: `introduction` → `$screen-recording.components.screenRecordingPermission` → tool stimulus → questionnaire(s) → `debrief`.
2. **No-link mode only**: create `public/<studyName>/assets/placeholder-tool.html` — a minimal static page stating the tool's anticipated purpose (from the Phase A description) and a visible note that this is a stand-in until the real link is available. Add a one-line `TODO` comment inside `config.json` next to the `path` field marking it as the placeholder to replace. The only change needed later is swapping that one `path` value for the real URL — call this out clearly in the README (Phase F) so it isn't lost.
3. Generate `assets/introduction.md` and `assets/debrief.md` from the Phase C draft — placeholder debrief copy is fine, but don't invent the introduction's substantive framing without the user's input.
4. Register the study in `public/global.json`: add `<studyName>` to `configsList`, and `"<studyName>": { "path": "<studyName>/config.json" }` to `configs`.
5. No parser/schema changes are needed — this only adds a new study instance using existing component types.

## Phase F — Generate README.md

Write `public/<studyName>/README.md`, adapted from `study-from-repo`'s Phase F shape but reflecting this skill's differences:

- **Title + description** — the tool's purpose (from the user's description) and what participants do with it.
- **Source** — the URL (live-link mode) or "no link yet — placeholder, see below" (no-link mode), plus the date.
- **Decisions made** — pulled from the running log:
  - What the user wanted to learn (Phase B), in their own words.
  - The embeddability decision (iframe wrap vs. new-tab-plus-entire-screen fallback) and why, if live-link.
  - The intro-page framing chosen (Phase C) and the questionnaire(s) chosen (Phase D), each tied back to the stated goal.
- **What this study captures** — be explicit and honest: screen recording, think-aloud audio (if enabled), and questionnaire responses only. No interaction-level state tracking exists for this study, because there is no code to instrument.
- **If running in no-link mode** — a clearly separated section: "Before running with real participants," stating that `components.<toolStimulusId>.path` in `config.json` currently points at the local placeholder (`assets/placeholder-tool.html`) and must be updated to the real URL once available, plus a reminder to re-check embeddability (`curl -sI <url>`) at that point since the placeholder's iframe-friendliness says nothing about the real tool's.
- **Where things live** — `public/global.json` entry, `public/<studyName>/config.json`, the `assets/` files.
- **Running this study** — `yarn serve`, then the study's `configsList` name.
- **Where to go next** — common tweaks: add another questionnaire (add the library to `importedLibraries` + reference it in `sequence`), change intro/debrief copy, switch from iframe wrap to new-tab fallback (or vice versa) if embeddability changes.
- **Known limitations / TODOs** — placeholder copy, the no-link placeholder swap if applicable, and the fundamental one: no fine-grained interaction data, by design, since the tool isn't part of this codebase.

## Phase G — Verify

1. `yarn typecheck` and `yarn lint`.
2. Start the dev server (`yarn serve`, or use the `run` skill) and load the new study by its `configsList` name.
   - **Live-link, iframe wrap**: confirm the tool actually renders inside the iframe (a blank frame means embedding is blocked despite the header check — fall back to the new-tab approach if so).
   - **Live-link, new-tab fallback**: confirm the intro/task instructions are clear enough to follow, and that the screen-share picker appears when the recording-permission step is reached.
   - **No-link**: confirm the placeholder page renders and clearly reads as a stand-in.
   - Confirm the questionnaire(s) render and record answers.
3. Optionally add a Playwright spec under `tests/`, modeled on `tests/demo-screen-recording.spec.ts` if one exists, or a similar screen-recording demo spec.

Report back what was scaffolded, what this study will and won't capture (tied to the stated goal), any copy that still needs the user's input, and — for no-link mode — a clear reminder of the one-line swap needed once the real link arrives. Point to the generated `public/<studyName>/README.md` for the fuller writeup.

## Phase H — Offer deployment and recruitment (optional)

Once the local click-through passes, mention `revisit-deploy` (to host it as a live, shareable site) and `revisit-prolific` (to recruit participants, including the peripheral-requirements/compliance-language conventions for think-aloud studies) — don't start either unprompted, just offer them. For no-link-mode studies, note that deployment/recruitment should wait until the real link is swapped in.
