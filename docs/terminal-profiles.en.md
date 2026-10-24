# Terminal capabilities and themes

[한국어 (default)](terminal-profiles.md) · **English**

User theme and rendering capability are independent inputs. The baseline comparison is Dark/Light/Monochrome × 8/16/256/True Color: 12 combinations.

| Profile | Reference representation | Considerations |
| --- | --- | --- |
| ANSI8 | Indices 0–7 | Do not rely on bright indices for essential distinctions |
| ANSI16 | Indices 0–15 | Also test base color + Bold becoming a bright foreground |
| Indexed256 | Indices 0–255 | The initial 16 colors may use the user's palette |
| True Color | RGB or explicit indices | Record capability detection and actual transport |

The reference checker uses tcell's nominal RGB for the initial 16 colors, the 16–231 color cube, and the 232–255 grayscale ramp. Emulator base colors can differ; calculated results are not measurements.

Compare both bold models: font weight only, and foreground indices 0–7 becoming 8–15. Do not assume every terminal follows either model exactly. Record reverse video, Dim, underline, and character width as separate capabilities.

TERM alone does not establish color, mouse, or extended key support. Record reported capability, terminal/version, SSH/tmux path, palette, and bold settings in the [evidence template](../evidence/README.en.md).

Product-specific function keys and database confirmation policies remain application contracts. This guide defines no new terminal input protocol.
