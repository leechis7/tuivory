# Compose UI with Tuivory imports only

[Korean (default)](ui-facade.md) · **English**

0.8.0 TVR-26 provides go/ui, go/terminal, tuivory::ui, shared input and byte-span conversion. [Release/installation](release-0.8.0.en.md) · [Shared rules](../design/ui-facade.en.md) · [API guide](api/README.en.md).

**0.8.0:** compose Go UI through `github.com/leechis7/tuivory/go` alone. Existing `/ui` and `/terminal` paths remain compatible. [Single import and name mappings](ui-facade.en.md).

## Public paths

| Purpose | Go | Rust |
| --- | --- | --- |
| Shared models/components | github.com/leechis7/tuivory/go | forms/text/containers etc. |
| Application/legacy widgets | root package (compatibility: go/ui) | ui::Terminal/Frame, ui::widgets/layout/buffer/style/text etc. |
| Semantic renderers | Root New…View | Existing widgets/Styles under ui::components |
| Events/screens | root package (compatibility: go/terminal) | ui::terminal::{event,cursor,terminal,execute,…} |
| Shared input/edit requests | InputEvent, InputFromKey/InputFromMouse, EditingAction | input::InputEvent, from_key/from_terminal, editing_action |
| Terminal lifetime | tuivory.NewApplication Run/Stop/SetScreen | ui::Session, SessionOptions, finish/Drop |

Go uses one root import; existing /ui and /terminal paths remain supported without direct tview/tcell imports. Rust external manifests declare **only tuivory**, enabling the required features. Preserve existing root APIs and tuivory::ratatui paths. SDK compatibility aliases retain pinned backend type/method/trait identity; they do not promise source/ABI interchangeability across backend replacement.

Rust features: default core (1.85+), ratatui rendering (1.88+), terminal I/O (1.88+). The existing playground feature includes terminal as a compatible alias. Hosts retain database/global-key/clipboard execution policy.

## Migrating Go imports

```go
import tuivory "github.com/leechis7/tuivory/go"

app := tuivory.NewApplication()
view := tuivory.NewWidgetTextView().SetText("Hello / 한글")
app.SetRoot(view, true)
app.SetInputCapture(func(key *tuivory.EventKey) *tuivory.EventKey {
    if key.Key() == tuivory.KeyCtrlQ { app.Stop(); return nil }
    return key
})
// Handle app.Run() errors in your function.
```

Existing root NewForm/NewButton/NewGrid/NewList/NewTextView/NewTreeView semantics remain unchanged. Use the compatibility names below; return types, callbacks and inherited methods retain their identity. Prefer [shared components](controls.en.md) for new screens.

| /ui compatibility name | Single root import name |
| --- | --- |
| Button / NewButton | WidgetButton / NewWidgetButton |
| Form / NewForm | WidgetForm / NewWidgetForm |
| Grid / NewGrid | WidgetGrid / NewWidgetGrid |
| List / NewList | WidgetList / NewWidgetList |
| TextView / NewTextView | WidgetTextView / NewWidgetTextView |
| TreeView / NewTreeView | WidgetTreeView / NewWidgetTreeView |
| TreeNode / NewTreeNode | WidgetTreeNode / NewWidgetTreeNode |
| Theme / Styles / GetStyles / SetStyles | WidgetTheme / WidgetStyles / GetWidgetStyles / SetWidgetStyles |

Other application/primitive/box/input/textarea/flex/pages/table/color/event/constant/screen symbols keep their names at the root. Existing /ui and /terminal imports remain valid. See root and sdk fields in the [generated mapping](../design/go-facade-symbols.json).

Original Application behavior, including default Ctrl+C exit, is retained. Hosts assigning Ctrl+C to copy intercept it as in the [controls example](../go/examples/controls/main.go). Containers forward key/mouse/paste/drag input; hosts choose global behavior.

### Global configuration

Go cannot alias another package's variables. Borders/WidgetStyles are startup snapshots; assignment does not mutate backend globals. Use setters **before the event loop**. Concurrent runtime global updates are unsupported.

```go
theme := tuivory.GetWidgetStyles()
theme.PrimitiveBackgroundColor = tuivory.ColorBlack
tuivory.SetWidgetStyles(theme)
borders := tuivory.GetBorders()
borders.TopLeft = '+'
tuivory.SetBorders(borders)
```

