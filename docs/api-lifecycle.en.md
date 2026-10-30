# API support status and migration

[한국어 (default)](api-lifecycle.md) · **English**

The first deprecation release is **0.5.0**. Existing 0.4.0 tags remain intact. [Release guide](release-0.5.0.en.md).

## Reading API status

| Status | Meaning | Use in new code |
| --- | --- | --- |
| Supported | Provided for its intended purpose | Available, including low-level APIs |
| Compatibility | Retained for older code with documented limitations/effect | Check the preferred path; this status alone does not add a compiler warning |
| Deprecated | A replacement exists and new use is discouraged | Migrate using the designation, rationale and examples |
| Removed | Absent from actual source/release | Consult the removal release and old-to-new migration guidance |

A more convenient API does not automatically deprecate a supported lower-level one. Deprecation does not mean immediate removal. Removal is reviewed/approved separately and announced in advance. Only the user decides product major versions. No APIs are removed by this task. Supported status is not a promise to retain an API forever; reassess it when replacement coverage changes.

## Current audit

Public APIs outside the explicit deprecation list are supported. The following covers commonly confused APIs and explicit exceptions, rather than redefining every public symbol.

| Language/API | Status | Purpose or migration |
| --- | --- | --- |
| Go `Styler` and shared component models/views | Supported | Existing-widget styling and shared component interaction/rendering |
| Go `Styles.PopupShadowStyle`, `DimRegion`, `WideSafeScreen` | Supported | Custom popup/shadow drawing and wide-glyph protection; TVR-19 in 0.5.0 `ShadowView` wraps popups and uses the first two APIs internally; arbitrary-region drawing and boundary protection remain supported |
| Go `Pair.Style`, `ControlStyle` / Rust `Styles::role`, `Styles::control` | Supported | Compose explicit original-role backgrounds; distinct from surface-bound styling |
| Go `TextOnSurface`, `ControlStyleOnSurface` / Rust `text_on_surface`, `control_on_surface` | Supported since 0.4.0 | Actual-surface plain-text backgrounds, contrast and states |
| Go `RowsView.PreserveBackgrounds` / Rust `RowsWidget::preserve_backgrounds`, `RawRowsWidget` | Supported since 0.4.0 | Preserve explicit backgrounds in grids/custom rows |
| Rust `MenuWidget`, `MenuBarWidget`, `MenuPopupWidget` | Supported | Types, models and input behavior remain supported; prefer `new` in 0.5.0 |
| Go `Colors.SelectionText` | Deprecated — 0.5.0 | Historical snapshot unused by rendering; use live `Styles.SelectionFG` |
| Go `Styles.FieldStyle` | Deprecated — 0.5.0 | `Styles.TextStyle(Field, Body)`, preserving custom colors |
| Go `Styles.FooterButtonStyle` | Deprecated — 0.5.0 | `Styles.TextStyle(Footer, Body)` |
| Go `Styles.PopupCardStyle` | Deprecated — 0.5.0 | `Styles.TextStyle(Panel, Body)` |
| Go `Styler.Table` | Deprecated — 0.5.0 | `Styler.TableOn(table, Canvas)` |
| Go `Grid.Click` | Deprecated — 0.5.0 | `Grid.Pointer` for mouse input, `Focus` + `Handle` for programmatic control |
| Rust `Grid::click` | Deprecated — 0.5.0 | `Grid::pointer` for mouse input, `focus` + `handle` for programmatic control |
| Rust `MenuWidget::focused` | Deprecated — 0.5.0 | `MenuWidget::new(model, styles).ascii(ascii)` |
| Rust `MenuBarWidget::focused` | Deprecated — 0.5.0 | `MenuBarWidget::new(model, styles)` |
| Rust `MenuPopupWidget::focused` | Deprecated — 0.5.0 | `MenuPopupWidget::new(model, styles, title).ascii(ascii).padding(padding)` |
| Rust other `focused` fields, including `RowsWidget` and `FormWidget` | Supported | These control real focus presentation, unlike the ignored menu fields |

### Three Rust menu focused fields

- Rationale: since 0.4.0, menus render selection/open state independently of input focus. These fields remained for compatibility and have no visual effect.
- First deprecation release: **0.5.0**, matching Rust `since` and the lifecycle list.
- Replacement: the `new` constructors and `ascii`/`padding` setters above. Unicode and padding=1 are defaults; the bar has no extra settings.
- Existing struct literals still compile but specifying these fields emits deprecation warnings. Hosts using `deny(deprecated)` or warnings-as-errors must migrate. The fields are not removed, and actual input focus is unchanged.
- Removal: **not scheduled**. Do not automatically remove them in this release or the next.

