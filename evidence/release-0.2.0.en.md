# 0.2.0 release preparation validation

[한국어 (default)](release-0.2.0.md) · **English**

This is historical preparation evidence. See the [release guide](../docs/release-0.2.0.en.md) and attached Release manifest for final assets/publication checks.

Checked local 0.2.0 candidates on Linux ARM64 on 2026-10-28. [Scope and publication boundaries](../docs/release-0.2.0.en.md) · [Candidate version, base commit, SHA256 and results](release-0.2.0-results.json).

## Results

| Check | Result |
| --- | --- |
| Product/Cargo/lock/crate versions | All 0.2.0; dependency versions unchanged |
| `make test check` | Go race/vet, shared data/contracts, palette, links, tools and Shell passed |
| Rust 1.85.1 core, 1.88.0 all-features | Tests, rustdoc, fmt and clippy passed |
| Isolated Go module/external import | Public APIs and post-Show output passed without repository design/ |
| Standalone Rust crate/external Ratatui host | 0.2.0 packaging, models/renderers and static external host passed |
| ARM64/x86_64 static ELF | Eight Go/Rust playground/catalog binaries lack PT_INTERP/DT_NEEDED; external hosts are static too |
| Five candidate archives/crate | SHA256SUMS, actual extraction, contents and execution passed |
| Archived ARM64 native PTYs | Four bilingual playground and twenty bilingual five-mode catalog scenarios passed startup/actions, theme/resize and exit/restoration |
| Actual Rust candidate references | All thirty five-mode/bilingual/three-theme references generated and match docs; six forms images with old titles refreshed |
| Archived x86_64 on CentOS 7.4 | Pinned official image, actual 3.10.0-693 kernel, glibc 2.17-196: eight bilingual Go/Rust playground/catalog scenes and two external static hosts passed |

The first external Rust check stopped because `/tmp` exceeded its disk quota. Rerunning with ignored `bin/release-validation/` as temporary storage passed. No source fix or skipped check was needed.

## Reproduction commands

```sh
make test check
# RUSTUP_TOOLCHAIN=1.85.1
make test-rust check-rust
# RUSTUP_TOOLCHAIN=1.88.0
make test-rust-ui check-rust-ui
make build build-rust build-go-x86_64 build-rust-x86_64
python3 tools/build_rust.py --arch arm64 --examples
python3 tools/build_rust.py --arch x86_64 --examples
cargo package --manifest-path rust/Cargo.toml --locked --allow-dirty
python3 tools/check_go_module.py --static-output /tmp/go-host
python3 tools/check_rust_module.py --ratatui --static-output /tmp/rust-host
```

Archived executables were passed directly to smoke_playground.py/smoke_catalog.py. References came from snapshot_catalog.py. check_centos74.py received archived x86_64 executables and external hosts. VM catalog startup uses default forms mode; other modes' actual input is covered by native PTYs and models/APIs by external hosts. See result JSON for precise binary hashes.

## Remaining publication stages

Candidates are local under `bin/releases/v0.2.0/`, not final release assets. These are dirty builds from uncommitted source based on dev `b9993d6`; rebuild from the finalized commit after publication approval. Preparation commits, remote CI, main integration, new tags, GitHub Release and actual 0.2.0 tag installation have not run. Earlier dev CI is not evidence for preparation-branch changes.

Customer-server SSH, font-specific physical terminals and LazyOra/LazyBeaver integration remain separate. Existing 0.1.0 tags/assets and remote main/dev branches are unchanged. Epics stay open.
