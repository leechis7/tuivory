# Tuivory Go

[한국어 (default)](README.md) · **English**

TVR-7 in 0.11.0: [grid editing and data work](../docs/grid-workspace.en.md). Extends root-only `Grid / NewGridView`, preserving legacy edit requests by default.

**Do not use 0.10.1:** [Withdrawal and upgrade](../docs/withdrawn-versions.en.md). Use 0.10.2 or later.

**0.10.2 TVR-26:** [Windows Go facade](../docs/ui-facade.en.md) no longer references Unix-only terminal APIs. Available in 0.10.2; do not use 0.10.1.

**0.10.2 TVR-29:** [Compact popup shadows](../docs/popup-shadows.en.md) use one cell right and half a row down; preserve borders and the off default.

0.10.0 TVR-7: [responsive Go Modal](../docs/modals.en.md) wraps long buttons inside narrow terminals. Modal is an SDK adapter embedding its backend, an exception to raw alias identity. Included in 0.10.0.
0.10.0 TVR-18: [opt-in Go/Rust tab/tree drag and drop](../docs/drag-drop.en.md), immutable host-approved movement requests, captured outside input, cancellation and keyboard alternatives. Available starting with 0.10.0.


**0.9.1 TVR-27:** [Unified example executables](../docs/examples.en.md) provide one file per language, built only for the current Linux host architecture. Select examples with `--demo tree`, `--demo menu`, `--demo syntax`, etc.

**0.9.0 TVR-24:** [optional Oracle SQL/PLSQL analysis, common tokens and editor migration](../docs/syntax.en.md). Go uses one root import; Rust opts in with syntax-sql.

**0.10.0:** compose Go UI through `github.com/leechis7/tuivory/go` alone. Existing `/ui` and `/terminal` paths remain compatible. [Single import and name mappings](../docs/ui-facade.en.md).

[Public API reference](../docs/api/go.en.md)

The library owns component rendering/internal interaction; hosts own real screens, global keys, cross-component focus and business bindings. Examples are optional compositions, not required screen templates. [Component/application boundary](../docs/component-boundary.en.md).

Product version is **0.12.4** in root `VERSION`. The Go module is distributed through subdirectory tag `go/v0.12.4`. [Release guide](../docs/release-0.12.4.en.md).

All Go implementation code and module configuration live in this directory. The module path is `github.com/leechis7/tuivory/go`; the package name is `tuivory`. Requires Go 1.24 or later.

```sh
go get github.com/leechis7/tuivory/go@v0.12.4
```

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

The current release is `v0.12.4`, tagged `go/v0.12.4` because the module lives in `go/`. The first tag `go/v0.0.1` is preserved.

From the repository root:

```sh
go -C go run ./cmd/tuivory --lang en
make build
make test
make check
```

Language selection is included in `v0.2.0`. From this directory, use `go run ./cmd/tuivory --lang en` for the English playground, `go run ./examples/starter` for the starter template (Korean labels), or `go test -race ./...` for Go tests. `make build` creates one unified executable for the current Linux host architecture in `bin/go/`. Run it with `--lang en` for English or `--lang ko` for Korean. Omitting the flag, including with `make run`, defaults to Korean.

Shared candidate tokens originate in [design/tokens](../design/tokens/README.en.md). `internal/tokens/candidate.json` is a generated distribution copy produced by `tools/export_tokens.py`; do not edit it manually. The module embeds this data, so consumers need neither the repository root nor a generation step.

[API and usage](../docs/go-package.en.md) · [Style coverage](../docs/go-style-coverage.en.md) · [Project overview](../README.en.md)

TVR-7 fixes in 0.9.2 preserve wide text during table restyling and correct splitter/comparison separator contrast. [Drawing rules](../docs/overlay-drawing.en.md) · [Style fixes](../docs/lazyora-extraction.en.md).

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

0.7.0 TVR-26 adds SDK-only Go/Rust UI composition, shared input/byte-span conversion and terminal lifetime. [API mappings, examples and availability](../docs/ui-facade.en.md).

The TVR-8 follow-up in 0.9.2 fixes missing Dim on eight-color Go token samples and missing themed disabled dropdown field styling. [Go twelve-palette views and validation](../docs/disabled-states.en.md).

0.9.2 also improves dark/8 SQL highlighting with seven foreground/attribute combinations shared by Go/Rust, retaining >=4.5:1 reference text contrast. [Rules and terminal limitations](../docs/syntax.en.md).

TVR-7 in 0.12.4: [real grid cursor and backend integration](../docs/grid-workspace.en.md). For real cursors in 0.12.4, Go uses NewCursorScreen/NewGridView, Rust GridWidget::render_frame.
