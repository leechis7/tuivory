# TVR-8 control-state/focus/popup validation

[한국어 (default)](focus.md) · **English**

2026-10-28, local changes on `codex/TVR-8-focus-popup-foundation`. This records local validation before publication. After approval, record remote CI/PR/merge results separately in TVR-8 comments; earlier published-commit CI does not validate this stage. [API and reproduction](../docs/focus.en.md)

| Check | Result |
| --- | --- |
| Shared specification | Six state cases and 24 sequential scenarios from `design/interaction-cases.json` passed in Go/Rust: navigation, disabled/hidden skipping, nesting, empty scopes, routing, close requests, restoration and invalid-request atomicity |
| Additional boundaries | Stable-ID reorder/wrapping, Go copy ownership, 64-popup limit/overflow rejection, empty-ID and required-role checks passed |
| Theme/presentation | Three themes × four color profiles passed role/focus checks; all state markers retained |
| Go | Race tests/vet and isolated go/ external imports/rendering passed |
| Rust core | Rust 1.85.1 default-feature tests/rustdoc/fmt/clippy passed |
| Rust UI | Rust 1.88.0 all-feature tests/rustdoc/fmt/clippy and packaged-crate external Ratatui API/rendering passed |
| Actual PTYs | Go/Rust in both languages passed Tab/Shift+Tab, disabled skipping, busy activation guard, nested popups, background-pointer blocking, Escape restoration, theme/profile/ASCII changes, 40×16/120×36 resizing, Ctrl+Q exit and terminal restoration |
| Static distribution | Go CGO-disabled and Rust musl x86_64 hosts/external apps passed ELF architecture/interpreter/shared-library checks |
| CentOS 7.4 | Actual `3.10.0-693.el7.x86_64` kernel/7.4.1708 userspace/glibc 2.17 VM passed four localized startup/exit/restore checks and external static-host APIs/rendering |
| Localized references | Actual Rust TestBackend at 120×32 generated and language-checked dark/light/blackwhite/popup/nested/ASCII views: six per language, twelve total |
| Shared assets/docs | Token/component specification synchronization, palette/local Markdown links and Shell syntax passed |

Reproduce with `tools/check_centos74.py`, passing the two new examples through `--binary` and external hosts through `--consumer`. Log: `/tmp/tuivory-focus-centos74.log`; original hashes: `/tmp/tuivory-focus-centos74.json`; preserved [JSON record](focus-results.json). Kernel/image digests are pinned in the checker. QEMU TCG boots the actual legacy kernel rather than relying solely on containers sharing the modern host kernel.

Input editing, form submission, a complete Dialog widget, physical target servers, SSH/fonts and LazyOra/LazyBeaver integration remain separate. Simulation, reference SVG, local PTY and legacy-kernel VM results are distinct; the core owns neither a terminal nor a DB. Default product builds are unchanged; each stage requires explicit publication approval.
