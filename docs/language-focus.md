# 독립 언어 포커스 범위 API

**한국어 (기본)** · [English](language-focus.en.md)

TVR-15·16·30·31·32의 API입니다. 다섯 언어의 `Focus`는 앱이 정한 대상 목록과 팝업 범위를 관리하는 순수 모델입니다. 화면을 그리거나 이벤트 루프·전역 키를 소유하지 않습니다. 0.12.0에서 제공합니다.

| 기능 | Python | TS/JS | C | C++ | Java |
| --- | --- | --- | --- | --- | --- |
| 생성 | `Focus(id,targets)` | `new Focus(id,targets)` | `tui_focus_new` | `Focus(id,targets)` | `new Focus(id,targets)` |
| 대상 | `FocusTarget(id,state,hidden)` | `FocusTarget` | `TuiFocusTarget` | `FocusTarget` | `FocusTarget` |
| 현재 상태 | `scope_id/focused/depth` | `scopeId/focused/depth` | `tui_focus_scope/focused/depth` | `scope_id()/focused()/depth()` | `scopeId()/focused()/depth()` |
| 이동 | `focus(id)/move(previous)` | 동일 | `tui_focus_focus/move` | 동일 | 동일 |
| 범위 수명 | `open/update/close` | 동일 | `tui_focus_open/update/close` | 동일 | 동일 |
| 입력 경로 | `route(target)` | 동일 | `tui_focus_route` | 동일 | 동일 |
| 닫기 요청 | `request_close()` | `requestClose()` | `tui_focus_request_close` | `request_close()` | `requestClose()` |

대상 ID와 범위 ID는 비어 있거나 중복될 수 없습니다. 숨김·비활성 대상은 건너뛰고 읽기 전용·busy 대상은 포커스를 받을 수 있습니다. 루트 깊이는 0이며 팝업은 최대 64단계입니다. `open(id,targets,initial,dismissible)`는 최초 대상이 있으면 포커스를 받을 수 있는지 먼저 확인하고, 실패하면 기존 상태를 보존합니다. 비어 있는 범위도 열 수 있습니다.

`update(scope,targets)`는 대상 목록을 복사하고 안정 ID로 포커스를 유지합니다. 대상이 사라지거나 비활성/숨김으로 바뀌면 첫 가능한 대상으로 이동합니다. 팝업 아래 범위도 갱신할 수 있으며 잘못된 갱신은 전체 스택을 보존합니다. 닫을 때는 팝업을 열기 전 대상 ID로 복원하고, 복원할 수 없으면 현재 가능한 대상을 사용합니다.

`route('')`는 키보드 입력을 최상위 범위로 보냅니다. 마우스는 적중한 범위 ID를 전달하며 최상위 범위와 다르면 `blocked=true`입니다. **대상이 없는 팝업도 아래 화면으로 입력을 흘리지 않습니다.** `route`는 최상위 `scope_id/scopeId`와 차단 여부만 반환하고 실제 이벤트 전달은 앱이 결정합니다.

Escape는 `request_close`를 호출할 수 있는 앱 전역 키의 예입니다. 닫기 가능한 팝업이면 `{id,reason:'escape'}` 요청을 반환하며 스택은 바꾸지 않습니다. 잠긴 팝업이나 루트에서는 요청이 없습니다. 앱이 승인한 후 `close(id)`로 실제 닫습니다. 다른 팝업의 오래된 콜백이나 루트 닫기는 거부합니다. 바깥 클릭은 자동으로 닫지 않습니다. C는 요청이 없으면 빈 ID, Python은 `None`, TS는 `undefined`, C++/Java는 optional을 반환합니다.

```python
import tuivory as ui
focus = ui.Focus('screen', [ui.FocusTarget('open')])
focus.open('confirm', [ui.FocusTarget('cancel')], 'cancel', True)
assert focus.route('screen').blocked
request = focus.request_close()
if request:  # 앱의 판단을 거쳐 실제 닫음
    focus.close(request.id)
assert focus.focused == 'open'
```

C 생성자와 갱신은 ID·대상을 복사하고 `tui_focus_free`가 전체 스택을 해제합니다. 반환된 문자열·요청은 빌린 값으로 관련 갱신/닫기/해제 전에만 사용합니다. C 생성 실패는 `NULL`, 조작 실패는 `TUI_INVALID/TUI_NOMEM`이며 다른 언어는 예외를 사용합니다. Python/TS/기타 런타임과 C++도 입력 대상을 소유한 사본으로 보관합니다.

[공유 24단계 사례](../design/interaction-cases.json)로 중첩·차단·안정 ID 갱신·잘못된 초기 대상·닫기 요청·빈 범위·복원을 검사합니다. 추가로 64단계 한계와 사본 소유권, 외부 패키지와 C/C++ ASan/UBSan을 검사합니다. [검증 기록](evidence/language-focus-results.json)에 로컬과 원격 CI·게시를 구분합니다. 순수 상태 모델이므로 새 화면 이미지나 UI 캡처 성공을 주장하지 않습니다. 팝업 조합은 [메뉴](language-menu.md)와 [오버레이 예제](language-popups.md)에서 제공합니다.

[독립 언어 지원](languages.md) · [폼](language-forms.md) · [API](api/README.md)
