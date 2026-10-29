# TVR-7 shared menu validation

[한국어 (default)](menu.md) · **English**

2026-10-29, baseline `50bf212`, uncommitted/unpublished working source on `codex/TVR-7-menus`. The preceding boundary correction was committed with approval as `50bf212`, without a push. No menu commit/push/PR/merge/tag/Release/remote CI was performed. Existing v0.2.0 tags lack the new Menu API. Keep TVR-7 open.

## Reference and change

Read LazyOra [menu.go](https://github.com/leechis7/lazyora/blob/98a2f47e8621838101d5db781232a699dba382f3/internal/ui/menu.go) and [menu_groups.go](https://github.com/leechis7/lazyora/blob/98a2f47e8621838101d5db781232a699dba382f3/internal/ui/menu_groups.go) at public commit `98a2f47e8621838101d5db781232a699dba382f3`; verified the corresponding local menu files were unmodified. Adopt entry/back flow, parent selection, original caller, limited drawing and separator/disabled/shortcut principles. No SQL/transaction/taxonomy code or automatic grouping threshold was transferred.

Add Go/Rust Menu models, bar/content renderers/popup geometry, a Rust popup surface/border, database-free hosts and bilingual guides/references. Existing ListModel/SearchPicker/other component APIs remain unchanged. Hosts own taxonomy/items/eligibility, global keys, screen composition and actual commands.

## Coverage

- Mirror `design/menu-cases.json` into standalone Go/Rust test assets. Compare three-level entry/return, parent selection, root switching, context roots, mnemonics and original ReturnID.
- Empty messages, depth 32/33, item count above 10,000, missing/cyclic parents, duplicate IDs/mnemonics, separator children, disabled guards, atomic invalid updates and explicit close/return after disabling an open ancestor.
- Widths 0..89/heights 0..11, Unicode/ASCII, CJK/emoji/combining clusters, long labels/bar overflow, literal shortcuts/tags and popup viewport bounds.
- dark/light/blackwhite × 8/16/256/True Color × Unicode/ASCII: Go physical Runes/Bytes/styles/outside area after Show; Rust TestBackend popup wide-glyph edges and a single title. Go bar clicks retain no mouse capture.
- Full Go race/vet; Rust 1.85.1 core; Rust 1.88.0 all features/targets/doctests/fmt/Clippy.
- Eight actual PTYs: Go/Rust × Korean/English × initial Unicode/ASCII. Exercise F10/Shift+F10/Alt, nested/back/root navigation, disabled skipping, original-panel restoration and actual typing, paste/background blocking, dynamic eligibility, bar/outside clicks, theme/profile/ASCII changes, resizing and terminal restoration. Korean text is checked on the ANSI-interpreted screen.
- Install/import the isolated Go module and packaged Rust crate without design assets, checking requests/caller context and actual menu rendering. Inspect Go physical bytes after Show and Rust TestBackend popup border/content.
- Four CGO-free Go/musl Rust ARM64/x86_64 menu artifacts and two external x86_64 hosts contain no PT_INTERP/DT_NEEDED.
- Boot actual CentOS 7.4.1708 userspace, kernel `3.10.0-693.el7.x86_64`, glibc `2.17-196.el7.x86_64` under QEMU TCG: final x86_64 bilingual startup/exit scenes for both examples plus both external hosts. VM examples start with menus closed; hierarchical interaction is validated on ARM64 PTYs.
- Eight localized primary-menu references plus two localized nested references, shared token/fixture equivalence, seven Python tooling tests, Markdown links/whitespace. References are actual Rust TestBackend output, not Go/physical/SSH captures.

[Results JSON](menu-results.json) records final state and exact source/reference/artifact hashes. Temporary outputs/logs live in ignored `bin/validation/`. Actual LazyOra/LazyBeaver integration, customer SSH/fonts/physical terminals, remote CI and installation from new public tags remain outside this validation.

## Reproduce

```sh
go -C go test -race ./...
go -C go vet ./...
make check-rust-ui test-rust-ui
# Run the core separately under Rust 1.85.1
cargo test --manifest-path rust/Cargo.toml --locked
python3 tools/check_go_module.py --static-output bin/validation/go-menu-host-linux-x86_64
python3 tools/check_rust_module.py --ratatui --static-output bin/validation/rust-menu-host-linux-x86_64
python3 tools/smoke_menu.py /PATH/TO/menu --lang ko
python3 tools/smoke_menu.py /PATH/TO/menu --lang en --ascii
python3 tools/snapshot_menu.py /PATH/TO/RUST/menu
python3 tools/export_tree_cases.py --check
python3 tools/check_links.py
```

Run PTYs for both language binaries and both UI languages/initial character modes. Follow [static distribution](../docs/static-build.en.md) for ELF/legacy-kernel execution. Default product-build policy is unchanged; menu examples use `bin/<language>/menu-linux-<architecture>`.

[Menu guide](../docs/menus.en.md) · [Component/application boundary](../docs/component-boundary.en.md)
