# Roadmap

[한국어 (default)](roadmap.md) · **English**

## Product goal and boundary

Tuivory is a **TUI component library** imported by hosts. Go/tview and Rust/Ratatui provide shared controls/styles/internal interaction and configurable layout tools. Hosts choose screen composition, global focus, commands/keys, content/data and business actions. Host UI-composition code alone is not a reason to require migration into the library. [Boundary](component-boundary.en.md).

The root is language-neutral: shared specifications/tokens live in design/, implementations/packages in language directories. Examples are usage hosts, not mandatory screen templates. The user decides product major versions and releases.

## Current scope

- **Published v0.2.0**: Go `go/v0.2.0`, Rust `rust/v0.2.0`. Shared state/focus, forms, flat lists/search, trees, tabs, panels/splits, paths/status, basic Grid, feedback/progress, layout/Help APIs and bilingual examples. [Support audit](component-audit.en.md) · [Release](release-0.2.0.en.md).
- **TVR-17 local commit `e34b824`**: options/presets, ranges, column configuration, status and stale-response protection on the same Grid. Not published to GitHub/version tags. [Grid](grid.en.md).
- **TVR-7 boundary follow-up**: documentation/audit and examples demonstrating host-selected layout/focus order/quit keys. Included in this local commit; unpublished on GitHub work. [Examples and boundary](component-boundary.en.md).
- **Python/JavaScript/Shell**: token-reading/reference-output examples today, not complete UI packages.

## Next steps

1. Support real host integration using the responsibility/support matrix. Distinguish the original Go-derived styles from the shared candidate palette.
2. After approved TVR-17 publication/release, validate actual LazyOra integration. Record implementation, local checks, publication and actual integration separately.
3. Nested menus are a confirmed gap and a candidate for a separate TVR issue after requirements are confirmed. Do not duplicate existing tab overflow or shortcut-help rendering.
4. Expand [TVR-15 Python](https://leechis7.atlassian.net/browse/TVR-15) and [TVR-16 TypeScript/JavaScript](https://leechis7.atlassian.net/browse/TVR-16) as normal runtime-based packages. Per the user's exception, static linking, standalone executables and CentOS validation are not mandatory.
5. Collect actual LazyOra/LazyBeaver and customer-terminal evidence for Go/Rust. Keep SQL, sessions, persistence and business workflows out of the common core.

Keep shared UI epic TVR-7 and language foundation epics TVR-5/6 open. Commit/publication requires explicit approval for the change; staged integration targets dev, while main/tags/Release require a separate release instruction. Do not conflate local tests with remote CI, physical-terminal/SSH or application-integration evidence.
