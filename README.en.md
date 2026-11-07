# Tuivory — TUI component library

[한국어 (기본)](README.md) · **English**

Tuivory provides reusable components for terminal applications, including trees, menus, forms, dialogs, text editors, and data grids. The library handles drawing and interaction within each component. Your application composes screens, supplies data, and handles actions.

Tuivory supports Go/tview and Rust/Ratatui, with independent implementations for Python, TypeScript/JavaScript, C, C++, and Java. [Language support](docs/languages.en.md)

## Install

```sh
go get github.com/leechis7/tuivory/go@v0.12.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.12.0", features = ["ratatui"] }
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

- [Releases](docs/release-0.12.0.en.md) · [Changelog](CHANGELOG.en.md) · [Withdrawn versions](docs/withdrawn-versions.en.md)

[Attribution and license](NOTICE.en.md)
