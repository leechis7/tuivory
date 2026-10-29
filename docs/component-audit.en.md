# Shared UI support audit — TVR-7

[한국어 (default)](component-audit.md) · **English**

Re-audited on 2026-10-29, distinguishing published v0.2.0 from local TVR-17 commit `e34b824`. Boundary corrections, grid options and shared menus are integrated into dev and included in 0.3.0; keep the epic open. Current scope below takes precedence; the 2026-10-27 table is historical. [Boundary](component-boundary.en.md).

## Current support and host responsibilities

| Area | Public Go / Rust support | Missing capability or host responsibility |
| --- | --- | --- |
| Inputs/forms | Form models/renderers, editing/choice, required values and submit requests | Connection/settings screens, business validation and saving |
| Tree | NewTree/TreeState/NewTreeView / tree::Tree/TreeState/TreeWidget | Real data, loading and item execution |
| Menu/search | NewList/NewSearchPicker / collections::ListModel/SearchPicker, flat items/filtering/selection requests | v0.2.0 is flat. 0.3.0 Menu/NewMenuView and menu::Menu/MenuPopupWidget add hierarchy/back/bar/single-popup support. Hosts own content/remote candidates |
| Tabs | Tabs/TabState/NewTabView / components::Tabs/TabState/TabsWidget, overflow/edited/close requests | SQL/session ownership, document storage and close approval |
| Panels/splits | NewPanelView/NewSplitView / Styles::panel/split_rects, geometry inside assigned areas | Screen placement/axis/initial sizes/visibility/responsive composition |
| Focus/popups | FocusStack navigation/blocking/restoration within host-defined scopes | Cross-component order, scope registration, terminal/event wiring |
| Status/path/help | StatusLine/Breadcrumbs/Help and language renderers | Contextual items, command/key assignment, whole help screens/contents |
| Grid | Published v0.2.0 Grid/GridSource/basic rendering; TVR-17 options/ranges/status are included in 0.3.0 | Queries, business editing, transactions, real clipboard/exports |
| Themes/validation | Shared tokens/semantic styles, state preservation, cell width/static-distribution checks | Actual host/customer-terminal checks remain separate; no claim of full Go extracted-styler/Rust candidate-palette parity |

After the boundary audit, the user requested [shared Menu improvements](menus.en.md) under existing TVR-7. Distinguish released 0.2.0 from the new implementation; command taxonomy/execution remains host-owned. Tab overflow and shortcut-help rendering already exist and should not be duplicated. [Different host policy on existing components](component-boundary.en.md).

## Starting-point record — 2026-10-27

Historical comparison of TVR-5 baseline `b67a4cb` with the initial TVR-7 implementation.

| Area | Go at start | Rust at start | Result and remaining boundary |
| --- | --- | --- | --- |
| Tree | `Styler.Tree` applies colors/roles to stock tview nodes; hierarchy/input belong to tview/host | No shared tree | Both now have stable IDs, expansion/selection/scroll state, renderers, controls, and examples. [Tree API](tree.en.md) |
| Tabs | `Styler.Tab(button, active)` colors only; collection/closing/overflow belong to host | None | Implemented independent active/focused IDs, overflow, edited/closable indicators, request events, and public renderers. [API](workspace.en.md) |
| Panels/splitters | `Box`, `RefreshBorders`, and `Surface` styles; layout/resizing belong to tview/host | `Styles::block(title, focused)` borders; host layout | Implemented titles, padding, focus/ASCII panels, column/row splits, minimum sizes, dragging/keys, compact mode and restoration |
| Status bar | `FooterButton` style only; host priorities/omission | Example Paragraph, no public status component | Implemented semantic/non-color cues, status/shortcut priority, whole-item packing and omitted counts |
| Breadcrumbs | No dedicated API | No dedicated API | Implemented stable IDs, current-location priority, ancestor omission, cell widths and navigation requests |
| Semantic styles | Actual LazyOra-derived styles plus separate candidate JSON interpretation | Candidate JSON core and Ratatui conversion | Tree uses identical candidate roles; this does not establish parity with the full Go styler |
| Terminal/validation | tcell simulations, existing bilingual PTY checks, isolated Go module | TestBackend, existing bilingual PTY checks, packaged external Cargo usage | All shared components participate in isolated imports, common specifications, twelve-palette rendering, bilingual PTY and integrated input checks |

