# Unified example executables

[한국어 (default)](examples.md) · **English**

**0.10.2 TVR-29:** [Compact popup shadows](popup-shadows.en.md) now use one cell right and half a row down with stronger dark-theme contrast. Available in 0.10.2.

**0.9.1 TVR-27 change:** Go/Rust examples share one executable per language. Release archives use this layout starting with 0.9.1.

```sh
make build                 # one Go executable
make build-rust            # one Rust executable
```

The builder detects the Linux server's CPU architecture. ARM64 servers produce only `bin/go/tuivory-linux-arm64` and `bin/rust/tuivory-linux-arm64`. x86_64 servers produce `tuivory-linux-x86_64` in the same directories. There is no cross compilation. After the new executable passes static ELF inspection, obsolete example and other-architecture binaries for that language are removed. Historical release archives and validation records are preserved.

Requires Go 1.24+, Rust examples 1.88+, and Python 3. Rust uses the musl standard library **matching the host** and rustup's bundled rust-lld. Install it once with `rustup target add aarch64-unknown-linux-musl` on ARM64 or `rustup target add x86_64-unknown-linux-musl` on x86_64.

Examples on the current ARM64 server:

```sh
./bin/go/tuivory-linux-arm64 --list
./bin/go/tuivory-linux-arm64 --demo tree --lang ko
./bin/rust/tuivory-linux-arm64 --demo syntax --lang en
./bin/rust/tuivory-linux-arm64 --demo catalog --mode grid --grid-preset data
./bin/go/tuivory-linux-arm64 --demo menu --ascii --shadow auto
./bin/go/tuivory-linux-arm64 --demo controls --help
```

| `--demo` | View |
| --- | --- |
| `playground` | Original theme/widget playground, default |
| `tree` | Tree navigation |
| `workspace` | Tabs, panels, splits and status bar |
| `focus` | States, focus and nested popups |
| `catalog` | Forms, collections, grid, feedback and layout (`--mode`) |
| `menu` | Menus, context menus and shadows |
| `controls` | Inputs, buttons, surfaces, editors and containers |
| `syntax` | Oracle SQL/PLSQL highlighting and editing |

Choose the UI language with `--lang ko|en`. Without `--demo`, the original playground starts. Use `--demo NAME --help` for example options. All demos are included in the same executable and require no separate demo executable, source checkout or language runtime at execution time. No DB or real clipboard connection is performed.

Source commands such as `make run-tree-go` and `make run-syntax-rust` remain available. `make run ARGS="--demo tree --lang ko"` and `make run-rust ARGS="--demo syntax --lang en"` run the unified entrypoints from source. Python, JavaScript and Shell references continue to run from source.

Static ELF inspection and bilingual unified-executable checks:

```sh
python3 tools/check_showcase.py bin/go/tuivory-linux-arm64 bin/rust/tuivory-linux-arm64
python3 tools/snapshot_tree.py bin/rust/tuivory-linux-arm64 --demo tree --output .cache/validation/tree-images
```

[Example sources](examples.en.md) · [Static distribution](static-build.en.md) · [Local validation record](evidence/showcase-results.json). Passed 24 bilingual PTY scenarios per language, static ELF checks and 20 unchanged reference images. Remote CI/publication, x86_64 execution and CentOS validation were not performed.


Go is the reference for the examples. Rust also provides the default playground navigation, theme/color selectors, password, disabled button, and focus order. Tree title/button alignment and SQL editor padding/pointer coordinates follow Go. Both unified executables accept value options such as `--lang=en`, `--theme=light`, and `--colors=16`. Terminal backends and automatic color detection remain language-specific, so actual terminal output can vary. [Rust screens and controls](rust-playground.en.md).

## Example sources and component guides

The library owns component rendering/internal interaction; hosts own real screens, global keys, cross-component focus and business bindings. Examples are optional compositions, not required screen templates. [Component/application boundary](component-boundary.en.md).

Implementation code lives inside each language directory. This guide indexes examples and a shared static layout.

| Language | Example | Available scope |
| --- | --- | --- |
| Go | [Starter](../go/examples/starter/main.go), [tokens](../go/examples/tokens/main.go) | Working Go style API and runnable playground |
| Rust | [Token reader](../rust/examples/tokens.rs), [playground](rust-playground.en.md) | JSON validation, color/style core, Ratatui adapter, bilingual interactive host |
| Python | [Token reader](../python/examples/read_tokens.py) | Data example; no UI package |
| JavaScript | [Token reader](../javascript/examples/read-tokens.mjs) | Data example; no UI package |
| Shell | [ANSI sample](../shell/examples/terminal-colors.sh) | Reference output; no style function package |

