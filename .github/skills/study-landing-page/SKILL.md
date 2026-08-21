---
name: study-landing-page
description: Add a link-in-bio-style landing page for a study — a small set of option cards (e.g. "Just View the Tool" vs. "Take the Study") that let a visitor pick between trying the underlying tool directly with no recording/study overhead, or starting the full reVISit study (recording, tasks, questionnaires). Use when the user wants a pre-study chooser page, a "just want to look around" option, or a shareable link that fans out to a few destinations for a single study.
---

Some studies wrap a tool that people may want to explore before (or instead of) taking the full study — think of the multi-link chooser pages ("linktree"-style) that route a visitor to one of several destinations. This skill adds that chooser as a small, per-study **landing page**, reusing the same card-based visual language as reVISit's own study-switcher home page (`src/components/ConfigSwitcher.tsx`), but scoped to a single study and driven by a tiny per-study data file — no new study-config schema, no parser changes.

This skill is a companion to `study-from-link` and `study-from-repo`: those skills scaffold the actual study (introduction, tasks, recording, questionnaires). This skill adds an *optional* front door in front of an existing study that offers a no-study/no-recording path alongside the "take the study" path. Run it after the study itself exists (or scaffold both in the same session if the user asks for a new study with a landing page from the start).

## Phase 0 — Inspect before editing

1. Identify the target study's key in `public/global.json` and the path to its `config.json` or `config.yaml`. Do not infer the key from the folder name; internal study links must use the registered key.
2. Check for both shared infrastructure pieces:
  - `src/components/Landing.tsx`, exporting the route-level `Landing` component.
  - A `/:studyId/landing` route in `src/GlobalConfigParser.tsx`, placed before `/:studyId/*`.
3. If both exist, do not edit shared source code. Adding another landing page is a data-only change in the target study folder.
4. If either is absent, install the shared infrastructure once, following the mechanism and behavior contract below. Match the repository's current React Router, Mantine, `PREFIX`, config-resolution, app-shell, and page-title patterns; add a colocated unit test for the new component. Then continue with the target study's data file.

The discriminating check after setup is direct navigation to `/<registered-study-key>/landing`: it must fetch the target study's sibling `landing.json`, not initialize a participant session through `Shell`.

## How the mechanism works (read this before scaffolding)

