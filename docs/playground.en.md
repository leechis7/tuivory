# Tuivory playground

[한국어 (default)](playground.md) · **English**

Explore how the style rules look in interactive widgets. Data is synthetic. The playground connects to no database or network service and does not save settings or inputs.

## Run

```sh
go -C go run ./cmd/tuivory --lang en
```

This guide describes current repository source. `--lang` and shared UI are included in v0.1.0. Requires Go 1.24 or later. With mise, run `mise install`, then use `go` normally. Default local binary:

```sh
make build
./bin/go/tuivory-linux-arm64 --lang en
```

`make build` creates only Linux ARM64. On other hosts, run source with `go -C go run ./cmd/tuivory --lang en`.

```sh
go -C go run ./cmd/tuivory --lang en --theme light --colors 16
go -C go run ./cmd/tuivory --lang en --theme blackwhite --colors 8 --mouse=false
```

`--theme`: dark / light / blackwhite. `--colors`: auto / 8 / 16 / 256 / truecolor. `--lang`: ko / en; Korean is the default. One binary supports both languages; no separate English build is needed.

Color selection is a **token profile preview**. It does not change terminal capabilities or the palette. The library or terminal may approximate unsupported colors. Auto uses the capability reported by the library. If TERM is missing, this process uses ansi.

## Controls

| Key | Action |
| --- | --- |
| Tab / Shift+Tab | Move between controls on the current view |
| Arrow keys | Navigate lists, grids, choices, or button groups |
| Enter | Activate a button, open a choice, or edit a grid name cell |
| F1 | Open scrollable help |
| F2 | Cycle Dark → Light → Monochrome |
| F3 | Cycle Auto → 8 → 16 → 256 → True Color |
| F4 | Preview current inputs in a popup |
| F5 | Toggle input error indicators |
| F6 | Switch Components → Color tokens → Controls |
| Esc | Close the open choice or popup first |
| Ctrl+Q | Quit |

The mouse also operates choices, buttons, checkboxes, and the grid. Outside clicks do not activate the background or close a modal. Tab stays inside the modal; closing it restores focus to its caller.

## Try this first

1. Change the name, checkbox, and choice.
2. Press F2/F3 and confirm that values and selections remain.
3. Press Enter in the grid's Name cell, enter a new value, press Tab, and Save. Look for `* Edited`.
4. Press F4, switch theme with F2 while the popup is open, then return with Esc.
5. Open the Color tokens view with F6 and compare foreground/background samples for 16 roles.

Normal views need at least 80×24 cells. Below 100 columns the left menu is hidden; F6 still reaches every view. Smaller windows display a resize message. Restoring the size restores the existing popup and input state.

## Images and validation scope

[Dark](images/playground-dark-en.svg) · [Light](images/playground-light-en.svg) · [Monochrome](images/playground-blackwhite-en.svg) · [Popup](images/playground-popup-en.svg)

[Korean dark](images/playground-dark.svg) · [Korean light](images/playground-light.svg) · [Korean monochrome](images/playground-blackwhite.svg) · [Korean popup](images/playground-popup.svg)

These reference images are generated from actual application widget cells on a tcell SimulationScreen. They are not SecureCRT/MobaXterm captures or support guarantees. Use the [evidence template](../evidence/README.en.md) for separate terminal observations.

```sh
make -C go test
make -C go check
python3 tools/smoke_playground.py bin/go/tuivory-linux-arm64 --lang ko
python3 tools/smoke_playground.py bin/go/tuivory-linux-arm64 --lang en
TUIVORY_SNAPSHOT_DIR="$PWD/docs/images" go -C go test ./internal/playground -run '^TestSnapshot$' -count=1
```

The snapshot test generates both languages; English filenames end in `-en`. Status contrast is checked against the actual card surface. Insufficiently contrasting accents fall back to body text; words such as OK/Warning/Error preserve meaning.

The playground uses the [Go styles extracted from LazyOra](lazyora-extraction.en.md). Shared JSON supplies role ordering and cross-language examples; candidate CSV data is distinct from the extracted palette. The playground does not include a SQL editor, database features, or a general widget SDK.
