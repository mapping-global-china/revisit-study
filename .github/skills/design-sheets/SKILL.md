---
name: design-sheets
description: Run the EvalOps four-activity design-sheet workflow (Sense & Orient, Loop & Co-Create, Reflect & Pivot, Transition & Hand-Off) to make evaluation cadence, roles, and metrics explicit and continuous across a project's life, producing accumulating markdown artifacts. Use at project start, repeatedly during prototyping loops, at pivot points, and at handoff — not a one-shot scaffold.
---

You are operationalizing the EvalOps framework for a visualization/study project in this repo. Read `.github/skills/revisit-skill-core/references/designsheets.md` now. EvalOps is a **thin overlay** on top of whatever design process the team already follows (DSM, Nested Model, or just building the study directly) — it does not replace that process, it makes evaluation's **cadence** (when checks happen), **roles** (who owns them), and **metrics** (how evidence ties to goals) explicit and continuous instead of implicit or left until the end.

**This skill is invoked repeatedly across a project's lifetime, not once.** Sense & Orient runs near project start; Loop & Co-Create runs every time a prototyping loop closes (many times); Reflect & Pivot runs after several loops accumulate, at a natural review point; Transition & Hand-Off runs once, at handoff. Ask the user which phase they're in — don't assume Phase 1 just because this is the first time the skill is invoked for a study.

## Phase 1 — Sense & Orient

**Goal**: establish the evaluation baseline before design begins.

1. **List & Explore**: identify prior work, domain constraints, existing baseline artifacts relevant to this project.
2. **Align (Metrics)**: define what "success" looks like by mapping tasks to metrics. **Invoke `ahon-metric-mapping`** for this step — don't reinvent the task-to-metric table here.
3. **Prepare (Roles & Cadence)**: document who owns evaluation, who represents stakeholders, and the cadence/rhythm for evaluation loops (small loops per prototype change vs. big loops per phase transition).
4. **Exit condition**: the team agrees the metrics reflect the design goals and the mapping is documented (i.e. `design/ahon-metrics.md` exists and is confirmed).

**Output**: `public/<studyName>/design/sense-and-orient.md`:

```markdown
# Sense & Orient: <studyName>

Grounding: EvalOps

## List & Explore
<prior work, constraints, baseline artifacts>

## Align (Metrics)
See design/ahon-metrics.md for the full task-to-metric table.
Summary: <1-2 sentence recap of what "better" means for this project>

## Prepare (Roles & Cadence)
- **Cadence**: <e.g. biweekly reviews, ad-hoc small loops>
- **Roles**: <who owns evaluation, who represents stakeholders, who records decisions>

## Closure
**Decision**: metrics + cadence + roles confirmed, ready for Loop & Co-Create.
**Next cadence**: <when the first Loop & Co-Create closure is expected>
```

## Phase 2 — Loop & Co-Create

**Goal**: close small design-evaluation loops during active sketching/prototyping, each ending in a decision rather than open-ended exploration.

1. **Recap & Plan**: review the metrics from Sense & Orient (or the most recent Reflect & Pivot) to decide exactly which question this loop must answer.
2. **Define the Loop (Roles)**: who builds the prototype/sketch, who runs the feedback session, who summarizes findings. Note the participation mode (internal-team-led / consultative / collaborative).
3. **Execute & Document**: capture what changed, feedback received, immediate next step.
4. **Exit condition**: decisions, findings, and next steps are documented and agreed.

**Output**: `public/<studyName>/design/loop-and-cocreate-<n>.md` (increment `<n>` — each closed loop gets its own numbered file, so the sequence of decisions across the project stays inspectable):

```markdown
# Loop & Co-Create <n>: <studyName>

**Question this loop answers**: <tied to a specific metric from design/ahon-metrics.md>

## Defining the Loop
- **Builder**: <who>
- **Feedback session lead**: <who>
- **Summarizer**: <who>
- **Participation mode**: internal-team-led | consultative | collaborative

## Execute & Document
**Changed**: <what was built/modified>
**Feedback**: <what was learned>

## Closure Record
**Decision**: <what was decided>
**Rationale**: <why>
**Owners**: <who is accountable for follow-up>
**Next cadence**: <when the next loop or review happens>
```

## Phase 3 — Reflect & Pivot

**Goal**: pause after several Loop & Co-Create cycles to analyze accumulated evidence and decide whether to continue, pivot, or defer.

1. **Reflect (Cadence)**: shift from small loops to a larger, planned review — list which `loop-and-cocreate-*.md` files this review covers.
2. **Analyze Evidence**: compare accumulated evidence against the metrics in `design/ahon-metrics.md` (re-run `ahon-metric-mapping` first if metrics themselves need revisiting).
3. **Re-Orient (Decide)**: explicitly decide **continue / change direction (pivot) / defer** for each idea under review, with rationale.
4. **Exit condition**: consensus reached and documented on the direction.

**Output**: `public/<studyName>/design/reflect-and-pivot-<n>.md`:

```markdown
# Reflect & Pivot <n>: <studyName>

**Loops reviewed**: <list of loop-and-cocreate-*.md files>

## Analyze Evidence
<how the accumulated prototype/feedback aligns with or falls short of design/ahon-metrics.md>

## Re-Orient
| Idea / Direction | Decision | Rationale |
| :--- | :--- | :--- |
| <idea> | Continue / Pivot / Defer | <why> |

## Closure Record
**Decision**: <summary>
**Owners**: <who>
**Next cadence**: <when the next Loop & Co-Create or Reflect & Pivot happens>
```

## Phase 4 — Transition & Hand-Off

**Goal**: package the project for stakeholders/downstream developers without losing evaluation momentum. Run once, at handoff.

1. **Prepare (Artifacts)**: bundle code, design rationale, `design/ahon-metrics.md`, and all `loop-and-cocreate-*.md` / `reflect-and-pivot-*.md` closure records.
2. **Align (Continuous Evaluation)**: define the logic/metrics the downstream team will use to judge ongoing success — usually a continuation of the existing AHON mapping, revised if the handoff changes scope.
3. **Final Cadence**: one internal loop to confirm handoff artifacts are complete, then one larger collaborative loop to verify the new team has everything they need.

**Output**: `public/<studyName>/design/transition-handoff.md`:

```markdown
# Transition & Hand-Off: <studyName>

## Prepare (Artifacts)
- Metrics: design/ahon-metrics.md
- Loop closure records: <list>
- Reflect & Pivot records: <list>
- Code / other artifacts: <pointers>

## Align (Continuous Evaluation)
<the metrics/logic the downstream team should use going forward, and why>

## Final Cadence
- **Internal confirmation loop**: <status/date>
- **Collaborative handoff loop**: <status/date, who from the new team participated>

## Closure Record
**Decision**: handoff complete / pending <items>.
**Owners (new team)**: <who>
```

## Common pitfalls

- **Evaluation as a culminating assessment.** Don't wait until the end to invoke this skill — Phase 2 loops should close continuously during active prototyping.
- **Loss of rationale.** Every phase's output must end in a closure record (decision, rationale, owners, next cadence) — a phase without one isn't actually closed, even if the prototyping work itself is done.
- **Unbounded ideation.** If Loop & Co-Create keeps producing loops with no Reflect & Pivot in sight, that's a sign to trigger Phase 3 — use the accumulated metrics to force a continue/pivot/defer decision rather than iterating indefinitely.
- **Skipping the metrics step.** Don't hand-wave "Align (Metrics)" in Phase 1 — invoke `ahon-metric-mapping` and get an actual table; vague success criteria cause the collected evidence to not answer the question it was meant to.
