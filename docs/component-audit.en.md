# Shared UI support audit — TVR-7

[한국어 (default)](component-audit.md) · **English**

Audited local source on 2026-10-27. TVR-5 baseline commit `b67a4cb` is not published to GitHub. This audit distinguishes the starting point from the new Tree implementation; it does not declare the whole epic complete.

| Area | Go at start | Rust at start | Result and remaining boundary |
| --- | --- | --- | --- |
| Tree | `Styler.Tree` applies colors/roles to stock tview nodes; hierarchy/input belong to tview/host | No shared tree | Both now have stable IDs, expansion/selection/scroll state, renderers, controls, and examples. [Tree API](tree.en.md) |
| Tabs | `Styler.Tab(button, active)` colors only; collection/closing/overflow belong to host | None | Next: independent active/focused IDs, overflow, edited/closable indicators, event model |
| Panels/splitters | `Box`, `RefreshBorders`, and `Surface` styles; layout/resizing belong to tview/host | `Styles::block(title, focused)` borders; host layout | Next: titles, padding, minimum sizes, keyboard/mouse resizing |
| Status bar | `FooterButton` style only; host priorities/omission | Example Paragraph, no public status component | Next: status/shortcut priorities and complete-item omission |
| Breadcrumbs | No dedicated API | No dedicated API | Next: stable path items, current location, long-path omission |
| Semantic styles | Actual LazyOra-derived styles plus separate candidate JSON interpretation | Candidate JSON core and Ratatui conversion | Tree uses identical candidate roles; this does not establish parity with the full Go styler |
| Terminal/validation | tcell simulations, existing bilingual PTY checks, isolated Go module | TestBackend, existing bilingual PTY checks, packaged external Cargo usage | Tree now participates in independent imports, shared navigation contract, twelve-palette rendering, and bilingual PTY checks |

## Principles adopted from the reference

Inspected [yelog/lazydb](https://github.com/yelog/lazydb) at pinned commit `9c54a65ba35fc594f4ff6f0e7767958563929e7e`. No implementation was copied and no database-specific types/state were imported.

- [Explorer model](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/model/explorer.rs): stable identity, expansion set, selection, and logical rows versus viewport. Tuivory accepts host-supplied flat parent-ID data instead of database catalogs.
- [Explorer/tab rendering](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/ui/mod.rs): indentation, disclosure, icons, primary/secondary hierarchy, and separate click targets. Applied to Tree in this phase; tabs remain next.
- [Layout](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/ui/layout.rs): separate minimum sizes from user size preferences. Its application-specific widths are not adopted.
- [Shortcut hints](https://github.com/yelog/lazydb/blob/9c54a65ba35fc594f4ff6f0e7767958563929e7e/src/ui/shortcut_hints.rs): cell measurement, complete-hint packing, and omitted counts inform the later status-bar contract.

## Implementation sequence

1. **Tree — this phase**: shared data/state/event contract, public Go/tview and Rust/Ratatui renderers, database-free bilingual examples, contract fixtures, and external usage checks.
2. **Tabs**: separate active/focused IDs, keyboard navigation followed by confirmation, immediate click activation, close requests approved by the host, long titles and overflow. Requesting close never deletes host documents.
3. **Panels/splitters**: explicit titles, padding, focus, minimum sizes, keyboard resizing and dragging, narrow-screen alternatives; separate preferred sizes from actual layout.
4. **Status/breadcrumbs**: retain current location when shortening paths, prioritize critical status, and define contextual shortcut/message priorities and omitted counts. Apply semantic roles, non-color cues, and Unicode/ASCII conventions throughout.

Only phase 1 is implemented. Phases 2–4 APIs, implementations, and validation remain. TVR-7 stays open/in progress; these changes are committed locally/unpublished. Neither the TVR-5 commit nor earlier CI success establishes remote verification of this code.
