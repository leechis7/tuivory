# Notices, progress and data states — TVR-12

[한국어 (default)](feedback.md) · **English**

Public Go types: `NoticeQueue`, `Progress`, `DataState` with corresponding views; Rust `feedback` models and Ratatui widgets provide the same behavior.

Notices carry IDs, text/detail, info/success/warning/error severity, priority, absolute expiry and actions. Duplicate IDs explicitly update; invalid severity/action IDs fail. Sort by severity/priority, report omitted items and preserve the highest-priority notice in a one-line viewport. Error/persistent/actionable notices never auto-expire or get evicted for capacity. Hosts handle full-queue errors.

Visible/expire operations accept consistent host-supplied monotonic units; zero expiry means no deadline. Models own no timers/threads. Dismiss/action operations are requests; hosts explicitly remove notices or run retries. Use nonblocking messages for routine feedback and compose important decisions with popup scopes as appropriate.

Progress accepts loading/ready/empty/error/success/cancelled states, amounts/messages and cancellation policy. Unknown totals use a host-frame spinner; known totals clamp to 0–100%. Cancel requests never change the operation. DataState presents loading/empty/error/ready without fetching data.

Demo keys: Enter retry request, t host-clock advance/expiry, c cancellation request, Delete explicit dismissal. A synthetic host applies outcomes. ASCII severity markers supplement colors. Tests cover persistence, capacity, disabled actions, request immutability, progress/cancel bounds, narrow cells and localized PTYs.

## Run and boundaries

```sh
make run-catalog-go ARGS="--mode feedback --lang ko"
make run-catalog-rust ARGS="--mode feedback --lang en"
```

Hosts own data, business actions, clocks and terminal lifecycle. Public models emit requests and render literal cell-clipped rows. These APIs are included in v0.2.0. Static linking, Unicode/ASCII and color-profile requirements remain.

![Notices, progress and data states](images/feedback-dark-en.svg)

[Light](images/feedback-light-en.svg) · [Blackwhite](images/feedback-blackwhite-en.svg)

Actual Rust TestBackend 120×36 reference, not a Go capture or physical/SSH terminal result. Generate six localized references with `tools/snapshot_catalog.py BINARY --mode feedback`.

[Backlog](components-backlog.en.md) · [Static distribution](static-build.en.md)

In 0.4.0, plain text follows the actual surface while explicit field/selection/edit backgrounds remain. See [surface/contrast design rules](../design/surfaces.en.md) and [fix evidence](../evidence/background-fix.en.md).

Do not automatically prefix ordinary disabled items with `[-]` or `-`. Keep checkbox, radio, and check-menu selection indicators. Disabled labels, values, buttons, and notice actions use the disabled role with muted foregrounds and no active background. Use gray at 16 colors or higher and `Dim` at 8 colors. Block pointer activation/focus and keyboard execution; clicking a disabled option must not move parent focus. [Twelve-palette comparison and limits](disabled-states.en.md).
