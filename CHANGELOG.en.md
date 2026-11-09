# Changelog

[한국어 (default)](CHANGELOG.md) · **English**

## 0.12.2

- Grid current cells use a dedicated background and keep the edited asterisk. Dark and light 8-color grids use blue for headers and current cells and teal for selected ranges.

## 0.12.1

- Grid headers use a dedicated background across all seven implementations, including dividers and unused space.

## 0.12.0

- TVR-7 centers every wrapped dialog button row in Go, Rust, Python, TypeScript/JavaScript, C, C++, and Java. Rust adds a reusable Dialog model and Ratatui widget.

- TVR-15/16/30/31/32: Independent grids support captured pointer range selection, Shift+Arrow, column resize and reorder, and whole-grapheme selection in the editor. The integrated examples exercise the shared interaction rules.

- TVR-15/16/30/31/32: Add independent input decoders and optional terminal sessions for fragmented UTF-8, keys, mouse, literal paste, resize, canceled reads and mode/listener restoration, verified in actual PTYs. Java optionally uses OS stty without JNI. Consolidate language API navigation into a catalog table.

- TVR-15/16/30/31/32: Add independent tree/tab drag and drop, host-approved immutable moves, keyboard moves, captured pointers and preview-only scrolling/expansion. Validate stale data/layout/theme cancellation, C ownership/static consumers, bilingual integrated examples/APIs and 240 actual terminal combinations.

- TVR-15/16/30/31/32: Independent data grids add stable-ID virtual sources, pinned/hidden/reordered columns, bounded automatic sizing, raw/display/NULL states, revision-safe host-approved editing and quoted TSV batches, range copying, Unicode find, view snapshots and actual hardware cursors. Add localized integrated examples, API docs and real-output/package regression checks.

- TVR-15/16/30/31/32: Independent SQL/PLSQL classification, source-tagged results, optional cached automatic binding and failure/secret protection. Add fixed Unicode17 character data, dark ANSI8 cues/italic preservation, bilingual SQL APIs/examples and True Color/ANSI8 screens.

- TVR-15/16/30/31/32: Independent TextDocument wrapping/numbers/scrolling, real cursors/source-aware clicks, explicit markup/exact UTF-8 ranges, search/selection priority and stale-style expiry. Add viewer/editor backgrounds, disabled/secret handling, atomic source limits, bilingual examples/APIs and actual-output checks.

- TVR-15/16/30/31/32: Independent popup shadows (auto/solid/off/Dim) and dialogs with default Cancel and wrapped buttons. Add both-edge wide-glyph repair, covered-cursor/failure atomicity/disabled-input checks and bilingual examples, APIs and actual-output validation.

- TVR-15/16/30/31/32: Independent borderless Surface, actual-background text/control styles, contrast fallback and disabled Dim; preserve explicit selection/edited/field/header backgrounds and provide exact-style drawing. Update bilingual APIs/examples/screens and actual ANSI regressions.

- TVR-15/16/30/31/32: Independent configured row/column/grid/layer containers, modal focus restoration, captured pointer routing, clipped virtual child painting and cell/style/cursor copying; repair both source/destination wide-glyph edges and register Grid cursors after painting. Add bilingual APIs, integrated examples, actual screens and package/output regressions.

- TVR-15/16/30/31/32: Independent spacing/weighted stacks, drawer geometry, badges, request-only removable chips and literal priority hints; bilingual integrated examples, API and all-palette actual-output verification.

- TVR-15/16/30/31/32: Add independent notice queues, progress and data states with important-notice retention, atomic overflow rejection, expiry, host-handled retry/dismiss/cancel requests and disabled-action blocking. Include bilingual integrated examples, APIs, captures and actual-output checks.

- TVR-15/16/30/31/32: Add independent hierarchical menus, bars, context popups and placement, disabled blocking, mnemonics, return targets and background input blocking. Provide bilingual examples in five languages, narrow-area and actual-output wide-edge checks, and API documentation.

- TVR-15/16/30/31/32: Independent lists/search pickers with stable-ID selection, shared Unicode17 full case folding, disabled/secondary/icon rows, pending commit/cancel, real query cursors and bilingual examples. C output groups repeated SGR sequences while preserving rendered cells/styles/cursor; PTY CI is split by language.

