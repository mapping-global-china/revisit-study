---
name: ahon-metric-mapping
description: Map a study's user tasks to concrete, domain-grounded success metrics using the Analyst Hierarchy of Needs (AHON) as a shared reference point, per the EvalOps framework. Callable standalone during early goal-scoping, or from Phase 1 of the design-sheets skill.
---

You are helping a study designer translate abstract goals and user tasks into concrete evaluation metrics, using the Analyst Hierarchy of Needs (AHON) as grounding per the EvalOps framework. Read `.github/skills/revisit-skill-core/references/designsheets.md` now. The point is to answer "what does *better* mean here?" before prototyping starts, so later design loops have something concrete to check against instead of drifting.

## When to invoke

- **Early goal-scoping** for a new project/feature — during `study-from-repo` Phase B, `study-from-link` Phase B, or `study-from-paper` Phase 2 — whenever "success" for a task is ambiguous (fuzzy terms like "intuitive," "useful," "trustworthy").
- **As part of `design-sheets` Phase 1 (Sense & Orient)** — that skill's metrics step calls into this one; you can also run this skill on its own without going through the full 4-phase design-sheets workflow.
- **Re-run any time metrics need revisiting** — e.g. entering `design-sheets` Phase 3 (Reflect & Pivot), when accumulated evidence suggests the original metrics no longer reflect what matters.

## Workflow

1. **Identify the core tasks** the tool/feature is meant to support (e.g. "trace an AI summary statement back to its source document," "condense several reports into a brief").
2. **Map each task to an AHON need level.** AHON (Girona et al. 2024) articulates domain-grounded analyst requirements — use it to categorize what kind of analyst need each task addresses (e.g. summarization/synthesis, provenance/verification, sensemaking). If unfamiliar with a task's AHON category, ask the user how analysts in their domain would describe the underlying need, rather than guessing.
3. **Define a concrete success metric per task** — the thing that, if it improved, would mean the task is genuinely better supported (e.g. "reduction in manual synthesis errors," "success rate of multi-document source tracing without losing context"). Avoid metrics that can't be observed from what the study actually collects (see `provenance-analysis` and `revisit-analysis` for what's measurable from a ReVISit deployment).
4. **Assign cadence and ownership** for each metric — how often it's checked (small loop / per-feature vs. big loop / biweekly) and who owns tracking it. These map directly to EvalOps' cadence/roles pillars (see `design-sheets`).
5. **Confirm the table with the user** before treating it as settled — these mappings are meant to be a durable shared reference point across the project, not a one-off list.

## Output artifact

Write or update `public/<studyName>/design/ahon-metrics.md`:

```markdown
# AHON Task-to-Metric Mapping: <studyName>

Grounding: EvalOps / AHON (Girona et al. 2024)

| Task Description | AHON Need Level | Evaluation Metric ("What is Better?") | Cadence | Role/Owner |
| :--- | :--- | :--- | :--- | :--- |
| <task> | <AHON category> | <metric> | <e.g. Small Loop (Weekly)> | <owner, participation mode: internal-team-led / consultative / collaborative> |

## Notes
<anything the user flagged as still ambiguous, or metrics deliberately deferred>
```

If the file already exists (revisited during Reflect & Pivot), add a dated `## Revision <date>` subsection noting which rows changed and why, rather than silently overwriting the original mapping — this preserves the rationale trail EvalOps is meant to protect.

## Common pitfalls

- **Unstructured exploration.** Skipping this mapping and going straight to prototyping means there's no clear pass/fail signal later — flag this if a user wants to skip straight to building.
- **Loss of rationale across handoffs.** If this mapping isn't persisted (i.e. not written to `design/ahon-metrics.md`), downstream teams lose the definition of "better" — always write the artifact, don't just discuss it in chat.
- **Misaligned cadence.** Evaluating a high-level AHON need on too short a cadence produces noisy data; evaluating a basic task too infrequently risks rework. Match cadence to the task's actual complexity, and say so if the user proposes a mismatch.
- **Treating metrics as summative only.** These metrics are meant to be checked during small loops (`design-sheets` Phase 2), not just once at the end.
