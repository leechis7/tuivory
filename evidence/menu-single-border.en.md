# Single-border menu validation

[한국어 (default)](menu-single-border.md) · **English**

This records historical validation for this phase. See [subsequent validation](background-fix.en.md) for background and disabled-state changes.


Unreleased TVR-7 changes after 0.3.0 remove separate menu focus decoration at the user's request. Existing tags/Release assets are unchanged. [Presentation rules](../docs/menus.en.md).

- Go: MenuView and the menu bar do not add focus underlining. NewPanelView directly wrapping MenuView preserves input focus while using a single border, plain title and hint border style. Other panels retain their focus cues.
- Rust: MenuWidget/MenuBarWidget/MenuPopupWidget follow the same rule. Public focused fields remain source-compatible without adding separate menu focus decoration.
- Across 12 palettes × Unicode/ASCII, physical Go output after Show and Rust TestBackend check single borders, titles, selection styles, wide-glyph boundaries and focused/unfocused rendering.
- Actual Go/Rust bilingual PTYs exercise nested/back navigation, background key/paste blocking, caller restoration, mouse, resize and terminal exit. Ten localized UI images are refreshed.

Final local outcomes and source/image hashes are in [the results JSON](menu-single-border-results.json). No commit, publication, remote CI, release or CentOS validation is performed. Distinguish the [previous 0.3.0 menu evidence](menu.en.md).