- TVR-15/16/30/31/32: Independent host-owned focus scopes with atomic updates, input blocking, close requests, stable-ID restoration and a 64-popup limit.

- TVR-15/16/30/31/32: Independent forms/controls with validation, pending select commit/cancel, password/state handling, bounded pointer routing, real input cursors, and bilingual examples.

- TVR-15/16/30/31/32: Independent grapheme editing, literal UTF-8 ranges, password/read-only behavior, clipped real cursor drawing, and bilingual text examples.

- TVR-15/16/30/31/32: independent workspace components in all five language families; shared tab/path/status cases, compact split, hit testing, bilingual unified examples and 240 PTY combinations.

- TVR-15/16/30/31/32: independent Python, TS/JS, C, C++ and Java package foundations and Tree implementations; shared palettes/fixtures, local installation/linking and bilingual documentation. Epics remain in progress; full catalog parity and external publication are not complete.

## 0.11.1 — 2026-11-06

- TVR-7: Real Go/Rust inline-grid cursors, shared grapheme/cell/mouse viewport, focus/pending/NULL/clipping/closure lifetime and opt-in Go terminfo factory preserving cursor shape/blink. Rust adds Frame integration while retaining buffer-only Widget. Bilingual APIs/design/examples/references and backend cursor/PTY/escape regressions updated.

## 0.11.0 — 2026-11-06

- TVR-7: Go/Rust host-approved in-cell editing and navigation, independent dirty-cell/row-gutter cues, column pinning/visibility/reordering, quoted TSV paste requests, loaded-data find/global-search requests, serializable view state and raw-value details. Preserves the existing grid and default edit event. Adds shared fixtures, physical output/PTY coverage, bilingual APIs/design/examples and references. Available from 0.11.0.

## 0.10.2 — 2026-11-03

- Cumulative replacement including all TVR-29 improvements from withdrawn 0.10.1: Go/Rust half-row shadows, retained borders, dark contrast, drawing/input safety and bilingual examples/references.

- TVR-26: preserve backend build constraints in terminal/root facade generation, fix Windows import compilation, and add root-only OS/architecture consumers plus native Windows/macOS/Linux CI. Preserve API names and native-only example builds; update bilingual availability/API guides.

## 0.10.1 — 2026-11-03

**DO NOT USE:** withdrawn due to Windows Go facade compilation failure; retracted as a Go module. Upgrade to 0.10.2. [Details](docs/withdrawn-versions.en.md).

- TVR-29: replace the old two-cell/one-row default with compact Go/Rust half-row popup shadows; improve actual-backdrop contrast, ASCII fallback, geometry/input safety, wide-glyph regressions and bilingual references. Dim remains a whole-cell compatibility mode outside the example cycle.

## 0.10.0 — 2026-11-02

- TVR-18: add shared request-only tab/tree drag and drop, threshold/capture, immutable approved reorder/reparent, stable IDs/metadata, cycle/permission/stale rejection, temporary scrolling/expansion, keyboard alternatives and twelve-palette Unicode/ASCII feedback. Update bilingual design/API/guides/examples/screens and physical/PTY/consumer regressions.

- TVR-7: keep confirmation buttons inside narrow terminals, wrapping rows and retaining focused-button visibility, original indices/callbacks, keyboard/mouse and raw-backend interoperability. Update Go root/compatibility Modal, bilingual example/screens/API guidance.

## 0.9.2 — 2026-11-02

- TVR-7: improve dark/8 SQL highlighting with seven readable foreground/attribute combinations shared by Go/Rust and the Go legacy adapter; add physical rendering regressions and bilingual references.

- TVR-7 LazyOra defects: preserve CJK/emoji when a Table repaints backgrounds, selection or attributes through WideSafeScreen while retaining true-overlap repair. Fix twelve-palette splitter and comparison header/separator contrast; validate Go Show/Sync, the corresponding Rust path and an independent host. Improve the eight-color syntax policy.

- TVR-27 follow-up: fix first-paint styling so Go card padding does not retain the terminal background. align the Rust default playground with Go navigation, theme/color selectors, password, disabled button, and Auto color cycling; check example-only parity for twelve palettes and both localized guides. Align tree positioning and SQL editor padding/pointer coordinates, support `--option=value` through the unified launcher, and refresh bilingual docs and reference screens.

