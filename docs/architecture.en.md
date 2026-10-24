# Language-neutral repository architecture

[한국어 (default)](architecture.md) · **English**

Tuivory provides terminal UI styles for use across languages. Shared design and validation contracts are independent of each language implementation and package. Go source, go.mod, and go.sum stay out of the repository root.

```text
tuivory/
├── design/       Shared specifications, JSON tokens, schemas, CSV candidates
├── docs/         Shared documentation and language usage guides
├── go/           Go module, public API, internal implementation, examples
├── python/       Python token reading example
├── javascript/   Node.js token reading example
├── shell/        POSIX ANSI output example
├── examples/     Example index and shared static layouts
├── tools/        Data generation, checks, isolated module validation
└── evidence/     Validation records
```

Go is the only implemented UI style package. Other language directories provide data consumption or reference examples and state their current limits. They are not required to call Go.

## Shared data and distribution assets

Shared candidate data is `design/tokens/candidate.json`, sourced from `design/themes/lazyora-candidate.csv`. Python and JavaScript read the shared JSON.

Go embed cannot include files outside the module. The exporter therefore writes identical JSON to `go/internal/tokens/candidate.json`. This is a generated distribution asset, not another source; do not edit it manually. Checks compare it byte for byte. Downloading only the Go module requires neither repository-root data nor a generation step.

```sh
python3 tools/export_tokens.py
python3 tools/export_tokens.py --check
python3 tools/check_go_module.py
```

The isolated module check copies only `go/` to a temporary directory, tests it, and verifies an external project using the public API and embedded tokens. It does not copy `design/`.

## Public Go API

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

The submodule path is `github.com/leechis7/tuivory/go`, package `tuivory`. Implementation details stay in `go/internal/`. The host owns the screen, events, terminal capability detection, and database state.

The first Go release is `v0.0.1`, tagged `go/v0.0.1`. [Go guide](go-package.en.md) · [Installation and usage](installation.en.md)

## Further implementations

Maintain Go usability and validate LazyOra integration, then extend APIs, distribution, and UI templates for Python, JavaScript, and Shell through separate work items. [Shared specification](../design/README.en.md) · [Examples](../examples/README.en.md) · [Roadmap](roadmap.en.md)
