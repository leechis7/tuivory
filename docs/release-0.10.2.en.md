# Tuivory 0.10.2 release

[한국어 (default)](release-0.10.2.md) · **English**

**Do not use 0.10.1.** See [withdrawal/upgrade instructions](withdrawn-versions.en.md). Version 0.10.2 fixes Go root-import compilation on Windows. Generation preserves backend build constraints, filename OS/architecture conditions and complementary implementations through terminal and root facade stages. Public names and existing Unix behavior remain; NewStdIoTty is absent on Windows as in the backend.

```sh
go get github.com/leechis7/tuivory/go@v0.10.2
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.2", features = ["ratatui"] }
```

Root-only consumers cover Windows AMD64/ARM64 and Linux/macOS AMD64/ARM64. New native Windows/macOS/Linux generation/simulation CI distinguishes compile/simulation checks from physical terminal/font validation. [API availability](ui-facade.en.md) · [Pre-release local history](evidence/tvr26-windows-facade-results.json).

Go 1.24+, Rust core 1.85+, UI 1.88+. Rust implementation is unchanged; its product version is aligned. Linux ARM64/x86_64 example archives each contain one static executable per language, built on native hosts. Windows/macOS SDK checks do not add new distributed executable targets.

RELEASE-MANIFEST.json/SHA256SUMS in the [release assets](https://github.com/leechis7/tuivory/releases/tag/go/v0.10.2) record source identity, main/platform CI, public tags, withdrawal metadata and downloaded execution. No CentOS or real LazyOra business-integration checks.
