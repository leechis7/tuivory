# Tuivory 0.9.0 release

[한국어 (default)](release-0.9.0.md) · **English**

Go and Rust now provide optional Oracle SQL/PLSQL analysis and common highlighting roles. Go keeps one root package import; Rust enables `syntax-sql`. Applications can also attach their own analyzers.

```sh
go get github.com/leechis7/tuivory/go@v0.9.0
```

```go
import "github.com/leechis7/tuivory/go"
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.9.0", features = ["terminal", "syntax-sql"] }
```

UTF-8 byte selection/replacement, undo/redo, automatic analysis after editing and stale-result removal are supported. Disabled, selection, search and syntax styling share a consistent priority while preserving component backgrounds. [Analysis, migration and examples](syntax.en.md) · [Shared specification](../design/syntax.en.md) · [API reference](api/README.en.md).

Requires Go 1.24+, Rust core 1.85+, or Rust UI/terminal 1.88+. Rust default features exclude the SQL analyzer. No new native dependency is required. The crate is not published to crates.io.

The [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.9.0) provides **20** static Go/Rust Linux ARM64/x86_64 playground/catalog/menu/controls/syntax executables, a Rust crate, SHA256SUMS and RELEASE-MANIFEST.json. Run `bin/<language>/tuivory-syntax-linux-<architecture>` from the matching archive with `--lang ko` or `--lang en`, optionally `--ascii`.

The final manifest records source identity, static ELF inspection, public-tag installation, downloaded executable checks and GitHub CI. The [local implementation snapshot](evidence/syntax-results.json) predates publication. Long documents use full analysis, with no incremental-analysis latency guarantee.

SQL execution, safety policy, DB connections, actual LazyOra adoption and Go/Rust source analyzers are outside this release. CentOS validation is not performed. TVR-7 remains open.
