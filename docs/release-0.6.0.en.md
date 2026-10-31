# Tuivory 0.6.0 release

[Korean (default)](release-0.6.0.md) · **English**

Adds shared Go/Rust surface, input, editing and layout APIs. See the [usage/API mappings and runnable previews](controls.en.md) and [language-neutral specification](../design/controls.en.md).

- **TVR-22:** Borderless opaque Surface, `PanelView.SetBorder(false)` correction, wide-glyph boundary protection and shadow composition.
- **TVR-23:** Secret masking and explicit raw getters, standalone Input/Button/Check/Select, selection/paste/copy requests, disabled/Busy handling.
- **TVR-24:** Multiline Editor/Buffer and TextView, grapheme/UTF-8 positions, selection, undo/redo, read-only, line numbers, scrolling, host syntax spans and explicit markup.
- **TVR-25:** Row/Column/Grid/Layer/Drawer, size constraints, virtual scrolling, clipping, input forwarding, modal isolation and focus restoration.
- **TVR-21:** Documentation navigation and generated Go/Rust API declarations. Also fixes duplicate focused Rust panel titles.

```sh
go get github.com/leechis7/tuivory/go@v0.6.0
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.6.0", features = ["ratatui"] }
```

Requires Go 1.24+, Rust core 1.85+, UI/examples 1.88+. Assets include static Go/Rust Linux ARM64/x86_64 playground/catalog/menu/**controls** executables, a Rust crate, SHA256SUMS and RELEASE-MANIFEST.json. Not published to crates.io. Consult the [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.6.0) manifest for actual build, tag and CI results; the [implementation-time local record](../evidence/controls-results.json) is separate from release validation.

Run `make run-controls-go` / `make run-controls-rust`, adding `ARGS="--lang en"` for English. The complete TVR-26 backend facade is excluded; current renderer types remain visible in public APIs. Python, JS/TS and C/C++ implementations are excluded. Text Layout traverses the complete document and includes a 10,000-line regression. No CentOS validation; TVR-7 remains open.
