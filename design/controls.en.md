# Shared surface, control, text and container specification

[Korean (default)](controls.md) · **English**

Language-neutral rules for TVR-22–25 in 0.6.0. Maintain [usage/API mappings](../docs/controls.en.md) and [shared scenarios](controls-cases.json) together. Do not require Go/tview or Rust/Ratatui types as the shared data format.

| Area | Rule |
| --- | --- |
| Surface | Fill opaque surface before children. Default border/padding zero. Repair entire graphemes crossing an edge, preserving outside styles |
| Input | Stable IDs and independent state. Disabled blocks interaction; busy blocks editing/activation; read-only permits selection/copy |
| Secrets | Raw retrieval is explicit. Model display/diagnostic projections and copy/cut never include secret plaintext |
| Text | Logical content is UTF-8. Cursor/Anchor/style ranges use extended grapheme indices and half-open ranges. Cell and byte coordinates require separate conversion |
| Editing | Selection replacement and last 128 edits of Undo/Redo. Paste normalizes to LF/spaces. Read-only/disabled edits are ignored |
| Markup | Literal by default. Explicitly parse [role]text[/] and [[ escape. Unknown/unbalanced tags fail before mutation |
| Layout | row/column/grid/layers, stable child IDs, min/max/fixed/weight tracks, spans, padding/gap. Tiny layouts remove gaps then shrink in declaration order |
| State | Resize/reflow/palette changes do not recreate content, selection, scroll or surviving focus IDs |
| Layers | Later declarations paint above earlier ones. Last visible modal blocks lower input. Drags route by capture ID, removed captures clear, closing restores the caller |
| Errors | Invalid fields/options/IDs/ranges/roles return error/Result. Failed setters preserve prior state atomically |
| Events | change/select/activate/submit/cancel/copy/cut request host work. No database, SQL, authentication, clipboard or file I/O |

Ornaments follow Unicode/ASCII and twelve palettes. ASCII never transliterates user content. Never draw partial graphemes. Map pointer/scroll viewport cells to original text coordinates. Renderer virtual canvases are limited to 65,535 cells per axis and 1,000,000 total cells. Pure geometry allows axis values up to 1,000,000 and up to 1,024 items/tracks. Go signed screen coordinates support internal clipping; shared logical fixture rectangles are nonnegative.

Current conformance implementations are Go and Rust. Stable IDs, values/events and offset units allow future idiomatic Python, JavaScript/TypeScript, C/C++ adapters. Those implementations, ABI/memory ownership and a complete backend facade remain future work.

## Values and lifetimes

Models own original text, selection and Undo history, retaining them across rendering. Event strings are values; clipboard and storage operations are never automatic. Go exposes immutable string values, while Rust raw getters borrow &str from the model. Rust widget/Styles references are borrowed for rendering and follow Rust lifetimes alongside any required &mut model reference. Go Container constructors and SetOptions/SetChildren copy configuration lists while retaining the same child component instances. Rendering callbacks run synchronously. These rules align semantics across languages; they do not define a shared C ABI or memory layout.
