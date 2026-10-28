# Language examples

[한국어 (default)](README.md) · **English**

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

[TVR-9: Inputs and forms](../docs/forms.en.md): `Form / FormField / FormWidget`. Public Go/Rust APIs and localized hosts; unreleased dev source.

[TVR-10: Lists, menus and search selection](../docs/collections.en.md): `ListModel / SearchPicker / ListWidget / SearchPickerWidget`. Public Go/Rust APIs and localized hosts; unreleased dev source.

[TVR-11: Tables and data grid](../docs/grid.en.md): `Grid / GridSource / GridWidget`. Public Go/Rust APIs and localized hosts; unreleased dev source.

[TVR-12: Notices, progress and data states](../docs/feedback.en.md): `NoticeQueue / Progress / DataState`. Public Go/Rust APIs and localized hosts; unreleased dev source.
