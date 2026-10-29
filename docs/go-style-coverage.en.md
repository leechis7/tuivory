# LazyOra → Tuivory Go style coverage

[한국어 (default)](go-style-coverage.md) · **English**

Baseline: LazyOra `4530a1156853fa8629a16f654f87680fe2b52e01`. The [capture manifest](../go/internal/style/testdata/lazyora-source.json) records source SHA-256 hashes. Extracted styles are checked as follows.

| Source style | Tuivory API | Validation |
| --- | --- | --- |
| Actual palettes in `theme.go`, `style_tokens.go` | `tuivory.NewStyles` | 3 themes × 4 profiles × 20 colors = 240 values |
| Surface and semantic text | `SurfaceColor`, `SurfaceText`, `TextColor`, `TextStyle` | Every surface/text role combination |
| Input, selection, button, focus, disabled, edited, editor | Respective `*Style` methods | Source foreground/background/attributes |
| Focus borders against backgrounds | `BorderStyle`, `RefreshBorders` | 5 surfaces × focused/unfocused |
| `grid.go` palettes, cells, headers, active cells | `GridColors`, `GridCellStyle`, `GridHeaderStyle`, `GridActiveStyle` | All stripe/current-row/NULL/edited/range combinations |
| Row numbers, dividers, grid status | `GridGutterStyle`, `GridDividerColor`, `GridStatusStyle` | Source ANSI/monochrome/light branches |
| `sql_colors.go` calculations | `SyntaxStyle` | 5 surfaces × 7 syntax roles; host owns lexer |
| `choice.go` choices | `DropDownStyle`, `DropDown`, `NewChoice`/`Choice` | Source values per profile, form overrides, wide Korean glyph regression |
| Lists, checkboxes, trees in `widgets.go` | `List`, `Checkbox`, `Tree` | Existing widget application and role recoloring |
| Forms, modals, editor in `theme.go` | `Form`, `Modal`, `Editor` | Actual form rendering, preserved values and internal focus |
| `styleDataTable`, comparisons | `TableOn`, `ComparisonHeaderStyle` | Body/header states and monochrome header exception |
| `tabs.go`, `toolbar.go` | `TabStyle`/`Tab`, `FooterButtonStyle`/`FooterButton` | Active tabs and footer colors/attributes |
| `panel_resize.go`, `form_popup.go` | `SplitterStyle`, `PopupBackdrop`, `PopupCardStyle`, `PopupShadowStyle` | Limited color options and original attributes |
| Traversal in `theme_apply.go` | `Apply`, `Roles`, `StyleChildren` | Hidden pages, values, selections, focus, and scroll preservation |

Base colors and calculations are compared against [1,572 source cases](../go/internal/style/testdata/lazyora-matrix.json) across 12 profiles. Application strings, keymaps, database branches, SQL word lists, range coordinates, and popup layout/input routing are not copied into the shared core. Pass only the state needed for style calculation.

Special application headers (`Accent`, Panel background, Bold), status, and hints can combine public roles and tcell attributes without forcing application-specific meanings into shared names.

Capture commands verify that the local LazyOra Go style files match HEAD, then run only the source functions in a temporary Go program. They import neither Oracle nor LazyOra packages. Normal tests use fixtures and require no LazyOra checkout.

```sh
python3 tools/capture_lazyora_styles.py /path/to/lazyora
python3 tools/capture_lazyora_matrix.py /path/to/lazyora
make -C go test
```

The new shared component API is documented in the [Go/Rust Tree guide](tree.en.md). This candidate-palette implementation is separate from the existing Go-derived styles and stock `Styler.Tree`, and is included in v0.1.0. The [TVR-7 audit](component-audit.en.md) distinguishes state/controls, host responsibilities, and remaining phases.

## Shared workspace components

The [tabs, panels, splitters, status, and breadcrumbs guide](workspace.en.md) documents public Go/Rust APIs and shared control/color/state principles. Run database-free bilingual integrated examples with `make run-workspace-go ARGS="--lang en"` or `make run-workspace-rust ARGS="--lang en"` from the root. These APIs are included in `go/v0.1.0` and `rust/v0.1.0`; CI evidence and actual application integration are distinguished in [work tracking](https://leechis7.atlassian.net/browse/TVR-7).

The 0.4.0 fix binds direct DropDown/Choice panel boxes/labels and Apply host surfaces. Preserve extracted palette/style-calculation comparisons, distinguishing these composition corrections. [Surface design rules](../design/surfaces.en.md).
