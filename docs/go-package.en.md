# Tuivory Go style package

[한국어 (default)](go-package.md) · **English**

The Go code is an independent submodule in `go/`. Its module path is **`github.com/leechis7/tuivory/go`**, and its single public package is **`tuivory`**. Requires Go 1.24 or later.

```sh
go get github.com/leechis7/tuivory/go@v0.1.0
```

The current release is `v0.1.0`, tagged `go/v0.1.0`.

| Module path | Responsibility |
| --- | --- |
| `tuivory.go` | Public API, role and state types |
| `internal/style` | Theme, profile, and state calculations |
| `internal/widgets` | Applying and reapplying styles to stock tview widgets |
| `internal/tokens` | Shared token loader and generated distribution JSON |

Applications import the public package. The application uses host libraries such as tview and tcell to create widgets and own the terminal.

## A runnable application

In a Go module with Tuivory installed, save this as `main.go` and run `go run .`:

```go
package main

import (
    "log"

    "github.com/leechis7/tuivory/go"
    "github.com/rivo/tview"
)

func main() {
    app := tview.NewApplication()
    form := tview.NewForm().AddInputField("Name", "", 24, nil, nil)
    form.AddButton("Quit", func() { app.Stop() })
    form.SetBorder(true).SetTitle(" Tuivory ")

    styler, err := tuivory.New("dark", "256")
    if err != nil {
        log.Fatal(err)
    }
    styler.Form(form)
    if err := app.SetRoot(form, true).Run(); err != nil {
        log.Fatal(err)
    }
}
```

Use Tab to reach **Quit**, then Enter to exit. From a repository checkout, you can also run the [starter template](../go/examples/starter/main.go), which supports F2 to switch themes and Ctrl+Q to quit:

```sh
go -C go run ./examples/starter
go -C go run ./cmd/tuivory --lang en --theme light --colors 16
```

These commands and the `--lang` option describe `v0.1.0` source. The playground accepts `--lang en` for English or `--lang ko` for Korean (the default); the starter template keeps Korean example labels. Language selection affects the playground UI, not the public style API. Themes: `dark`, `light`, `blackwhite`. Profiles: `8`, `16`, `256`, `truecolor`. When the application owns the screen, it can select a profile with `tuivory.ProfileForColors(screen.Colors(), limited)`. Detection is separate from style calculation: the package does not read stdin or change the terminal palette.

## Roles and states

`Styles` exposes palette values and style calculation methods. Select a theme and profile with `NewStyles`; the application can customize individual color fields. There is no global theme state.

- Surfaces: `Canvas`, `Panel`, `Field`, `Footer`, `Editor`.
- Text roles: `Body`, `Hint`, `Accent`, `Warning`.
- Basic styles: inputs, selections, buttons, focused buttons, disabled content, edited content, and editors.
- Additional styles: dropdowns, active tabs, footer buttons, comparison headers, splitters, popup cards, backdrops, and shadows.
- Grid states: default, striped, current row, NULL (italic), edited, range selection, active cell, header, separators, row numbers, and status lines.
- Syntax: keywords, functions, types, strings, numbers, comments, and parameters. The host maps lexer output to `SyntaxKind`; SQL/Oracle parsing and database state are outside the package.

Apply styles to existing application widgets:

```go
styler.Form(form)
styler.List(list)
styler.Editor(editor)
styler.Text(hint, tuivory.Panel, tuivory.Hint)

styler.Grid(table, func(row, col int) tuivory.CellState {
    return tuivory.CellState{
        Null: nullCells[row][col],
        Edited: changedCells[row][col],
        InRange: selectedCells[row][col],
    }
})
tokenStyle := styler.Styles.SyntaxStyle(tuivory.SyntaxKeyword, styler.Styles.EditorStyle())
```

