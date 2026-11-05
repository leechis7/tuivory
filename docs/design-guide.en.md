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
