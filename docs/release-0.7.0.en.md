# Tuivory 0.7.0 release

[한국어 (default)](release-0.7.0.md) · **English**

TVR-26 adds SDK compatibility paths and shared input APIs so Go/Rust apps can compose their UI using only Tuivory imports. [Usage and migration](ui-facade.en.md) · [Language-neutral specification](../design/ui-facade.en.md) · [API reference](api/README.en.md).

- Go `go/ui`, `go/terminal`: pinned tview/tcell types, functions, constants and configuration setters preserve existing type/callback identity.
- Rust `ui`, `ui::components`, `ui::terminal`: rendering/events through one Cargo dependency. The `terminal` feature adds `Session` cleanup on normal exit, initialization failure and panic unwind.
- Shared `InputEvent`, editing-action normalization and UTF-8 byte-to-grapheme syntax spans. Invalid boundaries return errors while preserving previous highlighting.
- Public Go/Rust examples use SDK paths without direct backend imports. Visual output and themes remain identical to 0.6.0.

```sh
go get github.com/leechis7/tuivory/go@v0.7.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.7.0", features = ["terminal"] }
```

Requires Go 1.24+, Rust core 1.85+, UI/terminal 1.88+. Rendering-only Rust apps can use the `ratatui` feature. Not published to crates.io.

The [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.7.0) provides Go/Rust Linux ARM64/x86_64 static playground/catalog/menu/controls executables, the Rust crate, SHA256SUMS and RELEASE-MANIFEST.json. The manifest records source identity, static ELF inspection, public-tag installation, downloaded execution and GitHub CI results. The [implementation-time local snapshot](../evidence/ui-facade-results.json) remains separate historical evidence.

Run `make run-controls-go` / `make run-controls-rust`; add `ARGS="--lang en"` for English. Actual LazyOra migration and DB integration are outside this release. Compatibility aliases retain pinned backend identity; backend replacement and ABI compatibility are not guaranteed. Python/JS/TS/C/C++ remain design targets. CentOS is not validated. TVR-7 stays open.
