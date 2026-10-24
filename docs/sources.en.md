# Official references and origins

[한국어 (default)](sources.md) · **English**

Initial research date: 2026-10-23. Framework APIs and versions may change; recheck official documentation when implementing an adapter. These are design references, not endorsements of this guide.

| Source | Use |
| --- | --- |
| [Textual Themes](https://textual.textualize.io/guide/design/) | Theme variables, widget styles, text/background roles |
| [Lip Gloss](https://github.com/charmbracelet/lipgloss#advanced-color-usage) | Explicit color choices for output capability |
| [Ratatui colors](https://www.ratatui.rs/examples/style/colors/) | Profile comparison in actual widgets |
| [Carbon color guidance](https://www.carbondesignsystem.com/building-blocks/foundations/color/guidelines) | Semantic tokens, layers, states |
| [DTCG 2025.10](https://www.designtokens.org/tr/2025.10/format/) | Tokens, types, aliases; this project is not a fully compatible implementation |
| [WAI keyboard guidance](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/) | Focus versus selection, navigation between/within areas |
| [WAI modal guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) | Background input blocking and focus restoration |
| [W3C use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) | Non-color meaning and contrast references |
| [xterm documentation](https://www.invisible-island.net/xterm/manpage/xterm.html) | boldColors and base foreground brightening |

This does not claim terminal implementations of web ARIA/CSS or WCAG certification. Full external documents are not reproduced; links and original application judgments are provided.

## Initial material

The initial work originated in [LazyOra](https://github.com/leechis7/lazyora) LORA-69, baseline [a38c46e](https://github.com/leechis7/lazyora/commit/a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7).

- `docs/tui-style-guide/principles.md` → shared principles.
- `docs/ui-style-palette-candidate.csv` → review theme example.
- `shell/examples/terminal-colors.sh` → terminal color sample.
- Contrast calculations in `tools/theme_audit.py` → independent palette checker.

Application widget capture harnesses, Go Oracle code, and large screen galleries were not transferred. Application checks stay distinct from independent tools, with case links provided instead. See [NOTICE](../NOTICE.en.md) for licensing and origins.