- TVR-8 follow-up: preserve Dim on eight-color disabled Go playground token samples and apply themed disabled styling to Styler.DropDown/Choice fields. Add post-Show twelve-palette/theme-round-trip/input-blocking regressions and bilingual Go reference images.

## 0.9.1 — 2026-11-01

- TVR-28: reserve `bin/` for executables; move temporary outputs, release archives and historical worktrees to `.cache/`. Consolidate root example guidance and evidence into `docs/`, updating links, build paths and bilingual layout documentation.

- TVR-27: combine Go/Rust interactive demos into one executable per language, selected with `--demo`. Build statically only for the current Linux host architecture and retire obsolete local example binaries. Update bilingual usage/build guides and unified PTY validation.

## 0.9.0 — 2026-11-01

- TVR-24 follow-up: optional Oracle SQL/PLSQL highlighting analyzer, shared byte tokens/role fallbacks, custom analysis and source-tagged worker results. Add edit/undo refresh, search/selection/disabled precedence, byte selection/replacement, existing Go syntax-color adapter, linear span application and 10,000-line validation. Update root-only Go/Rust feature examples, bilingual previews/APIs/specifications. Go/Rust source analyzers remain planned; SQL execution/safety and actual LazyOra migration are excluded.

## 0.8.0 — 2026-10-31

- TVR-26 follow-up: compose apps, screens, events, colors and shared components through the single Go root package. Keep semantic model names; distinguish conflicting compatibility widgets with Widget names. Preserve /ui and /terminal paths; update public examples, external consumer checks and bilingual APIs/guides.

## 0.7.0 — 2026-10-31

- TVR-26: Add language-neutral UI rules, Go ui/terminal and Rust ui/terminal paths reusing existing types/widgets/renderers. Provide shared InputEvent/edit requests, byte syntax-range conversion, Rust Session lifetime/restoration and SDK-only examples/external conformance checks. Future languages and ABI support remain designs, not implemented products.

## 0.6.0 — 2026-10-31

- TVR-22–25: Add borderless opaque surfaces, secret/standalone controls and rich form operations, grapheme-safe text editing/viewing with explicit markup, and row/column/grid/layer/drawer layout execution. Reuse existing models/styles, preserve state/input isolation, and provide bilingual examples, source-generated APIs and regression fixtures. Fix duplicated focused Rust panel titles. Full backend facade TVR-26 remains separate.

- TVR-21: Reorganize documentation by purpose, add source-generated Go/Rust public API references and CI drift detection, and refresh current installation/version guidance. Existing guide paths and historical evidence remain available.

## 0.5.0 — 2026-10-30

- TVR-19: Add default-off popup shadows through Go `ShadowView`, Rust `ShadowWidget` and menu popups: Auto/Solid/Dim, default two-cell-right/one-row-down shadows with softer Auto shading, full-footprint placement, card-only input, wide-glyph boundary protection, bilingual examples and 12-palette images. [Usage](docs/popup-shadows.en.md).

- TVR-20: audit API overlap; deprecate six Go methods/fields and four Rust methods/fields with replacements while preserving legacy behavior. Add warning-free menu constructors, bilingual migration guides and source/doc checks; correct current Go version guidance to 0.4.0.

## 0.4.0 — 2026-10-30

- TVR-7: do not automatically prefix ordinary disabled items with `[-]` or `-`. Keep checkbox, radio, and check-menu selection indicators. Disabled labels, values, buttons, and notice actions use the disabled role with muted foregrounds and no active background. Use gray at 16 colors or higher and `Dim` at 8 colors. Block pointer activation/focus and keyboard execution; clicking a disabled option must not move parent focus. [Twelve-palette comparison and limits](docs/disabled-states.en.md).


- TVR-7: fix plain-text background leakage across Go/Rust rows, paths/status, notifications/progress/data states and labels; bind real surfaces with contrast correction. Preserve explicit state/grid/custom backgrounds, align direct Go choice helpers and hosts, and synchronize bilingual design rules/docs/live references.

