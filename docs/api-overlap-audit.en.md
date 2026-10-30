# Public API overlap audit

[한국어 (default)](api-overlap-audit.md) · **English**

TVR-20 audits unreleased source after 0.4.0. Beyond menu fields, the review covers the API families below using Go root exports and methods/fields exposed through aliases such as Styles/Styler, plus all-feature Rust public rustdoc items. Inherited/implemented third-party tview/Ratatui APIs are not counted as duplicate Tuivory APIs. Declaration inventories locate symbols; the behavior comparisons below determine semantic overlap.

## Overlap being retired

| Target | Duplicate behavior/problem | Replacement and checks |
| --- | --- | --- |
| Go `Styles.FieldStyle` | Identical to Field/Body colors/attributes | `TextStyle(Field, Body)`; twelve palettes and customized colors |
| Go `Styles.FooterButtonStyle` | Identical to Footer/Body colors/attributes | `TextStyle(Footer, Body)`; twelve palettes and customized colors |
| Go `Styles.PopupCardStyle` | Direct forwarding to Panel/Body | `TextStyle(Panel, Body)`; twelve palettes and customized colors |
| Go `Styler.Table` | Same table presentation as `TableOn(table, Canvas)` | Explicit surface API; post-Show Korean/CJK, selection, headers and borders |
| Go `Colors.SelectionText` | Historical selected-foreground copy; rendering reads separate `Styles.SelectionFG` | Use live SelectionFG. Verify that snapshot writes have no rendering effect while the live setting applies |
| Go `Grid.Click` / Rust `Grid::click` | Legacy mouse path mixing row IDs and horizontal coordinates | Unified `Pointer/pointer`; programmatic IDs use `Focus/focus` + `Handle/handle`. Document DisableMouse behavior differences |
| Rust three menu `focused` fields | Ignored compatibility fields since 0.4.0 | `new`, `ascii`, `padding`; match legacy literals and new render/state behavior across twelve palettes |

In total, **10** public methods/fields are deprecated in unreleased source. Existing behavior and names remain for source compatibility; removal is not scheduled. The [lifecycle/migration guide](api-lifecycle.en.md) and [registry](../design/api-lifecycle.json) define exact targets, rationale, replacements and publication status.

## Remaining families and consolidation conditions

| APIs compared | Decision and rationale |
| --- | --- |
| `New` / `NewStyles`, `Styler` / `Styles` / `Colors` | Widget application, style calculation and value data are different layers. Consolidation needs actual usage/custom-color configuration design first |
| Candidate token Parse/Candidate/Resolve / extracted styles | Palette values and semantic roles differ. Direct substitution changes screens; palette consolidation must come first |
| Serialized JSON / parsed tokens / resolved palette | Serialization, validation and framework color representation differ |
| Original-role styles / actual-surface styles / background-preserving Rows | Explicit selection/edit/field/custom backgrounds differ from plain-text surface correction. Consider consolidation when one configuration API covers all semantics |
| Existing `Styler.Form/Input/List/Tree/Grid/Comparison` / shared models/views | Applying styles while retaining existing tview objects/state/cells differs from new data-driven interactive components. Reassess once existing object/callback/custom-style migration is ready |
| Selection/button/button-focus/tab/comparison-header styles | Some profiles happen to share colors, but full themes, custom colors, modifiers and state composition differ |
| `Styles.Disabled` / `DisabledStyle`, `GridColors.RangeBG` / actual range styling | Candidates needing a coherent replacement for historical values, live configuration and rendered styles. Provide read/write/custom-composition paths before deciding deprecation |
| `PopupShadowStyle` / `DimRegion` / TVR-19 popup options | Style creation, explicit-region drawing and complete popup composition have different scope. **Low-level APIs are not promised permanent retention.** Reassess when the new options can replace direct composition |
| Model Handle / individual Open/Close/Focus/Resize | Input action routing and programmatic control share implementations but offer different model entry paths |
| FormKey/NavigationKey/MenuKey / model actions | tcell event translation differs from framework-independent model control, analogous to crossterm host wiring |
| Grid SetSource / ApplySource and revision | Immediate replacement differs from stale asynchronous response rejection; preserve data/sort/selection restoration semantics |
| Tree/Tabs models / Go/Rust renderers / stock-widget styles | Stable-ID navigation/events differ from framework rendering or styling existing widgets |
| StackLayout / StackRects / Ratatui stack_rects, split models/views | Length allocation, cell geometry, Ratatui Rect conversion and actual input/rendering are separate responsibilities sharing the same base calculations |
| Paths/status/Notice/Progress/DataState/Badge/Chip/Help models/rows/views | Layout/host requests are separated from rendering; model-only consumers must remain possible |
| Go public aliases / internal declarations; Rust re-exports | One symbol exposed through a public import is not multiple independently implemented features |

This audit does not promise permanent support for every current API. Update the registry and decisions when replacements or real host migration evidence become available. Do not describe unimplemented TVR-19 options or host-owned screen composition as completed replacements.

See the [TVR-20 results](../evidence/api-lifecycle-results.json) for validation, public declaration/item inventories and source hashes. Go 751 declarations and Rust 159 public item pages use different counting units and are not comparable API counts. Validation is local; no commit, publication or remote CI was performed.
