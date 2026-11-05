# Installation and quick start

[한국어 (default)](installation.md) · **English**

**Do not use 0.10.1:** [Withdrawal and upgrade](withdrawn-versions.en.md). Use 0.10.2 or later.

Source example builds use the 0.9.1 TVR-27 [single executable per language and host architecture detection](examples.en.md).

Current version: **0.11.0**. Go 1.24+, Rust core 1.85+, Rust UI/examples 1.88+.

## Go

```sh
go get github.com/leechis7/tuivory/go@v0.11.0
```

```go
import "github.com/leechis7/tuivory/go"

styler, err := tuivory.New("dark", "256")
if err != nil { return err }
styler.Button(button)
```

Use your host-created tview button. The Go module lives under go/, not the repository root.

## Rust

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.11.0", features = ["ratatui"] }
```

Rust is distributed through Git tags, not crates.io. Omit ratatui for models/tokens only; a local checkout can use a path dependency to rust/.

## Run examples

From a checkout of the release tag:

```sh
make run
make run-rust ARGS="--lang en"
make run-menu-go ARGS="--shadow auto"
make run-menu-rust ARGS="--shadow auto"
```

Korean is the default; use --lang en for English. Examples require no database. Hosts own terminal lifecycle, global shortcuts and business actions.

## Static executables

The release provides Linux ARM64/x86_64 static Go/Rust executables. Local `make build` and `make build-rust` each produce one unified executable for the current Linux host architecture. Binaries live under bin/<language>/ with OS/architecture in their names. CentOS is not validated. Python/JavaScript currently provide token-reading examples, not UI packages.

[API](api/README.en.md) · [Components](components.en.md) · [Release](release-0.11.0.en.md) · [Static builds](static-build.en.md)
