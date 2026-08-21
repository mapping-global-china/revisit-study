---
name: revisit-skill-core
description: Shared portable grounding references and conventions used by other ReVISit agent skills. Installed as a transitive dependency; not intended for direct invocation.
user-invocable: false
disable-model-invocation: true
---

# ReVISit Skill Core

This package holds shared, redistributable grounding used by other skills:

- `references/designsheets.md`: EvalOps activities, cadence, roles, metrics, and closure records.
- `references/typology.md`: CHOOSE, ACTIVATE, and CREATE decision-task definitions and distinctions.

Calling skills explicitly load the relevant reference. The source paper PDFs are not bundled.
