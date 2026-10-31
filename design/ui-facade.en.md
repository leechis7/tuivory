# Shared UI API rules

[Korean (default)](ui-facade.md) · **English**

Shared UI specification for 0.8.0 TVR-26. Go/Rust are implemented; Python, JavaScript/TypeScript and C/C++ are future adapters. Maintain [API/migration mappings](../docs/ui-facade.en.md) and [input/offset scenarios](ui-input-cases.json) together.

**0.8.0:** compose Go UI through `github.com/leechis7/tuivory/go` alone. Existing `/ui` and `/terminal` paths remain compatible. [Single import and name mappings](../docs/ui-facade.en.md).

## Responsibilities and layers

| Layer | Shared rule | Go | Rust |
| --- | --- | --- | --- |
| Models/events | Stable IDs, original data, selection, state, requests | Root package | collections/forms/text etc. |
| Controls/surfaces/layout | Drawing, internal interaction, constraints, clipping, input/modal isolation | Root component Views | ui::components widgets |
| Application/widget compatibility | Preserve pinned SDK backend type/method identity | root (compatibility: go/ui) | ui Terminal/Frame and child modules |
| Terminal compatibility | Screens, keys/pointers, styles, explicit terminal I/O | root (compatibility: go/terminal) | ui::terminal and Session |
| Host policy | Screen structure, cross-component focus order, global keys, database/business/clipboard execution | Host | Host |

Reuse [component rules](controls.en.md), [Tree](../docs/tree.en.md), [surfaces](surfaces.en.md), [state/focus](../docs/focus.en.md), menu and shadow specifications. Shared values are not defined by backend structures or lifetime syntax. Compatibility aliases do not promise source/binary interchangeability across backend replacements. Preserve existing APIs/methods/traits without requiring identical Go/Rust function names.

## Shared input values

InputEvent contains kind and optional key/text/modifiers/phase/x/y/button/width/height. JSON scenarios check semantics; they do not define a network protocol or C memory layout.

- kind: key, pointer, paste, resize, focus. Positions and sizes are screen cells with top-left origin. Subtract content origins and add virtual scroll offsets when routing locally.
- key: enter/escape/tab/backspace/delete/insert/left/right/up/down/home/end/page_up/page_down/f1… or the input character. Ctrl letters use lowercase keys plus a ctrl modifier.
- Ordered modifiers: shift, ctrl, alt, meta. Rust Super/Meta maps to meta. Raw UTF-8 text is preserved; editing models normalize pasted text.
- Key phase is press/repeat/release. Go tcell reports presses and repeated events; Rust only knows phases reported by the terminal. Collapsed combinations such as Tab/Ctrl+I and Enter/Ctrl+M cannot be reconstructed.
- Pointer phases: down/up/move/drag/scroll_up/scroll_down/scroll_left/scroll_right; buttons: left/right/middle/none. Preserve Go widget click/double_click events. Do not infer click counts from Rust raw events or invent unsupported movement/button/focus reports.
- EditingAction maps Ctrl+A/C/X/Z/Y, movement/selection/newline/scrolling/text/paste to model requests. Release and unknown Ctrl combinations do not edit. Forms may map Enter to activate; hosts process global bindings first.
- Raw input precedes secret-field handling and contains user data. Secret protection applies to model masking/diagnostic projections; the library does not automatically log input.

## Original text and highlighting

Original content is UTF-8; Cursor/Anchor/default SyntaxSpan use half-open grapheme indices. GraphemeIndex/grapheme_index accepts exact byte boundaries and rejects offsets inside combining/CJK/emoji clusters. SetByteSyntax/set_byte_syntax indexes boundaries once, converts and validates complete lexer ranges before applying them atomically. Errors retain previous highlighting. Hosts retain lexing, SQL interpretation and execution.

## Lifetimes and execution

Go strings/events are values and child components retain instance identity. Rust raw getters borrow &str from models and widgets borrow for rendering. Callbacks are synchronous; hosts update models on their UI execution flow or queue worker results. SDKs do not execute database/authentication/file/clipboard business operations.

Hosts explicitly choose terminal lifetime. Rust's terminal-feature Session configures/restores raw/alternate-screen/mouse/paste state. Duplicate entry and entry while another controller owns raw mode fail; finish/Drop releases state, including initialization failures and panic unwind. Forced termination/abort cannot guarantee Drop. Go Application preserves Run/Stop/SetScreen and callback behavior. Apply global style/border setters before the event loop.

## Future languages and compatibility

| Language | Planned integration | Separate decisions/implementation |
| --- | --- | --- |
| Python | Python package, model/value/event APIs and terminal adapter | Object/buffer lifetimes and supported runtimes |
| JS/TS | npm package, typed events and asynchronous terminal adapter | Node runtime and Promise/worker queue integration |
| C/C++ | Opaque handles, length-delimited UTF-8, explicit results/releases, C++ RAII | ABI versions, integer ranges, allocator ownership, callback/thread rules |

These are not implemented. FFI should use copies/explicit ownership rather than exposing borrowed Rust/Go pointers as a shared ABI. New adapters must conform to shared ID/state/input/width/offset/layout scenarios. Document model changes separately from compatibility adapters and follow the [API lifecycle policy](../docs/api-lifecycle.en.md).
