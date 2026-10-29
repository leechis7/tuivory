# Language-neutral repository architecture

[한국어 (default)](architecture.md) · **English**

Tuivory provides reusable TUI components and styles across languages. Shared design and validation specifications are independent of each language implementation and package. Go source, go.mod, and go.sum stay out of the repository root.

```text
tuivory/
├── design/       Shared specifications, JSON tokens, schemas, CSV candidates
├── docs/         Shared documentation and language usage guides
├── go/           Go module, public API, internal implementation, examples
├── rust/         Rust core, Ratatui adapter, independent Cargo package, examples
├── python/       Python token reading example
├── javascript/   Node.js token reading example
├── shell/        POSIX ANSI output example
├── examples/     Example index and shared static layouts
├── bin/          Git-ignored playground executables in bin/go/ and bin/rust/
├── tools/        Data generation, checks, isolated module validation
└── evidence/     Validation records
```

Go and Rust provide shared component models, tokens/styles and tview/Ratatui renderers. Rust core requires 1.85+, while the Ratatui adapter/interactive examples require 1.88+. Models calculate internal state, selection, scrolling and requests. Hosts connect terminals, event loops, screen composition, global focus and business actions. [Boundary](component-boundary.en.md). Other languages currently provide token-reading/reference examples, with missing UI-package scope stated in their READMEs; they are not required to call Go.

## Shared data and distribution assets

Shared candidate data is `design/tokens/candidate.json`, sourced from `design/themes/lazyora-candidate.csv`. Python and JavaScript read the shared JSON.

Go embed cannot include files outside the module. The exporter therefore writes identical JSON to `go/internal/tokens/candidate.json`. Rust also embeds the same JSON at `rust/src/data/candidate.json` with `include_str!`; Cargo.toml and Rust source stay in rust/. Both copies are generated distribution assets, not additional sources; do not edit it manually. Checks compare it byte for byte. Downloading only the Go module requires neither repository-root data nor a generation step.

```sh
python3 tools/export_tokens.py
python3 tools/export_tokens.py --check
python3 tools/check_go_module.py
python3 tools/check_rust_module.py
```

The isolated module check copies only `go/` to a temporary directory, tests it, and verifies an external project using the public API and embedded tokens. It does not copy `design/`.

## Public Go API

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

The submodule path is `github.com/leechis7/tuivory/go`, package `tuivory`. Public component APIs live in the `go/` package sources; extracted styles/assets and other private implementation live in `go/internal/`. The host owns the screen, events, terminal capability detection, and database state.

The first Go release is `v0.0.1`, tagged `go/v0.0.1`. [Go guide](go-package.en.md) · [Installation and usage](installation.en.md)

The Rust check copies only rust/, verifies a Cargo package, and runs an external path-dependent project without shared source data or a Go checkout. See [Rust scope and API](../rust/README.en.md).

## Further implementations

Maintain Go usability and validate LazyOra integration, then extend APIs, distribution, and UI templates for Python, JavaScript, and Shell through separate work items. [Shared specification](../design/README.en.md) · [Examples](../examples/README.en.md) · [Roadmap](roadmap.en.md)

The new shared component API is documented in the [Go/Rust Tree guide](tree.en.md). This candidate-palette implementation is separate from the existing Go-derived styles and stock `Styler.Tree`, and is included in v0.1.0. The [TVR-7 audit](component-audit.en.md) distinguishes state/controls, host responsibilities, and remaining phases.

## Shared workspace components

The [tabs, panels, splitters, status, and breadcrumbs guide](workspace.en.md) documents public Go/Rust APIs and shared control/color/state principles. Run database-free bilingual integrated examples with `make run-workspace-go ARGS="--lang en"` or `make run-workspace-rust ARGS="--lang en"` from the root. These APIs are included in `go/v0.1.0` and `rust/v0.1.0`; CI evidence and actual application integration are distinguished in [work tracking](https://leechis7.atlassian.net/browse/TVR-7).

## Distribution boundary

Go, Rust and future executables are distributed statically; libraries must not add mandatory native dependencies that prevent hosts from linking statically. Shared assets are embedded in each module. Distinguish interpreter-based references from standalone distributions. [Static distribution policy and checks](static-build.en.md)

Workspace examples allow host-selected split axis, focus order and quit keys. [Composition examples](component-boundary.en.md#same-components-different-host-policy).
