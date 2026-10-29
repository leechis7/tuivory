# Component background audit — TVR-7

[한국어 (default)](background-audit.md) · **English**

Follow-up: user authorized fixes under the [surface design rules](../design/surfaces.en.md) and [fix evidence](../evidence/background-fix.en.md). The audit below is historical pre-fix evidence; preserve its hashes and observations.

Audited on 2026-10-29, including uncommitted menu/focus changes after 0.3.0. **Text backgrounds differing from their component surfaces are confirmed.** This request is an audit: no renderer, token or host implementation was fixed. Existing work is preserved. [Exact results/source hashes](../evidence/background-audit-results.json).

## Scope and method

- Go: 47 cases × 12 palettes = **564 renderings**, covering shared models/Rows, Tree/tabs/menus/lines/panels/splits and direct/Apply/Form paths of the existing tview Styler. Inspect physical Runes/Styles after Show.
- Rust: 32 cases × 12 palettes = **384 renderings**, using the same model/Rows paths and dedicated Tree/tabs/menu/popup/Line/panel/split renderers with TestBackend cells. Row-based components use each real model's layout and the same public Rows renderer used by their thin specialized wrappers.
- Total **948**, dark/light/blackwhite × 8/16/256/truecolor. Controlled cell probes use 48×12 ASCII data to isolate background behavior from character width.
- Generate **156** current Rust host references: 144 Korean scenes across all palettes plus 12 dark-256 English mirrors. Scenes cover playground/dialog, Tree, workspace, focus/dialog, menus and five catalog modes. Cross-check Go host color bindings through source and existing actual Go references.
- Surface/text/row-edge differences are observations, not defect counts. Interpret field/selection/edit/stripe/frame/host-child backgrounds in context.

## Confirmed causes and findings

| ID | Finding | Affected paths |
| --- | --- | --- |
| BG-1 | Rows fills surface, then paints text with a complete body/info/success/warning/error style including canvas background. A differently colored strip ends at the text length. | Form labels/options, plain list/search results, shortcut hints, notices, progress/spinners, data states |
| BG-2 | Line renderers likewise apply complete semantic styles to glyphs. | Current breadcrumb segment and body/info/warning/error status items |
| BG-3 | Host examples use raw body/control styles inside surface panels. Ratatui Paragraph fills its assigned text rectangle with canvas background, contrasting with panel padding. | Rust menu preview/header, some focus/playground text regions. Go counterpart TextViews explicitly bind surface BG. Distinguish host composition from shared-control defects. |
| BG-4 | Direct Go Styler.DropDown/Choice changes field/list styles while a standalone box/label can retain default black. | Reproduced direct-helper path; Apply with a Panel surface is normal. Clarify standalone helper scope and surface binding. |

Sources: [Go RowsView](../go/rows_view.go#L30), [Rust RowsWidget](../rust/src/ratatui/rows.rs#L11), [Go drawLineRuns](../go/component_views.go#L450), [Rust LineWidget](../rust/src/ratatui/components.rs#L98). Distinct body/canvas and surface/panel tokens are valid design; globally making them equal would be inappropriate.

## Complete component assessment

| Component | Assessment |
| --- | --- |
| Forms/inputs | Label/plain option/error text context leakage confirmed. Distinct field/button backgrounds are intentional. |
| Tree | Plain primary/secondary text uses surface correctly; selection fills the row. Go frame-versus-selection differences are normal. |
| List | Plain unselected text leaks canvas BG. Glyph-length selection extent is a separate design review. |
| Search picker | Input field background is intentional; plain result rows share the list issue. |
| Menus/menu bar | Plain menu rows use surface correctly; selection fills complete spans. Open-menu bar highlighting is intentional. |
| Tabs | Inactive body versus active header backgrounds distinguish state and fill complete tab segments; not automatically a defect. |
| Panels | Own surface/frame is normal. An unstyled Go host TextView retaining black is a host-child context issue. Default Rust Paragraph inherits the existing surface. |
| Splitters | Surface/divider/focus.border binding is normal. |
| Breadcrumbs | Current body segment leaks canvas BG; preceding hint segments are normal. |
| Status bar | Body/semantic text leaks canvas BG; explicit selection/edit backgrounds remain separate. |
| Notices | Info/success/warning/error text needs surface context while retaining severity foreground/icons. |
| Progress/spinners | Default info text leaks BG. Separate plain-text background from progress-bar semantics. |
| Data states | Ready/loading/error text affected; empty hint already matches surface. |
| Badge | Default body creates a glyph-length background patch. Its intended badge-surface policy is unspecified and needs a design decision. |
| Chip | Same default-body path; decide whole-chip versus internal-text surface policy first. |
| Shortcut hints | Normal body rows leak; disabled rows match surface, making only enabled entries appear as strips. |
| Data grid | Simple UseSurface=false is a documented canvas choice. Review cell-versus-empty-area continuity without declaring the option defective. Data UseSurface/current-row/stripes/selection/edit differences are intentional. |
| Focus/spacing/density/Stack/Drawer geometry | State/coordinate APIs do not paint text; attached renderers/hosts own the actual background. |

## Reproducing profiles

| Profile | body/canvas BG | surface/panel BG |
| --- | --- | --- |
| dark-256 | 236 (#303030) | 237 (#3a3a3a) |
| dark-truecolor | #2e3440 | #3b4252 |
| light-16 | 15 (reference #ffffff) | 7 (reference #c0c0c0) |
| light-256 | 255 (#eeeeee) | 254 (#e4e4e4) |
| light-truecolor | #f3f5f7 | #e4eaf0 |

Common plain-text leakage reproduces in these five profiles in both languages. Other profiles have equal backgrounds, masking the same path. This does not limit intentional field/selection differences or standalone Go helper/default-black issues to these five. Physical ANSI RGB values depend on terminal settings.

Example: dark-256 Help `[Enter] Run` has BG 236 while trailing space has 237. Plain menu rows use 237 throughout; selected menu rows use 24 throughout. See illustrative_cells in the results JSON.

## Recommended fix order (not implemented)

1. Bind actual drawing-surface context in Rows and Line renderers. Plain/secondary/status text should inherit it; explicit field/button/selection/edited regions retain their own BG. Do not blanket-override grid/custom-role backgrounds.
2. Recheck foreground contrast on the actual surface. Moving reference **light-16 success** foreground #008000 onto surface #c0c0c0 without adjusting it yields **about 2.82:1**. This is a prospective background-only-change calculation, not a newly asserted current contrast defect. Go host textOnSurface already combines background binding and contrast adjustment.
3. Align Go/Rust host text regions and existing direct Go helper surface rules.
4. Decide badge/chip, simple-grid empty-area and list-selection extent policies, then validate physical before/after output and state preservation during theme/profile changes.

## Limits and preservation

No physical servers/SSH/fonts, remote CI, CentOS validation, commits, publication or release. Rendering/differing-cell counts are not bug counts. Audit the extracted Go Styler and shared candidate palette as distinct color systems. Probes/raw logs/156 references remain in local ignored bin/validation/background-audit/; the tracked results JSON records summaries, representative cells and source/evidence hashes.
