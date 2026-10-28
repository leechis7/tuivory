# TVR-14 overlay boundary validation

[한국어 (default)](overlay-drawing.md) · **English**

Checked on Linux ARM64 with Go/tcell v2.13.10 on 2026-10-28. [TVR-14](https://leechis7.atlassian.net/browse/TVR-14) · [API and reproduction scope](../docs/overlay-drawing.en.md).

## Reproduction and repair

Before repair, writing `한` at `(2,0)` and border `│` at `(3,0)`, then calling `Show()`, left logical `│` at `(3,0)` but empty `GetContents()` output there. Writing `界` over a cell followed by `Z`, then overwriting only the wide start, also exposed the hidden `Z` again.

`WideSafeScreen` clears entire intersected old graphemes and normalizes new continuation cells. `DimRegion` clears partial graphemes at both rectangle edges while preserving interior text. `PanelView`, public Choice, and Go playground popups/choices share the internal implementation.

## Passed local checks

| Method | Result |
| --- | --- |
| `make test check` | Full Go race/vet, token/contract copies, palette, links, tools and Shell checks passed |
| `go/drawing_test.go` | Five writing paths, CJK/emoji, both card/shadow edges, multiple frames, Sync, last-column/clipping/styles checked via output Runes/Bytes after Show |
| Actual widget integration | Focused Go popup borders, open Choice lists and Unicode/ASCII panels inspected after Show |
| `tools/check_go_module.py --static-output /tmp/tuivory-tvr14-external-x86_64` | Isolated module without repository design/, external single-import API/output checks, and x86_64 ELF without PT_INTERP/DT_NEEDED passed |
| Go PTYs | Bilingual playground startup/exit/restoration; bilingual focus nesting/pointer blocking/state/theme/ASCII/resize; all five Korean catalog modes' actions/theme/resize/restoration passed |

New regressions run through existing CI's full Go tests and external-import paths. This document records the local validation stage before commit/publication. Subsequent commits, PRs, remote CI and dev integration are recorded in TVR-14 comments. A new CentOS VM execution, customer-server/SSH, font-specific physical terminals and LazyOra application integration are outside these local checks. Rust/Ratatui is outside this repair. Existing release tags and assets remain unchanged.
