# Front-layer input and split-pane focus

[한국어 (기본)](layer-input.md) · **English**

When a popup or another workspace is in front, input that it declines does not fall through to an editor behind it. The application chooses stacking order, the front layer ID, and any pass-through regions. Tuivory handles event targeting and gesture cancellation.

In Go, keep the layer stack mounted as the application input root. Change its children to open and close a layer. The stack cancels outstanding capture and restores the prior focus when the front layer closes.

```go
base := tuivory.ContainerChild{Item: tuivory.LayoutItem{ID: "workspace"}, Child: workspace}
layers, err := tuivory.NewLayerStack([]tuivory.ContainerChild{base}, palette)
if err != nil { return err }

layers.SetFrontInput(true, nil) // Input goes to the front layer only.
app.SetRoot(layers, true).SetFocus(layers)

// Open: overlay is a ContainerChild with its own ID and display bounds.
if err := layers.SetChildren([]tuivory.ContainerChild{base, overlay}); err != nil { return err }
// Close: keep the same layer stack.
if err := layers.SetChildren([]tuivory.ContainerChild{base}); err != nil { return err }
```

To allow exceptions, pass a screen-coordinate predicate to `SetFrontInput(true, func(x, y int) bool { ... })`. Only pointer input can pass behind the front layer at those positions. Keys and paste still require actual focus on the front layer. They are consumed when it has no focus. Call `InvalidateLayerInput()` before replacing workspace contents under the same child and ID. Custom children that hold drag state can clear it in `CancelPointer()`.

`SplitView` sends keys and paste to the visible pane that owns focus. Moving the pointer across a divider does not transfer focus. The app still decides global shortcuts and Tab order.

Rust and the independent SDKs expose the same model for a host input loop. In Rust, use `tuivory::layer_input::LayerInput` with `ContainerState`. Use `set_front` on open or close and cancel outstanding capture for each returned ID. When a layer marked modal closes, `ContainerState::reconcile` restores the previous focus.

```rust
let cancelled = gate.set_front("popup");
for layer in cancelled { host.cancel_pointer(&layer); }
let route = gate.pointer("down", 1, hit_layer, in_pass_through);
if !route.target.is_empty() { host.dispatch_pointer(&route.target, &route.action); }
let target = gate.keyboard_target(focused_layer);
if !target.is_empty() { host.dispatch_key_or_paste(target, input); }
```

- Pass the layer ID from hit testing. In a pass-through region, hit-test behind the front layer. Use an empty ID for no target. An empty result means consume the event.
- Pointer actions are `down`, `move`, `up`, `click`, `double`, and `wheel`. Use the same button ID (1–255) for a press, release, and click. Use 0 for unknown-button motion or wheel. If the backend reports a release followed by a click, forward both in that order. A double-click across a scope change is returned as a single `click`.
- Python, TypeScript/JavaScript, C++, and Java expose `LayerInput`; C exposes `tui_layer_input_*` and reports the capture to cancel via callback. The Shell reference has no layer or split-pane input router.

[Input routing fixtures](../design/layer-input-cases.json) · [Component and application responsibilities](component-boundary.en.md)
