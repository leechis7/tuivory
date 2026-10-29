# Framework-independent TUI design principles

[한국어 (default)](principles.md) · **English**

Status: draft. These project rules generalize findings from LazyOra; they are not an externally approved universal TUI standard. See the [roadmap](roadmap.en.md) and [LazyOra proposal](https://github.com/leechis7/lazyora/blob/a38c46ed7f5d85e1fc8f823ef4bfe6fabfdb17f7/docs/ui-style-proposal.md) for sources and application examples.

## 1. Derive styles from meaning

Interpret base palette → semantic tokens → component/state. Keep token roles separate from color values.

- Body, input, hint, selection, warning, and error have distinct meanings even when rendered with the same color.
- Styles depend on theme, capability, component, state, and actual background. Define foreground and background together.
- Components do not choose RGB or ANSI indices directly. Titles and read-only form descriptions also use the correct role/surface combination.
- Application-specific uncommitted cells can extend the generic edited state. Do not put Oracle terminology into shared tokens.

Validation: change equal-valued tokens A/B to different values; only the intended regions should update. Inferring roles by tracing color values fails this requirement.

## 2. Separate theme from capability

Theme is an appearance choice; a profile describes rendering capability. A dark theme does not imply True Color.

- Baseline profiles are ANSI8, ANSI16, Indexed256, and TrueColor. Resolve monochrome separately in each.
- Record colors, keys, mouse, line drawing, and bold behavior as independent capabilities.
- Distinguish reference ANSI RGB from the user's actual palette. Do not change that palette to make checks pass.
- Limited profiles may lose less-important color distinctions; preserve action and state meanings.
- Library color approximation and readable design need separate validation.

Validation: no out-of-range indices. Record approximations and check contrast after composition.

## 3. Separate focus, selection, and edited state

Focus receives the next input; selection identifies chosen items; edited state describes data.

| State | Default representation | Alternatives and constraints |
| --- | --- | --- |
| Focus | Strong border, double line, or dedicated marker | ASCII border/marker on basic terminals |
| Selection | Readable selected foreground/background | `>` for single selection; multi-selection differs from checkbox state |
| Edited | Background or independent status marker | Keep `*` or an edited label |
| Error/warning | Semantic color and short explanation | Remain identifiable without color |
| Disabled | Disabled style and blocked action | Do not hide essential explanations using faint text |

Define composition per component. A grid can prioritize editing → current selection → edited → normal/striped backgrounds. Keep edited markers when selection covers edited color. This is an example, not a universal order.

Validation: selection and edits remain after moving focus elsewhere. Presentation markers must not contaminate original values, copy, or export data.

## 4. Keep limited-color output readable

Use reference targets of 4.5:1 for regular text and 3:1 for focus borders, with real terminal observations. These are internal review targets, not an accessibility certification.

- Check the model where Bold makes base foreground colors brighter.
- Do not represent essential body, hint, or NULL information only with Dim.
- Selection, errors, busy state, and edits remain identifiable in monochrome.
- Low-contrast colors are limited to decoration or replaced by body text. Eight-color output need not distinguish every syntax category by color.
- Assess markers and wording alongside bold, underline, and reverse video because support varies.

Validation: distinguish palette calculations, composed widget captures, and terminal observations. Do not count decorative lines and disabled items under one contrast total presented as a bug count.

## 5. Define component input handling rules

Tab/Shift+Tab moves between areas; arrows navigate within lists/groups by default. Application keymaps extend this; product-specific function keys are not a shared standard.

- Inputs expose label, field, and cursor; choices add an expansion marker.
- Buttons distinguish focus, default action, and dangerous action. Appearance changes do not change the Enter default.
- Lists/trees/tabs expose selection and keyboard position and document confirmation timing.
- Menu separators are not selectable; define submenu entry/return and top-level movement.
- Modals cycle focus internally, block background input, and restore caller focus. Outside clicks do not confirm.
- Cancellation first handles the current step, such as an open dropdown or active input. Undo follows the application's state handling rules.

Validation: essential actions work using only the keyboard. Mouse selection/confirmation semantics agree with keyboard behavior where mouse is supported.

## 6. Lay out using cells and layers

Measure display cells rather than bytes or string length. Align drawing and input order for full-screen layers and child widgets.

- Account for two-cell Korean glyphs, combining marks, and line-drawing differences. Do not directly import pixel-based CSS.
- Opaque popups paint blank cells and padding. Dropdowns handle partially covered wide glyphs without leaving old fragments.
- Small windows reduce spacing and use scrolling while preserving confirm/cancel paths.
- Provide a way to inspect truncated content. Do not cut off warnings, errors, or primary buttons.
- Cell spacing and card size are adjustable design defaults. LazyOra's two horizontal cells and one vertical row are one example.

Validation: recompute layouts at several sizes; clicks at overlapping positions reach only the front layer.

## 7. Theme changes preserve state

Reapply current tokens rather than rebuilding screens or replacing historical color values.

Validation: values, selections, scrolling, focus, and work state match before and after a theme round trip. Hidden tabs/pages have correct styles when revealed. Applying the same styles twice has the same result.

## 8. Keep evidence and exceptions with rules

Extend items using this form:

```text
ID: focus.selection.separation
Status: proposal / reference palette checked / application capture checked / real terminal observed
Problem: selection appears identical to the input target
Rule: keep selection state and focus indication independent
Applies to: lists, tabs, grids
Exception: explain input handling rules where input is itself selectable
Validation: select, move elsewhere, identify selection/focus in monochrome
Evidence: official sources + application case/capture + observed terminal information
```

Do not assign one status to the whole guide. Record validation levels separately for principles, theme values, adapters, components, and terminal observations.

## Standalone execution and static linking

All distributed language executables must run without dynamic loaders, shared libraries or separately installed language runtimes; libraries preserve host static linking. Build dependencies are allowed. Interpreter-based references remain distinct from standalone distributions. [Static distribution](static-build.en.md)
