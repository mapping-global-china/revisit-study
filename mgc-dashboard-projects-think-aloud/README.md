# MGC Dashboard Think-Aloud Study

This study captures how participants explore the MGC dashboard projects page while thinking aloud.

## Source

- URL: https://mgc-vis.netlify.app/dashboard/projects
- Source mode: Live-link mode (external tool reached over the network)
- Date scaffolded: 2026-08-05

## Decisions made

- Study goal: Observe how people navigate and interpret the dashboard projects page, and where they get stuck or confused during natural exploration.
- Capture model: Screen recording plus think-aloud audio only; no post-task questionnaire was requested.
- Embedding decision: Iframe wrap selected. Header check via `curl -sI` showed no explicit `X-Frame-Options` or `frame-ancestors` restriction at scaffold time.
- Intro framing: Free exploration prompt with explicit think-aloud instructions and recording disclosure.
- Participant reference: Intro includes a name text field (`introduction.participantName`) so recordings can be referenced later.

## What this study captures

This study captures:
- Screen recording
- Think-aloud microphone audio
- Intro response (participant name)

This study does not capture interaction-level state logs or click-by-click provenance. Because the linked tool is external and not instrumented in this repo, no Trrack-style interaction logging is available.

## Where things live

- Global registration: `public/global.json`
- Study config: `public/mgc-dashboard-projects-think-aloud/config.json`
- Intro copy: `public/mgc-dashboard-projects-think-aloud/assets/introduction.md`
- Debrief copy: `public/mgc-dashboard-projects-think-aloud/assets/debrief.md`

## Running this study

1. Run `yarn serve`.
2. In the study selector, choose `mgc-dashboard-projects-think-aloud`.

## Where to go next

- Change intro/debrief language in the assets files.
- Add post-task questionnaire(s) by adding libraries to `importedLibraries` and appending components after the website stimulus.
- If iframe rendering fails at runtime, switch to a new-tab workflow and instruct participants to share **Entire Screen**.

## Known limitations / TODOs

- No fine-grained interaction telemetry is available by design for this external-link study.
- If embedding behavior changes on the host site, you may need to move to the new-tab fallback approach.
