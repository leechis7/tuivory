# Design guide

[한국어 (default)](design-guide.md) · **English**

Shared visual and interaction rules. Hosts choose themes and terminal capabilities.

- [Principles](principles.en.md)
- [Patterns](patterns.en.md)
- [Surfaces and contrast](../design/surfaces.en.md)
- [Disabled states](disabled-states.en.md)
- [Terminal profiles](terminal-profiles.en.md)
- [Tokens](../design/tokens/README.en.md)
- [Themes](../design/themes/README.en.md)

## 0.11.0 grid state rules

[Grid workspace](grid-workspace.en.md) defines field/pending/error surfaces, permanent dirty-cell `*` cues and independent row-gutter markers. Selection/focus must not erase dirty identity. Row `Edited` no longer colors unrelated cells. Pinned/ordinary column areas are disjoint and clipped on narrow terminals; visibility/order/state use stable IDs. Hosts own permission, typed NULL values, approval/transactions, global search and persistent storage. All themes/color depths and ASCII/Unicode use existing semantic roles. [Shared controls rules](../design/controls.en.md).

## Real grid cursor (0.11.1)

The editor buffer contains no synthetic caret character. Share grapheme viewport geometry across text, mouse and local cursor projection. Focused views own only position/visibility; NULL, pending, clipping, invalidation and blur suppress stale cursors. Go uses NewGridView with NewCursorScreen/PreserveCursorTty to remove backend default shape/blink controls. Rust uses GridWidget::render_frame; buffer-only Widget cannot register a terminal cursor. Hosts retain global focus/layer choice. [Integration and evidence](grid-workspace.en.md).

[Independent Python·TypeScript/JavaScript·C·C++·Java support](languages.en.md): unreleased independent-component implementation work. Each implementation/runtime is independent; the existing 0.11.1 release is unchanged.

Drag previews preserve source data, selection and expansion. Feedback keeps the actual background and uses bold/underline; ! identifies rejection. Theme/layout/focus changes cancel capture, and final moves require host approval.
