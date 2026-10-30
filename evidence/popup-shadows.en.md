# TVR-19 popup-shadow validation

[Korean (default)](popup-shadows.md) · **English**

Uncommitted source on `codex/TVR-19-popup-shadow` after baseline `6c67262`. TVR-20 was committed at the user's request. TVR-19 has not been committed, pushed, run in remote CI or released; public 0.4.0 lacks these APIs.

Added Go `ShadowView`, Rust `ShadowWidget`/`MenuPopupWidget::shadow` and shared placement. Shadows default off, with Auto/Solid/Dim options and card-only input. Go's wrapper uses the existing `PopupShadowStyle`/`DimRegion`; neither is newly deprecated.

- Shared 32-case geometry: normal/edge/tiny/empty/offset viewport/oversized/custom offsets, plus integer extremes.
- Dark/light/monochrome × 8/16/256/True Color × four modes × Korean/CJK/emoji/combining graphemes. Go post-Show output and Rust buffers cover no Dim leakage into content, both edges, outside styles and host backdrop restoration. Also checked generic Rust widget edges and Go shadow click/focus rejection.
- Full Go race/vet, Python checks, shared data/API/docs links, Rust 1.85.1 core and 1.88.0 all features/targets/doctest/fmt/Clippy. Independent Go modules and Rust packages imported and ran all four modes.
- Sixteen PTYs: Go/Rust × Korean/English × four modes. Checked navigation, original-panel return, blocked paste, mouse, theme/profile/glyph changes, resize, exit and terminal restoration. Enabled cases cycle F6 four times; Auto cases start in ASCII.
- Generated twelve localized SVGs from real Rust widgets, each covering twelve palettes. All ten existing default-off menu SVGs remain byte-identical.
- Default `make build` Go Linux ARM64 output passes static ELF checks with no dynamic loader or DT_NEEDED. No new required Rust dependencies; no CentOS validation.

Dim is a foreground terminal attribute. SVG brightness is an approximation, not a guarantee of actual terminal rendering. It does not darken blank backgrounds and terminals may ignore it. Solid black may disappear on black surfaces; Auto uses a pattern there. Hosts own placement, closing and backdrop redraws.

[Usage and views](../docs/popup-shadows.en.md) · [Structured results](popup-shadow-results.json). Detailed local logs live under `bin/validation/TVR-19/` and are excluded from distribution.

Follow-up: reduced the default right offset from two cells to **one**, retaining one row down, following user feedback. Reran shared geometry, Go shadow race tests, five Rust popup-shadow tests, localized image generation and Go Korean/Rust English Dim PTYs. The full-suite and sixteen-PTY results above precede this width adjustment.

Final adjustment: restored the default to **two cells right and one row down** for terminal cell proportions, and softened Auto by raising its RGB channel factor from 60% to 80% of the surface. The 256-color mode quantizes to nearby gray; 8/16-color and black-surface pattern fallbacks remain unchanged. Reran shared 32-case geometry, Go shadow race/post-Show and five Rust popup-shadow tests, localized image generation and links/data checks. The one-cell adjustment above is intermediate history.
