# Tuivory — TUI component library

[한국어 (default)](README.md) · **English**

Reusable TUI components for **Go/tview and Rust/Ratatui**. Hosts compose screens, supply data and execute actions. Python/JavaScript currently provide token-reading examples; reusable UI packages are planned.

**0.7.0** · [Release](docs/release-0.7.0.en.md) · [Documentation](docs/README.en.md) · [API](docs/api/README.en.md)

## Install

```sh
go get github.com/leechis7/tuivory/go@v0.7.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.7.0", features = ["ratatui"] }
```

Go 1.24+, Rust core 1.85+, Rust UI 1.88+. [Installation details](docs/installation.en.md)

## Try examples

```sh
make run
make run-menu-go ARGS="--shadow auto"
make run-menu-rust ARGS="--shadow auto"
```

Korean is the default UI; add `--lang en` for English.

![Tuivory](docs/images/playground-dark-en.svg)

## Documentation

- [Installation](docs/installation.en.md)
- [Component guides](docs/components.en.md)
- [API reference](docs/api/README.en.md)
- [Design guide](docs/design-guide.en.md)
- [Responsibilities](docs/component-boundary.en.md)
- [Development and history](docs/development.en.md)

[Attribution and license](NOTICE.en.md)

0.6.0 TVR-22–25 adds borderless Surface, standalone/secret controls, text editing/viewing and row/column/grid/layer containers. [Usage, source availability and examples](docs/controls.en.md).

0.7.0 TVR-26 adds SDK-only Go/Rust UI composition, shared input/byte-span conversion and terminal lifetime. [API mappings, examples and availability](docs/ui-facade.en.md).