```rust
// Before: focused warns in 0.5.0
let popup = MenuPopupWidget {
    model: &mut menu,
    styles: &styles,
    title: "Menu",
    ascii: true,
    focused: true,
    padding: 1,
};

// After: new constructor in 0.5.0, no deprecation warning
let popup = MenuPopupWidget::new(&mut menu, &styles, "Menu")
    .ascii(true)
    .padding(1);
```

These are alternative before/after blocks. Hosts still wire menu selection/open state, actual input focus, background blocking and caller restoration. Constructors do not impose an application-wide focus policy.

## Updating code, documentation and releases

1. Establish the rationale and a warning-free replacement first. Preserve required configuration/behavior/performance and verify legacy paths.
2. Record the target, status, replacement, rationale, designation and removal plan in the [lifecycle list](../design/api-lifecycle.json), updating this paired usage guide.
3. Add a GoDoc `Deprecated: ...` paragraph to the affected public declaration or Rust `#[deprecated(note = "...")]` to the symbol. Mark only the field/method when the type remains supported. Version 0.5.0 marks the six Go methods/fields above. The Go compiler itself does not emit deprecation warnings; GoDoc, IDEs and analysis tools consume the metadata.
4. When shipping an unreleased entry, change `availability` to `released`, set `deprecated_since` to its first release, and use the same Rust `since` and bilingual documentation version. Preserve old tags and historical introduction versions.
5. Once removal is approved, announce the actual removal release and migration, then mark the entry `removed`, retaining its history. There are currently no removed entries.
6. Use warning-free paths in examples and independent consumers. Allow warnings narrowly only for legacy compatibility regressions; do not suppress deprecation warnings across the project/library.

```sh
python3 tools/check_api_lifecycle.py
```

The check compares source deprecation annotations with the list, paired docs and replacement declarations. CI's validate job also runs it. See [Go usage](go-package.en.md), [Rust](../rust/README.en.md) and [menus](menus.en.md). Report local verification separately from remote CI and publication.

## Overlap migrations and differences

Compare returned styles, surfaces, options, input and data ownership rather than names alone. The [API-family overlap audit](api-overlap-audit.en.md) records each decision. Version 0.5.0 deprecates six Go methods/fields and four Rust methods/fields, ten symbols in total. Their first deprecation release is 0.5.0; removal is not scheduled.

```go
// Equivalent styles and Canvas table surface
field := styles.TextStyle(tuivory.Field, tuivory.Body)   // replaces FieldStyle()
footer := styles.TextStyle(tuivory.Footer, tuivory.Body) // replaces FooterButtonStyle()
card := styles.TextStyle(tuivory.Panel, tuivory.Body)    // replaces PopupCardStyle()
styler.TableOn(table, tuivory.Canvas)                  // replaces Table(table)
```

Legacy style methods retain their behavior. Preserve `Canvas` when migrating `Table`; choosing `Panel` changes the background. These Go replacements and the grid pointer APIs are already available in public 0.4.0.

```go
// Convert host mouse coordinates to grid-local cells.
// Instead of Grid.Click(rowID, kind, x, width, height):
event := grid.Pointer("click", localX, localY, width, height, false)
// Continue forwarding out-of-bounds move/up while a drag is captured.
```

```rust
let event = grid.pointer("click", local_x, local_y, width, height, false);
```

`Grid.Click/click` mixes a row ID, horizontal coordinate and `@header` discriminator in a legacy mouse entry point. `Pointer/pointer` unifies vertical coordinates, headers, gutters, dragging, ranges, wheels and mouse-disable options. For compatibility, old calls retain their original behavior, including bypassing DisableMouse on direct calls. Migration therefore requires more than renaming arguments. Hosts performing programmatic ID-based actions should call `Focus/focus` and then `Handle/handle("select")` or `"sort"`. The pointer path respects mouse-disable configuration.

`Colors.SelectionText`, including the same promoted field on Styles, is a historical palette snapshot. Writing it does not change rendering. Configure `styles.SelectionFG = color`, consumed by `SelectionStyle()`. Preserve the old field value/order and struct-literal compatibility.
