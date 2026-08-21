# Provenance rehydration: concepts and degrade-gracefully modes

This capability turns a timestamped observation from a screen recording into
the exact application state and action sequence that produced it, by reusing
the trrack provenance graph already recorded alongside the video. It is
invoked as a step inside another skill's analysis phase (`revisit-usability-analysis`
or `refinement-from-video`), not run standalone.

## Why this is possible at all

- Every `react-component` stimulus that tracks interactions does so via
  Trrack, and its `StoredAnswer.provenanceGraph.stimulus` holds the full node
  graph: each node has `createdOn` (epoch ms), `event` (the registered action
  name), and a `state` (checkpoint or RFC-6902 patch).
- `analysis/primitives.py`'s `reconstruct_states(nodes)` already knows how to
  turn that graph into `[(node, state, change), ...]` with the full JSON
  state at every node. This capability **reuses that function** rather than
  reimplementing state reconstruction.
- Every stimulus component is contractually required (`StimulusParams<T, S>`)
  to accept a `provenanceState` prop and rehydrate its local state from it —
  this is exactly what replay/analysis tooling already relies on, and exactly
  what a generated repro test feeds in as a prop.

## The two-clocks problem

A video recording's timeline (`00:00` = recording start) and a trrack node's
`createdOn` (epoch milliseconds) are **different clocks**. `rehydrate_node.py`
anchors them using the task's own `answers[identifier].startTime` (also epoch
ms) as the zero point for that task's portion of the video.

This anchor is an **approximation**: `MediaRecorder` start latency and
dropped frames mean actual drift of roughly 1-2 seconds is normal. Every
result carries a `timing_confidence` (`approximate` | `low`) and a
`timing_note` explaining the drift — never present a rehydrated state as
frame-exact, and never omit the caveat when rendering it into a report.

## Code correlation mechanism

A node's `event` field is the literal string passed as the first argument to
`registry.register(...)` in the study's `trrack.ts` (or `useProvenance.ts` /
`SharedStateContext.tsx` for the shared-context pattern from `study-from-repo`).
`correlate_action.py` greps for that exact registration call and returns the
file/line — this is precise, not a guess, because the event name **is** the
registration key. If the event string isn't found anywhere under the study's
`src/public/<studyName>/` assets, it returns `not-correlated` with an empty
`locations` list — never invent a location.

## Degrade-gracefully modes

Always check these in order and report honestly which mode applied — don't
silently produce a partial result without saying why.

1. **No provenance available.** The flagged component is `markdown`,
   `questionnaire`, `website` without trrack wiring, or the answer's
   `provenanceGraph.stimulus` is empty/absent. `rehydrate_at_timestamp()`
   returns `{"matched": false, "reason": "..."}`. The calling skill's finding
   gets `rehydration: {available: false}` or omits the block entirely — this
   is the common case, not an error state.
2. **Provenance available, repo not available/not confirmed.** State and
   `action_sequence` are populated; skip `correlate_action.py` and set the
   finding's `code` block (if any) to `status: "not-correlated"`. No repro
   spec is generated (it needs the repo to locate the component source).
3. **Provenance + repo available.** Full pipeline: state + action sequence +
   code correlation (exact file/line of the registration). If the finding is
   high/critical severity and reproducible, **ask the user before** running
   `generate_repro_spec.py` — it writes a new file into `src/public/**`, and
   per this repo's norms, new files aren't created silently.

## What the generated repro spec can and cannot assert

This repo has no `jsdom` or `@testing-library/react` — existing component
unit tests (`TaskProvenanceNodes.spec.tsx`, `useNextStep.spec.tsx`) render
with `renderToStaticMarkup` from `react-dom/server` and assert on the
resulting markup string or on exported pure functions. The generated repro
spec follows the same pattern: it can assert on what the component renders
**synchronously** from `parameters` + `provenanceState` props. It **cannot**
exercise `useEffect`-driven DOM work (e.g. a d3 canvas draw, or an
`IntersectionObserver`) because there's no real DOM to run those effects
against. The scaffold says this plainly in a comment and leaves the actual
assertion as a `// TODO` — the script's job is reproducing the state, not
guessing what "correct" looks like.

The generated spec always wraps the component in `<MantineProvider>` (per the
existing pattern in `Landing.spec.tsx`/`ErrorLoadingConfig.spec.tsx`) since
nearly every stimulus component uses Mantine UI primitives and throws without
it (`MantineProvider was not found in component tree`).

### Known environment gap: `@trrack/core` import fails under default Vitest config

Confirmed by running the generated spec for `MfvTrial.tsx` (which imports
`@trrack/core`): Vitest's default module externalization can't resolve
`@trrack/core`'s ESM build, which does `import { configureStore, ... } from
'@reduxjs/toolkit'` — `@reduxjs/toolkit`'s package is CJS, so Node's ESM
interop rejects the named import (`SyntaxError: Named export 'configureStore'
not found`). This is a **pre-existing gap**, not something introduced by this
skill — no spec in this repo imported a `@trrack/core`-using component before
provenance-rehydration existed.

**Fix, not yet applied to the shared `vite.config.ts`** (this skill doesn't
edit shared config without asking): add to `test.server.deps.inline` in
`vite.config.ts`:

```ts
test: {
  // ...existing options...
  server: {
    deps: {
      inline: ['@reduxjs/toolkit', '@trrack/core'],
    },
  },
},
```

Verified locally (scratch config, not committed) that this resolves the
import error; after that, only the `MantineProvider` wrapping (already
handled by the generated spec) remained necessary for the spec to run and
pass. **Ask the user before adding this to the real `vite.config.ts`** — it's
a shared, repo-wide test config change, same "confirm before editing shared
config" norm as everywhere else in these skills. If declined, note in the
finding/note that the generated repro spec requires this config addition to
run, and it doesn't run out of the box yet.

## Invocation contract for calling skills

A calling skill's analysis/synthesis phase should, per finding/note with a
timestamp:

1. Load the relevant `answers[identifier]` from the fetched `participantData.json`.
2. Call `has_provenance(answer)` (from `rehydrate_node.py`). If false, skip —
   don't force a rehydration attempt.
3. If true, call `rehydrate_at_timestamp(answer, video_timestamp_s)` and
   attach the result (state, action_sequence, timing_confidence/timing_note)
   to the finding's optional `rehydration` block.
4. If `code_repo` is confirmed for this run, call `correlate_action.py` with
   the matched node's `event` and the study name; use its result to fill (or
   upgrade) the finding's existing `code` block.
5. If the finding is `revision_ready`/`issue_ready` and high/critical
   severity, offer (don't auto-run) `generate_repro_spec.py`; record the
   resulting path in `rehydration.repro_spec_path` if the user accepts.
