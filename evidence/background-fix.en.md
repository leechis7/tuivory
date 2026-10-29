# Background leakage fix evidence — TVR-7

[한국어 (default)](background-fix.md) · **English**

A later phase retuned disabled foregrounds and removed ordinary disabled prefixes. See the [current comparison](../docs/disabled-states.en.md). Counts and JSON hashes below record the earlier phase.


Fix findings from the [pre-fix audit](../docs/background-audit.en.md) on the existing uncommitted branch. Preserve original tokens, raw-style APIs and grid options. [Bilingual design guide](../design/surfaces.en.md).

## Changes

- Go/Rust Rows and breadcrumb/status Line bind plain body/hint/disabled/info/success/warning/error text to surface. Use the better surface foreground if original contrast is inadequate.
- Preserve field/button/selection/edited/header/editor/grid.* and custom-role backgrounds. Normal Badge/Chip follows plain-text rules. Do not change tab segments, list selection extent or simple/data grid design.
- Go NewGridView and Rust GridWidget preserve role backgrounds. Manual compositions can use Go RowsView.PreserveBackgrounds / Rust RowsWidget.preserve_backgrounds().
- Export Go TextOnSurface/ControlStyleOnSurface and Rust Styles::text_on_surface/control_on_surface; retain existing raw APIs.
- Bind direct Go DropDown/Choice box/labels, Apply host surfaces, Go/Rust focus and Rust menu/tree/workspace/playground text regions. Reuse the same common helper for the Go host's existing contrast correction.

## Validation scope

Compare the same 564 Go and 384 Rust renderings: 948 total. Grid probes explicitly use the same preservation path as public GridView/GridWidget. Remove plain-text/row-edge background mismatches while preserving previous observations for intentional grid/tab/tree/menu backgrounds. Check nominal reference contrast for 850 nonblank plain-text runs; the minimum is about 4.504:1.

Across twelve palettes, add physical Go-after-Show and Rust TestBackend regressions for labels/spans, breadcrumbs/status, selection/edit/custom roles, raw preservation, explicit canvas and light-16 success foreground correction. Check full Go race/vet and isolated consumers, Rust full features/targets/doctests/fmt/Clippy and packaged external consumers. Actual PTYs verify model/selection/input, theme changes, resize and normal exit.

Consult [final results JSON](background-fix-results.json) for exact outcomes/source/image hashes and unexecuted checks. Refresh Korean/English UI references together; Go SimulationScreen and Rust TestBackend are distinct from physical servers/SSH/fonts.

## Reproduction

```sh
go -C go test -race ./...
go -C go vet ./...
make test-rust-ui check-rust-ui
python3 tools/check_go_module.py
python3 tools/check_rust_module.py --ratatui
python3 tools/smoke_playground.py bin/go/tuivory-linux-arm64 --lang en --resize
python3 tools/check_links.py
python3 tools/export_tokens.py --check
```

Audit probes/raw logs remain in ignored bin/validation/background-audit/ and background-fix/. Preserve pre-fix JSON as history. These changes remain uncommitted/unpublished; no remote CI, CentOS validation, tags or Release.

## Earlier disabled-state cue draft (superseded)

Help, lists/search, forms, and disabled notice actions add `[-]`; menu bars use the existing compact menu `-` cue. Disabled values/buttons use the disabled role instead of active backgrounds, retaining values and activation exclusions. Both languages test markers, retained values, and menu-bar widths/hit exclusions. Another 20 affected catalog/menu PTY cases are run, with bilingual guides and references refreshed.
