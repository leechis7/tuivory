# Tuivory Go

[한국어 (default)](README.md) · **English**

[Public API reference](../docs/api/go.en.md)

The library owns component rendering/internal interaction; hosts own real screens, global keys, cross-component focus and business bindings. Examples are optional compositions, not required screen templates. [Component/application boundary](../docs/component-boundary.en.md).

Product version is **0.6.0** in root `VERSION`. The Go module is distributed through subdirectory tag `go/v0.6.0`. [Release guide](../docs/release-0.6.0.en.md).

All Go implementation code and module configuration live in this directory. The module path is `github.com/leechis7/tuivory/go`; the package name is `tuivory`. Requires Go 1.24 or later.

```sh
go get github.com/leechis7/tuivory/go@v0.6.0
```

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

The current release is `v0.6.0`, tagged `go/v0.6.0` because the module lives in `go/`. The first tag `go/v0.0.1` is preserved.

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

The [tabs, panels, splitters, status, and breadcrumbs guide](../docs/workspace.en.md) documents public Go/Rust APIs and shared control/color/state principles. Run database-free bilingual integrated examples with `make run-workspace-go ARGS="--lang en"` or `make run-workspace-rust ARGS="--lang en"` from the root. These APIs are included in `go/v0.5.0` and `rust/v0.5.0`; CI evidence and actual application integration are distinguished in [work tracking](https://leechis7.atlassian.net/browse/TVR-7).

[Overlay drawing API](../docs/overlay-drawing.en.md): CJK/emoji edges of popups, cards and shadows, and post-Show output tests.

[Shared menus](../docs/menus.en.md): Go/Rust hierarchy, bar/back navigation, shortcuts/disabled state, popup/caller-context requests and bilingual database-free hosts. Included in 0.5.0.

In 0.5.0, menus use single borders and current-item/open-menu cues. Input blocking and caller restoration remain. [Menu presentation rules](../docs/menus.en.md).

Version 0.5.0 TextOnSurface / Styles::text_on_surface and ControlStyleOnSurface / Styles::control_on_surface bind plain text to its real surface and correct contrast. Preserve original tokens/raw styles and explicit state/custom backgrounds. [Bilingual surface design guide](../design/surfaces.en.md).

[Disabled states across twelve palettes](../docs/disabled-states.en.md): no ordinary disabled prefixes, gray/Dim foregrounds, blocked input and localized runnable references.

[API lifecycle, deprecation and migration](../docs/api-lifecycle.en.md) · [Public API overlap audit](../docs/api-overlap-audit.en.md): document targets, replacements and first-release/removal plans.

TVR-19 in 0.5.0 adds optional popup shadows, disabled by default: `off/auto/solid/dim`, placement including the full footprint, card-only hit testing and wide-glyph boundary protection. Hosts own backdrop redraws and opening/closing. [APIs, runnable examples and 12-palette views](../docs/popup-shadows.en.md).

0.6.0 TVR-22–25 adds borderless Surface, standalone/secret controls, text editing/viewing and row/column/grid/layer containers. [Usage, source availability and examples](../docs/controls.en.md).
