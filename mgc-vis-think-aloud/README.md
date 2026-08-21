# MGC Visualization — Stakeholder Think-Aloud Study

## Description

A screen-recording and think-aloud study for stakeholder review of the MGC visualization tool at `https://mgc-vis.shresthalucky.com.np/`. Participants explore the live tool while narrating their thoughts, and audio + screen is recorded for the study team to review.

## Source

- **URL**: https://mgc-vis.shresthalucky.com.np/
- **Date added**: 2026-08-21
- **Mode**: Live-link, iframe wrap (see Known Limitations below)

## Decisions Made

### Goal (Phase B)
Stakeholder reaction session — not a controlled experiment. Goal is to capture first-impressions, confusion points, and open reactions to the tool via think-aloud audio and screen recording. No fine-grained interaction logs exist; all behavioral signal is in the recordings.

### Embedding approach (Phase A)
The site is behind **HTTP Basic Authentication** (nginx `www-authenticate: Basic realm="Restricted"`). No `X-Frame-Options` or `Content-Security-Policy` headers blocking iframes were detected at study creation time. The study is scaffolded as an iframe (`type: website`) pointing at the base URL.

**⚠ Known issue**: Modern browsers (Chrome 85+, Firefox, Safari) suppress HTTP Basic Auth credential dialogs inside cross-origin iframes. If the frame renders blank, switch to the new-tab fallback (see Known Limitations / TODOs below).

### Intro framing (Phase C)
Free exploration with think-aloud. No directed tasks — stakeholders are asked to explore naturally and narrate reactions. Credential reminder is included in the introduction and the iframe instruction text.

### Questionnaire (Phase D)
None — kept simple per the study designer's intent. The recordings themselves are the primary data artifact.

## What This Study Captures

- **Screen recording** of whatever is visible in the ReVISit browser tab during the exploration step
- **Think-aloud audio** throughout the exploration
- **Participant name** (entered at introduction) so the study team can match recordings to stakeholders

**What this study does NOT capture:** fine-grained interaction events, click logs, or application state — there is no instrumentation code in the external tool.

## ⚠ Before Running With Real Participants

### HTTP Basic Auth + Iframe Warning

The `mgc_vis_tool` component in `config.json` embeds the tool via iframe:

```json
"path": "https://mgc-vis.shresthalucky.com.np/"
```

Modern browsers block the HTTP Basic Auth dialog inside iframes. Test this locally first (`yarn serve`, open `mgc-vis-think-aloud`) and check whether the frame renders or shows blank.

**If the iframe is blank, switch to the new-tab fallback:**
1. Change the `mgc_vis_tool` component's `instruction` text to tell participants to open the link in a new tab.
2. Update `assets/introduction.md` to add a step: "When the browser asks what to share, choose **Entire Screen** — not 'This Tab' — so your activity in the other tab is captured."

### Credentials

Login credentials for the tool are sent to participants separately (by email). No credentials are embedded in `config.json`.

## Where Things Live

| File | Purpose |
|------|---------|
| `public/mgc-vis-think-aloud/config.json` | Study configuration |
| `public/mgc-vis-think-aloud/assets/introduction.md` | Intro page copy (includes credential reminder) |
| `public/mgc-vis-think-aloud/assets/debrief.md` | Debrief page copy |
| `public/mgc-global.json` | Global registry (study is listed here) |

## Running This Study

```sh
yarn serve
```

Then open the study at the URL shown in the terminal and select **mgc-vis-think-aloud** from the study list.

## Where to Go Next

- **Add a post-exploration questionnaire**: add a library to `importedLibraries` (e.g. `"sus"`, `"umux-lite"`) and add its component/sequence reference after `mgc_vis_tool` in `sequence.components`.
- **Add directed tasks**: split the single `website` component into multiple sequential components, each with its own `instruction`.
- **Switch to new-tab fallback**: see the "If the iframe is blank" instructions above.
- **Deploy for real participants**: see the `revisit-deploy` skill.

## Known Limitations / TODOs

- [ ] **Test the iframe before sending to stakeholders** — HTTP Basic Auth in iframes is blocked in modern browsers; confirm the frame renders with a credential prompt or login form.
- [ ] No interaction-level data is captured — by design, since the external tool has no instrumentation.
- [ ] Debrief copy is minimal — update `assets/debrief.md` if you want to add next-steps or a contact email.
