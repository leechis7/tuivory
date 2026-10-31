# Tuivory 0.8.0 release

[한국어 (default)](release-0.8.0.md) · **English**

Go apps compose their entire UI with **one Tuivory import**. Application/widget/screen/key/mouse/color/configuration APIs are available at the root.

```sh
go get github.com/leechis7/tuivory/go@v0.8.0
```

```go
import "github.com/leechis7/tuivory/go"
```

Existing semantic constructors remain unchanged. Conflicting compatibility widgets use names such as `WidgetForm`/`NewWidgetForm` and `WidgetButton`/`NewWidgetButton`. Existing /ui and /terminal paths remain valid; tview/tcell remain internal dependencies. [Single-import example, name mappings and configuration](ui-facade.en.md) · [Go API reference](api/go.en.md).

This TVR-26 follow-up converts public Go examples to the root import and updates generated mappings, external consumer checks and bilingual documentation. Type/callback identity and presentation remain unchanged. Rust functionality is unchanged; its version follows the product version.

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.8.0", features = ["terminal"] }
```

Requires Go 1.24+, Rust core 1.85+, UI/terminal 1.88+. Rendering-only Rust apps can use the `ratatui` feature. Not published to crates.io.

The [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.8.0) provides Go/Rust Linux ARM64/x86_64 static playground/catalog/menu/controls executables, the Rust crate, SHA256SUMS and RELEASE-MANIFEST.json. The final manifest records source identity, static ELF inspection, public-tag installation, downloaded execution and GitHub CI results. The [implementation-time local snapshot](../evidence/go-single-import-results.json) remains separate historical evidence.

Actual LazyOra migration, DB integration and future language implementations are outside this release. CentOS is not validated. TVR-7 stays open.
