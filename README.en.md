# Tuivory — TUI component library

[한국어 (기본)](README.md) · **English**

Tuivory provides reusable components for terminal applications, including trees, menus, forms, dialogs, text editors, and data grids. The library handles drawing and interaction within each component. Your application composes screens, supplies data, and handles actions.

Tuivory supports Go/tview and Rust/Ratatui, with independent implementations for Python, TypeScript/JavaScript, C, C++, and Java. [Language support](docs/languages.en.md)

## Install and run an example

Download the wheel, npm archive, SDK or JAR for your language. The commands below assume the download is in your current directory. [Download release assets](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.5)

### Go

Go 1.24+. Import `github.com/leechis7/tuivory/go`. The example command runs from a Tuivory source checkout. [Go guide](go/README.en.md)

```sh
go get github.com/leechis7/tuivory/go@v0.12.5
```

```sh
make run ARGS="--demo catalog --mode grid --grid-sample --grid-preset data --lang en"
```

### Rust

Rust core requires 1.85+. The Ratatui UI and examples require 1.88+. Run the example from a Tuivory source checkout. [Rust guide](rust/README.en.md)

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.12.5", features = ["ratatui"] }
```

```sh
make run-rust ARGS="--demo catalog --mode grid --grid-sample --grid-preset data --lang en"
```

### Python

Python 3.11+. Install the wheel in your virtual environment, then use `import tuivory` in your application. [Python guide](python/README.en.md)

```sh
python -m pip install ./tuivory-0.12.5-py3-none-any.whl
python -m tuivory --demo grid --lang en
```

### TypeScript / JavaScript

Node.js 22+. Use `import * as ui from "tuivory"` in an ESM application. The package includes JavaScript and TypeScript declarations. [TypeScript / JavaScript guide](javascript/README.en.md)

```sh
npm install ./tuivory-0.12.5.tgz
npm exec -- tuivory --demo grid --lang en
```

### C

Use a C11 compiler. Extract the SDK, compile `src/tuivory.c` with `-Iinclude`, and link the resulting object or static library into your application. [C guide](c/README.en.md)

```sh
tar -xzf tuivory-c-0.12.5-sdk.tar.gz
```

### C++

Use a C++17 compiler. Extract the SDK, add its `include/` directory to your build, and include `tuivory.hpp`. [C++ guide](cpp/README.en.md)

```sh
tar -xzf tuivory-cpp-0.12.5-sdk.tar.gz
```

### Java

Java 17+. Add the JAR to your application’s classpath and import the component types with `import static io.tuivory.Tuivory.*;`. [Java guide](java/README.en.md)

```sh
javac -cp tuivory-0.12.5.jar MyApp.java
```

The examples default to Korean. Add `--lang en` for English. [More examples](docs/examples.en.md)

![Tuivory](docs/images/playground-dark-en.svg)

## Documentation

- [Installation](docs/installation.en.md)
- [Component guides](docs/components.en.md)
- [API reference](docs/api/README.en.md)
- [Design guide](docs/design-guide.en.md)
- [Responsibilities](docs/component-boundary.en.md)
- [Development and history](docs/development.en.md)

- [Releases](docs/release-0.12.5.en.md) · [Changelog](CHANGELOG.en.md) · [Withdrawn versions](docs/withdrawn-versions.en.md)

[Attribution and license](NOTICE.en.md)
