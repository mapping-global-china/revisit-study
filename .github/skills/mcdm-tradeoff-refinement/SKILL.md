---
name: mcdm-tradeoff-refinement
description: Add weighted multiple-criteria rigor to an existing CHOOSE node (Brumar et al. 2025 typology) when a decision involves trading off several competing criteria. A refinement layered on top of an existing decision-abstraction.md or decision-hierarchy.md CHOOSE task, not a from-scratch entry point.
---

You are refining a specific **CHOOSE** task with multiple-criteria decision-making (MCDM) rigor. Read `.github/skills/revisit-skill-core/references/typology.md` now. MCDM is a mathematical formalism for selecting among options given multiple competing criteria and a decision-maker's preferences over them — this skill applies it as a **refinement on top of an existing CHOOSE node**, not as a way to classify decisions from scratch (that's `decision-task-abstraction`/`decision-task-hierarchy`).

## When to invoke

Only when there is an existing CHOOSE task — from `public/<studyName>/design/decision-abstraction.md` or `decision-hierarchy.md` — where the study designer has said something like "it's not just picking the best one on a single measure, there are several things being traded off" (e.g. price vs. mileage vs. condition; speed vs. accuracy vs. explainability). If no CHOOSE node exists yet, tell the user to run `decision-task-abstraction` or `decision-task-hierarchy` first to establish one.

## Workflow

1. **Identify the target CHOOSE node.** Ask which task in the source file this refines (by name).
2. **Enumerate the criteria** the comparison actually trades off (not just the single feature the CHOOSE node's summary line may have implied) — e.g. price, mileage, condition, driver-assist tech.
3. **Elicit weights** for each criterion from the user — relative importance, doesn't need to be precise (e.g. "price matters about twice as much as mileage").
4. **Score each candidate option** against each criterion (numeric, or ordinal if numbers aren't natural for that criterion).
5. **Compute the resulting top-k** using the weighted scores — a simple weighted sum is usually sufficient; don't introduce a more complex MCDM method (AHP, TOPSIS, etc.) unless the user specifically asks for one.
6. **Handle the zero/insufficient-option case.** MCDM refinement sits downstream of any ACTIVATE filtering — if ACTIVATE returned too few or zero options, note the fallback (loosen the ACTIVATE threshold, or re-run CREATE to generate more candidates) rather than letting CHOOSE silently rank an empty or tiny set.
7. **Confirm the weighting and resulting ranking with the user** — trade-off weights are a judgment call, not something to lock in unilaterally.

## Output

**Append** a `## MCDM Refinement: <node name>` section to the source file (`decision-abstraction.md` or `decision-hierarchy.md`) that contains the target CHOOSE node:

```markdown
## MCDM Refinement: <CHOOSE node name>

Grounding: Brumar et al. (2025) typology (MCDM as a mathematical formalism for CHOOSE-type decisions)

**Criteria and weights**:

| Criterion | Weight | Notes |
| :--- | :--- | :--- |
| <criterion> | <weight> | <e.g. direction: higher/lower is better> |

**Option scores**:

| Option | <Criterion 1> | <Criterion 2> | ... | Weighted score |
| :--- | :--- | :--- | :--- | :--- |
| <option> | <score> | <score> | ... | <computed> |

**Resulting top-k**: <the chosen options, k = ...>

**Fallback if too few options available**: <e.g. "if ACTIVATE upstream returns < k options meeting the price/mileage threshold, loosen the mileage threshold by 10% before re-running this ranking">
```

If this section already exists for the node (re-run after criteria/weights changed), replace it in place.

## Common pitfalls

- **Conflating ACTIVATE and CHOOSE in the same step.** Absolute threshold filtering (e.g. "exclude anything over budget") is ACTIVATE and belongs upstream, before this refinement — don't fold hard cutoffs into the weighted-scoring table.
- **Assuming the weighted ranking guarantees quality.** CHOOSE only guarantees *quantity* (top-k). If nothing upstream filtered out unacceptable options (no ACTIVATE step), the "best" k by weighted score could still be a bad set — say so rather than implying MCDM rigor fixes that.
- **Over-formalizing.** If the user can't articulate stable weights or criteria, don't force a numeric table — note the ambiguity in the source file and suggest they revisit once the trade-off is clearer, rather than fabricating precision that isn't there.
- **Picking a complex MCDM method unprompted.** Default to a simple weighted sum; only reach for AHP/TOPSIS/etc. if the user asks, since added mathematical rigor here is meant to serve clarity, not obscure it.
