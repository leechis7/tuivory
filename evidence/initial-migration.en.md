# Tuivory initial repository validation

[한국어 (default)](initial-migration.md) · **English**

2026-10-24 · Linux ARM64 · first release target 0.0.1 · [TVR-2](https://leechis7.atlassian.net/browse/TVR-2)

This is the initial release's historical validation record; executable paths below reflect that time. Follow the [playground guide](../docs/playground.en.md) for the current Go build path and commands.

## Initial scope

The independent repository organizes shared design/, language directories, Go internals/public API, and the database-free playground. Product, package, command, and draft token names use tuivory. The LazyOra checkout was not modified. Source attribution and copyright are preserved in [NOTICE](../NOTICE.en.md).

The source CSV, LazyOra source manifest, 240-color and 1,572-style fixtures, license, and dependency checksums matched the source byte for byte. Shared tokens and the Go embedded copy retained color/role data apart from the format identifier.

## Local validation

- `make test`: Go race and three Python tests passed, including source style and widget/state checks.
- `make check`: Go vet, 192 reference color pairs, token/CSV agreement, local links, and Shell syntax passed.
- `make build`: generated Linux ARM64 `bin/tuivory-linux-arm64`.
- `make check-consumers`: Go/Python/Node.js agreed on 12 palettes and 192 pairs.
- `python3 tools/check_go_module.py`: isolated go/ tests and an external project using the public API/embedded tokens passed using local replace.
- `python3 tools/smoke_playground.py bin/tuivory-linux-arm64`: actual PTY startup, one Ctrl+Q, and alternate-screen restoration passed.
- Dark/light/monochrome/popup SVGs regenerated from actual widgets and passed XML checks.
- Verified there was no root go.mod and all Go source stayed in go/.

VCS metadata discovery initially failed before the temporary directory became a Git repository. After initialization, the same default build and cross-language data checks passed without bypassing product code or build checks.

## Scope of the evidence

These are the initial local results. Remote CI, tags, Release, and external project use through the Go proxy without replace are recorded separately below and in the release issue. They do not establish complete SSH/user-palette compatibility or Python/JavaScript/Shell UI package completion.

## Publication and release results

- Release commit: `cf06d95f4334f65436197ae4f12faf35783f5b7a`.
- Both validate/go-package jobs passed in [remote CI](https://github.com/leechis7/tuivory/actions/runs/40057059473).
- [Tuivory v0.0.1 Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.0.1) and Go tag `go/v0.0.1` published.
- A new application project outside the repository successfully ran `GOWORK=off GOPROXY=https://proxy.golang.org go get github.com/leechis7/tuivory/go@v0.0.1`. Without local replace, it checked 12 theme/profile combinations, input preservation, embedded token format, and palette resolution.
- Module checksum: `h1:5xsN+SnSOgwVFGheRzCaS7CXsq6waPiW3+FIKjZTUAg=`.

Automatic GitHub development integration administration was outside tool access. The user was given the GitHub for Atlassian selected-repository path, and repository/CI/Release Web links were added to Jira. Web links alone do not establish automatic integration.
