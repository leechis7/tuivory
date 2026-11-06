# Independent language focus scope API

[한국어 (기본)](language-focus.md) · **English**

This unreleased TVR-15/16/30/31/32 API provides an independent `Focus` in all five languages. It is a pure model of host-defined targets and popup scopes; it does not draw screens or own event loops/global keys. It is absent from public 0.11.1.

| Feature | Python | TS/JS | C | C++ | Java |
| --- | --- | --- | --- | --- | --- |
| Construct | `Focus(id,targets)` | `new Focus(id,targets)` | `tui_focus_new` | `Focus(id,targets)` | `new Focus(id,targets)` |
| Target | `FocusTarget(id,state,hidden)` | `FocusTarget` | `TuiFocusTarget` | `FocusTarget` | `FocusTarget` |
| Current state | `scope_id/focused/depth` | `scopeId/focused/depth` | `tui_focus_scope/focused/depth` | `scope_id()/focused()/depth()` | `scopeId()/focused()/depth()` |
| Move | `focus(id)/move(previous)` | same | `tui_focus_focus/move` | same | same |
| Scope lifetime | `open/update/close` | same | `tui_focus_open/update/close` | same | same |
| Input route | `route(target)` | same | `tui_focus_route` | same | same |
| Close request | `request_close()` | `requestClose()` | `tui_focus_request_close` | `request_close()` | `requestClose()` |

Target and scope IDs must be nonempty and unique. Hidden/disabled targets are skipped, while read-only and busy targets remain focusable. Root depth is zero; up to 64 popup layers are allowed. `open(id,targets,initial,dismissible)` checks any explicit initial target before changing the stack. Invalid operations preserve prior state. Empty scopes are permitted.

`update(scope,targets)` copies targets and retains focus by stable ID. Removed, disabled, or hidden targets fall back to the first eligible target. Scopes beneath a popup can be updated; invalid updates preserve the entire stack. Closing restores the target that had focus before opening, or the current eligible fallback if it can no longer be restored.

`route('')` routes keyboard input to the top scope. Pointer callers supply the hit scope ID; a different scope produces `blocked=true`. **Empty popups still block input to underlying screens.** The route reports the top `scope_id/scopeId` and blocking decision; hosts perform actual delivery.

Escape is an example of a host global key that may call `requestClose`. A dismissible popup returns `{id,reason:'escape'}` without changing the stack. Locked popups and the root return no request. The host approves and calls `close(id)` explicitly. Stale callbacks for another popup and attempts to close the root are rejected. Outside clicks do not close automatically. No request is represented by an empty ID in C, `None` in Python, `undefined` in TS, and an optional in C++/Java.

```python
import tuivory as ui
focus = ui.Focus('screen', [ui.FocusTarget('open')])
focus.open('confirm', [ui.FocusTarget('cancel')], 'cancel', True)
assert focus.route('screen').blocked
request = focus.request_close()
if request:  # The host decides whether to close.
    focus.close(request.id)
assert focus.focused == 'open'
```

C constructors/updates copy IDs and targets, and `tui_focus_free` releases the entire stack. Returned strings/requests are borrowed until the relevant update, close, or destruction. C construction returns `NULL` on failure; operations return `TUI_INVALID/TUI_NOMEM`. Other languages throw. Python/TS/other runtimes and C++ also retain owned copies of input targets.

[Shared 24-step fixtures](../design/interaction-cases.json) cover nesting, input blocking, stable-ID updates, invalid initial targets, close requests, empty scopes, and restoration. Additional checks cover the 64-layer limit, ownership, external packages and C/C++ ASan/UBSan. [Evidence](evidence/language-focus-results.json) separates local checks from remote CI/publication. This pure state model introduces no new image or UI-capture claim. Unified popup composition examples will be connected in the menu/overlay milestone.

[Independent languages](languages.en.md) · [Forms](language-forms.en.md) · [API](api/README.en.md)
