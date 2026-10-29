# Focus border validation

[한국어 (default)](focus-borders.md) · **English**

This records historical validation for this phase. See [subsequent validation](background-fix.en.md) for background and disabled-state changes.


Unreleased TVR-7 follow-up after 0.3.0. Go tview cards and ordinary popups already render double focus borders; the previous suggestion that they were single-bordered was incorrect. Align explorer/token/help border colors and document/verify a shared rule: double active area, single inactive area, single menu popup. Individual unframed controls stay unframed. Rust shared panels already support this rule.

Validate seven Go areas (input, buttons, list, grid, explorer, tokens, help) and help/preview/edit popups across twelve palettes. Inspect physical Runes/Bytes after Show at all corners and both edge directions, border colors, focus restoration and theme/resize behavior. Existing wide-glyph popup regressions remain. Rust TestBackend checks active/inactive Unicode and ASCII shared panels plus the menu exception. Update fourteen bilingual Go playground references (including explorer/grid/edit scenes).

[Results and exact hashes](focus-borders-results.json) · [Usage](../docs/playground.en.md) · [Menu follow-up](menu-single-border.en.md).

No commit, publication, remote CI, release or CentOS validation is performed. Existing 0.3.0 tags/assets remain unchanged.

An actual PTY reproduced a Go resize deadlock: reflow → Pages.HidePage → SetFocus reentered Application’s draw lock. Move page/focus changes to the UI update queue. An isolated validation-only pyte VT parser checks actual borders and resize/restoration without adding product dependencies. Preserve `smoke_playground.py --resize` as a permanent regression and wire it into CI; remote CI has not run.
