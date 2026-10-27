# Theme candidates and reference checks

[한국어 (default)](README.md) · **English**

[lazyora-candidate.csv](lazyora-candidate.csv) contains **12 profiles × 16 roles, or 192 foreground/background pairs**, created during LazyOra design. It is neither a dump of the current deployed palette nor a standard palette for every TUI.

| Column | Meaning |
| --- | --- |
| profile | Theme and capability, e.g. dark-8 / light-256 / blackwhite-truecolor |
| role | Semantic role |
| foreground / background | Index or True Color #RRGGBB |
| reference_fg / reference_bg | RGB interpreted through the reference palette |
| contrast | Reference contrast under a regular-font model |
| target | Internal review target for the role |
| font_weight | none or bold |

```sh
python3 tools/check_palette.py design/themes/lazyora-candidate.csv
```

The checker validates required columns, duplicate roles, color ranges, reference RGB, finite target/contrast values, calculations, and the bold-to-bright model. Failures return exit code 1. It does not require every input to have exactly the bundled 192 rows, so partial role tables can also be checked.

Targets of 4.5:1 for regular text and 3:1 for focus borders are internal design references. CSV rows specify their own target. Passing does not certify whole-screen accessibility; layers, cursor, glyph width, Dim, reverse video, and behavior require separate checks.

The [shared JSON draft](../tokens/README.en.md) is generated from this CSV and read by Go/Python/Node.js/Rust. Go has a token loader and tcell style adapter; Rust has a core and optional Ratatui adapter. DTCG extensions and a complete widget SDK are not provided. CSV and draft JSON do not imply future API compatibility guarantees.
