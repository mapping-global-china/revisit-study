---
name: study-from-paper
description: Set up a partial replication of a published study as a new ReVISit study — read the paper, identify its experiments and key findings, help the user pick ONE finding and a minimal design subset to replicate first, then scaffold the study (stimuli, conditions, measures, sequence) and hand off to the existing deploy/recruit/analyze skills. Use when the user wants to "replicate a paper", "recreate a study from a paper", or "test a published finding".
---

You are turning a published paper into a runnable **partial replication** in this repo. The goal is NOT a full replication of everything in the paper — it is the smallest faithful study that tests one key finding, built so the user can extend it later. The user provides the paper (PDF path, URL, or DOI) and optionally which experiment/finding they care about.

This skill front-loads *reading and deciding*; the building reuses the machinery you already have: stimulus construction follows `study-from-repo` Phases C–E patterns, provenance follows `provenance-analysis`, and afterward `revisit-deploy` → `revisit-prolific` → `revisit-analysis` take it live. Keep a running decisions log throughout (same discipline as `study-from-repo`) — it becomes the README's "Replication decisions" section.

## Phase 1 — Read the paper and map its experiments

Read the paper (fetch the URL/DOI landing page, or read the PDF the user provides — ask for a text/HTML version if the PDF is unreadable). Produce a compact **experiment map** and show it to the user:

For each study/experiment in the paper:
- **N and population** (crowdsourced? students? experts?)
- **Design**: between/within/mixed; the factors and their levels (e.g. 6 chart types × 3 data sizes)
- **Tasks and stimuli**: what participants actually did and saw
- **Measures**: DVs (accuracy, time, preference, confidence...), instruments used (SUS? NASA-TLX? custom Likert?)
- **Key findings**: the 1–3 headline results, with effect direction and (if reported) size
- **Feasibility flags**: anything hard to replicate in reVISit — physical apparatus, eye tracking, longitudinal sessions, proprietary datasets, in-lab-only protocols. Say plainly what's out of scope.

## Phase 2 — Pick the finding and shrink the design (the core judgment step)

**Stop and confirm with the user.** One ask-questions round:

