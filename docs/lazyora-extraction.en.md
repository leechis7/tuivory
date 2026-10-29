# Extracting the first Go style package from LazyOra

[한국어 (default)](lazyora-extraction.md) · **English**

Tuivory's first language implementation extracts Go/tcell/tview styles refined in LazyOra. Application and database code are not transferred into the shared package.

## Source and preserved scope

Baseline commit: [4530a1156853fa8629a16f654f87680fe2b52e01](https://github.com/leechis7/lazyora/commit/4530a1156853fa8629a16f654f87680fe2b52e01). At capture time the source checkout had unrelated documentation edits, but these Go files had no uncommitted changes.

| Source | Extracted behavior | File SHA-256 |
| --- | --- | --- |
| [theme.go](https://github.com/leechis7/lazyora/blob/4530a1156853fa8629a16f654f87680fe2b52e01/internal/ui/theme.go) | Palettes, input/selection/button/editor styles, background-aware borders, form/modal handling | `9acafb3ef7c245d3256ebcb8c06d1a447ed6168d9efe3cd55ef3bbd30b2f42ce` |
| [style_tokens.go](https://github.com/leechis7/lazyora/blob/4530a1156853fa8629a16f654f87680fe2b52e01/internal/ui/style_tokens.go) | Theme/profile resolution, selected/edited/disabled/focus tokens | `014314dfe40e64ac5bf35e8740579b3b661717be04d2e73b6db24242c54ee4d4` |
| [widgets.go](https://github.com/leechis7/lazyora/blob/4530a1156853fa8629a16f654f87680fe2b52e01/internal/ui/widgets.go) | List and checkbox styles | `113550fd413a8e3e40c1134c369e99172a73854d767fc12477c03a1278d1fd08` |

`tuivory.NewStyles(theme, profile)` preserves source colors and calculation order. It receives explicit arguments instead of screen, user configuration, or terminal I/O. All colors are returned values; input, selection, and edited styles have independent methods.

`go/internal/widgets` styles inputs, buttons, editors, lists, checkboxes, forms, modals, and basic tables without clearing values or rebuilding widgets. `Form` owns input/read-only-description DrawFunc hooks to handle tview's color overrides on each Draw. Existing application hooks must be composed explicitly or replaced by individual styling methods.

The host owns focus cycles, modal input blocking, and application-wide widget traversal. Grid palette/state composition and syntax-role calculations are also extracted. SQL lexers, database connections, application state, and the local tview fork are excluded; stock tview is supported.

## Candidate CSV versus actual implementation

[candidate.json](../design/tokens/candidate.json) is a cross-language reference generated from design-stage CSV, not a claim to match the actual LazyOra palette. For example, the actual dark/truecolor editor background is `#242d3a`, and the button background is `#81a1c1`.

The Go playground uses the extracted palette and input/button/dropdown/grid styles mapped to 16 display roles. Success/error have no separate source color and use body text plus state wording. Shared JSON remains the candidate data. Any future move of the real implementation into shared data must resolve this difference explicitly.

## Starter template

```sh
go -C go run ./examples/starter
go -C go run ./cmd/tuivory --lang en
```

The database-free starter has a form, inputs, checkbox, buttons, and F2 theme switching; its labels remain Korean. It fixes the profile to 256 for deterministic output. A host owning the screen can pass detection through `ProfileForColors(screen.Colors(), limited)`. Playground language selection belongs to current source, not the published `v0.0.1` tag.

## Validation

The [source fixture](../go/internal/style/testdata/lazyora-styles.json) records 12 profiles × 20 colors by independently running only source palette/token functions. It is not generated from Tuivory's resolver. Tests compare all 240 values.

To recapture, supply a local checkout of the baseline commit. These commands replace fixtures and must be reviewed with source changes:

```sh
python3 tools/capture_lazyora_styles.py /path/to/lazyora
make -C go test
make -C go check
```

Checks cover 12 profiles, three-view contrast, theme round trips, selections, and modals. Form checks inspect rendered read-only-description colors and value/focus preservation. Record real terminal observations, remote CI, and publication separately.

## Additional Go coverage

The [coverage table](go-style-coverage.en.md) describes extracted calculations; the [usage guide](go-package.en.md) covers roles, states, and reapplication. In addition to 240 colors, tests compare foreground/background/attributes across 1,572 original style cases.

```sh
python3 tools/capture_lazyora_matrix.py /path/to/lazyora
```

Syntax style calculations work with stock tcell. Stock tview TextArea lacks the LazyOra fork's `SetTextStyleFunc`, so Tuivory does not reproduce that hook. Actual LazyOra integration calls Tuivory's `SyntaxStyle` from the host lexer and hooks. The template does not claim complete syntax-highlighted rendering.

Following the disabled-state refinement, Go DisabledStyle() applies the shared disabled foreground/Dim policy. The extracted Disabled field and original comparison JSON retain historical colors; separate twelve-palette output tests validate the new adapter. Explicit custom Disabled colors remain intact. [Current rules](disabled-states.en.md).
