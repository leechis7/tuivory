# Confirmation dialogs on small screens

[한국어 (default)](modals.md) · **English**

The 0.10.0 Go `NewModal()` clamps its window to the terminal and wraps long buttons across rows. Rust has no equivalent Go compatibility Modal type; compose dialogs with shared Form and layout containers.

```go
import ui "github.com/leechis7/tuivory/go"

modal := ui.NewModal().SetText("Handle pending changes.").
    AddButtons([]string{"Save changes and continue", "Discard changes and continue", "Cancel"}).SetFocus(2)
modal.SetDoneFunc(func(index int, label string) {
    // Original button index; Esc reports -1 and an empty label.
    // The host decides whether to save, discard or close the screen.
})
```

At small heights buttons take priority over message text. If all rows cannot fit, scroll to keep the focused button visible. At extreme sizes that cannot display a complete glyph, labels may be clipped. Enlarging the screen restores original labels and order. Tab/Shift+Tab, arrows, Enter, Esc, mouse and callbacks remain supported; `SetFocus` uses the original button order. Repeated `AddButtons` calls retain cumulative callback indices.

The root and compatibility `/ui` `Modal` is now an **SDK adapter embedding the backend Modal**, rather than a raw backend type alias. Existing SDK calls stay the same. For explicit interoperability with external code requiring the raw backend, pass `modal.Modal`; drawing that embedded object directly bypasses the responsive fix. Update text/buttons through SDK methods. `Styler.Modal` and `Apply` support both SDK and legacy backend Modals.

```sh
make build
./bin/go/tuivory-linux-arm64 --demo controls --modal --lang en --theme light --colors 8
```

The filename follows the host architecture. F2 changes theme, F3 color count; Ctrl+Q/Esc exits. The example only displays requests, without saving or DB connections.

![40-column light confirmation](images/modal-light-en.svg)
![40-column dark confirmation](images/modal-dark-en.svg)

Go physical post-`Show()` buffers check both languages × twelve palettes, 120→80→40→20→8→3→1 columns and recovery, button bounds/text/callbacks and keyboard/mouse. Images are references generated from those buffers, not physical font verification.

[Components](components.en.md) · [Public UI paths](ui-facade.en.md) · [API](api/go.en.md)

[Local validation record](evidence/tvr7-18-results.json): 216 Modal palette/language/size cases, Go/Rust shared drag and physical-buffer regressions, 58 bilingual PTY scenarios, isolated Go/packaged Rust consumers, core Rust 1.85.1 and native ARM64 static executables passed. This record preserves pre-publication local evidence. Final CI/public-tag/download checks are recorded in the [0.10.0 release](release-0.10.0.en.md) asset manifest.
