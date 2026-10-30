# Tuivory shared specification

[한국어 (default)](README.md) · **English**

Status: draft. Tuivory provides reusable TUI components and styles. This specification provides shared guidance for consistent themes, color profiles, and component states across packages. It and the [shared tokens](tokens/README.en.md) are language-independent; they declare neither a stable product version nor an external standard.

## Specification scope

| Area | Shared components/specification | Language adapter | Host responsibility |
| --- | --- | --- | --- |
| Color/theme | Semantic roles, foreground/background, profiles | Framework color conversion | Theme/profile choice, terminal detection, reapplication wiring |
| State | Focus/selection/edited/error/disabled composition | Widget rendering and state wiring | Originals, business state and action eligibility |
| Layout | Cell width, minimum sizes, splitting/padding inside an assigned area | Framework areas, scrolling and layers | Screen layout, order, visibility and initial sizes |
| Input | Navigation inside controls/defined scopes, modal blocking/restoration | Convert framework events into component actions | Scope order, cross-component focus and global keys/commands |

Use [principles](../docs/principles.en.md), [component patterns](../docs/patterns.en.md), and [terminal profiles](../docs/terminal-profiles.en.md) as the shared baseline rather than duplicating their specifications.

## Token interpretation

1. The host selects theme and capability (8/16/256/truecolor). `auto` is not a data profile.
2. The loader finds the palette and roles. Missing roles/profiles must not silently receive substitutes.
3. Adapters convert ANSI indices as indices and RGB as RGB. Reference RGB is for validation.
4. Widgets compose actual surfaces and states. Borders, underlines, words, and markers supplement color.
5. Reapplication preserves application values, selections, focus, and scroll.

Current JSON covers color roles and font weight only. There is no engine executing complete spacing, border, or component state definitions from JSON. The linked guides define these specifications for validation in language implementations.

## Cross-implementation validation

Each language implementation must read identical token values. `make check-consumers` compares Go/Python/Node.js across 12 palettes and 192 pairs. `make check-rust-consumers` includes Rust in the same comparison. These checks do not establish equal widget rendering or keyboard behavior.

New widget adapters need framework-specific checks for theme round trips, focus/selection separation, modal input blocking/restoration, small windows, and Korean cell handling. Record [terminal evidence](../evidence/README.en.md).

[Shared UI audit](../docs/component-audit.en.md) and [Tree specification/implementation](../docs/tree.en.md) describe this TVR-7 phase. `tree-navigation.json` defines behavior scenarios checked by Go/Rust; `tools/export_tree_cases.py` generates module-local test copies.

## Shared interaction rules

`interaction-cases.json` covers state roles/markers/action permissions, focus navigation, nested popups, restoration and invalid requests. Mirror it into Go/Rust tests with `tools/export_tree_cases.py`. The [control-state/focus/popup guide](../docs/focus.en.md) defines the specification; framework events and terminal I/O remain outside the model.

## Layout defaults

`layout-tokens.json` defines draft compact/comfortable spacing and the cell-width threshold. Go/Rust embed matching code defaults and verify mirrored test data; no external runtime file or complete JSON layout engine is introduced. [Layout API](../docs/layout.en.md).

At either horizontal overlay/shadow edge, replace intersected wide graphemes with spaces while retaining outside styles. Hosts repaint backgrounds; regressions inspect buffers after presentation. [Go implementation and validation scope](../docs/overlay-drawing.en.md).

[TVR-17 grid options, priority and original-value/host boundaries](../docs/grid.en.md): simple/data presets on one Go/Rust core; included in 0.4.0.

Follow the [component/application boundary](../docs/component-boundary.en.md). Example screens/keymaps are host choices, not a mandatory application framework.

[Shared menus](../docs/menus.en.md): Go/Rust hierarchy, bar/back navigation, shortcuts/disabled state, popup/caller-context requests and bilingual database-free hosts. Included in 0.4.0, absent from v0.2.0 tags.

[Surface/text background rules](surfaces.en.md): actual-surface plain text, explicit state backgrounds, contrast correction and binding APIs.

[Disabled states across twelve palettes](../docs/disabled-states.en.md): no ordinary disabled prefixes, gray/Dim foregrounds, blocked input and localized runnable references.

[API lifecycle, deprecation and migration](../docs/api-lifecycle.en.md) · [Public API overlap audit](../docs/api-overlap-audit.en.md): distinguish unreleased targets, replacements and first-release/removal plans.

TVR-19 in 0.5.0 adds optional popup shadows, disabled by default: `off/auto/solid/dim`, placement including the full footprint, card-only hit testing and wide-glyph boundary protection. Hosts own backdrop redraws and opening/closing. [APIs, runnable examples and 12-palette views](../docs/popup-shadows.en.md).
