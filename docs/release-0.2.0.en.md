# Tuivory 0.2.0 release

[한국어 (default)](release-0.2.0.md) · **English**

Product `VERSION` and Rust manifest/lock are **0.2.0**. The [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.2.0) provides static executables, standalone crate and checksums. Go/Rust tags identify the same final commit. Keep TVR-5/6/7 epics open.

## Included changes

| Scope | Contents |
| --- | --- |
| Static Go/Rust distribution | CGO-disabled Go, Rust musl/bundled LLD, ELF loader/shared-library rejection, CentOS 7.4 x86_64 execution and external static hosts |
| [TVR-8 states/focus](focus.en.md) | Common state composition, stable IDs, nested popup scopes, close requests and focus restoration |
| [TVR-9 inputs/forms](forms.en.md) | Grapheme editing, read-only/required/host errors, checks/radios/selection/submit requests |
| [TVR-10 lists/search](collections.en.md) | ID-based lists/menus, disabled/separator rows, independent focus/selection/activation, query/confirm/cancel |
| [TVR-11 grids](grid.en.md) | Virtual sources, cell/row selection, viewports and edit/copy/sort/filter requests |
| [TVR-12 feedback](feedback.en.md) | Notice queues and persistent critical errors, progress/cancel requests, loading/empty/error states |
| [TVR-13 layout](layout.en.md) | Spacing/density, Stack/Drawer placement, badges/chips and prioritized keyboard help |
| [TVR-14 Go drawing](overlay-drawing.en.md) | Both card/shadow edges protected against wide-glyph overlap, with post-Show output regressions |

TVR-8–13 include models, public adapters and database-free bilingual examples in both languages. The catalog has five modes and thirty localized dark/light/blackwhite references. TVR-14 targets Go/tcell and does not add equivalent Rust APIs. Existing Tree/tabs/panels/splits/breadcrumb APIs remain.

Hosts own data, DB operations, validation/save/search, clipboard I/O, clocks and terminal lifecycle. Python/JavaScript/Shell remain interpreter-based token references, not UI libraries or independent executable distributions. Actual LazyOra/LazyBeaver and customer-server/SSH integration are outside validation.

## Installation and tags

```sh
go get github.com/leechis7/tuivory/go@v0.2.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.2.0", features = ["ratatui"] }
```

Go has no self-version field in go.mod: tag `go/v0.2.0` determines the module version. Rust retains `publish = false` and is not published to crates.io. Local development can use Go replace/Rust path dependencies. Existing 0.1.0 lacks the new TVR-8–14 APIs.

Requirements: Go 1.24+, Rust core 1.85+ (validated on 1.85.1), and Ratatui/catalog 1.88+ (validated on 1.88.0). Existing Go-derived styles and shared candidate tokens remain separate datasets.

## Release assets

Release attachments and local `bin/releases/v0.2.0/` use the filenames below. Each Linux archive includes that language's static playground and five-mode catalog, bilingual running instructions, attribution and license. Default `make build` still produces one Go Linux ARM64 binary. Catalog, x86_64 and Rust assets use explicit preparation commands.

| File | Purpose |
| --- | --- |
| `tuivory-go-v0.2.0-linux-arm64.tar.gz` | Go Linux ARM64 playground/catalog |
| `tuivory-go-v0.2.0-linux-x86_64.tar.gz` | Go x86_64 playground/catalog for CentOS 7.4 |
| `tuivory-rust-v0.2.0-linux-arm64.tar.gz` | Rust Linux ARM64 musl playground/catalog |
| `tuivory-rust-v0.2.0-linux-x86_64.tar.gz` | Rust x86_64 musl playground/catalog for CentOS 7.4 |
| `tuivory-0.2.0.crate` | Standalone Rust source/APIs/examples/embedded data |
| `SHA256SUMS` | Archive/crate checksums |

Assets are statically rebuilt and checked from the finalized commit. Attached `RELEASE-MANIFEST.json` records the build commit/version, archive/binary hashes and final validation. Preserve existing 0.1.0 tags/assets. Distinguish old Rust GNU ARM64 binaries requiring glibc 2.39 from new static musl assets.

## Validation and publication records

The [preparation evidence](../evidence/release-0.2.0.en.md) is a historical record of pre-publication dirty candidates. Use the Release attachments SHA256SUMS and RELEASE-MANIFEST.json for final asset hashes. PR/main/dev CI, final commit, actual tag installation and downloaded-asset checks are recorded in [TVR-7](https://leechis7.atlassian.net/browse/TVR-7) and TVR-5/6 comments. Earlier candidate hashes or CI do not validate final assets.

Validation covers static ELF, external Go/Rust imports, bilingual native PTYs and actual CentOS 7.4 kernel execution. VM catalog startup uses default forms mode; other modes' input is checked with native PTYs. Customer SSH, font-specific physical terminals and LazyOra/LazyBeaver integration remain separate.