- **Route**: `/:studyId/landing`, registered once in [src/GlobalConfigParser.tsx](../../../src/GlobalConfigParser.tsx) alongside the existing `/:studyId/*` (Shell) and `/` (ConfigSwitcher) routes. This is shared infrastructure — do not duplicate it per study.
- **Component**: [src/components/Landing.tsx](../../../src/components/Landing.tsx) exports:
  - `Landing` — the route-level component. Resolves `:studyId` via `resolveConfigKey` (same helper `Shell` and `ConfigSwitcher` use), fetches `<studyFolder>/landing.json` (sibling of that study's `config.json`), and renders `LandingPageView`, or a graceful "no landing page configured, go to study" fallback if the fetch 404s or the file doesn't exist.
  - `LandingPageView` — the presentational card list, reusable/testable independent of routing.
  - `LandingPageConfig` / `LandingPageCard` — the TypeScript shape of `landing.json` (title, description, and a `cards` array, each with `id`, `title`, `description?`, `buttonText`, `href`).
  - `isExternalHref` — `href`s starting with `http://`/`https://` open in a new tab (external tool, no wrapping); anything else is treated as an app-relative path (prefixed with `PREFIX`, same tab) — typically the study's own `configsList` key to link to `/​<studyId>` for "take the study," or a path to a local static asset (like a placeholder tool page) for "view the tool."
- **Data file**: `public/<studyName>/landing.json`, colocated with that study's `config.json`. This is deliberately **not** part of `StudyConfig` or the JSON-schema-validated config — it's a small, optional, independently-fetched file so adding a landing page never requires parser/schema changes (`yarn generate-schemas`) or touches `studyConfigs` validation. A study with no `landing.json` behaves exactly as before; nothing about the existing study route changes.
- **Not registered in `global.json`** — the landing page isn't a separate "study," it's a front door for a study that's already registered there. Reference the existing `configsList` entry for the "take the study" card's `href`.

## Phase A — Confirm the destinations with the user

Ask (don't assume) how many cards and what each should say/link to. The common shape is exactly two:

1. **"Just view the tool" card** — no study, no recording, no questionnaire. The `href` here is usually one of:
   - An external link to the real, already-running tool (if one exists) — mark it external (`https://...`) so it opens in a new tab and is clearly not part of the recorded study.
   - A path to a local placeholder/demo page (e.g. the same `assets/placeholder-tool.html` a `study-from-link` no-link-mode study already scaffolds) if no real link exists yet — confirm with the user whether this should point at the same placeholder used inside the study, or something else entirely.
   - Confirm the wording — don't invent copy about what the tool does beyond what the user has told you.
2. **"Take the study" card** — links to the study itself. Use the study's `configsList` key as the internal `href` (e.g. `"href": "infinity-pool"` → resolves to `/infinity-pool`). Briefly describe what taking the study involves (recording, tasks, questionnaire) so the choice is informed.

If the user wants more than two cards (e.g. separate cards per task, or a third "watch a demo video" card), that's supported — `cards` is just an array; each entry needs `id`, `title`, `buttonText`, `href`, and an optional `description`.

## Phase B — Scaffold `landing.json`

Start from [assets/landing.json](./assets/landing.json) and create `landing.json` beside the target study's registered config path. Replace every `{{...}}` placeholder; do not leave template values in a finished page.

The resulting file should have this shape:

```json
{
  "title": "<Tool or study name>",
  "description": "<one-line framing of the choice>",
  "cards": [
    {
      "id": "tool",
      "title": "Just View the Tool",
      "description": "<what they get, and that it's not recorded/tracked>",
      "buttonText": "Open <ToolName>",
      "href": "<https://real-tool-url or a local asset path>"
    },
    {
      "id": "study",
      "title": "Take the Study",
      "description": "<what taking the study involves>",
      "buttonText": "Start the Study",
      "href": "<registered-study-key>"
    }
  ]
}
```

If the "view the tool" link isn't available yet (same situation `study-from-link`'s no-link mode handles for the study itself), point `href` at the same placeholder page the study uses, and add a top-level `"TODO"` key (never rendered, purely a note for future editors) explaining what to swap in later and pointing at the study's own placeholder-swap TODO if one exists (see `public/infinity-pool/config.json`'s `meta.TODO` pattern and its README's "Before running with real participants" section). Keep both TODOs in sync — they usually reference the same eventual link.

Do not add the landing file to `public/global.json`, `importedLibraries`, or the study sequence. The route discovers it from the registered config path.

## Phase C — Verify

1. `yarn typecheck` and `yarn lint`.
2. Start the dev server (`yarn serve`) and open `/<studyName>/landing` directly (there's no link to it from the home page `ConfigSwitcher` yet by design — it's meant to be shared directly, e.g. via a QR code or a recruitment link — so navigate to it manually to check).
3. Click through each card: external `href`s should open in a new tab and load the real/placeholder tool; the "take the study" card should land on the study's own introduction page at `/<studyName>`.
4. If `landing.json` is missing or malformed, confirm `/<studyName>/landing` still renders the graceful fallback (a "Go to Study" button) rather than a blank page or crash.

## Phase D — Optional test coverage

`Landing.tsx` separates `LandingPageView` (pure presentational, easy to unit test with `renderToStaticMarkup` + `MantineProvider`, no router/fetch mocking needed) from `Landing` (the route-level data-fetching wrapper). Prefer testing `LandingPageView` directly with a hand-built `LandingPageConfig` fixture — see [src/components/Landing.spec.tsx](../../../src/components/Landing.spec.tsx) for the pattern (renders title/description/cards, and checks external vs. internal `href`s get the right `target` attribute).

## Notes / non-goals

- This does not add a "no study" mode inside the study config itself — it's purely a routing front door. If the user actually wants a study that has *no* recorded/tracked component at all, that's just a study whose components don't enable recording; no special config is needed for that.
- Don't wire the landing page into `ConfigSwitcher`'s study cards automatically — ask the user first whether they want a link there (e.g. an extra small link/badge on the `StudyCard`) or whether the landing URL will only ever be shared directly (e.g. via Prolific, a QR code, or social media, matching the "link-in-bio" framing the user asked for).
