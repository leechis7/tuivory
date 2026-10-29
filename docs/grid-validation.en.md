# TVR-17 local validation

[한국어 (default)](grid-validation.md) · **English**

Publication update: integrated into dev in PR #16; included in 0.3.0. The local checks below are historical pre-commit evidence; current release validation is documented in [the release guide](release-0.3.0.en.md).

Validated against `codex/TVR-17-grid-options` working source on 2026-10-29. Prior documentation changes were committed as `c1a9b9a`; TVR-17 was uncommitted during validation and is included in this local commit; it remains unpublished on GitHub. TVR-17 is absent from the v0.2.0 tags/Release. These local checks are separate from remote CI, actual LazyOra/DB integration and SSH/SecureCRT/MobaXterm validation.

## Coverage

- Existing Go full race suite, final grid race suite and `go vet ./...`.
- Rust 1.85.1 core tests/doctests; Rust 1.88.0 all features/targets/doctests, fmt and warning-free Clippy.
- Basic API regression; stable IDs/ranges/originals/widths/scrolling after option round trips; atomic invalid-option rejection.
- CJK/emoji/combining clusters at widths 0..79/heights 0..11, two character modes, three densities and three overflow policies.
- Original TSV ranges/bulk-copy delegation; bounded viewport reads on 100,000 virtual rows; visible auto-fit/manual sizing precedence; density-aware paging and stable viewport when moving upward.
- Readonly cell edit guards, edited precedence, cell metadata, range/resize dragging, ignored hover/unsupported events and stale/duplicate response rejection.
- dark/light/blackwhite × 8/16/256/True Color × Unicode/ASCII: Go Runes/Bytes/styles after Show, Rust visible TestBackend characters/styles, both wide-glyph edges and redraw after overlays. Hidden TestBackend continuation cells are skipped according to the leading glyph's width, matching terminal presentation.
- Go/Rust data-preset PTYs in both languages: edit, Shift ranges, raw copy, details, sorting, header mouse input, scrolling, resize and terminal restoration. English runs also exercise ASCII fallback.
- Isolated Go module and packaged Rust crate imported/rendered by external apps without design assets. Check Go physical divider bytes after Show and Rust TestBackend divider output.
- CGO-free Go/musl Rust ARM64 and x86_64 ELF artifacts without PT_INTERP/DT_NEEDED; separate x86_64 external apps satisfy the same checks.
- Fourteen localized comparison SVGs, shared token/fixture equivalence, seven Python tooling tests and local Markdown links.

Local logs/temporary outputs live in ignored `bin/release-validation/`. Existing tags/assets remain unchanged.

## Reproduce

```sh
go -C go test -race ./...
go -C go vet ./...
make check-rust-ui test-rust-ui
# Run the core separately under Rust 1.85.1
cargo test --manifest-path rust/Cargo.toml --locked
python3 tools/check_go_module.py --static-output bin/release-validation/go-grid-host-linux-x86_64
python3 tools/check_rust_module.py --ratatui --static-output bin/release-validation/rust-grid-host-linux-x86_64
make build build-go-x86_64
python3 tools/build_rust.py --arch x86_64 --examples
python3 tools/build_rust.py --arch arm64
python3 tools/smoke_catalog.py /PATH/TO/catalog --mode grid --lang ko --grid-preset data
python3 tools/smoke_catalog.py /PATH/TO/catalog --mode grid --lang en --ascii --grid-preset data
python3 tools/snapshot_catalog.py /PATH/TO/RUST/catalog --mode grid --grid-sample --grid-preset data --name grid-data
python3 tools/snapshot_catalog.py /PATH/TO/RUST/catalog --mode grid --grid-sample --grid-preset simple --name grid-simple
```

`/PATH/TO/catalog` is each language's host-architecture validation executable. When temporary storage is limited, point TMPDIR and the Go cache at a workspace with sufficient capacity. See [static distribution](static-build.en.md) for ELF/target-kernel validation.

Go/Rust static demos started/exited in both languages and both external grid apps passed on CentOS 7.4.1708 x86_64, kernel `3.10.0-693.el7.x86_64`, glibc `2.17-196.el7.x86_64`. QEMU TCG boots the actual legacy kernel/userspace; this does not establish physical-server/SSH results or ARM64 CentOS execution. [Environment/artifact hashes](../evidence/grid-options-results.json).

[Grid API and support](grid.en.md)
