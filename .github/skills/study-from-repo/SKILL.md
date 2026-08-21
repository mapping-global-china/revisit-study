---
name: study-from-repo
description: Convert an external repository (React or not) into a new ReVISit study — analyze the source, understand what the study designer actually wants to learn, convert or wrap it into a compliant stimulus component, wire up Trrack provenance tracking, and scaffold the study's config.json, assets, and public/global.json registration.
---

You are turning an existing external codebase (a researcher's prototype, visualization, or interactive tool that lives outside this repo) into a runnable ReVISit study. This is judgment-heavy — repo shapes vary — so work through the phases below, ask the user to confirm decisions at the marked points, and don't silently guess on anything ambiguous.

The user provides: a source (local path or git URL) and a target study name. Assume the study designer is likely **new to ReVISit and to Trrack/provenance tracking** — they think in terms of what they want to learn about their users, not in terms of state variables or trrack actions. Meet them where they are: ask about goals in plain language, and do the translation into ReVISit/Trrack concepts yourself.

Normalize the study name per `public/README.md`'s convention (periods/spaces/slashes → underscores) before using it as a folder name.

**Keep a running decisions log as you go.** At every confirm-with-user checkpoint in Phases A–D — the stimulus/sequencing questions (Phase A), the goal-elicitation dialogue (Phase B: the stated goal, any ambiguity-resolving follow-ups, the final translation, and what was deliberately left untracked), the conversion strategy (Phase C), and the tracking implementation approach (Phase D) — jot down the question asked and the answer given. This is not a separate mechanism, just keep it in mind through the phases below. It becomes the "Decisions made during conversion" section of the README in Phase F. The point of this whole log-and-README step is to keep the conversion legible to the study designer — what they wanted to learn, how that became something measurable, and exactly where — rather than a black box that just produces a working study.

## Phase A — Analyze the source repo

1. If the source is a git URL, clone it into the scratchpad directory (read-only exploration, don't modify it).
2. Detect the stack: look for `package.json` and its `dependencies`/`devDependencies` to identify React/Vue/Svelte/etc., or plain HTML/JS/CSS with no framework.
3. Identify candidate "stimulus" entry point(s) — the main App/page/component(s) a participant would interact with — and any natural multi-step structure (routes, wizard steps, distinct pages/screens). This maps to the study's `sequence` later.
4. Enumerate state/interaction candidates that are *technically* capable of being provenance-tracked (raw material for Phase B, not yet something to present to the user):
   - React: `useState`/`useReducer`/context values, especially ones driven by user interaction (clicks, selections, filters, drags).
   - Non-React: DOM event listeners, global variables/state stores that change on interaction.
5. **Stop and confirm with the user** (plain language, no ReVISit jargon): which artifact(s) become stimuli, and how they should be sequenced (fixed/random/blocks, any intro/consent/debrief steps). Save the "what should we track" question for Phase B — that's a different kind of question (about measurement goals, not structure) and deserves its own dedicated back-and-forth.

## Phase B — Understand the research goal and translate it into measurements

This is where a novice study designer actually needs the most help, and where a black-box "it just picks things to track" approach would undermine the point of the project. Don't ask "what state should we track" — ask what they want to learn, then do the translation yourself.

1. **Ask, in plain language, what the user wants to learn about how people use this tool.** Not "what to track" — their research goal. If they're unsure or vague, prompt with concrete examples: "are people able to complete their task without getting stuck?", "does the interface feel responsive?", "which features do people actually use vs. ignore?", "do people get confused and backtrack?"
2. **Map the stated goal against the Phase A step 4 candidates, and be explicit about scope:**
   - **In scope** — anything ReVISit/Trrack can observe in the browser: the sequence and timing of interactions (clicks, selections, drags, navigation), the time between any two specific events, which features/paths get used vs. never touched, backtracking/retry patterns, whether and how a task got completed.
   - **Out of scope** — anything not observable client-side: backend performance, model accuracy, precision/recall, or any metric that would need server-side logs. Say this plainly if the user asks for something in this category, so they know to look elsewhere for it rather than assuming the study covers it.
3. **Don't silently resolve ambiguity.** If the stated goal uses a fuzzy term — "responsive," "latency," "useful," "intuitive," "engaging" — stop and ask a concrete follow-up with 2–3 grounded options before deciding what to track. For example, "responsive" could mean: (a) time from clicking something to the UI visibly updating, (b) time to complete the whole workflow end-to-end, or (c) how fast it *feels*, which can't be observed and would need a survey question instead of tracking. Mention in one sentence — not a lecture — that vague operational definitions cause real problems later: the data collected can end up not actually answering the question it was meant to, or not matching the statistical analysis the user plans to run on it. If the goal is fundamentally about which decision the tool supports (e.g. picking the best option vs. filtering to acceptable ones vs. generating something new), `decision-task-abstraction` can formalize that translation — or `decision-task-hierarchy` if the tool has several interdependent decision steps worth organizing into levels first.
4. **Confirm the final shortlist of concrete signals with the user, phrased against their stated goal, not raw variable names.** E.g.: "To see whether people get stuck, I'll track which metric is active, which item is selected or hovered, and the time between selecting an item and changing the metric" — not "I'll track `activeMetricId`, `selectedItemId`...". To define what "better" means for these tracked signals before prototyping, consider `ahon-metric-mapping` (standalone, or as Phase 1 of the broader `design-sheets` EvalOps workflow if the project will run many design iterations).
5. **Recommend think-aloud (audio) or screen recording when the stated goal needs them, not by default.** ReVISit supports both natively (`uiConfig.recordAudio` for think-aloud, `uiConfig.recordScreen` for screen recording — see Phase E for wiring). Suggest them when they'd genuinely fill a gap Trrack state-tracking leaves:
   - **Think-aloud (audio)** — when the goal is about *why* participants do something, their reasoning, confusion, or subjective reactions ("do they find this confusing," "what are they thinking while they explore") — things state tracking alone can't capture, since it only sees *what* changed, not *why*.
   - **Screen recording** — when the stimulus is a `website`/iframe wrap (Phase C) where fine-grained provenance tracking is hard or impossible to instrument, or when the goal needs visual detail Trrack state doesn't capture (mouse movement, reading patterns, exact rendered layout at a moment in time).
   - Don't turn these on automatically — they add participant burden and storage cost. Ask, note the answer in the decisions log, and only wire them in Phase E if confirmed.
6. This confirmed shortlist is exactly what Phase D implements. If nothing useful survives this conversation (the user's goal is entirely out of ReVISit's scope), say so honestly rather than tracking something arbitrary just to have something to show.

## Phase C — Convert or wrap

Reference `src/store/types.ts` (search for `StimulusParams`) for the target interface every React stimulus component must accept: `{ parameters, setAnswer, provenanceState, setProvenance }`.

- **React source**: adapt the confirmed component(s) to `StimulusParams<T, S>`. Drop routing/global-store assumptions that don't make sense once embedded as a single stimulus (e.g. react-router usage, app-level Redux/Zustand stores that assumed a whole-page app). Use `src/public/demo-react-trrack/assets/DemoReactTrrack.tsx` as the canonical shape to match.
- **Non-React source, reasonably small/simple**: port it into a `StimulusParams`-compliant React component of the same target shape.
- **Non-React source, large or opaque**: do not force a risky rewrite. Wrap it as a `type: "website"` component instead (see `WebsiteComponent` in `src/parser/types.ts` and the concrete pattern in `public/demo-html-trrack/`) — serve the original app's static assets as-is and bridge via `public/revisitUtilities/revisit-communicate.js` (`Revisit.postAnswers`, `Revisit.postProvenance`, `Revisit.onProvenanceReceive`).
- Place non-code assets (images/css/data files) under `public/<studyName>/assets/`. Place bundled code under `src/public/<studyName>/assets/` — only code under `src/public/**` is resolved at runtime, via the `import.meta.glob` lookup in `src/controllers/ReactComponentController.tsx`; the config's `path` for a `react-component` must match that location relative to `src/public/`.

## Phase D — Wire provenance tracking (Trrack)

Using the shortlist confirmed in Phase B:

- **Simple case** — one self-contained stimulus component with modest state: apply the inline pattern from `src/public/demo-react-trrack/assets/DemoReactTrrack.tsx` directly. Build a `Registry`/`initializeTrrack` (from `@trrack/core`) inside a `useMemo`, call `trrack.apply(label, action(payload))` on each tracked interaction, forward `trrack.graph.backend` through `setAnswer`/`setProvenance`, and hydrate local state from `provenanceState` on replay.
- **Complex case** — a multi-component app with state shared/derived across components (like `EvalOpsApp`): scaffold a per-study triplet at `src/public/<studyName>/{types.ts,useProvenance.ts,SharedStateContext.tsx}`, templated from `src/public/evalops2/{types.ts,useProvenance.ts,SharedStateContext.tsx}` but starting with an **empty** `ProvenanceStateModel` (no evalops2-specific fields). Wrap the study's component tree in the new `SharedStateProvider`. Then, for each confirmed tracked state variable, run:
  ```
  /trrack <stateName> <componentFile> <studyName>
  ```
  (the third argument targets the new study folder instead of the default `evalops2`).
- **Website/iframe case**: use the postMessage-based pattern from `public/demo-html-trrack/` — CDN-loaded `@trrack/core`, `trrack.currentChange(() => {...})`, `Revisit.postAnswers(...)`/`Revisit.postProvenance(trrack.graph.backend)`, and `Revisit.onProvenanceReceive(...)` for replay.

## Phase E — Scaffold the study

1. Create `public/<studyName>/config.json`, using `public/demo-react-trrack/config.json` and `public/evalops2/config.json` as structural references:
   - `studyMetadata`, `uiConfig` (including `helpTextPath`).
   - `components`: one entry per stimulus/intro/consent/debrief, correct `type`/`path`/`parameters`. Use `baseComponents` + per-instance `parameters` for repeated trial shapes.
   - `sequence`: `order`, nested blocks, `interruptions`, `skip` — per the flow confirmed in Phase A.
2. Generate stub markdown assets (e.g. `assets/introduction.md`) and ask the user to refine the content — don't invent study-specific copy on their behalf beyond a placeholder.
3. Register the study in `public/global.json`: add `<studyName>` to `configsList`, and `"<studyName>": { "path": "<studyName>/config.json" }` to `configs`.
4. **If think-aloud or screen recording was confirmed in Phase B**, wire it into `config.json` (see `public/demo-screen-recording/config.json` for the concrete pattern):
   - Set `uiConfig.recordAudio: true` for think-aloud, and/or `uiConfig.recordScreen: true` (+ optionally `recordScreenFPS`) for screen recording. Either can be overridden per-component if only some stimuli need it.
   - For screen recording specifically: add `"screen-recording"` to top-level `importedLibraries`, and insert `"$screen-recording.components.screenRecordingPermission"` into `sequence.components` *before* the first component that records the screen, so permission is requested up front.
5. No parser/schema regeneration is needed for this — it only adds a new study instance, not new component types. Only run `yarn generate-schemas` if you also changed `src/parser/types.ts`.

## Phase F — Generate README.md

Write `public/<studyName>/README.md`. This is the human-readable counterpart to everything Phases A–E just did — it exists so the study designer can see what they wanted to learn, how that became something measurable, exactly where in the code that happens, and how to keep building from here, instead of treating the conversion as a black box. Include:

- **Title + description** — one paragraph on the original tool/repo and what participants do with it (from `studyMetadata.description` plus your own understanding of the source).
- **Source** — original repo path/URL, and the conversion date.
- **Decisions made during conversion** — pull from the running log kept since Phase A, restructured as the actual conversation that happened:
  - **What you told us you wanted to learn** — the user's stated goal from Phase B, in their own words/paraphrased.
  - **How we translated that into measurable signals** — the ambiguity-resolving follow-ups from Phase B and the final concrete signals chosen, each tied back explicitly to the stated goal.
  - **What's out of scope and why** — anything the user asked about that ReVISit can't observe client-side, named plainly.
  - Stimulus scope, sequencing, and conversion strategy (React port vs. `website` wrap) with the reasoning for each.
  - Whether think-aloud (audio) and/or screen recording were recommended and/or enabled, and why (or why not, if considered and declined).
- **Where things live** — a short map, not full file contents: the `public/global.json` entry (`configsList` + `configs["<studyName>"]`), `public/<studyName>/config.json`, and the `src/public/<studyName>/` file tree with a one-line role for each file.
- **Provenance tracking** — a table, one row per tracked field/interaction, with columns for the field name, its type, where it's registered, and where it's recorded on change — each with a `file:line` reference. Get real line numbers by grepping right before writing this section, e.g.:
  ```
  grep -n "reg.register\|trrack.apply\|initializeTrrack" src/public/<studyName>/useProvenance.ts src/public/<studyName>/SharedStateContext.tsx
  ```
  (adjust the file list for the simple/inline case — grep the single stimulus file instead — or for the website case, grep for `trrack.currentChange`/`Revisit.postProvenance` in the HTML/JS asset). Add one caveat line under the table noting these line numbers are a snapshot as of generation and may drift if the file is edited afterward — don't build any freshness-tracking beyond that note.
- **Running this study** — `yarn serve`, then the study's `configsList` name / URL path.
- **Where to go next** — a short, concrete list of common tweaks and exactly where to make them, so the study designer can keep building without coming back to the skill for everything. E.g.:
  - Track something new → add a `reg.register(...)` call in `useProvenance.ts` plus a matching state/effect in `SharedStateContext.tsx` (or run `/trrack <field> <componentFile> <studyName>` if using the shared-context pattern).
  - Change instruction/consent/debrief wording → edit `assets/introduction.md` / `assets/debrief.md` directly.
  - Add a pre/post questionnaire (e.g. NASA-TLX, demographics) → add the library to `importedLibraries` in `config.json` and reference it in `sequence`.
  - Change what appears in the study list → edit `public/global.json`.
  - Add think-aloud or screen recording later → set `uiConfig.recordAudio`/`recordScreen` in `config.json` (see `public/demo-screen-recording/config.json`); screen recording also needs `"screen-recording"` in `importedLibraries` and its permission component in `sequence`.
- **Known limitations / TODOs** — placeholder intro/debrief copy, anything you flagged as imperfect during conversion.

## Phase G — Verify

1. `yarn typecheck` and `yarn lint`.
2. Start the dev server (`yarn serve`, or use the `run` skill) and load the new study by its `configsList` name. Click through the full sequence; confirm `setAnswer` fires for each stimulus and the provenance graph accumulates (check via devtools/console). Confirm replay hydration if the study supports it.
3. Optionally add a Playwright spec under `tests/`, modeled on `tests/demo-react-trrack.spec.ts`.

Report back what was converted, what's tracked and why (tied to the user's stated goal), and any assets/copy that still need the user's input (e.g. placeholder introduction text), and point to the generated `public/<studyName>/README.md` as the fuller writeup.

## Phase H — Offer deployment (optional)

Once the local click-through passes, mention that the study can be deployed as a live, shareable site via the `revisit-deploy` skill (it detects Netlify/Supabase/Render tooling, provisions storage and hosting, and generates a one-command redeploy script). Don't start deployment unprompted — just offer it. If the study's stimulus calls its own backend (localhost `apiUrl` or similar), note that sharing with participants will require hosting that backend, which is exactly what `revisit-deploy` handles.