- TVR-7: fix the Go playground resize deadlock caused by page/focus changes under the draw lock; queue reflow on the UI loop and add bilingual PTY resize/exit CI regression.

- TVR-7: align Go explorer/token/help focus border colors with cards; verify double active/single inactive borders across explorer/editor/grid/dialog areas, preserving the single-border menu exception. Add bilingual live references and physical output regressions.

- TVR-7: use single menu popup borders without separate title/item focus decoration. Preserve selection/open-menu cues, input blocking and caller restoration.

## 0.3.0 — 2026-10-29

- Stop CentOS validation per user instruction and remove the CI VM stage. Preserve static distribution, ELF inspection and normal execution checks; retain previous results as history.

- TVR-7: add Go/Rust Menu/bar/popup, hierarchical entry/return, disabled/shortcut cues and original caller requests informed by LazyOra. Hosts retain commands/global keys; include shared navigation fixtures, bilingual hosts/docs/references and rendering/PTY/external-import checks.

- TVR-7: clarify component-library/application responsibilities and actual support; demonstrate host-selected layout/focus order/quit keys with the same Go/Rust components. Provide nested menus through the shared Menu in this release.

- TVR-17: extend the existing Go/Rust grid with presentation/input options, simple/data presets, range copy, stale-response protection, public catalog comparisons and bilingual documentation/images.

- Treat Python/TypeScript/JavaScript support as normal runtime-based packages without mandatory static distribution, standalone executables or CentOS checks; align work rules, contribution/distribution guides and TVR-15/16 scope.

- Align documentation and public API descriptions: use specification for shared design/API definitions and rules for interaction, input handling and navigation; keep Korean/English wording synchronized.

## 0.2.0 — 2026-10-28

- TVR-14: Go [wide-glyph overlay drawing](docs/overlay-drawing.en.md). Shared APIs repair both popup/card/shadow edges and stale continuations, with physical output regressions after Show.

- TVR-13: [Layout, density and supporting components](docs/layout.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-12: [Notices, progress and data states](docs/feedback.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-11: [Tables and data grid](docs/grid.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-10: [Lists, menus and search selection](docs/collections.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-9: [Inputs and forms](docs/forms.en.md). Shared Go/Rust models, renderers, executable hosts, validation and bilingual documentation/references; included in 0.2.0.

- TVR-8 shared control-state/focus/popup foundation: public Go/Rust state composition, stable-ID navigation, nested scopes, dismissal/restoration and input routing; executable hosts, twelve localized references, shared specifications, PTY and external static-host checks. [API](docs/focus.en.md) · [ordered backlog](docs/components-backlog.en.md). Included in v0.2.0 tags.

- Apply static distribution and host-linking requirements to Go, Rust and future languages. Add Rust musl/bundled LLD, Go CGO-disabled ELF checks, explicit x86_64 builds and CentOS 7.4 kernel/external-host validation. Existing v0.1.0 tags/assets remain unchanged. [Support scope](docs/static-build.en.md)

## 0.1.0 — 2026-10-27

- Implemented remaining TVR-7 UI: independent active/focused tabs, overflow and edited/close requests, padded focus/ASCII panels, column/row splits with keys/dragging and compact restoration, breadcrumb omission/navigation, semantic status/shortcut priorities and packing. Added public Go/Rust APIs, external usage checks, bilingual integrated examples, eight reference SVGs, PTY input checks and synchronized guides; distributed in v0.1.0.


- TVR-7 support audit and shared Tree: Go/tview and Rust/Ratatui stable IDs, expansion/selection/scroll, node metadata, keyboard/mouse and ASCII, shared navigation rules, external imports, bilingual examples and images. Tree changes are included in v0.1.0; tabs, panels, status, and breadcrumbs are included in the subsequent implementation below.

- Added the Rust core crate: candidate tokens, profiles, color/style values, strict JSON validation, embedded distribution data, and external project usage validation. Added an optional Ratatui 0.30.2 adapter, Crossterm 0.29 bilingual interactive example, Linux ARM64 build, language-matched reference images, and PTY checks. The core requires Rust 1.85+; the adapter/example require 1.88+. Distributed through Git tag `rust/v0.1.0`; there is no crates.io release.

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
