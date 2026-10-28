# TVR-9–13 component validation

[한국어 (default)](components.md) · **English**

This records local validation methods and boundaries. Track each stage's PR/final-dev CI and merge commit in TVR-9–13 Jira comments; an earlier stage's success does not validate later changes. Publication is approved into dev only; main/tags/Releases remain separate.

| Stage | Public API and meaningful checks |
| --- | --- |
| TVR-9 | Forms/views: grapheme editing/caret, read-only guards, required/host errors, pending/confirmed/cancelled choices, width and actual input/submit/cancel |
| TVR-10 | Lists/menus/search picker: stable IDs, disabled/separator skipping, focus/selection/activation separation, query/empty results/cancel and wide cells |
| TVR-11 | Virtual grids: viewport-bounded row access over 100,000 rows, ID restoration, original copies, edit guards, empty data, column bounds and header sorting |
| TVR-12 | Notices/progress/data states: critical/action persistence, full queues, request immutability, host clocks, progress/cancel limits and one-row priority |
| TVR-13 | Spacing/stacks/badges/chips/help: shared defaults, widths 0–240/non-overlap/bounds/preferences, zero/99+, removal guards, shortcut conflicts/priorities |

Use Go race/vet, Rust all-feature tests/rustdoc/fmt/clippy and shared token/contract/document/Shell checks. Core CI uses Rust 1.85.1; UI uses 1.88.0. External checks isolate go/ or a packaged Cargo crate, validate APIs/rendering and export static x86_64 hosts.

```sh
make test check test-rust-ui check-rust-ui
python3 tools/check_go_module.py --static-output /tmp/go-host
python3 tools/check_rust_module.py --ratatui --static-output /tmp/rust-host
python3 tools/smoke_catalog.py BINARY --mode forms --lang ko
python3 tools/smoke_catalog.py BINARY --mode collections --lang en --ascii
python3 tools/smoke_catalog.py BINARY --mode grid --lang en
python3 tools/smoke_catalog.py BINARY --mode feedback --lang ko
python3 tools/smoke_catalog.py BINARY --mode layout --lang en
```

PTYs cover real keys/pointer input, guarded actions, 40×16/120×36 resize and normal exit/terminal restoration. F2/F3 theme/profile changes preserve models. The harness reads UTF-8 wide cells/cursor motion; it does not establish physical-terminal/font visual parity.

Static CI checks Go CGO-disabled/Rust musl ELF artifacts and external hosts, then boots official CentOS 7.4.1708 userspace/glibc 2.17 with its actual 3.10.0-693 kernel for startup/exit and external APIs/rendering. VM catalog startup uses default forms mode; other modes are covered by native PTYs and external core APIs.

Actual Rust TestBackend at 120×36 produces six localized dark/light/blackwhite SVGs per mode, thirty across five modes. Reproduce with tools/snapshot_catalog.py BINARY --mode MODE. These are neither Go captures nor physical-server/SSH evidence. See [guides and scope](../docs/components-backlog.en.md). DB/real clipboard I/O, application validation/save/search/cancellation and LazyOra/LazyBeaver integration remain host work.
