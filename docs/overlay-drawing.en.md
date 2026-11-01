# Wide glyphs and overlay drawing — TVR-14

[한국어 (default)](overlay-drawing.md) · **English**

When CJK or emoji cross Go/tcell popup, card, drop-down or shadow edges, a border present in the logical buffer can disappear after `Show()`, or an older hidden character can reappear. Clipping text alone does not repair underlying wide-glyph starts and continuation cells.

Go v0.2.0 exposes `WideSafeScreen` and `DimRegion` to repair these boundaries. This change targets Go/tcell; it does not establish Rust/Ratatui API support or validation. No mandatory native library or runtime dependency is added.

## Host usage

```go
// The host initializes and owns screen (a tcell.Screen).
// Each frame draws the background, shadow, then card.
background.Draw(screen)
tuivory.DimRegion(screen, tuivory.CellRect{
    X: cardX + 1, Y: cardY + 1, Width: cardWidth, Height: cardHeight,
})
card.SetRect(cardX, cardY, cardWidth, cardHeight)
card.Draw(tuivory.WideSafeScreen(screen))
screen.Show() // Do not call twice if tview Application owns presentation.
```

Pass the wrapper to the **entire Draw call**, including the card border and content. Use that screen for direct cell writes too. `SetContent`, `SetCell`, `Put`, `PutStr` and `PutStrStyled` all apply the same repair. `Put` separates the first grapheme from remaining text, preserving combining characters and ZWJ emoji. A wide glyph that cannot fit at the last screen column becomes a one-cell space; the returned width is the one cell actually stored. Out-of-bounds writes are ignored. Widgets/hosts still own card content clipping and text omission.

Both cells of an intersected old wide glyph become spaces. If its start lies just outside the left edge, or its continuation lies just outside the right edge, that outside cell is cleared too, retaining its original style. New continuation cells are normalized so stale content cannot reappear later. Unaffected neighboring glyphs survive.

`DimRegion(screen, rect)` applies Dim to the screen-clipped rectangle. It preserves fully contained graphemes and replaces entire wide glyphs crossing either horizontal edge with spaces. Outside styles remain unchanged. Card and shadow boundaries are separate: draw the shadow, then draw the card through the safe screen. Shadows composed of two strips can call it for each rectangle.

`PanelView`, the open list of public `Choice`, and Go playground popups/choices already use the shared repair. Wrap cards built from external tview widgets as above. Wrapping an already-safe screen returns that screen. The wrapper forwards terminal initialization, input, `Show` and `Sync` to the original screen and creates no event loop.

**Repaint the background from host data** when closing, moving or resizing a popup. This API neither saves background snapshots nor automatically restores clipped text. Call it on the UI drawing goroutine, as with tview; multi-cell repairs are not concurrent transactions.

## Repainting table backgrounds and selection

The TVR-7 follow-up preserves text when a table reads a cell with `GetContent` and writes the same text with `SetContent` to change only its background, foreground or attributes. `Get`/`Put` follow the same rule. Restyling a wide continuation updates the entire grapheme instead of erasing CJK, ZWJ emoji, flags or combining characters. This applies only to an immediate repaint whose read coordinates, text and style are still current.

Writing different text or a border retains the existing overlap repair at both edges. Write a space without a preceding read, or call `safe.SetCell(x, y, style)` with no characters, to explicitly erase. Calls to `Show`, `Sync`, `Clear` and `Fill` through the wrapper discard its preceding read. Use `Table.Draw(WideSafeScreen(screen))` or wrap the table in `SurfaceView`/`ShadowView`; no application-local table rendering workaround is required.

Across languages, style updates must preserve source text while actual replacements repair intersected wide glyphs. This defect and fix concern Go/tcell. Separate twelve-palette selection/redraw regressions verify the existing Rust Table → SurfaceWidget → ShadowWidget path; they do not claim the same Rust defect was reproduced.

## Validation

TVR-7 follow-up: Go checks twelve palettes across safe-screen/Surface/Shadow combinations, selection 0→1→0, Show/Sync, and actual output runes/bytes, foreground/background and attributes. Explicit blank erasure and stale-read invalidation are also covered. Rust passes twelve-palette wrapped-Table selection/redraw and existing shadow-boundary tests. An independent host provides 24 initial and 24 post-selection bilingual PTY screens verifying original text, selection changes, splitter/separator contrast and normal exit. [Local validation record](evidence/tvr7-lazyora-rendering-results.json). This local record is historical pre-release evidence; final CI/publication checks are recorded in the [0.9.2 release](release-0.9.2.en.md) asset manifest. CentOS is not checked.

`go/drawing_test.go` inspects **output Runes and Bytes from `GetContents()` after `SimulationScreen.Show()`**. Testing only `GetContent()` misses borders omitted during presentation. Coverage includes:

- CJK, simple/ZWJ/flag emoji, all five positioned writing APIs, both edges, stale continuations and unaffected neighbors.
- Background redraw, popup reopening, multiple frames, `Sync`, overlapping wide-glyph replacement, combining marks and screen edges.
- Both shadow edges, interior graphemes, outside styles, negative/off-screen/extreme rectangle clipping.
- Shadows across dark/light/blackwhite × 8/16/256/truecolor and Unicode/ASCII panel borders.
- Actual focused Go playground popup borders and open `Choice` list output after `Show()`.

```sh
make test check
python3 tools/check_go_module.py
```

The external single-import check also calls both APIs and inspects output after `Show()`. These are tcell simulation results, not customer-server, SSH or physical-terminal/font validation. Track commit, remote CI and publication separately in TVR-14.

[Go API](go-package.en.md) · [Popup focus](focus.en.md) · [Playground](playground.en.md)

TVR-19 in 0.5.0 adds optional popup shadows, disabled by default: `off/auto/solid/dim`, placement including the full footprint, card-only hit testing and wide-glyph boundary protection. Hosts own backdrop redraws and opening/closing. [APIs, runnable examples and 12-palette views](popup-shadows.en.md).

0.6.0 TVR-22–25 adds borderless Surface, standalone/secret controls, text editing/viewing and row/column/grid/layer containers. [Usage, source availability and examples](controls.en.md).
