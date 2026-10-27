# Tuivory Rust package

[한국어 (default)](README.md) · **English**

TVR-5 provides a shared candidate-token/style core, optional Ratatui adapter, and database-free interactive example. The default core requires Rust 1.85+ (verified with 1.85.1); the Ratatui 0.30.2 adapter and Crossterm 0.29 example require Rust 1.88+ (verified with 1.88.0). The core and adapter do not depend on Go, terminal I/O, or databases.

## Usage

Version 0.1.0 is distributed through Git tag `rust/v0.1.0`, not crates.io. Use a Git dependency or a local path to rust/:

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.1.0" }
# Add features = ["ratatui"] for the optional adapter.
```

```toml
[dependencies]
tuivory = { path = "/path/to/tuivory/rust" }
```

```rust
use tuivory::{Color, ColorProfile, Theme, TokenDocument};

fn main() -> Result<(), tuivory::Error> {
    let document = TokenDocument::candidate()?;
    let palette = document.palette(Theme::Dark, ColorProfile::Indexed256)?;
    let selection = palette.style("selection")?;
    assert!(matches!(selection.foreground, Color::Indexed(_)));
    Ok(())
}
```

## Available scope

- `Theme`: dark/light/blackwhite. `ColorProfile`: 8/16/256/truecolor.
- `profile_for_colors(count, limited)`: selects from host-reported capability with the same thresholds as Go; it does not detect the terminal.
- `TokenDocument::candidate()`: loads shared JSON embedded in the crate.
- `TokenDocument::from_json()`: validates format, roles, profiles, color ranges, reference RGB, weight, fields, and duplicate keys.
- `tokens()`: independent raw palette. `palette()` and `style(role)`: foreground/background/weight values preserving ANSI indices versus RGB.
- Twelve palettes, 192 pairs, and 16 semantic roles, including selection, button focus, disabled, edited, warning, and error. Missing roles or palettes return errors instead of silent substitutes.

Shared candidate JSON is distinct from the actual LazyOra-derived Go styles. This crate does not claim parity with the entire Go widget styler. The host owns data, focus, selection, scrolling, and events. Shared complex components such as trees and tabs belong to TVR-7; actual LazyBeaver application integration has not been validated.

## Ratatui integration

Enable the optional feature with Rust 1.88+. Default features have no framework dependency. The `ratatui` feature does not force a terminal backend.

```toml
[dependencies]
tuivory = { path = "/path/to/tuivory/rust", features = ["ratatui"] }
ratatui = { version = "0.30.2", default-features = false }
```

```rust
use tuivory::{ColorProfile, Theme};
use tuivory::ratatui::Styles;

fn main() -> Result<(), tuivory::Error> {
    let styles = Styles::new(Theme::Dark, ColorProfile::Indexed256)?;
    let selection = styles.role("selection")?;
    let panel = styles.block("Panel", true)?;
    Ok(())
}
```

`Styles::from_palette()` accepts a validated custom palette. `role()` returns a Ratatui Style; `block(title, focused)` applies role colors and double borders when focused. Core Color/Style `Into` conversions preserve ANSI indices, RGB, and bold. Replace Styles on theme changes while retaining host widget state.

Inputs, lists, tables, and modals are host code in the [interactive example](../docs/rust-playground.en.md), rather than reusable widget APIs.

## Example and validation

Run from the repository root. The example prints JSON without ANSI control codes or terminal configuration changes.

```sh
cargo run --manifest-path rust/Cargo.toml --locked --example tokens -- dark 256
make test-rust
make check-rust
make check-rust-consumers
python3 tools/check_rust_module.py
```

Run adapter and interactive checks separately with Rust 1.88+:

```sh
make test-rust-ui check-rust-ui
python3 tools/check_rust_module.py --ratatui
make run-rust ARGS="--lang en"
make build-rust
./bin/rust/tuivory-linux-arm64 --lang en
```

`make build-rust` produces one Linux ARM64 executable and requires the Linux ARM64 GNU target toolchain/linker. It was validated on a Linux ARM64 host. Default `make build` still produces only Go. See [English views and controls](../docs/rust-playground.en.md).

`make check-rust-consumers` compares Go/Python/Node.js/Rust against the shared tokens and requires those tools. `make check-consumers` retains the existing Go/Python/Node.js check. Install format/lint components with `rustup component add rustfmt clippy`.

The isolated check copies only rust/, builds a Cargo package, then builds/runs an external path-dependent project against that package. `--ratatui` also checks TestBackend rendering in the external project. This does not validate crates.io downloads. Validation executables stay in temporary directories. Local state/rendering checks and Korean/English PTY startup, Ctrl+Q exit, and screen restoration passed; remote terminals and GitHub CI have not been run.

Shared sources live in [design/tokens](https://github.com/leechis7/tuivory/blob/main/design/tokens/README.en.md). `src/data/candidate.json` is generated by `python3 tools/export_tokens.py`; do not edit it manually. `include_str!` bundles it so external Rust projects need neither design/ nor generation tools.

Cargo version 0.1.0 retains `publish = false` for Git distribution. It is not published to crates.io. [License](LICENSE) · [Origin notice](NOTICE.en.md)

## Shared Tree

`tuivory::tree::{Tree, TreeNode, TreeState, TreeAction, TreeEvent}` works without a framework on Rust 1.85+. Optional `tuivory::ratatui::TreeWidget` requires Rust 1.88+. It shares stable-ID expansion, selection, scroll, and event contracts with Go and renders icons, secondary text, counts, and Unicode/ASCII alternatives. [Tree guide](../docs/tree.en.md) · [Support audit](../docs/component-audit.en.md). Run `make run-tree-rust ARGS="--lang en"` from the root. These TVR-7 changes are included in `rust/v0.1.0`.

## Shared workspace components

The [tabs, panels, splitters, status, and breadcrumbs guide](../docs/workspace.en.md) documents public Go/Rust APIs and shared control/color/state principles. Run database-free bilingual integrated examples with `make run-workspace-go ARGS="--lang en"` or `make run-workspace-rust ARGS="--lang en"` from the root. These APIs are included in `go/v0.1.0` and `rust/v0.1.0`; CI evidence and actual application integration are distinguished in [work tracking](https://leechis7.atlassian.net/browse/TVR-7).
