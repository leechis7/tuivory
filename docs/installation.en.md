# Tuivory installation and usage

[한국어 (default)](installation.md) · **English**

Tuivory (TUI + ivory) is an independent terminal UI style project. Current module, command, and token identifiers use Tuivory; work is tracked in Jira project TVR. Original attribution is preserved in [NOTICE](../NOTICE.en.md).

## Published version and current source

The current Go version is `v0.1.0`, tagged `go/v0.1.0`.

```sh
go get github.com/leechis7/tuivory/go@v0.1.0
```

The module lives in `go/`. There is no root Go module; the package name is `tuivory`.

```go
import "github.com/leechis7/tuivory/go"

styler, err := tuivory.New("dark", "256")
```

v0.1.0 includes bilingual docs, playground language selection, and shared UI. Check out the tag and run from the root, or use Linux ARM64 playgrounds from the [release](https://github.com/leechis7/tuivory/releases/tag/go/v0.1.0):

```sh
go -C go run ./cmd/tuivory --lang ko
go -C go run ./cmd/tuivory --lang en
make build
./bin/go/tuivory-linux-arm64 --lang en
```

Requires Go 1.24 or later. `make build` produces one Linux ARM64 binary supporting both languages. Source execution runs on the current host. The starter template runs with `go -C go run ./examples/starter` and has Korean example labels.

## Rust usage

Rust is distributed through Git tag `rust/v0.1.0`. With Rust 1.85+, use `tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.1.0" }` or a local path dependency on rust/. It is not published to crates.io. It provides candidate tokens, colors, and style values. The optional Ratatui 0.30.2 adapter and Crossterm 0.29 interactive example require Rust 1.88+. Run `make run-rust ARGS="--lang en"`; `make build-rust` creates `bin/rust/tuivory-linux-arm64`. See [Rust views and controls](rust-playground.en.md) for terminal and target linker requirements. See the [Rust guide](../rust/README.en.md).

## Shared data and validation

The draft token format is `tuivory.tokens.draft`, shared sources live in `design/tokens/`, and distribution copies are `go/internal/tokens/candidate.json` and `rust/src/data/candidate.json`. The CLI is named `tuivory`; documentation image generation uses `TUIVORY_SNAPSHOT_DIR`.

Go projects can access embedded tokens through the public module alone. Python and JavaScript provide shared JSON reading examples; Shell provides an ANSI reference example. UI packages for those languages are not yet available.

[Go API](go-package.en.md) · [Architecture](architecture.en.md) · [Playground](playground.en.md) · [Validation evidence](../evidence/README.en.md)

The new shared component API is documented in the [Go/Rust Tree guide](tree.en.md). This candidate-palette implementation is separate from the existing Go-derived styles and stock `Styler.Tree`, and is included in v0.1.0. The [TVR-7 audit](component-audit.en.md) distinguishes state/controls, host responsibilities, and remaining phases.

## Shared workspace components

The [tabs, panels, splitters, status, and breadcrumbs guide](workspace.en.md) documents public Go/Rust APIs and shared control/color/state principles. Run database-free bilingual integrated examples with `make run-workspace-go ARGS="--lang en"` or `make run-workspace-rust ARGS="--lang en"` from the root. These APIs are included in `go/v0.1.0` and `rust/v0.1.0`; CI evidence and actual application integration are distinguished in [work tracking](https://leechis7.atlassian.net/browse/TVR-7).
