# Tuivory 0.10.0 release

[한국어 (default)](release-0.10.0.md) · **English**

Wrap long confirmation buttons inside 40-column terminals while retaining default Cancel and focus. Go/Rust tabs and trees gain opt-in drag and drop: hosts approve requests before immutable reorder/reparent application.

```sh
go get github.com/leechis7/tuivory/go@v0.10.0
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.0", features = ["terminal", "syntax-sql"] }
```

Requires Go 1.24+, Rust core 1.85+, UI/examples 1.88+. Go uses one root import; Rust declares only the tuivory dependency. Rust is distributed through Git, not crates.io.

- [Responsive Go Modal](modals.en.md): focused-button visibility at small heights, callbacks/keyboard/mouse and readable themed borders.
- [Go/Rust drag and drop](drag-drop.en.md): tab order and tree before/after/last-child moves; retain stable IDs/metadata/subtrees, reject cycles/disabled/locked/policy/stale requests, and support outside capture/cancel and keyboard alternatives. Preview scrolling/expansion stays separate from actual state.

Go `Modal` is now an SDK adapter embedding the backend Modal rather than a raw backend type alias. Existing SDK chaining such as `NewModal().SetText(...).AddButtons(...).SetFocus(...)` remains supported. Pass `modal.Modal` to external code requiring the raw backend type; drawing that embedded object directly bypasses responsive handling. [Interoperability guide](modals.en.md).

```sh
./bin/go/tuivory-linux-arm64 --demo controls --modal --lang en --theme light --colors 8
./bin/go/tuivory-linux-arm64 --demo workspace --drag --lang en
./bin/rust/tuivory-linux-arm64 --demo workspace --drag --lang en --ascii
```

Each [release archive](https://github.com/leechis7/tuivory/releases/tag/go/v0.10.0) for Go/Rust Linux ARM64/x86_64 contains one static executable. ARM64 builds on the local ARM64 host; x86_64 builds on GitHub x86_64 without cross compilation. Paths use `bin/<language>/tuivory-linux-<architecture>`. No separate runtime or shared libraries are required. [All examples](examples.en.md) · [Static builds](static-build.en.md).

Implementation [local evidence](evidence/tvr7-18-results.json) remains a pre-publication snapshot: 216 Modal palette/language/size cases, shared Go/Rust movement/physical-output regressions, 58 bilingual PTYs, external packages, Rust core MSRV and static executables. Final RELEASE-MANIFEST.json/SHA256SUMS record main CI, four binaries' source/static ELF/checksums, public-tag installation and downloaded execution. No CentOS, physical-font/SSH or real application business integration checks. Existing tags/assets are preserved.
