---
name: decision-task-hierarchy
description: Organize a project's CHOOSE/ACTIVATE/CREATE decisions into a multi-level goal tree (Brumar et al. 2025 typology) once scope has grown enough that a flat task list is hard to reason about. Invoked independently, any time in a project — does not require decision-task-abstraction to have just run.
---

You are helping a study designer organize decision tasks into a multi-level hierarchy, using the composability property of the Brumar et al. typology. Read `.github/skills/revisit-skill-core/references/typology.md` now. The typology's tasks (CHOOSE/ACTIVATE/CREATE) are composable and hierarchical by design — a CREATE step can generate the criteria a later ACTIVATE step uses, or an ACTIVATE filter can feed a CHOOSE ranking downstream. This skill makes that composition explicit as a goal tree, useful once a project has enough moving parts that a flat list of decisions stops being legible.

## When to invoke

Independently, any time — this is **not** a required follow-on to `decision-task-abstraction`. Two entry points:
- **Atomic tasks already classified**: the user (or `public/<studyName>/design/decision-abstraction.md`) already has a list of CHOOSE/ACTIVATE/CREATE tasks; this skill's job is purely to organize them into levels and expose dependencies.
- **Nothing classified yet**: the user just has a complex, real-world decision goal in mind. Classify atomic tasks as you go (Step 3 below covers this), then organize — don't require a separate abstraction pass first.

Typical trigger: project/tool scope has grown — several features, each with its own decision logic — and it's become hard to see how the pieces relate or where a new feature should plug in.

This skill does not render a diagram (`decision-problem-diagramming` does that afterward) and does not add multi-criteria weighting (`mcdm-tradeoff-refinement` layers that onto a specific CHOOSE node afterward).

## Workflow

1. **Define the overarching goal (Level 1).** What's the ultimate decision the tool/system supports? Identify the primary options, features, and criteria involved at this top level.
2. **Deconstruct into phases (Level 2).** Break the Level 1 goal into intermediate phases or milestones. Identify dependencies — where the output of one phase is the input to the next.
3. **Classify atomic tasks (Level 3).** For each Level-2 phase, enumerate its atomic decisions and classify each as CHOOSE, ACTIVATE, or CREATE (same classification rules as `decision-task-abstraction` — evaluation mechanic, not intent; see that skill's Common Pitfalls if unsure).
4. **Map information flow across levels.** For each atomic task: input options/data, evaluation constraints (thresholds, criteria, target k), output format and quantity/quality guarantees. Verify a parent task's output type matches what its child tasks need as input (composability check) — a mismatch here usually means a level boundary is misplaced.
5. **Confirm the tree with the user** before writing the final artifact — hierarchy placement is a judgment call the study designer should validate, not something to lock in silently.

## Output artifact

Write or update `public/<studyName>/design/decision-hierarchy.md`:

```markdown
# Decision Hierarchy: <studyName>

Grounding: Brumar et al. (2025) typology

## Level 1 — Goal
**Goal**: <the ultimate decision>
**Options / Features / Criteria**: <top-level entities>

## Level 2 — Phases

### Phase: <name>
- **Depends on**: <prior phase(s) or "none">
- **Atomic tasks**: <list of Level 3 task names below>

<repeat per phase>

## Level 3 — Atomic tasks

### <Task name> (Phase: <parent phase>)
- **Type**: CHOOSE | ACTIVATE | CREATE
- **Input options**: <...>
- **Evaluation mechanic**: dependent | independent | transformative
- **Criteria / threshold** (if any): <...>
- **Output**: <guarantees + what feeds the next task>

<repeat per atomic task>
```

If `decision-abstraction.md` already exists for this study, cross-link rather than duplicate: reference its task entries by name instead of re-describing them, and only add the Level 1/2 structure this skill introduces.

## Common pitfalls

- **Forcing a level that doesn't exist.** Not every project needs three levels — if a decision is genuinely flat (one CREATE feeding one CHOOSE, no intermediate phase), don't invent a Level 2 just to fill the template.
- **Overloading a single atomic task.** If a task both filters by threshold (ACTIVATE) and then picks the best remaining option (CHOOSE), that's two Level 3 nodes, not one.
- **Mismatched composition.** A parent phase's declared output type must match what its child atomic tasks expect as input — check this explicitly (Step 4); it's the most common source of a hierarchy that looks right but doesn't actually compose.
- **Ignoring the zero-return state.** If a Level 3 ACTIVATE task feeds a Level 3 CHOOSE task, note what happens when ACTIVATE returns zero options — the hierarchy should surface this failure path, not hide it.