These snippets assume that the host has already created the widgets and cell-state data. `Grid` derives Row/CurrentRow from the table's actual selection. Styles compose in this order: stripes → current row → NULL → edited → range selection. Active cells and active headers use separate styles. Edited and range-selection styles can override NULL italics, matching the original implementation. The application draws markers such as `*`, data, row numbers, and separators, and handles input.

## Changing themes

Create a new `Styler` and apply it to existing widgets. `Apply` traverses hidden Pages, Flex and Form children, and tree nodes without recreating widgets.

```go
roles := tuivory.Roles{
    Surfaces: map[*tview.Box]tuivory.Surface{hint.Box: tuivory.Panel},
    Text: map[*tview.TextView]tuivory.TextRole{hint: tuivory.Hint},
}
styler.Apply(roles, pages)
// Reapply application-specific state for grids, tabs, and footer buttons.
styler.Tab(tabButton, isActive)
styler.FooterButton(footerButton)
```

Custom wrappers can expose children through `StyleChildren() []tview.Primitive`. Call `RefreshBorders` after focus changes to recalculate borders for the current background and focus. Application focus and event callbacks are preserved.

For form choices, prefer `NewChoice`. It prevents common form input colors from overriding the choice styling and handles half-width remnants of Korean characters beneath an open dropdown. `Form` owns DrawFunc hooks for inputs, read-only descriptions, and stock DropDown widgets. Applications with existing DrawFunc hooks should use individual styling methods or compose hooks explicitly.

`Apply` preserves values but resets basic table cell styles. Reapply custom cell states afterward with `Grid` or individual APIs. The host owns modal focus cycling, background input blocking, and application actions.

## Verification and distribution

Go tests compare 240 palette values and 1,572 style cases captured by independently running the original LazyOra functions. See [extraction sources](lazyora-extraction.en.md) and [style coverage](go-style-coverage.en.md). Simulated screen checks and actual terminal observations are recorded separately.

There is no root Go module: install `github.com/leechis7/tuivory/go@v0.1.0`. The module embeds generated `go/internal/tokens/candidate.json` from shared sources in `design/tokens/`. Consumers need no repository-root files, Python, Shell, or generation tools. `python3 tools/export_tokens.py --check` checks the embedded copy against the shared source.

See [installation and usage](installation.en.md) for current module, command, and token identifiers. Original attribution and licensing are preserved in [NOTICE](../NOTICE.en.md). For setup and validation commands, return to the [English README](../README.en.md).

The new shared component API is documented in the [Go/Rust Tree guide](tree.en.md). This candidate-palette implementation is separate from the existing Go-derived styles and stock `Styler.Tree`, and is included in v0.1.0. The [TVR-7 audit](component-audit.en.md) distinguishes state/controls, host responsibilities, and remaining phases.

## Shared workspace components

The [tabs, panels, splitters, status, and breadcrumbs guide](workspace.en.md) documents public Go/Rust APIs and shared control/color/state principles. Run database-free bilingual integrated examples with `make run-workspace-go ARGS="--lang en"` or `make run-workspace-rust ARGS="--lang en"` from the root. These APIs are included in `go/v0.1.0` and `rust/v0.1.0`; CI evidence and actual application integration are distinguished in [work tracking](https://leechis7.atlassian.net/browse/TVR-7).

## Static linking

Tuivory does not introduce required shared libraries into host applications. Build distributed Linux apps with `CGO_ENABLED=0`, then check the final ELF and execution on the target kernel. Check native runtimes introduced by other application dependencies too. [Static distribution and external-host validation](static-build.en.md)

## Shared control states and focus

Unreleased public APIs `ControlState.Visual`, `ControlStyle`, `NewFocusStack` provide state appearance, stable-ID navigation, nested popup routing and restoration. See the [Go/Rust contract and examples](focus.en.md). Hosts connect actual widgets, data, business actions and terminal lifecycle.

[TVR-9: Inputs and forms](forms.en.md): `Form / FormField / FormWidget`. Public Go/Rust APIs and localized hosts; unreleased dev source.