0. If the replication's success criteria need grounding beyond "matches the paper's effect direction" — e.g. the paper's DVs don't map cleanly onto a clear notion of "better" for this replication — consider `ahon-metric-mapping` to build an explicit task-to-metric table before finalizing the finding/contrast below.
1. **Which experiment** (if the paper has several) — recommend the one that is (a) the paper's central claim and (b) most feasible in-browser.
2. **Which single finding** to target — phrase options as findings, not designs: "X is faster than Y for task Z", not "Experiment 2".
3. **The minimal contrast**: shrink the factor levels to the decisive comparison. The standard move: keep the paper's **winner and strongest loser** (or winner vs. baseline/control), drop the middle conditions. E.g. 6 visualization designs → the best and worst performers; 3 model variants → top model vs. baseline. State what's lost by shrinking (no dose-response curve, no interaction tests) so it's a conscious choice.
4. **Within vs. between**: prefer the paper's choice; if shrinking makes within-subjects feasible where the paper used between (fewer participants needed), offer it as an explicit deviation.
5. **Trial count**: scale down proportionally (e.g. paper's 40 trials/condition → 10–15 for a pilot) and say so in the decisions log.
6. **Measures**: map the paper's instruments onto existing libraries in `public/libraries/` — currently including vlat/mini-vlat/adaptive-vlat, calvi, nasa-tlx, sus, umux/umux-lite, ues, quis, smeq, sam, tam2, beauvis, previs, berlin-num, graph-literacy-scale, demographics, color-blindness, mic-check, virtual-chinrest, screen-recording. Use the library version even if the paper used a variant (note the deviation). Custom DVs (accuracy, response time) come free from reVISit's answer/timing records; interaction-level DVs need provenance tracking.

Also ask: think-aloud/screen recording (usually NO for replications — the original didn't have it and it changes timing behavior), and target N for the pilot.

## Phase 3 — Source or build the stimuli

In order of preference:

1. **Paper's supplemental material / OSF / GitHub**: many papers ship stimuli, datasets, or even runnable code. Ask the user if they have the supplement; check the paper for OSF/GitHub links. If a repo exists → this becomes a `study-from-repo` conversion (invoke that skill's Phases C–D for the stimulus work).
2. **Regenerate from description**: charts/stimuli described precisely enough to rebuild (chart type + data distribution + encodings). Build as a `react-component` stimulus (D3/vega per repo conventions) with parameters per condition — cite the paper section/figure each design decision comes from.
3. **Static assets**: if stimuli are images in the paper and quality suffices, extract to `public/<studyName>/assets/` and use `image` components — fastest path, note fidelity limits.

Faithfulness rules: reproduce the original's task wording as closely as the paper allows (quote it in the config `instruction` when printed in the paper); keep timing/deadline constraints if any; keep attention checks if the original had them.

## Phase 4 — Scaffold the study

Name convention: pick an **innocuous, participant-facing name** (e.g. `chart-assistant`, `graph-reading`) — the study name appears in the participant's URL, and a name like `replication-kim2018-perception` invites participants to look up the paper and bias their behavior. Record the paper linkage in the README, not the URL. Then standard scaffolding (see `study-from-repo` Phase E for mechanics):

- `public/<studyName>/config.json`:
  - `baseComponents` for the trial shape; one component per condition × trial via `parameters`.
  - **Condition assignment**: within-subjects → nested `sequence` blocks with `"order": "latinSquare"` (order counterbalancing, matching most papers' Latin-square designs); between-subjects → top-level block with `numSamples: 1` over condition blocks. Random trial order inside condition blocks unless the paper fixed it.
  - Measures: `importedLibraries` + sequence entries for mapped instruments; `correctAnswer` fields for accuracy DVs so reVISit scores automatically.
  - Demographics at the end (library), consent/intro at the start (placeholder copy flagged for IRB review).
  - **Pre-wire Prolific ID capture** (nearly every study recruits online): `uiConfig.urlParticipantIdParam: "PROLIFIC_PID"` plus an auto-filled ID response on the introduction (`{"id": "prolificId", "type": "shortText", "paramCapture": "PROLIFIC_PID", "required": false, "location": "belowStimulus", "placeholder": "Prolific ID"}`). Harmless when unused; see `revisit-prolific` Phase 2 for the full pattern including the completion redirect.
- Provenance: track what the finding needs (e.g. if the DV is just accuracy/time, minimal tracking suffices; if the finding involves strategy/interaction patterns, wire trrack per `provenance-analysis` conventions).
- Register in `public/global.json`; verify with `yarn typecheck` + click-through (`study-from-repo` Phase G).

## Phase 5 — README: the replication contract

Write `public/<studyName>/README.md` — this is the scientific record of what was and wasn't replicated:

- **Source**: full citation, DOI, which experiment.
- **Target finding**: the exact claim being tested, quoted from the paper.
- **Original vs. this replication** — a table: factors/levels kept vs. dropped, N, trial counts, measures (paper's instrument vs. library used), population, and every deviation with its rationale.
- **Predicted result**: what the original implies this study should find (direction + rough magnitude). This is what analysis compares against.
- **Extension paths**: which dropped conditions/measures to add back first if the pilot replicates.
- **Next steps**: point to `revisit-deploy`, `revisit-prolific` (with the paper's compensation/duration as reference), `revisit-analysis` (the analysis should test the predicted result explicitly).

Report back: the experiment map, the chosen finding and contrast, what was deviated from and why, and the study's local preview URL.

## Common pitfalls

- **Papers with many experiments**: never assume — Experiment 1 is often a pilot; the headline finding is usually in the middle experiments. Ask.
- **Underpowered shrinking**: dropping conditions is fine; dropping trial counts *and* N *and* conditions simultaneously can make the pilot uninformative. If the original effect was small, say the pilot may not detect it and suggest treating it as a feasibility run.
- **Stimulus fidelity**: perceptual studies (color, size, position encodings) are sensitive to rendering details the paper may not fully specify (exact pixel sizes, viewing distance). Note `virtual-chinrest` library exists for viewing-distance calibration if needed.
- **In-browser ≠ in-lab**: timing precision, screen variability, attention. Flag if the original controlled these tightly; consider the `test-device-restriction` pattern for enforcing desktop/screen size.
