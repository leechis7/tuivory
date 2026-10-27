# Changelog

[한국어 (default)](CHANGELOG.md) · **English**

## Unreleased

- Added the Rust core crate: candidate tokens, profiles, color/style values, strict JSON validation, embedded distribution data, and external project usage validation. Added an optional Ratatui 0.30.2 adapter, Crossterm 0.29 bilingual interactive example, Linux ARM64 build, language-matched reference images, and PTY checks. The core requires Rust 1.85+; the adapter/example require 1.88+. These changes remain committed locally/unpublished; there is no crates.io release.

- Separate playground build outputs under `bin/<language>/`. The default Go output is now `bin/go/tuivory-linux-arm64`; the default build still produces one Linux ARM64 binary.
- Added English project, Go usage, and contribution guides alongside the Korean default, with reciprocal language links.
- Added playground `--lang ko|en`: one binary supports default Korean and optional English, with English UI reference images in English documentation.
- These changes merged into `main`/`dev` through [PR #1](https://github.com/leechis7/tuivory/pull/1); they have no new version tag yet.
- Subsequent documentation work refreshes current usage and publication status, adds English counterparts and an index, and keeps source attribution in notices.

## 0.0.1 — 2026-10-24

- First Tuivory (TUI + ivory) release, providing a language-neutral repository and Go style package.
- Shared themes, color profiles, state rules, JSON, CSV, and schema live in `design/`.
- Go module `github.com/leechis7/tuivory/go` exposes style APIs and tview application methods through one public package, `tuivory`.
- Includes dark/light/blackwhite × 8/16/256/truecolor, a database-free interactive playground, and state preservation checks.
- Python/JavaScript provide token consumers; Shell provides an ANSI output example. UI style packages for these languages are future work.
- Releases are recorded against this repository's tags and Releases. See [installation and usage](docs/installation.en.md) and [origin notices](NOTICE.en.md).
