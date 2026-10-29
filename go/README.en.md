# Tuivory Go

[한국어 (default)](README.md) · **English**

The library owns component rendering/internal interaction; hosts own real screens, global keys, cross-component focus and business bindings. Examples are optional compositions, not required screen templates. [Component/application boundary](../docs/component-boundary.en.md).

Product version is **0.2.0** in root `VERSION`. The Go module is distributed through subdirectory tag `go/v0.2.0`. [Release guide](../docs/release-0.2.0.en.md).

All Go implementation code and module configuration live in this directory. The module path is `github.com/leechis7/tuivory/go`; the package name is `tuivory`. Requires Go 1.24 or later.

```sh
go get github.com/leechis7/tuivory/go@v0.2.0
```

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

The current release is `v0.2.0`, tagged `go/v0.2.0` because the module lives in `go/`. The first tag `go/v0.0.1` is preserved.

From the repository root:

```sh
go -C go run ./cmd/tuivory --lang en
make build
make test
make check
```

Language selection is included in `v0.2.0`. From this directory, use `go run ./cmd/tuivory --lang en` for the English playground, `go run ./examples/starter` for the starter template (Korean labels), or `go test -race ./...` for Go tests. `make build` creates a single Linux ARM64 product binary in the repository's `bin/go/` directory. Run it with `--lang en` for English or `--lang ko` for Korean. Omitting the flag, including with `make run`, defaults to Korean.

Shared candidate tokens originate in [design/tokens](../design/tokens/README.en.md). `internal/tokens/candidate.json` is a generated distribution copy produced by `tools/export_tokens.py`; do not edit it manually. The module embeds this data, so consumers need neither the repository root nor a generation step.

[API and usage](../docs/go-package.en.md) · [Style coverage](../docs/go-style-coverage.en.md) · [Project overview](../README.en.md)

## Shared Tree

Existing `Styler.Tree` styles stock tview nodes. New `NewTree`, `TreeState`, and `NewTreeView` provide stable IDs, expansion/selection/scroll, node icons/secondary text/counts, and keyboard/mouse behavior. Rust shares the same candidate tokens and controls. This does not port the complete Go-derived styler; the Tree APIs are included in v0.2.0. [API and example](../docs/tree.en.md) · [Support audit](../docs/component-audit.en.md). Run `make run-tree-go ARGS="--lang en"` from the root.

## Shared workspace components

The [tabs, panels, splitters, status, and breadcrumbs guide](../docs/workspace.en.md) documents public Go/Rust APIs and shared control/color/state principles. Run database-free bilingual integrated examples with `make run-workspace-go ARGS="--lang en"` or `make run-workspace-rust ARGS="--lang en"` from the root. These APIs are included in `go/v0.2.0` and `rust/v0.2.0`; CI evidence and actual application integration are distinguished in [work tracking](https://leechis7.atlassian.net/browse/TVR-7).

[Overlay drawing API](../docs/overlay-drawing.en.md): CJK/emoji edges of popups, cards and shadows, and post-Show output tests.

[Shared menus](../docs/menus.en.md): Go/Rust hierarchy, bar/back navigation, shortcuts/disabled state, popup/caller-context requests and bilingual database-free hosts. Unreleased source, absent from v0.2.0 tags.
