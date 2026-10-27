# Tuivory Go

[한국어 (default)](README.md) · **English**

All Go implementation code and module configuration live in this directory. The module path is `github.com/leechis7/tuivory/go`; the package name is `tuivory`. Requires Go 1.24 or later.

```sh
go get github.com/leechis7/tuivory/go@v0.0.1
```

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

The first release is `v0.0.1`. Its repository tag is `go/v0.0.1` because this is a submodule in `go/`.

From the repository root:

```sh
go -C go run ./cmd/tuivory --lang en
make build
make test
make check
```

Language selection is available in current repository source and is not included in the published `v0.0.1` tag. From this directory, use `go run ./cmd/tuivory --lang en` for the English playground, `go run ./examples/starter` for the starter template (Korean labels), or `go test -race ./...` for Go tests. `make build` creates a single Linux ARM64 product binary in the repository's `bin/go/` directory. Run it with `--lang en` for English or `--lang ko` for Korean. Omitting the flag, including with `make run`, defaults to Korean.

Shared candidate tokens originate in [design/tokens](../design/tokens/README.en.md). `internal/tokens/candidate.json` is a generated distribution copy produced by `tools/export_tokens.py`; do not edit it manually. The module embeds this data, so consumers need neither the repository root nor a generation step.

[API and usage](../docs/go-package.en.md) · [Style coverage](../docs/go-style-coverage.en.md) · [Project overview](../README.en.md)

## Shared Tree

Existing `Styler.Tree` styles stock tview nodes. New `NewTree`, `TreeState`, and `NewTreeView` provide stable IDs, expansion/selection/scroll, node icons/secondary text/counts, and keyboard/mouse behavior. Rust shares the same candidate tokens and controls. This is neither a port of the complete Go-derived styler nor an API available in published tags. [API and example](../docs/tree.en.md) · [Support audit](../docs/component-audit.en.md). Run `make run-tree-go ARGS="--lang en"` from the root.
