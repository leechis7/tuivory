# Tuivory 0.10.2 release

[한국어 (default)](release-0.10.2.md) · **English**

**Do not use 0.10.1.** See [withdrawal/upgrade instructions](withdrawn-versions.en.md). Version 0.10.2 fixes Go root-import compilation on Windows. Generation preserves backend build constraints, filename OS/architecture conditions and complementary implementations through terminal and root facade stages. Public names and existing Unix behavior remain; NewStdIoTty is absent on Windows as in the backend.

## Includes all 0.10.1 improvements

**0.10.2 is the cumulative replacement for 0.10.1.** Withdrawal applies to the old version; none of the following features have been removed or reverted.

- **Go/Rust half-row popup shadows:** auto/solid use one cell right and half a row down, preserving borders and the off default.
- **Theme contrast:** shade the actual backdrop in dark/light themes, with near-black/8/16/256-color fallbacks and ASCII dots.
- **Safe drawing and input:** retain CJK/emoji edge repair, original partial-cell background colors and card-only hit testing.
- **Bilingual examples, guides and references:** include clean actual-widget examples and seam-free SVG cells. Dim remains a whole-cell compatibility mode.

[Shadow APIs/examples](popup-shadows.en.md) · [Cumulative changelog](../CHANGELOG.en.md). Version 0.10.2 adds the Windows facade fix and 0.10.1 withdrawal to these changes. “Rust implementation is unchanged” below means **no additional implementation change relative to 0.10.1**; its shadow improvements remain included.

## Installation and validation

```sh
go get github.com/leechis7/tuivory/go@v0.10.2
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.2", features = ["ratatui"] }
```

Root-only consumers cover Windows AMD64/ARM64 and Linux/macOS AMD64/ARM64. New native Windows/macOS/Linux generation/simulation CI distinguishes compile/simulation checks from physical terminal/font validation. [API availability](ui-facade.en.md) · [Pre-release local history](evidence/tvr26-windows-facade-results.json).

Go 1.24+, Rust core 1.85+, UI 1.88+. Rust implementation is unchanged; its product version is aligned. Linux ARM64/x86_64 example archives each contain one static executable per language, built on native hosts. Windows/macOS SDK checks do not add new distributed executable targets.

RELEASE-MANIFEST.json/SHA256SUMS in the [release assets](https://github.com/leechis7/tuivory/releases/tag/go/v0.10.2) record source identity, main/platform CI, public tags, withdrawal metadata and downloaded execution. No CentOS or real LazyOra business-integration checks.
