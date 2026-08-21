---
name: decision-task-abstraction
description: Classify a study's user decisions into CHOOSE, ACTIVATE, or CREATE (Brumar et al. 2025 typology) to name what "better" means before building or auditing a feature. Use at the start of a project/feature, or periodically to retrofit an audit onto an existing tool.
---

You are helping a study designer name the decision-making tasks their tool/feature is meant to support, using the three-task typology from Brumar et al. Read `.github/skills/revisit-skill-core/references/typology.md` now. The output is a plain-language spec, not code — it exists so anyone building or evaluating the feature later knows exactly what kind of decision it's meant to support and what "success" looks like for that decision type.

## When to invoke

- **Start of a new project or feature**, during goal-scoping (e.g. as part of `study-from-repo` Phase B or `study-from-link` Phase B) — before deciding what to track or build, name the decision(s) the tool needs to support.
- **Periodically, or as a retrofit**, on an already-built tool — audit what decision types the current design actually supports, to find gaps (e.g. a filter UI that silently behaves like CHOOSE when the domain expert actually needs ACTIVATE's quality guarantee).

This skill does **not** organize tasks into a multi-level goal tree (that's `decision-task-hierarchy`) and does **not** render a diagram (that's `decision-problem-diagramming`, a rendering step you can run afterward on this skill's output). It does not add multi-criteria weighting to a CHOOSE task (that's `mcdm-tradeoff-refinement`, layered on top afterward if needed).

## Workflow

1. **Identify the base entities.** Ask the user (or infer from the study's stated goal / existing config) for:
   - **Options** — the information entities being evaluated (e.g. chart designs, evacuation routes, candidate summaries).
   - **Features** — characteristics of those options (e.g. price, confidence score, distance).
   - **Criteria** — preferences/standards applied to features (e.g. "under $20k", "confidence > 0.8").
2. **For each user decision in scope, classify it as exactly one of:**
   - **CHOOSE** — returns the top/best *k* options. Evaluation is **dependent** (options compared against each other). Guarantees quantity (*k* items), not absolute quality.
   - **ACTIVATE** — returns options meeting/exceeding a threshold. Evaluation is **independent** (each option judged alone, can be evaluated simultaneously). Guarantees quality (all meet criteria), not quantity (0 to N may return).
   - **CREATE** — assembles, synthesizes, or generates new information; can add new options, add/modify features, or return an entirely different output type than the input. No quantity/quality guarantees.
   Classify by the **evaluation mechanic**, not by user intent or which analytical technique (sorting, filtering, correlating) implements it. See the pitfalls below before finalizing.
3. **State the constraints for each classified task**: input options, criteria/thresholds if any, and what the output guarantees (quantity vs. quality) — this is what makes the classification checkable later, not just a label.
4. **Note candidate biases** relevant to the design (CHOOSE: loss aversion, framing, anchoring; ACTIVATE: information bias, anchoring effect, algorithmic processing bias) — flag them as design risks, don't attempt to resolve them here.
5. **Write the artifact** (Step 6) and confirm it with the user before treating the classification as settled — misclassifying CHOOSE vs. ACTIVATE early causes real rework later (see Common Pitfalls).

## Output artifact

Write or update `public/<studyName>/design/decision-abstraction.md`:

```markdown
# Decision Abstraction: <studyName>

Grounding: Brumar et al. (2025) typology

## Entities
- **Options**: <description>
- **Features**: <list>
- **Criteria**: <list, if applicable>

## Decisions

### <Decision name>
- **Type**: CHOOSE | ACTIVATE | CREATE
- **Input options**: <description>
- **Evaluation mechanic**: dependent | independent | transformative
- **Criteria / threshold** (if any): <...>
- **Output guarantees**: <quantity k, or quality-all-meet-criteria, or none>
- **Candidate biases to watch for**: <...>

<repeat per decision>

## Open questions
<anything left unresolved, e.g. ambiguous decisions the user wants to think about more>
```

If the file already exists (retrofit/periodic use), append new decisions under `## Decisions` and update `## Open questions` rather than overwriting prior entries — this file accumulates over the project's life, same as the EvalOps design sheets (`design-sheets` skill) it commonly sits alongside.

## Common pitfalls

- **Confusing CHOOSE and ACTIVATE.** "Only cars under $20k" is ACTIVATE (independent threshold). "The cheapest available car" is CHOOSE (dependent comparison). If the user describes a hard cutoff, it's ACTIVATE; if they describe "the best," "the top N," or "compared to the others," it's CHOOSE.
- **Treating CREATE as a data loader.** CREATE represents genuine synthesis — reframing input into a new representation or generating something new — not just fetching/passing through data.
- **Letting intent dictate the type.** A user's *reason* for filtering (include the best vs. exclude the worst) doesn't change that it's still ACTIVATE if the mechanic is an independent threshold. Classify by mechanic, not motive.
- **Skipping the guarantees.** Writing down just "CHOOSE" without the quantity/quality guarantee loses the point of the classification — the guarantee is what a later evaluation should check against.
