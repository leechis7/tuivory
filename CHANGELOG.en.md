# Changelog

[한국어 (default)](CHANGELOG.md) · **English**

## 0.2.0 — 2026-10-28

- TVR-14: Go [wide-glyph overlay drawing](docs/overlay-drawing.en.md). Shared APIs repair both popup/card/shadow edges and stale continuations, with physical output regressions after Show.

- TVR-13: [Layout, density and supporting components](docs/layout.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-12: [Notices, progress and data states](docs/feedback.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-11: [Tables and data grid](docs/grid.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-10: [Lists, menus and search selection](docs/collections.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-9: [Inputs and forms](docs/forms.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-8 shared control-state/focus/popup foundation: public Go/Rust state composition, stable-ID navigation, nested scopes, dismissal/restoration and input routing; executable hosts, twelve localized references, shared contracts, PTY and external static-host checks. [API](docs/focus.en.md) · [ordered backlog](docs/components-backlog.en.md). Included in v0.2.0 tags.

- Apply static distribution and host-linking requirements to Go, Rust and future languages. Add Rust musl/bundled LLD, Go CGO-disabled ELF checks, explicit x86_64 builds and CentOS 7.4 kernel/external-host validation. Existing v0.1.0 tags/assets remain unchanged. [Support scope](docs/static-build.en.md)

## 0.1.0 — 2026-10-27

- Implemented remaining TVR-7 UI: independent active/focused tabs, overflow and edited/close requests, padded focus/ASCII panels, column/row splits with keys/dragging and compact restoration, breadcrumb omission/navigation, semantic status/shortcut priorities and packing. Added public Go/Rust APIs, external usage checks, bilingual integrated examples, eight reference SVGs, PTY input checks and synchronized guides; distributed in v0.1.0.


- TVR-7 support audit and shared Tree: Go/tview and Rust/Ratatui stable IDs, expansion/selection/scroll, node metadata, keyboard/mouse and ASCII, shared navigation contract, external imports, bilingual examples and images. Tree changes are included in v0.1.0; tabs, panels, status, and breadcrumbs are included in the subsequent implementation below.

- Added the Rust core crate: candidate tokens, profiles, color/style values, strict JSON validation, embedded distribution data, and external project usage validation. Added an optional Ratatui 0.30.2 adapter, Crossterm 0.29 bilingual interactive example, Linux ARM64 build, language-matched reference images, and PTY checks. The core requires Rust 1.85+; the adapter/example require 1.88+. Distributed through Git tag `rust/v0.1.0`; there is no crates.io release.

- Separate playground build outputs under `bin/<language>/`. The default Go output is now `bin/go/tuivory-linux-arm64`; the default build still produces one Linux ARM64 binary.
- Added English project, Go usage, and contribution guides alongside the Korean default, with reciprocal language links.
- Added playground `--lang ko|en`: one binary supports default Korean and optional English, with English UI reference images in English documentation.
- These changes merged into `main`/`dev` through [PR #1](https://github.com/leechis7/tuivory/pull/1); they have no new version tag yet.
- Subsequent documentation work refreshes current usage and publication status, adds English counterparts and an index, and keeps source attribution in notices.

## 0.0.1 — 2026-10-24

- First Tuivory (TUI + ivory) release, providing a language-neutral repository and Go style package.
- Shared themes, color profiles, state rules, JSON, CSV, and schema live in `design/`.
- Go module `github.com/leechis7/tuivory/go` exposes style APIs and tview application methods through one public package, `tuivory`.
- Includes dark/light/blackwhite × 8/16/256/truecolor, a database-free interactive playground, and state preservation checks.
- Python/JavaScript provide token consumers; Shell provides an ANSI output example. UI style packages for these languages are future work.
- Releases are recorded against this repository's tags and Releases. See [installation and usage](docs/installation.en.md) and [origin notices](NOTICE.en.md).
