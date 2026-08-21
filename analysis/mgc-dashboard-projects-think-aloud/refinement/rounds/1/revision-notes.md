# Revision notes — round 1

**Reviewer**: Lane (study designer / reviewer) · **Date**: 2026-08-05 · **Tool**: gemini-flash-latest

## Round summary

3 note(s). By category: flow-sequencing=1, other=1, stimulus-design=1

## Scope and grounding

Grounded in: config `public/mgc-dashboard-projects-think-aloud/config.json`

## Prioritized notes

| id | title | category | severity | confidence | already documented | owner |
|---|---|---|---|---|---|---|
| RN-002 | [app-product] Chart/table access and source attribution move around between views | flow-sequencing | medium | high | False | engineering |
| RN-001 | [app-product] Search looks global but behaves like a view-local filter | stimulus-design | medium | medium | False | engineering |
| RN-003 | [app-product] Map popups invite a report workflow that is not currently exposed | other | low | low | False | discussion |

## Note details

### RN-002: [app-product] Chart/table access and source attribution move around between views

**Category**: flow-sequencing · **Severity**: medium · **Confidence**: high · **Already documented**: False

**Observed**: The researcher clicks the bottom navigation controls ('View Charts', 'View Tables') in one view, then later inspects the Master Map and notes that the chart/table path is not available there in the same way.
**Lane said**: I wonder if source needs to go like down here where you have View Charts, View Tables. Don't think you can get to the charts from here, I don't know if that is potentially something that we should address or not.
**Interpreted**: The control cluster for switching between charts/tables and the source attribution placement are inconsistent across views, so the path to related views is hard to predict.
**Should match**: Consistent access to charts/tables and source attribution from every map view, especially Master Map.

**Evidence**: mgc_dashboard_projects @ 03:50–03:58; mgc_dashboard_projects @ 05:49–05:59

**Code**: not performed

**Next action**: Align the Master Map and topic views so the chart/table switch and source attribution either appear consistently or are explicitly disabled with rationale.
**Open questions**:
- Should Master Map expose the same chart/table navigation as the topic views?
- Should the source attribution sit with the bottom control cluster or elsewhere?

### RN-001: [app-product] Search looks global but behaves like a view-local filter

**Category**: stimulus-design · **Severity**: medium · **Confidence**: medium · **Already documented**: False

**Observed**: The researcher opens the search modal from different topic views and types 'port'.
**Lane said**: The search context seems to be restricted within the current view ('soft power'/'investments') rather than global, despite UI presentation suggesting cross-category search.
**Interpreted**: The search affordance implies cross-dataset search, but the behavior reads as local to the active view.
**Should match**: A search affordance that clearly communicates whether it searches the current view or all datasets, and behaves accordingly.

**Evidence**: mgc_dashboard_projects @ 02:30–03:05

**Code**: not performed

**Next action**: Decide whether search is intentionally scoped to the active view; if not, make the scope visible in the modal copy and filter behavior.
**Open questions**:
- Is the search intentionally local to the current view or meant to span all topic categories?

### RN-003: [app-product] Map popups invite a report workflow that is not currently exposed

**Category**: other · **Severity**: low · **Confidence**: low · **Already documented**: False

**Observed**: The researcher clicks a map popup marker for 'Port Jinja' in East Africa.
**Lane said**: Suggests linking map detail cards to external or internal AI tools to generate full reports on specific project locations.
**Interpreted**: This reads more like a feature idea than a design-fidelity defect: the reviewer wants a richer action from selected map points.
**Should match**: A path from map selection to a fuller project report, if that feature is intended for the product.

**Evidence**: mgc_dashboard_projects @ 04:48–05:13

**Code**: not performed

**Next action**: Decide whether AI/report generation from map markers is in scope; if not, keep this as a discussion item rather than a revision item.
**Open questions**:
- Is a report-generation action from map markers intended to be part of the product?

## Already-documented deviations re-raised

None.

## New fidelity concerns

None.

## Code correlation summary

Not performed — no repo supplied.

## Open questions / discussion agenda

- **RN-002** ([app-product] Chart/table access and source attribution move around between views): Should Master Map expose the same chart/table navigation as the topic views?; Should the source attribution sit with the bottom control cluster or elsewhere?
- **RN-001** ([app-product] Search looks global but behaves like a view-local filter): Is the search intentionally local to the current view or meant to span all topic categories?
- **RN-003** ([app-product] Map popups invite a report workflow that is not currently exposed): Is a report-generation action from map markers intended to be part of the product?

## Methodology

Model/tool: gemini-flash-latest · Run date: 2026-08-05
External processing:
- screenRecording/$screen-recording.components.screenRecordingPermission_1.webm -> Gemini Files API
- screenRecording/mgc_dashboard_projects_2.webm -> Gemini Files API
