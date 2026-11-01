# Tuivory 0.9.2 release

[한국어 (default)](release-0.9.2.md) · **English**

Go table repainting now preserves Korean, CJK and emoji through WideSafeScreen, including Surface and shadow wrappers. Splitter and comparison-header separators have readable contrast across all twelve palettes. Disabled dropdowns use the common disabled style, and the 8-color disabled sample retains Dim. Rust examples now follow Go navigation, palette and localized guidance; Go first-paint card backgrounds are corrected. Public APIs remain compatible with 0.9.1.

```sh
go get github.com/leechis7/tuivory/go@v0.9.2
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.9.2", features = ["terminal", "syntax-sql"] }
```

Go keeps the single `github.com/leechis7/tuivory/go` import. Rust is distributed through Git, not crates.io. Requires Go 1.24+, Rust core 1.85+, UI/examples 1.88+.

Each [release archive](https://github.com/leechis7/tuivory/releases/tag/go/v0.9.2) for Go/Rust Linux ARM64/x86_64 contains **one** executable: `bin/<language>/tuivory-linux-<architecture>`. No separate demo binary, language runtime or shared library is required.

```sh
./bin/go/tuivory-linux-arm64 --list
./bin/go/tuivory-linux-arm64 --demo tree --lang ko
./bin/rust/tuivory-linux-arm64 --demo syntax --lang en
```

Select playground/tree/workspace/focus/catalog/menu/controls/syntax within the same executable. [Complete example guide](examples.en.md).

`make build` and `make build-rust` target only the running Linux server architecture. ARM64 builds locally; x86_64 builds on GitHub's x86_64 server. `bin/` contains executables only; temporary builds/checks and local release archives use ignored `.cache/`. Example guidance is consolidated into the docs, and validation records move to `docs/evidence/`. [Layout](architecture.en.md) · [Static builds](static-build.en.md).

RELEASE-MANIFEST.json and SHA256SUMS record the final source commit, static ELF checks, public-tag installation, downloaded execution and CI. Existing release assets are preserved. CentOS is not validated.

Validation: post-Show/Sync physical buffers, whole-grapheme styling and overwrite recovery, all twelve palettes, independent single-import Go consumer, Rust TestBackend, bilingual PTY examples, API generation and static ELF checks. Implementation evidence remains pre-release history: [TVR-7](evidence/tvr7-lazyora-rendering-results.json), [disabled states](evidence/go-disabled-followup-results.json), [example parity](evidence/example-parity-results.json). Final publication evidence is recorded in the release asset manifest.
