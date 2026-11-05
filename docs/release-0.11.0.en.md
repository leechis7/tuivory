# Tuivory 0.11.0 release

[한국어 (default)](release-0.11.0.md) · **English**

A feature release expanding shared Go/Rust grid editing and data work. Includes all 0.10.2 Windows facade fixes and half-row popup shadows, contrast and wide-character protection. **Do not use 0.10.1**; its withdrawal remains in force. [Upgrade guidance](withdrawn-versions.en.md).

## Grid improvements

- Host-approved inline editing: Enter/double-click/optional typing, NULL, cursor/mouse/clipping, pending approval, rejection/retry/cancellation and stale-response guards.
- Independent dirty-cell and row markers: retain cell `*` under selection/error/disabled states and configure aggregate gutter markers separately.
- Left/right column pinning, visibility and order, header dragging, keyboard alternatives and narrow-screen clipping.
- Tab/Shift+Tab navigation to eligible cells only after successful submission approval.
- Quoted TSV range-paste requests with whole-batch preflight, explicit NULL mapping, stable IDs and approval-time eligibility checks.
- Loaded-data find, matching-cell styles, next/previous navigation and host global-search requests.
- View state for columns/selection/sort/location (Go JSON/Rust serde) and an optional raw-cell details viewer.

[APIs, options, bindings and screenshots](grid-workspace.en.md) · [Grid basics](grid.en.md) · [Changelog](../CHANGELOG.en.md).

## Compatibility and host responsibilities

Inline editing UI defaults to off, retaining `activate → edit`. Details remain requests unless `SetDetailsEnabled` enables the built-in viewer. **Row `State.Edited` now controls the row marker only.** Supply dirty-cell colors through `GridCellInfo.State.Edited`; hosts relying on inherited row-wide colors must adjust their metadata.

Go compatibility Application paste requires `EnablePaste(true)` and `PasteSafeScreen` to preserve LF/CRLF, without remapping normal Ctrl+J. Hosts retain DB validation/SQL/transactions, clipboard/storage and global bindings. No mandatory native dependencies were added.

## Install, examples and validation

```sh
go get github.com/leechis7/tuivory/go@v0.11.0
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.11.0", features = ["ratatui"] }
```

Go 1.24+, Rust core 1.85+, UI/examples 1.88+. Rust uses Git/.crate distribution, not crates.io. Linux ARM64/x86_64 examples each contain one static executable per language, built on native hosts. Run `--demo catalog --mode grid --grid-sample --grid-preset data --lang en`.

Pre-release local checks passed Go race/vet, Rust all-feature tests/doctests/fmt/clippy, standalone module/crate external consumers, 14 shared TSV cases, 1,536 physical-output state combinations per language, 96 bilingual/theme/profile/glyph-mode grid PTYs and 62 unified-demo runs. Bilingual APIs/design/examples and 28 references were updated. [Pre-release evidence](evidence/tvr7-grid-workspace-results.json) retains its original unpublished status.

Final source identity, remote CI, public-tag installation, downloaded execution and checksums are recorded in RELEASE-MANIFEST.json/SHA256SUMS on the [release](https://github.com/leechis7/tuivory/releases/tag/go/v0.11.0). No CentOS or real LazyOra DB integration checks.