DoubleClickInterval/NewLine/TabSize/DefaultFormFieldWidth/Height have Get…/Set… functions. SemigraphicJoints shares map entries; replace it with SetSemigraphicJoints. Terminal defaults/color maps are likewise startup values or shared maps; rebinding an SDK variable is not backend-global rebinding. See the [pinned symbol mapping](../design/go-facade-symbols.json); CI verifies generated output.

## Rust with one dependency

Use the public Git tag as a single dependency; a path to rust/ also works for local development.

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.8.0", features = ["terminal"] }
```

```rust
use tuivory::{
    input::InputEvent,
    text::TextDocument,
    ui::{Session, Terminal, backend::CrosstermBackend},
    ui::components::{Styles, TextWidget},
    ui::terminal::event::{self, Event, KeyCode, KeyModifiers},
    Theme, ColorProfile,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let session = Session::enter(Default::default())?;
    let mut terminal = Terminal::new(CrosstermBackend::new(std::io::stdout()))?;
    let styles = Styles::new(Theme::Light, ColorProfile::Indexed256)?;
    let mut text = TextDocument::editor("한글 é 😀");
    loop {
        terminal.draw(|f| f.render_widget(
            TextWidget { model: &mut text, styles: &styles, focused: true }, f.area()))?;
        if let Event::Key(key) = event::read()? {
            if key.code == KeyCode::Char('q') && key.modifiers.contains(KeyModifiers::CONTROL) { break; }
            let (action, value) = InputEvent::from_key(key).editing_action();
            text.handle(&action, &value);
        }
    }
    session.finish()?;
    Ok(())
}
```

The host selects the exit key. See [Rust controls](../rust/examples/controls/main.rs) for paste/mouse/resize/modal/theme composition. Session rejects duplicate entry and existing raw-mode ownership and cleans up initialization failures, finish/Drop and panic unwind. Forced termination/abort cannot guarantee restoration. Hosts retaining manual terminal lifetime can use SDK event/command compatibility paths.

## Removing the LazyOra fork

This work does not edit LazyOra. Downstream adoption occurs **using the 0.8.0 package**.

| Existing usage | SDK migration |
| --- | --- |
| tview/tcell types, constructors, constants, callbacks | root package and Widget name mappings above |
| Six fork-only Borders.…Focus fields and Box focus drawing | Shared PanelView/state presentation; Rust Styles.panel |
| Fork TextArea.SetTextStyleFunc byte-based styling | Shared Editor/TextView plus host spans and SetByteSyntax/set_byte_syntax |
| Standard TextArea/TextView retained temporarily | SDK compatibility widgets with upstream v0.42.0 behavior |
| third_party/tview replace | Remove after migrating extensions; rerun host app/tests |

Compatibility TextArea is upstream; fork-only methods are not claimed implemented. Byte ranges cutting combining/CJK/emoji clusters fail atomically, retaining previous highlighting. Keep drawing coordinates distinct from original UTF-8 positions.

```go
err := editor.SetByteSyntax([]tuivory.ByteSyntaxSpan{
    {Start: 0, End: 6, Role: "info"}, // Original byte range supplied by the host lexer
})
```

Rust uses text_offsets::ByteSyntaxSpan, TextDocument::set_byte_syntax and grapheme_index. Lexers, SQL execution and Vim/Toad keymaps remain host-owned. Downstream tests must preserve undo/redo/original text/masking/copy/focus and database-value semantics.

## Validation and availability

tools/check_ui_facade.py rejects direct backend imports in all public Go examples/root external tests and all Rust examples/UI conformance tests. Validate pinned Go exports, bilingual API declarations, shared input/byte-boundary scenarios and SDK-only isolated Go/packaged Rust consumers. Session PTY tests cover non-TTY initialization failure, duplicate entry, finish/re-entry and panic restoration.

Retain bilingual Unicode/ASCII, twelve-palette, popup/focus/selection/undo/redo/clipboard-request/resize regressions and static ARM64 checks. The [local validation snapshot](../evidence/ui-facade-results.json) is distinct from the [release validation manifest](https://github.com/leechis7/tuivory/releases/tag/go/v0.8.0). No CentOS validation. Python/JS/TS/C/C++ and ABI implementations remain [future work](../design/ui-facade.en.md).

[LazyOra package-symbol mappings](../evidence/ui-facade-consumer-map.json) audit first-party Go source/tests read-only; they do not claim app migration/build success. Compatibility widgets retain upstream diagnostic behavior; use shared password models for secret-safe display/diagnostic projections.

The [single-import local validation record](../evidence/go-single-import-results.json) is distinct from the [0.8.0 release validation manifest](https://github.com/leechis7/tuivory/releases/tag/go/v0.8.0).
