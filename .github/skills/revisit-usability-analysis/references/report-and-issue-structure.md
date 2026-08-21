# usability.qmd structure and issue-draft template

## Output layout inside `analysis/<studyName>/`

```
usability.qmd                      # report page (reads caches only)
analyze_usability.py               # on-demand AI analysis (process_media.py pattern)
data/findings/
  inventory.json                   # video inventory + pid↔pseudonym map (gitignored)
  raw/{pseudonym}_{taskId}.json    # cached raw model output per recording
  findings.json                    # normalized findings (schema: finding-schema.md)
  issues/F-00N-slug.md             # issue drafts (issue-ready findings only)
```

Register `usability.qmd` in `_quarto.yml` navbar (e.g. after Provenance). Everything under `data/` stays gitignored per the existing project `.gitignore`.

## usability.qmd sections (in order)

1. **Executive summary** — counts by category, top 3–5 findings by severity, one-paragraph takeaway.
2. **Scope and limitations** — which recordings were analyzed, by which tool; which were NOT analyzed and why; whether fallback evidence (transcripts/frames/event logs) substituted for video; chunking used; honesty about what the model may hallucinate.
3. **Prioritized findings table** — id, title, category, subtype, severity, confidence, occurrences count, owner. Sort severity desc, then confidence desc.
4. **Category × severity × confidence overview** — small crosstab or grouped counts, keeping the three dimensions visibly separate.
5. **Finding details** — one card/section per finding: occurrences with timestamps, observed / stated / interpreted / hypothesis blocks (labeled), expected-vs-observed, alternatives, code correlation (or "not correlated" / "not performed"), next action, open questions. When `rehydration.available` is true, add a **Reconstructed state & actions** subsection: the ordered `action_sequence` with offsets, the `timing_confidence`/`timing_note` caveat verbatim (never omit it), and a link to `repro_spec_path` if a repro spec was generated.
6. **Recurring patterns** — problems seen across ≥2 participants; note condition-specific vs universal.
7. **Code correlation summary** — repo, commit, branch, dirty flag; counts by correlation status; contradicted interpretations called out.
8. **Design and research themes** — design-opportunity findings grouped into themes; unmet needs.
9. **Open questions / discussion agenda** — every `needs-discussion` finding plus investigator-review items from preflight mode.
10. **Issue-draft index** — table linking finding id → `data/findings/issues/*.md` path.
11. **Methodology and provenance** — model/tool per artifact, run date, external-processing ledger (`run.externally_processed`), repo commit, privacy notes.

All content is loaded from `data/findings/findings.json` and `inventory.json` — no AI calls, no network access at render time.

## Issue-draft Markdown template (`make_issue_drafts.py` output)

```markdown
# {title}

Finding: {id} · Severity: {severity} · Confidence: {confidence}
Target repo: {github_target or "not specified"}
Analyzed at commit: {commit or "no code correlation"}

## Problem
{observed}

## Impact
{severity rationale; user or study impact}

## Evidence
- {pseudonym} @ {timestamp} ({task}, {condition}): {observed summary}
<!-- pseudonyms and timestamps only — no names, raw participant ids, or media links -->

## Steps to reproduce
Observed:
1. ...
Inferred (unverified):
1. ...

## Expected vs observed
{expected_vs_observed}

## Relevant code
{code.locations as file:lines — why} (status: {code.status})
Hypothesis: {hypothesis}

## Proposed approach
{next_action + implementation sketch}

## Acceptance criteria
- [ ] ...

## Validation plan
{tests to add/run; how to confirm with a re-recording}

## Open questions
- {open_questions}
```

Redaction rules (enforced by the script): drafts must not contain participant names, raw participant ids (24-char hex / uuid), `http(s)://` media URLs, or quotations longer than 140 characters. Link or attach raw recordings only if the user's stated privacy rules explicitly allow it — default is never.
