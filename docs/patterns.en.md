# Component patterns

[한국어 (default)](patterns.md) · **English**

These are draft shared design contracts. Adapters implement framework-specific key events and focus. See the [static layout example](../examples/components.txt).

| Component | Base state | Focus and selection | Input contract |
| --- | --- | --- | --- |
| Input | Distinct label/input surface, visible value/cursor | Indicate editing position and label/border | Tab navigation; editing keys follow host keymap |
| Choice | Expansion marker `v` or `▾` | Distinguish value from open-list selection | Define open/move/confirm/cancel |
| Button | Readable foreground/background, consistent appearance | Focus and default action are separate | Arrows within group; Enter/Space per host contract |
| List/tree | Items, hierarchy, expansion | Independent selection and input focus | Internal arrow navigation, documented confirmation |
| Tab | Identify current document/area | Active tab differs from focus | Define navigate/activate/close |
| Table/grid | Separate header and body | Compose current cell/range/edited state | Separate select/copy/edit |
| Menu | Groups and submenus | Separators are not selectable | Distinguish top-level movement, entry, return |
| Modal | Opaque card, padding, title | Focus cycles within it | Block background input and restore caller focus |
| Status/error | Brief meaning and next action | Words/symbols supplement color | Details/cancel path where needed |

## State composition

Edited, selected, editing, and error states may overlap. Compose role foreground/background pairs and validate final contrast. If current-cell selection covers an edited background, retain `*` or an edited label. Markers belong to presentation, not actual values or copied data.

## Popups and terminal cells

Blank cells are part of the card. Paint the popup interior before children, and prevent half of a two-cell Korean glyph from remaining from the previous layer. Record terminal-specific width behavior.

Example spacing is two cells horizontally and one row vertically within cards, one cell between labels/inputs, and two cells between buttons. These are adjustable examples, not mandatory dimensions. In smaller windows, reduce spacing first while preserving scrolling and confirm/cancel paths.

## Per-pattern records

Record problem → roles/states → keyboard/mouse contract → limited-terminal fallback → validation scenes → known exceptions. Do not combine computed contrast and actual terminal observations into one pass marker.
