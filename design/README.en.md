# Tuivory shared specification

[한국어 (default)](README.md) · **English**

Status: draft. Tuivory provides reusable terminal UI styles. This specification is an internal contract for consistent themes, color profiles, and component states across packages. It and the [shared tokens](tokens/README.en.md) are language-independent; they declare neither a stable product version nor an external standard.

## Contract boundaries

| Area | Shared contract | Language adapter/application responsibility |
| --- | --- | --- |
| Color | Semantic roles, foreground/background pairs, explicit profiles | Framework conversion and terminal detection |
| Theme | Shared roles, dark/light/blackwhite reference candidates | User-theme loading and whole-screen reapplication |
| State | Focus, selection, edited, error, disabled meanings | Widget composition order and contrast on actual surfaces |
| Layout | Terminal cells, Korean width, small windows | Measurement, scrolling, and layers in each framework |
| Input | Tab between areas, modal focus trapping/restoration | Key conversion, application keymaps and actions |

Use [principles](../docs/principles.en.md), [component patterns](../docs/patterns.en.md), and [terminal profiles](../docs/terminal-profiles.en.md) as the shared baseline rather than duplicating their contracts.

## Token interpretation

1. The host selects theme and capability (8/16/256/truecolor). `auto` is not a data profile.
2. The loader finds the palette and roles. Missing roles/profiles must not silently receive substitutes.
3. Adapters convert ANSI indices as indices and RGB as RGB. Reference RGB is for validation.
4. Widgets compose actual surfaces and states. Borders, underlines, words, and markers supplement color.
5. Reapplication preserves application values, selections, focus, and scroll.

Current JSON covers color roles and font weight only. There is no engine executing complete spacing, border, or component state definitions from JSON. The linked guides define these contracts for validation in language implementations.

## Cross-implementation validation

Each language implementation must read identical token values. `make check-consumers` compares Go/Python/Node.js across 12 palettes and 192 pairs. `make check-rust-consumers` includes Rust in the same comparison. These checks do not establish equal widget rendering or keyboard behavior.

New widget adapters need framework-specific checks for theme round trips, focus/selection separation, modal input blocking/restoration, small windows, and Korean cell handling. Record [terminal evidence](../evidence/README.en.md).

[Shared UI audit](../docs/component-audit.en.md) and [Tree contract/implementation](../docs/tree.en.md) describe this TVR-7 phase. `tree-navigation.json` defines behavior scenarios checked by Go/Rust; `tools/export_tree_cases.py` generates module-local test copies.
