# API reference

[한국어 (default)](README.md) · **English**

0.10.0 TVR-18: [opt-in Go/Rust tab/tree drag and drop](../drag-drop.en.md), immutable host-approved movement requests, captured outside input, cancellation and keyboard alternatives. Available starting with 0.10.0.


**Includes 0.9.0 TVR-24 APIs:** [optional syntax analysis and new editing APIs](../syntax.en.md) are available since 0.9.0.

**0.10.0:** compose Go UI through `github.com/leechis7/tuivory/go` alone. Existing `/ui` and `/terminal` paths remain compatible. [Single import and name mappings](../ui-facade.en.md).

This reference follows 0.10.2 source and **includes TVR-22–26 APIs**. [Availability and migration](../controls.en.md).

Reference version: **0.10.2**. Go module: `github.com/leechis7/tuivory/go`; Rust crate: `tuivory`. Enable `ratatui` for Rust renderers and `playground` for interactive examples.

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
python3 tools/generate_api_reference.py --rust-json .cache/rust/doc/tuivory.json
python3 tools/generate_api_reference.py --rust-json .cache/rust/doc/tuivory.json --check
python3 tools/check_links.py
```

Underlying Go aliases may show internal package names; applications use public tuivory aliases. Use cargo doc for full Rust trait implementations, including Default and Widget.

```sh
cargo doc --manifest-path rust/Cargo.toml --locked --all-features --no-deps --open
```

0.8.0 TVR-26: [shared UI APIs](../ui-facade.en.md) · [Go ui](go-ui.en.md) · [Go terminal](go-terminal.en.md). Rust ui::components aliases existing renderer APIs; new InputEvent/Session/byte-span APIs are in the Rust reference.

[Syntax analysis/highlighting APIs and editor migration](../syntax.en.md): 0.9.2 TVR-24 follow-up.

[Grid workspace APIs and host approval](../grid-workspace.en.md): 0.11.0 TVR-7 source; Go/Rust API declarations below include these additions.

TVR-7 in 0.11.1: [real grid cursor and backend integration](../grid-workspace.en.md). For real cursors in 0.11.1, Go uses NewCursorScreen/NewGridView, Rust GridWidget::render_frame.

[Independent Python·TypeScript/JavaScript·C·C++·Java support](../languages.en.md): unreleased independent-component implementation work. Each implementation/runtime is independent; the existing 0.11.1 release is unchanged.

[Independent-language workspace APIs and examples](../language-workspace.en.md): tabs/panels/splits/breadcrumbs/status lines are verified in all five implementations. Other catalog ports remain in progress.

[Independent text editing API](../language-text.en.md)

[Independent forms and controls API](../language-forms.en.md)

[Independent focus scope API](../language-focus.en.md)

[Independent lists and search pickers API](../language-collections.en.md)

[Independent menu/context-menu API](../language-menu.en.md)

[Independent notices/progress/data-state API](../language-feedback.en.md)

[Independent spacing/stack and badge/chip/hint API](../language-layout.en.md)

[Independent containers and cell-copy API](../language-containers.en.md)

[Independent Surface and background API](../language-surfaces.en.md)

[Independent popup shadows and dialogs](../language-popups.en.md)

[Independent document viewing/editing API](../language-documents.en.md)
