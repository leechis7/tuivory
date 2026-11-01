# Tuivory 0.9.1 release

[한국어 (default)](release-0.9.1.md) · **English**

Examples now share one executable per language, and the repository layout is simpler. Public SDK APIs remain compatible with 0.9.0.

```sh
go get github.com/leechis7/tuivory/go@v0.9.1
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.9.1", features = ["terminal", "syntax-sql"] }
```

Go keeps the single `github.com/leechis7/tuivory/go` import. Rust is distributed through Git, not crates.io. Requires Go 1.24+, Rust core 1.85+, UI/examples 1.88+.

Each [release archive](https://github.com/leechis7/tuivory/releases/tag/go/v0.9.1) for Go/Rust Linux ARM64/x86_64 contains **one** executable: `bin/<language>/tuivory-linux-<architecture>`. No separate demo binary, language runtime or shared library is required.

```sh
./bin/go/tuivory-linux-arm64 --list
./bin/go/tuivory-linux-arm64 --demo tree --lang ko
./bin/rust/tuivory-linux-arm64 --demo syntax --lang en
```

Select playground/tree/workspace/focus/catalog/menu/controls/syntax within the same executable. [Complete example guide](examples.en.md).

`make build` and `make build-rust` target only the running Linux server architecture. ARM64 builds locally; x86_64 builds on GitHub's x86_64 server. `bin/` contains executables only; temporary builds/checks and local release archives use ignored `.cache/`. Example guidance is consolidated into the docs, and validation records move to `docs/evidence/`. [Layout](architecture.en.md) · [Static builds](static-build.en.md).

The final RELEASE-MANIFEST.json and SHA256SUMS record source identity, static ELF checks for all four executables, public-tag installation, downloaded execution and GitHub CI. Implementation-time [example checks](evidence/showcase-results.json) and [layout checks](evidence/layout-results.json) remain historical pre-release snapshots. Existing 0.9.0 tags/assets are preserved. CentOS validation is not performed.
