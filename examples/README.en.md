# Language examples

[한국어 (default)](README.md) · **English**

**0.8.0:** compose Go UI through `github.com/leechis7/tuivory/go` alone. Existing `/ui` and `/terminal` paths remain compatible. [Single import and name mappings](../docs/ui-facade.en.md).

The library owns component rendering/internal interaction; hosts own real screens, global keys, cross-component focus and business bindings. Examples are optional compositions, not required screen templates. [Component/application boundary](../docs/component-boundary.en.md).

Implementation code lives inside each language directory. This directory indexes examples and a shared static layout.

| Language | Example | Available scope |
| --- | --- | --- |
| Go | [Starter](../go/examples/starter/main.go), [tokens](../go/examples/tokens/main.go) | Working Go style API and runnable playground |
| Rust | [Token reader](../rust/examples/tokens.rs), [playground](../docs/rust-playground.en.md) | JSON validation, color/style core, Ratatui adapter, bilingual interactive host |
| Python | [Token reader](../python/examples/read_tokens.py) | Data example; no UI package |
| JavaScript | [Token reader](../javascript/examples/read-tokens.mjs) | Data example; no UI package |
| Shell | [ANSI sample](../shell/examples/terminal-colors.sh) | Reference output; no style function package |

The [static component layout](components.txt) is language-independent reference material. The starter and static layout have Korean example labels; the current [playground](../docs/playground.en.md) supports `--lang en`.

## Executable locations

Example sources remain in their language directories. Put compiled playground executables in `bin/<language>/`, with OS and architecture in each filename. Currently, `make build` produces only `bin/go/tuivory-linux-arm64`. From the repository root, run `./bin/go/tuivory-linux-arm64 --lang ko` or `--lang en`.

With Rust 1.88+, run the Rust playground using `make run-rust ARGS="--lang en"`. `make build-rust` produces one `bin/rust/tuivory-linux-arm64`. The default core/JSON example requires Rust 1.85+ and runs with `cargo run --manifest-path rust/Cargo.toml --locked --example tokens -- dark 256`. Python, JavaScript, and Shell examples run from source by default; executable packaging can be decided when needed. Git ignores `bin/`.

## Shared Tree examples

[Go source](../go/examples/tree/main.go) · [Rust source](../rust/examples/tree/main.rs) · [Bilingual guide](../docs/tree.en.md). Run `make run-tree-go ARGS="--lang en"` or `make run-tree-rust ARGS="--lang en"` from the root. Both demonstrate the same database-free data/controls without extending the default product build.

## Shared workspace components

The [tabs, panels, splitters, status, and breadcrumbs guide](../docs/workspace.en.md) documents public Go/Rust APIs and shared control/color/state principles. Run database-free bilingual integrated examples with `make run-workspace-go ARGS="--lang en"` or `make run-workspace-rust ARGS="--lang en"` from the root. These APIs are included in `go/v0.1.0` and `rust/v0.1.0`; CI evidence and actual application integration are distinguished in [work tracking](https://leechis7.atlassian.net/browse/TVR-7).

## Control states, focus and nested popup hosts

[Go source](../go/examples/focus/main.go) · [Rust source](../rust/examples/focus/main.rs) · [Guide](../docs/focus.en.md). Run `make run-focus-go ARGS="--lang ko"` or `make run-focus-rust ARGS="--lang en"`. Hosts exercise read-only/busy/disabled navigation, nested popups, input routing/restoration and localized views. Default product builds are unchanged.

[TVR-9: Inputs and forms](../docs/forms.en.md): `Form / FormField / FormWidget`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

[TVR-10: Lists, menus and search selection](../docs/collections.en.md): `ListModel / SearchPicker / ListWidget / SearchPickerWidget`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

[TVR-11: Tables and data grid](../docs/grid.en.md): `Grid / GridSource / GridWidget`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

[TVR-12: Notices, progress and data states](../docs/feedback.en.md): `NoticeQueue / Progress / DataState`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

[TVR-13: Layout, density and supporting components](../docs/layout.en.md): `SpacingTokens / StackLayout / Badge / Chip / Help`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

See [overlay drawing](../docs/overlay-drawing.en.md) for Go popup/external-card usage. Existing playground popups/Choice and the focus example PanelView use the shared repair.

[TVR-17 grid comparison](../docs/grid.en.md): `make run-catalog-go ARGS="--mode grid --grid-sample --grid-preset data --lang en"`. Use `run-catalog-rust` for Rust or `--grid-preset simple` for the simple presentation. Both use the same five rows and row 2 name selection. TVR-17 is included in public releases.

[Host composition](../docs/component-boundary.en.md): pass `--layout rows --focus-order content,tree,tabs --quit-key ctrl-x` to the existing workspace. Both default and alternative hosts use the same public Go/Rust components; host options are included in public releases.

[Shared menus](../docs/menus.en.md): Go/Rust hierarchy, bar/back navigation, shortcuts/disabled state, popup/caller-context requests and bilingual database-free hosts. Included in public releases since 0.5.0.

[Controls, surfaces, editor and containers](../docs/controls.en.md): Go/Rust controls examples, available since 0.6.0.

0.8.0 Go/Rust examples use Tuivory SDK paths without direct backend imports; commands and visual output are retained. [New APIs, migration and availability](../docs/ui-facade.en.md).
