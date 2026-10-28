# Shared component expansion backlog

[한국어 (default)](components-backlog.md) · **English**

Registered under TVR-7 with user approval following the 2026-10-28 MUI review. Reuse existing Tree/tabs/panels/splits/status/breadcrumbs and distinguish Go styling/example-local behavior from shared public Go/Rust components.

| Order | Issue | Scope | Status |
| --- | --- | --- | --- |
| 1 | [TVR-8](https://leechis7.atlassian.net/browse/TVR-8) | Shared control states, focus and popup foundation | Local implementation/validation. [API](focus.en.md). Source publication approved; see issue comments for remote CI/merge evidence |
| 2 | [TVR-9](https://leechis7.atlassian.net/browse/TVR-9) | Inputs/buttons/checks/radios/selects/forms | Dev implementation/validation; CI and merge evidence in Jira |
| 3 | [TVR-10](https://leechis7.atlassian.net/browse/TVR-10) | Lists/menus/search selection | Dev implementation/validation; CI and merge evidence in Jira |
| 4 | [TVR-11](https://leechis7.atlassian.net/browse/TVR-11) | Tables/data grid | Dev implementation/validation; CI and merge evidence in Jira |
| 5 | [TVR-12](https://leechis7.atlassian.net/browse/TVR-12) | Notifications/progress/loading/empty/error views | Backlog |
| 6 | [TVR-13](https://leechis7.atlassian.net/browse/TVR-13) | Layout/density tokens, badges/chips/help and related components | Backlog |

Finish implementation, bilingual documentation/images and validation for each stage, report results and request explicit commit/publication approval for that stage. Earlier publication approval does not cover later stages. Do not start another feature branch before finishing the current stage's commit/publication; keep TVR-7 open.

Shared models provide state/event/presentation contracts. Hosts connect validation, search, DB/business actions, clocks, external I/O and terminal lifecycle. Verify static linking, Go/Rust parity, bilingual examples, Unicode/ASCII, color profiles and narrow layouts throughout. Reuse framework behavior and add shared adapters/composition where needed.

References: [MUI components](https://mui.com/material-ui/all-components/), [TextField](https://mui.com/material-ui/react-text-field/), [Dialog](https://mui.com/material-ui/react-dialog/), [MUI X Data Grid](https://mui.com/x/react-data-grid/), [theming](https://mui.com/material-ui/customization/theming/). Adapt web pixels/DOM/shadows/animation to terminal cells/focus/keyboard behavior. Evaluate command palettes as search+list+popup composition; defer image/custom-icon-font dependencies.

Approved stage publication/merges target `dev` only. After all work is complete, a separate user release instruction authorizes `main`, tags and Releases. Do not synchronize main/dev after each stage.

On 2026-10-28 the user explicitly authorized TVR-9 through TVR-13 implementation, commits, publication and individual dev merges in order without further approval prompts. Report each checkpoint; main/tags/Releases still require a separate instruction.
