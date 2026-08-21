---
name: provenance-analysis
description: Generate project-specific provenance analysis files (<project>_metrics.py and <project>_analysis.py) by sampling a ReVISit JSON export to discover event types, then producing named metric wrappers on top of primitives.py.
---

You are generating two Python files for a new provenance analysis project. The pattern mirrors what exists in the `analysis/` folder of the evalops2 project:

- `primitives.py` — generic, never changes, already exists
- `<project>_metrics.py` — project-specific event constants and named metric functions
- `<project>_analysis.py` — notebook entrypoint that imports and calls those functions

## Step 1 — Discover the event types

The user must provide a path to the ReVISit JSON export and tell you which `sequence_id` (component identifier string) to use when extracting the stimulus provenance graph. Use this Python snippet inline to sample the data:

```python
import json
from pathlib import Path
from collections import Counter

data = json.loads(Path("<data_path>").read_text())

# find the relevant answer
for p in data[:3]:
    for answer in p["answers"].values():
        if "<sequence_id>" not in answer["identifier"]:
            continue
        nodes = answer.get("provenanceGraph", {}).get("stimulus", {}).get("nodes", {})
        events = Counter(n["event"] for n in nodes.values())
        # also sample the root state shape
        root = next((n for n in nodes.values() if n["event"] == "Root"), None)
        root_state = root["state"]["val"] if root else {}
        print("Events:", dict(events))
        print("State keys:", list(root_state.keys()))
        break
```

Run this (or ask the user to run it) to get the event list and state shape before writing anything.

## Step 2 — Ask what to measure

After discovering events, ask the user:
1. Which events represent meaningful user actions worth naming? (e.g. "what does `highlightedIndex` mean in this app?") If the user is unsure which events matter, `decision-task-abstraction` can help by classifying the underlying decisions (CHOOSE/ACTIVATE/CREATE) the events serve — meaningful events are usually the ones that execute or complete a classified decision.
2. Are there any specific behavioral metrics they want to measure (time-to-first-X, dwell times, session cycles, latency between two events)? Once a metric is analyzed, log what was learned in a `design-sheets` Loop & Co-Create closure record (`public/<studyName>/design/loop-and-cocreate-<n>.md`) so the finding and its follow-up owner aren't lost.
3. What is the project name (used for the filename prefix)?

## Step 3 — Generate `<project>_metrics.py`

Use the discovered events and the user's answers to produce the file. Follow this structure exactly:

```python
"""
<Project>-specific behavioral metrics derived from the provenance graph.

Each function is a thin, named wrapper around primitives using the event types
specific to the <Project> app. For a different project, keep primitives.py as-is
and write a new <project>_metrics.py with its own event constants.
"""

from primitives import (
    event_pairs,
    events_of_type,
    first_event_of_type,
    inter_event_durations,
    session_duration,
)

# Event type constants for the <Project> provenance graph
EV_ROOT = "Root"
EV_<NAME> = "<event_type>"
# ... one constant per discovered event type

# ---------------------------------------------------------------------------
# <MetricName> — <one line description matching the schema if applicable>
# ---------------------------------------------------------------------------

def <metric_name>(resolved: list[tuple]) -> <return_type>:
    """
    <What this measures and how it maps to the metrics schema if applicable.>
    """
    ...

# Thin wrappers around primitives with <project> event types
def <name>_durations(resolved: list[tuple]) -> list[int]:
    """Durations (ms) between consecutive <event> events."""
    return inter_event_durations(resolved, EV_<NAME>)
```

Rules:
- One constant per event type, named `EV_<UPPERCASE_EVENT>` 
- Named metric functions (not generic ones) for anything the user wants to measure
- Thin wrappers at the bottom for generic primitives parameterized with this app's event types
- No imports beyond `primitives`

## Step 4 — Generate `<project>_analysis.py`

```python
# %%
import json
from pathlib import Path

from primitives import reconstruct_states
from <project>_metrics import (
    # list all functions from <project>_metrics.py
)

all_data = json.loads(Path("data/<datafile>.json").read_text())
print(f"Total Participants: {len(all_data)}")


# %%
def get_stimulus_nodes(participant, sequence_id):
    for answer in participant["answers"].values():
        if sequence_id not in answer["identifier"]:
            continue
        graph = answer.get("provenanceGraph", {}).get("stimulus", {})
        nodes = list(graph.get("nodes", {}).values())
        return sorted(nodes, key=lambda n: n["createdOn"])
    return []


# %%
nodes = get_stimulus_nodes(all_data[0], "<sequence_id>")
resolved = reconstruct_states(nodes)

print(f"Nodes: {len(resolved)}")
print(f"Session duration: {session_duration(resolved) / 1000:.1f}s")

# %%
# TODO: call your metric functions here
```

## Output

Write both files into the same directory as `primitives.py`. Tell the user what event types were found, what metric functions were generated, and what they should fill into the `# TODO` cell.
