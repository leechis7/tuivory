# 전면 레이어 입력과 분할창 포커스

**한국어 (기본)** · [English](layer-input.en.md)

팝업이나 다른 작업 화면이 앞에 있을 때, 그 화면이 처리하지 않은 입력도 뒤쪽 편집기로 전달하지 않습니다. 앱은 화면 순서·전면 레이어 ID·통과 영역을 정하고, Tuivory는 입력 대상과 제스처 취소를 처리합니다.

Go에서 레이어 스택을 앱의 입력 루트로 둡니다. 화면을 열거나 닫을 때 같은 스택의 자식만 바꾸면, 스택이 캡처를 취소하고 닫힌 화면의 이전 포커스를 복원합니다.

```go
base := tuivory.ContainerChild{Item: tuivory.LayoutItem{ID: "workspace"}, Child: workspace}
layers, err := tuivory.NewLayerStack([]tuivory.ContainerChild{base}, palette)
if err != nil { return err }

layers.SetFrontInput(true, nil) // 스택 전체에서 전면 레이어만 입력
app.SetRoot(layers, true).SetFocus(layers)

// 열기: overlay는 ID와 표시 크기가 지정된 ContainerChild입니다.
if err := layers.SetChildren([]tuivory.ContainerChild{base, overlay}); err != nil { return err }
// 닫기: 같은 스택을 유지합니다.
if err := layers.SetChildren([]tuivory.ContainerChild{base}); err != nil { return err }
```

의도된 예외가 있으면 `SetFrontInput(true, func(x, y int) bool { ... })`에 화면 좌표로 영역을 전달합니다. 해당 위치의 포인터 입력만 전면 레이어 아래로 통과할 수 있습니다. 키보드와 붙여넣기는 여전히 전면의 실제 포커스만 사용하며, 포커스가 없으면 전달하지 않습니다. 같은 자식과 ID로 작업공간 내용만 교체할 때는 `InvalidateLayerInput()`을 먼저 호출합니다. 사용자 정의 자식이 드래그 상태를 저장한다면 `CancelPointer()`에서 정리하세요.

`SplitView`의 키와 붙여넣기는 포커스가 있는 표시 중 패널로 전달됩니다. 선택하지 않고 포인터만 넘기는 동작은 포커스를 옮기지 않습니다. 전역 키와 Tab 순서는 앱이 정합니다.

Rust와 독립 SDK는 호스트 입력 루프에서 같은 모델을 호출합니다. Rust에서는 `tuivory::layer_input::LayerInput`과 `ContainerState`를 함께 쓸 수 있습니다. 열고 닫을 때 `set_front`로 범위를 바꾸고, 반환된 ID의 캡처를 취소합니다. `ContainerState::reconcile`은 앱이 모달로 표시한 레이어를 닫을 때 이전 포커스를 복원합니다.

```rust
let cancelled = gate.set_front("popup");
for layer in cancelled { host.cancel_pointer(&layer); }
let route = gate.pointer("down", 1, hit_layer, in_pass_through);
if !route.target.is_empty() { host.dispatch_pointer(&route.target, &route.action); }
let target = gate.keyboard_target(focused_layer);
if !target.is_empty() { host.dispatch_key_or_paste(target, input); }
```

- 히트 테스트로 얻은 레이어 ID를 전달합니다. 통과 영역에서는 전면을 건너뛴 ID를 전달합니다. 대상 없음과 빈 반환값은 입력을 소비하라는 뜻입니다.
- 포인터 이벤트는 `down`, `move`, `up`, `click`, `double`, `wheel`을 사용합니다. 같은 누름·놓기·클릭에서 동일한 버튼 ID(1–255)를 쓰고, 버튼을 모르는 이동이나 휠은 0을 씁니다. 놓기 후 클릭을 보고하는 백엔드는 순서대로 두 이벤트를 전달합니다. 더블 클릭이 화면 전환을 가로지르면 첫 클릭은 `click`으로 돌아옵니다.
- Python, TypeScript/JavaScript, C++, Java는 `LayerInput`을, C는 `tui_layer_input_*`를 제공합니다. C에서는 캡처를 취소할 ID를 콜백으로 받습니다. Shell 참조 구현에는 레이어나 분할창 입력 라우터가 없습니다.

[입력 경계 테스트 사례](../design/layer-input-cases.json) · [컴포넌트와 앱 책임](component-boundary.md)