## Principles adopted from the reference

Inspected [yelog/lazydb](https://github.com/yelog/lazydb) at pinned commit `9c54a65ba35fc594f4ff6f0e7767958563929e7e`. No implementation was copied and no database-specific types/state were imported.

- [Explorer model](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/model/explorer.rs): stable identity, expansion set, selection, and logical rows versus viewport. Tuivory accepts host-supplied flat parent-ID data instead of database catalogs.
- [Explorer/tab rendering](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/ui/mod.rs): indentation, disclosure, icons, primary/secondary hierarchy, and separate click targets. Applied to Tree and tab state, markers, overflow, and click boundaries.
- [Layout](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/ui/layout.rs): separate minimum sizes from user size preferences. Its application-specific widths are not adopted.
- [Shortcut hints](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/ui/shortcut_hints.rs): cell measurement, complete-hint packing, and omitted counts inform the implemented priority/whole-item packing rules.

## Implementation results

1. **Tree — implemented locally**: shared data/state/event specification, public Go/tview and Rust/Ratatui renderers, database-free bilingual examples, shared test cases, and external usage checks.
2. **Tabs**: separate active/focused IDs, keyboard navigation followed by confirmation, immediate click activation, close requests approved by the host, long titles and overflow. Requesting close never deletes host documents.
3. **Panels/splitters**: explicit titles, padding, focus, minimum sizes, keyboard resizing and dragging, narrow-screen alternatives; separate preferred sizes from actual layout.
4. **Status/breadcrumbs**: retain current location when shortening paths, prioritize critical status, and define contextual shortcut/message priorities and omitted counts. Apply semantic roles, non-color cues, and Unicode/ASCII conventions throughout.

Phases 1–4 now provide public Go/Rust APIs, database-free bilingual examples, related guides, and local validation. See the [integrated guide](workspace.en.md) and [examples](../examples/README.en.md). Tree is local commit 2005164; subsequent work is also saved in local commits with approval. CI/publication evidence is recorded in TVR; remote terminals and actual LazyOra/LazyBeaver integration require separate checks. TVR-7 stays open.

## 2026-10-28 follow-up

Registered [TVR-8–13](components-backlog.en.md) under TVR-7. The first [state/focus/popup foundation](focus.en.md) is included in v0.2.0, distinct from prior v0.1.0 publication. Forms, lists/search, virtual grids, feedback and layout/supporting APIs now follow TVR-9–13. A complete application Dialog/workflow remains host composition.

## TVR-9–13 result

Public Go/Rust [forms](forms.en.md), [lists/menus/search](collections.en.md), [virtual grids](grid.en.md), [notices/progress/data states](feedback.en.md), [spacing/geometry/badges/chips/help](layout.en.md) are implemented with localized catalog hosts and tests. Sort/filter/edit/copy, validation, clocks and business actions remain host-owned. Accordion/Drawer/Stepper reuse existing state and panel composition. All stages integrated through dev and are included in v0.2.0.

## TVR-17 grid configuration (0.3.0)

[Shared options/presets](grid.en.md) extend the existing Grid with Go/Rust ranges, original-value copy, numbering, columns, density, status, stale-response protection and identical comparison data. [Local validation](grid-validation.en.md) is separate from GitHub CI/tags and actual LazyOra integration.

## TVR-7 shared menus (0.3.0)

[Menu APIs](menus.en.md) add Go/Rust hierarchy, bar/back navigation, separators/disabled/shortcuts, popup placement and original-context requests. This addresses the audited gap after the user’s subsequent instruction without transferring host screen/business ownership. [Validation](../evidence/menu.en.md).
