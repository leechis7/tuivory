# Tuivory installation and usage

[한국어 (default)](installation.md) · **English**

Tuivory (TUI + ivory) is an independent terminal UI style project. Current module, command, and token identifiers use Tuivory; work is tracked in Jira project TVR. Original attribution is preserved in [NOTICE](../NOTICE.en.md).

## Published version and current source

The published Go version is `v0.0.1`, with repository tag `go/v0.0.1`.

```sh
go get github.com/leechis7/tuivory/go@v0.0.1
```

The module lives in `go/`. There is no root Go module; the package name is `tuivory`.

```go
import "github.com/leechis7/tuivory/go"

styler, err := tuivory.New("dark", "256")
```

Current `main` includes Korean/English documentation and playground language selection added after the release tag. These changes have not received a new version tag. To run the current playground, check out the repository and run from its root:

```sh
go -C go run ./cmd/tuivory --lang ko
go -C go run ./cmd/tuivory --lang en
make build
./bin/tuivory-linux-arm64 --lang en
```

Requires Go 1.24 or later. `make build` produces one Linux ARM64 binary supporting both languages. Source execution runs on the current host. The starter template runs with `go -C go run ./examples/starter` and has Korean example labels.

## Shared data and validation

The draft token format is `tuivory.tokens.draft`, shared sources live in `design/tokens/`, and the Go distribution copy is `go/internal/tokens/candidate.json`. The CLI is named `tuivory`; documentation image generation uses `TUIVORY_SNAPSHOT_DIR`.

Go projects can access embedded tokens through the public module alone. Python and JavaScript provide shared JSON reading examples; Shell provides an ANSI reference example. UI packages for those languages are not yet available.

[Go API](go-package.en.md) · [Architecture](architecture.en.md) · [Playground](playground.en.md) · [Validation evidence](../evidence/README.en.md)
