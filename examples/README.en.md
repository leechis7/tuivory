# Language examples

[한국어 (default)](README.md) · **English**

Implementation code lives inside each language directory. This directory indexes examples and a shared static layout.

| Language | Example | Available scope |
| --- | --- | --- |
| Go | [Starter](../go/examples/starter/main.go), [tokens](../go/examples/tokens/main.go) | Working Go style API and runnable playground |
| Python | [Token reader](../python/examples/read_tokens.py) | Data example; no UI package |
| JavaScript | [Token reader](../javascript/examples/read-tokens.mjs) | Data example; no UI package |
| Shell | [ANSI sample](../shell/examples/terminal-colors.sh) | Reference output; no style function package |

The [static component layout](components.txt) is language-independent reference material. The starter and static layout have Korean example labels; the current [playground](../docs/playground.en.md) supports `--lang en`.

## Executable locations

Example sources remain in their language directories. Put compiled playground executables in `bin/<language>/`, with OS and architecture in each filename. Currently, `make build` produces only `bin/go/tuivory-linux-arm64`. From the repository root, run `./bin/go/tuivory-linux-arm64 --lang ko` or `--lang en`.

Future Rust playground builds will use `bin/rust/`; Rust build commands and executables are not available yet. Python, JavaScript, and Shell examples run from source by default; executable packaging can be decided when needed. Git ignores `bin/`.
