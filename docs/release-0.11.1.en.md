# Tuivory 0.11.1 release

[한국어 (기본)](release-0.11.1.md) · **English**

This patch replaces the grid cell editor's literal `|` with a real terminal cursor. It includes [all 0.11.0 grid features](release-0.11.0.en.md) and earlier fixes. **Do not use 0.10.1.** [Withdrawal notice](withdrawn-versions.en.md).

## Changes and integration

- Go `NewGridView` manages actual cursor position and visibility. Create `NewCursorScreen` and connect it to Application to filter backend cursor-shape/blink overrides and preserve terminal user settings. Existing `NewScreen` and automatically created Application screens retain their existing behavior.
- Rust `GridWidget::render_frame(frame, area)` draws and registers the actual cursor. Existing buffer-only `Widget` rendering remains supported and does not register a terminal cursor.
- CJK, emoji, combining characters, long values, mouse positioning, dirty markers and padding share one cell viewport. A literal `|` in input remains ordinary data.
- Blur, NULL, pending approval, clipping and editor closure hide the cursor; rejection restores it for retry. Hosts own global focus and layer order.

[Go/Rust integration and APIs](grid-workspace.en.md) · [Design guide](design-guide.en.md) · [Examples](examples.en.md).

## Installation and examples

```sh
go get github.com/leechis7/tuivory/go@v0.11.1
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.11.1", features = ["ratatui"] }
```

Go 1.24+, Rust core 1.85+, UI/examples 1.88+. Rust uses Git/.crate distribution, not crates.io. Linux ARM64/x86_64 static examples are built on their respective native hosts, one executable per language. Preview editing with `--demo catalog --mode grid --grid-sample --grid-edit-preview`.

## Validation and scope

Passed local Go race/vet, Rust core/all-feature tests/doctests/fmt/clippy, external module/crate consumers, six Go OS/architecture compilations, 11 shared cursor cases, 24 physical-buffer cursor combinations per language, 96 PTY cases checking actual cursor/visibility commands, and 62 integrated example cases. [Pre-publication evidence](evidence/tvr7-grid-cursor-results.json) preserves its original uncommitted/unpublished status.

Physical SecureCRT and Windows/macOS console blinking were not tested locally. Checks cover cursor coordinates/visibility and absence of forced shape/blink commands. Existing form/find input presentation is outside this fix. SVG references cannot show actual blinking or cursor metadata. CentOS validation is not performed.

Final source, remote CI, public-tag installation, downloaded execution and checksums are recorded in RELEASE-MANIFEST.json/SHA256SUMS on the [release](https://github.com/leechis7/tuivory/releases/tag/go/v0.11.1).
