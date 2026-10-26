# Contributing

[한국어 (default)](CONTRIBUTING.md) · **English**

Start with the [shared specifications](design/README.en.md) and [dependency boundaries](docs/architecture.en.md). Keep framework types out of language-independent JSON, and consume shared tokens rather than duplicating their values in language implementations.

For documentation, theme, or tooling changes, explain the problem and reproduction conditions, then describe the relevant principle and how to verify the change.

- Rules: problem → affected use → rule → exceptions → validation → source.
- Themes: role-based foreground/background colors, terminal profile, attributes, reference palette, and the environments actually checked.
- Patterns: combinations of default, focused, selected, disabled, changed, and error states, plus keyboard and mouse behavior.
- Adapters: keep application data, databases, and input I/O ownership outside shared style calculations.

## Layout and validation

Keep Go source and module configuration in `go/`, shared design sources in `design/`, and other language implementations in their respective directories. Keep the repository root language-neutral.

The Go playground requires Go 1.24 or later. For Go changes, run:

```sh
make -C go test
make -C go check
python3 tools/check_go_module.py
```

The default local product build is `make build`, which creates one Linux ARM64 binary at `bin/go/tuivory-linux-arm64`. Put playground executables in `bin/<language>/`, with OS and architecture in each filename.

Run the documentation and shared-data checks from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_palette.py design/themes/lazyora-candidate.csv
python3 tools/check_links.py
python3 tools/export_tokens.py --check
sh -n shell/examples/terminal-colors.sh
```

For shared-data changes, also run `make check-consumers` to compare Go, Python, and Node.js output. Node.js 18 or later is required; the Python and Node.js examples have no external dependencies. This check builds a temporary Go validation program for the current host and removes it afterward.

The link checker verifies local file targets only. External URLs and Markdown fragments require separate checks. Use the [terminal evidence template](evidence/README.en.md) for real terminal observations; do not report an untested environment as passing. Distinguish local results from GitHub CI and publication status.

## Documentation language

From now on, create and update documentation in Korean and English in the same change. Korean remains the default; English versions live in `.en.md` files alongside their Korean counterparts. When updating an existing Korean-only document, add its English version in that change. Keep reciprocal language links at the top of each pair, and keep installation commands, public APIs, supported scope, and validation results aligned. UI images must use the language of their document. Label links to existing untranslated details as Korean.

Use meaningful English names for code identifiers and public formats. Commit message descriptions are written in Korean.

For feature additions, changes, and bug fixes, update affected documentation in the same change, including READMEs, usage and API guides, examples, UI images, and the changelog as applicable. Update Korean and English together, and confirm that the implementation, documentation, and validation results agree before completing the task.

## Work tracking and publication

Tuivory work is tracked in the **TVR** Jira project, independently of LazyOra. Check for an existing issue before starting, and obtain the maintainer's confirmation before creating one. Use the actual TVR issue key in the branch name. Move the issue to in progress when work begins, then complete it with validation evidence after implementation and required checks. Finish the current task before starting another feature branch.

Commits and GitHub publication require the maintainer's explicit approval for the change. The maintainer decides product major versions. See the [repository work rules](AGENTS.en.md) and [work tracking guide](docs/work-tracking.en.md).

## License

Project documentation and code use [AGPL-3.0-only](LICENSE). Preserve source attribution and notices, and check the terms before adding external material. See [NOTICE](NOTICE.en.md).
