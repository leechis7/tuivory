# Tuivory 0.3.0 release

[한국어 (default)](release-0.3.0.md) · **English**

Product `VERSION` and Rust manifest/lock versions are **0.3.0**. The [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.3.0) provides static Linux ARM64/x86_64 executables, a standalone Rust crate and checksums. Go `go/v0.3.0` and Rust `rust/v0.3.0` point to the same final commit. The TVR-7 epic remains open.

## Changes

- [Shared menus](menus.en.md): Go/Rust menu bars, hierarchical entry/back navigation, parent selection and original caller restoration, disabled items/separators/shortcuts/mnemonics, keyboard/mouse navigation, overflow and safe popup drawing.
- [Grid options](grid.en.md): simple/data presets on the same Grid, row numbers/padding/separators/alignment/status, range selection/original-value copying/stale-response protection and external host integration.
- [Component/application boundary](component-boundary.en.md): Tuivory is a TUI component library. Hosts own screen composition, global shortcuts, commands, DB/SQL and real clipboard/file I/O.
- Clarify terminology, bilingual guides/examples and normal runtime-package exceptions for Python/TypeScript/JavaScript. UI packages for those languages are not yet provided.
- Stop CentOS validation per user instruction and remove the CI VM stage. Preserve static distribution and ELF checks. Historical CentOS results do not establish compatibility for this release.

Existing 0.2.0 components remain available. [English menu reference](images/menu-dark-en.svg) · [Korean reference](images/menu-dark.svg).

## Installation

```sh
go get github.com/leechis7/tuivory/go@v0.3.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.3.0", features = ["ratatui"] }
```

Requires Go 1.24+, Rust core 1.85+, or Rust 1.88+ for Ratatui/executable examples. Rust uses Git distribution with `publish = false`; it is not published to crates.io. New menus and TVR-17 options are absent from previous 0.2.0 tags.

## Assets

| File | Contents |
| --- | --- |
| `tuivory-go-v0.3.0-linux-arm64.tar.gz` | Static Go Linux ARM64 playground/catalog/menu |
| `tuivory-go-v0.3.0-linux-x86_64.tar.gz` | Static Go Linux x86_64 playground/catalog/menu |
| `tuivory-rust-v0.3.0-linux-arm64.tar.gz` | Rust Linux ARM64 musl playground/catalog/menu |
| `tuivory-rust-v0.3.0-linux-x86_64.tar.gz` | Rust Linux x86_64 musl playground/catalog/menu |
| `tuivory-0.3.0.crate` | Standalone Rust sources, public APIs, examples and embedded data |
| `SHA256SUMS` | Archive/crate/manifest checksums |
| `RELEASE-MANIFEST.json` | Final source commit, asset/binary hashes and validation scope |

Executables are located at `bin/<language>/tuivory[-catalog|-menu]-linux-<architecture>` inside each archive. Select `--lang ko` or `--lang en`; use catalog `--mode grid --grid-preset data` for the new grid. Open menus with F10 and exit with Ctrl+Q. Default `make build` still produces one Go Linux ARM64 executable. Static executables require no dynamic loader, shared libraries or separately installed language runtime.

## Validation and publication evidence

Implementation and dev integration are recorded in [PR #16](https://github.com/leechis7/tuivory/pull/16), [menu evidence](../evidence/menu.en.md) and [grid evidence](grid-validation.en.md). Consult the Release `RELEASE-MANIFEST.json` and [TVR-7](https://leechis7.atlassian.net/browse/TVR-7) comments for release/main CI, final-commit asset builds/static ELF inspection, bilingual ARM64 PTYs, external Go/Rust installation/API/rendering from actual public tags, and uploaded-asset download/checksum results. Unexecuted checks are not considered passed.

CentOS, customer SSH, physical terminals/fonts, actual LazyOra/LazyBeaver and DB editing integration are outside this release validation. Existing tags/assets are preserved.
