# Tuivory 0.5.0 release

[Korean (default)](release-0.5.0.md) · **English**

Adds shared Go/Rust popup shadows and API deprecation guidance. Consult the GitHub Release manifest for publication and validation results.

- [Popup shadows](popup-shadows.en.md): off by default, Auto/Solid/Dim, two cells right and one row down. Auto uses softer True Color/256-color shading. Shadows exclude input targets and protect wide-glyph boundaries.
- [API lifecycle](api-lifecycle.en.md): deprecate six Go and four Rust duplicate APIs with replacements. Preserve existing behavior and provide Rust menu constructors.
- Updated bilingual examples, twelve-palette images and design/usage guides. Actual Dim brightness depends on the terminal.

```sh
go get github.com/leechis7/tuivory/go@v0.5.0
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.5.0", features = ["ratatui"] }
```

Requires Go 1.24+, Rust core 1.85+, UI/examples 1.88+. Assets include static Go/Rust Linux ARM64/x86_64 playground/catalog/menu executables, a Rust crate, SHA256SUMS and RELEASE-MANIFEST.json. Use `--shadow auto` or F6 in the menu example. No CentOS checks; TVR-7 remains open.
