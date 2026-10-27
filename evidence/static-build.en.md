# Static distribution validation

[한국어 (default)](static-build.md) · **English**

2026-10-28, TVR-5 and TVR-6. Validated local changes on `codex/TVR-5-centos74-musl`; these are not new commit, remote publication or GitHub CI results. [Reproduction commands and policy](../docs/static-build.en.md)

| Check | Environment/result |
| --- | --- |
| CentOS userspace | Official 7.4.1708 AMD64 image, glibc `2.17-196.el7.x86_64` |
| Actual guest kernel | Official CentOS `3.10.0-693.el7.x86_64`, booted with QEMU TCG |
| Go x86_64 | CGO disabled; playground, Tree and workspace passed Korean/English startup, Ctrl+Q exit and alternate-screen restoration |
| Rust x86_64 | Rust 1.88.0 musl/static PIE; the same three examples passed both languages, exit and restoration |
| External Go host | Standalone go/ module without shared design assets; static build and guest API/rendering checks passed |
| External Rust host | Packaged crate plus Ratatui without shared design assets; static build and guest API/rendering checks passed |
| Default ARM64 | Go/Rust static ELF checks and Korean/English PTY startup, exit and restoration passed on the current Linux ARM64 host |
| Dynamic dependency rejection | ELF architecture/loader/DT_NEEDED checks and static PIE acceptance/dynamic dependency rejection regressions passed |
| Remote CI/publication | Track subsequent CI/PR/merge results in TVR-5/TVR-6 comments. Existing v0.1.0 tags/assets unchanged |

An ARM64 Linux host emulated the x86_64 kernel with QEMU 10.2.1. The VM used neither networking nor KVM. Docker only exported the pinned image filesystem. Each run saves a serial log and JSON artifact hashes under `--output`; this run used `/tmp/tuivory-centos74.log` and `/tmp/tuivory-centos74.json`. Temporary files are not release assets.

Image digest: `sha256:78b63c089c40a2ca0d85db9125fb3193c6ff74814bba5f894c803e5ae02a4035`. Kernel SHA256: `8ede7f8d3c8f5e72f1a84713ad59b7b39211ea1af8887389cb50a189df937c6f`.

The physical target server, SSH, fonts, user terminals and LazyOra/LazyBeaver integration remain unverified. ARM64 results are not CentOS 7.4 ARM64 validation. The existing v0.1.0 Rust GNU ARM64 asset requires glibc 2.39 and differs from the new static artifacts. Layout did not change, so existing localized UI images remain current.

Final passing artifact hashes are preserved in the [JSON record](static-build-results.json). Go race/vet, seven Python checks, Rust all-feature tests/rustdoc/fmt/clippy and shared token/document-link checks also passed. Document checks exclude generated target/bin directories.