The [static component layout](examples-components.txt) is language-independent reference material. The starter and static layout have Korean example labels; the current [playground](playground.en.md) supports `--lang en`.


## Shared Tree examples

[Go source](../go/examples/tree/main.go) · [Rust source](../rust/examples/tree/main.rs) · [Bilingual guide](tree.en.md). Run `make run-tree-go ARGS="--lang en"` or `make run-tree-rust ARGS="--lang en"` from the root. Both demonstrate the same database-free data/controls through `--demo tree` in the unified executable.

## Shared workspace components

The [tabs, panels, splitters, status, and breadcrumbs guide](workspace.en.md) documents public Go/Rust APIs and shared control/color/state principles. Run database-free bilingual integrated examples with `make run-workspace-go ARGS="--lang en"` or `make run-workspace-rust ARGS="--lang en"` from the root. These APIs are included in `go/v0.1.0` and `rust/v0.1.0`; CI evidence and actual application integration are distinguished in [work tracking](https://leechis7.atlassian.net/browse/TVR-7).

## Control states, focus and nested popup hosts

[Go source](../go/examples/focus/main.go) · [Rust source](../rust/examples/focus/main.rs) · [Guide](focus.en.md). Run `make run-focus-go ARGS="--lang ko"` or `make run-focus-rust ARGS="--lang en"`. Hosts exercise read-only/busy/disabled navigation, nested popups, input routing/restoration and localized views. Default product builds are unchanged.

[TVR-9: Inputs and forms](forms.en.md): `Form / FormField / FormWidget`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

[TVR-10: Lists, menus and search selection](collections.en.md): `ListModel / SearchPicker / ListWidget / SearchPickerWidget`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

[TVR-11: Tables and data grid](grid.en.md): `Grid / GridSource / GridWidget`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

[TVR-12: Notices, progress and data states](feedback.en.md): `NoticeQueue / Progress / DataState`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

[TVR-13: Layout, density and supporting components](layout.en.md): `SpacingTokens / StackLayout / Badge / Chip / Help`. Public Go/Rust APIs and localized hosts; included in 0.2.0.

See [overlay drawing](overlay-drawing.en.md) for Go popup/external-card usage. Existing playground popups/Choice and the focus example PanelView use the shared repair.

[TVR-17 grid comparison](grid.en.md): `make run-catalog-go ARGS="--mode grid --grid-sample --grid-preset data --lang en"`. Use `run-catalog-rust` for Rust or `--grid-preset simple` for the simple presentation. Both use the same five rows and row 2 name selection. TVR-17 is included in public releases.

[Host composition](component-boundary.en.md): pass `--layout rows --focus-order content,tree,tabs --quit-key ctrl-x` to the existing workspace. Both default and alternative hosts use the same public Go/Rust components; host options are included in public releases.

[Shared menus](menus.en.md): Go/Rust hierarchy, bar/back navigation, shortcuts/disabled state, popup/caller-context requests and bilingual database-free hosts. Included in public releases since 0.5.0.

[Controls, surfaces, editor and containers](controls.en.md): Go/Rust controls examples, available since 0.6.0.

0.8.0 Go/Rust examples use Tuivory SDK paths without direct backend imports; commands and visual output are retained. [New APIs, migration and availability](ui-facade.en.md).


0.9.1 TVR-28 layout: use `.cache/validation/` for logs/generated references and `.cache/releases/` for local release archives. [Repository layout](architecture.en.md).

0.10.0 TVR-18: [opt-in Go/Rust tab/tree drag and drop](drag-drop.en.md), immutable host-approved movement requests, captured outside input, cancellation and keyboard alternatives. Available starting with 0.10.0.

## 0.11.0 grid workspace

Use the existing unified binary: `--demo catalog --mode grid --grid-sample --grid-preset data --lang en`. Add `--grid-edit-preview` to start inline editing. Synthetic host approval, rejection/retry, NULL, paste, find, column management, in-memory view restore and raw details use the same example; no additional executable. [Bindings and screenshots](grid-workspace.en.md).

TVR-7 in 0.11.1: [real grid cursor and backend integration](grid-workspace.en.md). For real cursors in 0.11.1, Go uses NewCursorScreen/NewGridView, Rust GridWidget::render_frame.

[Independent Python·TypeScript/JavaScript·C·C++·Java support](languages.en.md): unreleased package/Tree verification work. Each implementation/runtime is independent; the existing 0.11.1 release is unchanged.

[Independent-language workspace APIs and examples](language-workspace.en.md): tabs/panels/splits/breadcrumbs/status lines are verified in all five implementations. Other catalog ports remain in progress.

[Independent text editing API](language-text.en.md)

[Independent forms and controls API](language-forms.en.md)
