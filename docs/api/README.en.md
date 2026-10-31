# API reference

[한국어 (default)](README.md) · **English**

This reference follows 0.7.0 source and **includes TVR-22–26 APIs**. [Availability and migration](../controls.en.md).

Reference version: **0.7.0**. Go module: `github.com/leechis7/tuivory/go`; Rust crate: `tuivory`. Enable `ratatui` for Rust renderers and `playground` for interactive examples.

- [Go public declarations](go.en.md)
- [Rust public declarations](rust.en.md)
- [Deprecations and migration](../api-lifecycle.en.md)

[Go styles and palette usage](../go-package.en.md) · [Rust package and features](../../rust/README.en.md)

## Reading the specification

Declarations specify parameter and return types; the guides below specify allowed values, defaults, errors and state/event behavior. Handle constructor error/Result values. Events request host actions; they do not execute database or business commands. Go views route tview input, while Rust models accept actions and widgets render. Hosts own global keys, cross-component focus and backdrop redraws. Defaults and error policies differ by component.

| Component | Scope |
| --- | --- |
| [Tree](../tree.en.md) | Nodes, selection, expansion, scrolling |
| [Menu](../menus.en.md) | Menu bars and context menus |
| [Workspace](../workspace.en.md) | Tabs, panels, splits, breadcrumbs, status |
| [Focus](../focus.en.md) | States, focus, popups |
| [Forms](../forms.en.md) | Input, validation, submission |
| [Collections](../collections.en.md) | Lists and search pickers |
| [Grid](../grid.en.md) | Tables, editing, range selection |
| [Feedback](../feedback.en.md) | Notices, progress, data states |
| [Layout](../layout.en.md) | Layout, density, badges, shortcut help |
| [Shadows](../popup-shadows.en.md) | Popup shadows, placement, hit areas |
| [Drawing](../overlay-drawing.en.md) | Wide glyphs and region drawing |

## Regeneration

Declarations and original comments are generated from source. Update semantic guides in both languages. Rust extraction uses Rust 1.88.0 JSON format 45; RUSTC_BOOTSTRAP below is required only for documentation extraction. Adjust the JSON path when CARGO_TARGET_DIR is customized.

```sh
RUSTC_BOOTSTRAP=1 cargo +1.88.0 rustdoc --manifest-path rust/Cargo.toml --locked --all-features --lib -- -Z unstable-options --output-format json
python3 tools/generate_api_reference.py --rust-json rust/target/doc/tuivory.json
python3 tools/generate_api_reference.py --rust-json rust/target/doc/tuivory.json --check
python3 tools/check_links.py
```

Underlying Go aliases may show internal package names; applications use public tuivory aliases. Use cargo doc for full Rust trait implementations, including Default and Widget.

```sh
cargo doc --manifest-path rust/Cargo.toml --locked --all-features --no-deps --open
```

0.7.0 TVR-26: [shared UI APIs](../ui-facade.en.md) · [Go ui](go-ui.en.md) · [Go terminal](go-terminal.en.md). Rust ui::components aliases existing renderer APIs; new InputEvent/Session/byte-span APIs are in the Rust reference.
