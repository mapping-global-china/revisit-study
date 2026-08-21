# revision-notes.md structure and revision-notes-index.md

## Output layout inside `analysis/<studyName>/refinement/`

```
refinement/
  revision-notes-index.md          # running list of all rounds, updated each round
  rounds/
    1/
      data/                        # gitignored: raw recording, transcript, raw model output
        session/                   # fetched reviewer session (participantData.json, recording.webm)
        raw/                       # raw Gemini/Deepgram output per task recording
        revision_notes.json        # normalized notes (schema: finding-schema.md)
      revision-notes.md            # report page for this round
    2/
      ...
```

This lives inside the target study's `analysis/<studyName>/` folder but in its
own `refinement/` subtree, separate from the real-participant Quarto project
(`fetch_data.py`, `*.qmd`, etc.) that `revisit-analysis` scaffolds — the two
can coexist without collision, and `refinement/` doesn't require the Quarto
project to exist yet.

Everything under `data/` stays out of version control (add `refinement/rounds/*/data/`
to the study's `.gitignore` if one exists, or create a `refinement/.gitignore`
with `rounds/*/data/`).

## `rounds/<n>/revision-notes.md` sections (in order)

1. **Round summary** — reviewer name/role, date, which recording(s) were
   analyzed, which tool processed them, counts by category and severity.
2. **Scope and grounding** — what the model was shown: task instruction(s),
   and the README's "Original vs. this replication" table if present (cite
   `run.grounded_in`). State plainly if no video tool was available and which
   fallback evidence was used instead.
3. **Prioritized notes table** — id, title, category, severity, confidence,
   `already_documented`, occurrences count, owner. Sort severity desc, then
   confidence desc.
4. **Note details** — one section per note: occurrences with timestamps,
   observed / stated / interpreted / hypothesis blocks (labeled),
   `source_reference` (what the design should match), code correlation (or
   "not correlated" / "not performed"), next action, open questions. When
   `rehydration.available` is true, include a **Reconstructed state &
   actions** subsection (matched node/event, the `timing_confidence`/
   `timing_note` caveat verbatim, the ordered action sequence, and a link to
   `repro_spec_path` if a repro spec was generated) — see the
   `provenance-rehydration` skill.
5. **Already-documented deviations re-raised** — notes with
   `already_documented: true`, called out separately so it's clear the
   reviewer knew about the documented deviation but still flagged it (usually
   means it matters more than the README currently implies).
6. **New fidelity concerns** — notes with `already_documented: false` and
   `category: fidelity-to-source` — these are the ones most likely to need a
   README update or a design fix.
7. **Code correlation summary** — repo, commit, branch, dirty flag; counts by
   correlation status; contradicted interpretations called out.
8. **Open questions / discussion agenda** — every note with
   `open_questions` populated.
9. **Methodology** — model/tool used, run date, external-processing ledger
   (`run.externally_processed`), repo commit.

## `revision-notes-index.md`

One row per round, updated after each round runs:

| Round | Date | Reviewer | Notes | Fidelity concerns (new) | Report |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-08-03 | Lace Padilla | 4 | 1 | [rounds/1/revision-notes.md](rounds/1/revision-notes.md) |

Followed by a short "carried-forward open questions" list aggregating
unresolved `open_questions` across all rounds, so nothing gets lost between
review sessions.

## Note-details Markdown block (used within `revision-notes.md`, no separate issue-draft files)

Unlike `revisit-usability-analysis`, this skill does not produce separate
per-finding issue-draft files — revision notes are meant for discussion between
the study designer and the researcher, not standalone GitHub issues. Render
each note inline in `revision-notes.md`:

```markdown
### {id}: {title}

**Category**: {category} · **Severity**: {severity} · **Confidence**: {confidence} · **Already documented**: {already_documented}

**Observed**: {observed}
**Reviewer said** ({reviewer.name}): {stated}
**Interpreted**: {interpreted}
**Should match**: {source_reference}

**Evidence**: {occurrences as task @ timestamp}

**Code**: {code.locations as file:lines — why} (status: {code.status})

**Next action**: {next_action}
**Open questions**: {open_questions}
```

If the user later wants a GitHub issue from a specific revision note, that's a
separate explicit request — this skill does not create issues or issue drafts
on its own.
