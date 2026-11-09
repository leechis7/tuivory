# Tuivory — TUI component library

[한국어 (기본)](README.md) · **English**

Tuivory provides reusable components for terminal applications, including trees, menus, forms, dialogs, text editors, and data grids. The library handles drawing and interaction within each component. Your application composes screens, supplies data, and handles actions.

Tuivory supports Go/tview and Rust/Ratatui, with independent implementations for Python, TypeScript/JavaScript, C, C++, and Java. [Language support](docs/languages.en.md)

## Install and run an example

Download the wheel, npm archive, SDK or JAR for your language. The commands below assume the download is in your current directory. The Linux SDK examples use ARM64. On x86_64, replace `arm64` with `x86_64` in both filenames. [Download release assets](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.2)

### Go

Go 1.24+. Import `github.com/leechis7/tuivory/go`. The example command runs from a Tuivory source checkout. [Go guide](go/README.en.md)

```sh
go get github.com/leechis7/tuivory/go@v0.12.2
```

```sh
make run ARGS="--demo catalog --mode grid --grid-sample --grid-preset data --lang en"
```

### Rust

Rust core requires 1.85+. The Ratatui UI and examples require 1.88+. Run the example from a Tuivory source checkout. [Rust guide](rust/README.en.md)

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.12.2", features = ["ratatui"] }
```

```sh
make run-rust ARGS="--demo catalog --mode grid --grid-sample --grid-preset data --lang en"
```

### Python

Python 3.11+. Install the wheel in your virtual environment, then use `import tuivory` in your application. [Python guide](python/README.en.md)

```sh
python -m pip install ./tuivory-0.12.2-py3-none-any.whl
python -m tuivory --demo grid --lang en
```

### TypeScript / JavaScript

Node.js 22+. Use `import * as ui from "tuivory"` in an ESM application. The package includes JavaScript and TypeScript declarations. [TypeScript / JavaScript guide](javascript/README.en.md)

```sh
npm install ./tuivory-0.12.2.tgz
npm exec -- tuivory --demo grid --lang en
```

### C

A C11 compiler is required to build your application. Include `tuivory.h` and link the SDK’s `lib/libtuivory.a`. [C guide](c/README.en.md)

```sh
tar -xzf tuivory-c-0.12.2-linux-arm64.tar.gz
./tuivory-c-0.12.2-linux-arm64/bin/c/tuivory-linux-arm64 --demo grid --lang en
```

### C++

A C++17 compiler is required to build your application. Add the SDK’s `include/` directory and include `tuivory.hpp`. [C++ guide](cpp/README.en.md)

```sh
tar -xzf tuivory-cpp-0.12.2-linux-arm64.tar.gz
./tuivory-cpp-0.12.2-linux-arm64/bin/cpp/tuivory-linux-arm64 --demo grid --lang en
```

### Java

Java 17+. Add the JAR to your application’s classpath and import the component types with `import static io.tuivory.Tuivory.*;`. [Java guide](java/README.en.md)

```sh
java -jar tuivory-0.12.2.jar --demo grid --lang en
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

- [Releases](docs/release-0.12.2.en.md) · [Changelog](CHANGELOG.en.md) · [Withdrawn versions](docs/withdrawn-versions.en.md)

[Attribution and license](NOTICE.en.md)
