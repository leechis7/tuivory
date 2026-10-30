# API 지원 상태와 전환 안내

**한국어 (기본)** · [English](api-lifecycle.en.md)

현재 공개 릴리스는 **0.4.0**입니다. 아래 TVR-20 변경은 **0.4.0 이후 미배포 작업 소스**에만 있습니다. 기존 `go/v0.4.0`·`rust/v0.4.0` 태그를 수정하지 않으며, 새 Rust 생성자도 해당 태그에는 없습니다. 현재 작업 소스를 path 의존성으로 적용하거나 후속 릴리스 안내를 확인하세요. 제품 `VERSION`은 이번 작업에서 올리지 않습니다.

## 상태를 읽는 방법

| 상태 | 의미 | 새 코드에서의 사용 |
| --- | --- | --- |
| 지원 | 현재 목적에 맞게 제공하는 API | 사용 가능. 저수준 API도 포함 |
| 호환용 | 이전 코드 지원을 위해 남은 형태. 효과·제약을 따로 명시 | 권장 경로를 먼저 확인. 이 상태만으로 컴파일 경고를 붙이지 않음 |
| Deprecated | 대체 경로가 마련되어 새 사용을 중단하도록 안내하는 API | 대체 API로 전환. 지정 시점·이유·예제를 확인 |
| 제거됨 | 실제 소스/배포에서 없어진 API | 제거 릴리스와 이전 API → 대체 API 전환 안내 확인 |

지원 중인 기능을 단순히 더 편리한 API가 생겼다는 이유로 Deprecated로 지정하지 않습니다. Deprecated 지정은 즉시 제거한다는 뜻이 아닙니다. 제거 버전은 별도로 검토·승인하고 사전에 문서화합니다. 제품 major 버전은 사용자만 결정합니다. 이번 작업에서 제거한 API는 없습니다. 기본 지원 판정은 영구 유지 약속이 아니며, 아래 중복 점검 결과와 대체 기능이 바뀌면 다시 검토합니다.

## 현재 점검표

별도 Deprecated 목록에 없는 공개 API는 지원 상태입니다. 아래는 혼동하기 쉬운 주요 API의 용도와 명시적 예외입니다. 전체 공개 심볼의 재정의가 아닌, 지원 상태의 기본 규칙과 예외 목록입니다.

| 언어/API | 상태 | 용도 또는 전환 경로 |
| --- | --- | --- |
| Go `Styler`·공통 컴포넌트 모델/뷰 | 지원 | 기존 위젯 스타일 적용과 공통 컴포넌트 조작·그리기 |
| Go `Styles.PopupShadowStyle`·`DimRegion`·`WideSafeScreen` | 지원 | 직접 그리는 팝업/그림자·두 칸 문자 경계 보호. 현재 지원. TVR-19 옵션 구현 후 동등한 대체 가능 범위를 재검토 |
| Go `Pair.Style`·`ControlStyle` / Rust `Styles::role`·`Styles::control` | 지원 | 원래 역할의 명시적 배경을 사용하는 직접 조합. 표면 지정 API와 목적이 다름 |
| Go `TextOnSurface`·`ControlStyleOnSurface` / Rust `text_on_surface`·`control_on_surface` | 지원, 0.4.0부터 | 실제 표면 위 평문 배경·대비·상태 처리 |
| Go `RowsView.PreserveBackgrounds` / Rust `RowsWidget::preserve_backgrounds`·`RawRowsWidget` | 지원, 0.4.0부터 | 명시적 역할 배경을 보존하는 그리드/사용자 행 조합 |
| Rust `MenuWidget`·`MenuBarWidget`·`MenuPopupWidget` | 지원 | 타입·메뉴 모델·입력 동작은 계속 지원. 미배포 소스에서 `new` 생성자 권장 |
| Go `Colors.SelectionText` | Deprecated — 미배포 | 렌더링이 읽지 않는 과거 값 사본. 실제 전경은 `Styles.SelectionFG` |
| Go `Styles.FieldStyle` | Deprecated — 미배포 | `Styles.TextStyle(Field, Body)` — 사용자 색상 조정도 동일 |
| Go `Styles.FooterButtonStyle` | Deprecated — 미배포 | `Styles.TextStyle(Footer, Body)` |
| Go `Styles.PopupCardStyle` | Deprecated — 미배포 | `Styles.TextStyle(Panel, Body)` |
| Go `Styler.Table` | Deprecated — 미배포 | `Styler.TableOn(table, Canvas)` |
| Go `Grid.Click` | Deprecated — 미배포 | 마우스는 `Grid.Pointer`, 프로그램 제어는 `Focus`+`Handle` |
| Rust `Grid::click` | Deprecated — 미배포 | 마우스는 `Grid::pointer`, 프로그램 제어는 `focus`+`handle` |
| Rust `MenuWidget::focused` | Deprecated — 미배포 | `MenuWidget::new(model, styles).ascii(ascii)` |
| Rust `MenuBarWidget::focused` | Deprecated — 미배포 | `MenuBarWidget::new(model, styles)` |
| Rust `MenuPopupWidget::focused` | Deprecated — 미배포 | `MenuPopupWidget::new(model, styles, title).ascii(ascii).padding(padding)` |
| Rust 일반 `RowsWidget`·`FormWidget` 등의 `focused` | 지원 | 실제 포커스 표시를 제어함. 메뉴의 효과 없는 필드와 구분 |

### Rust 메뉴 focused 필드 3개

- 이유: 0.4.0부터 메뉴는 입력 포커스와 별개로 선택/열림 상태만 그립니다. 이 필드들은 호환 목적으로 남아 있었으며 표시 효과가 없습니다.
- 지정 시점: TVR-20, 0.4.0 이후 미배포 작업 소스. **Deprecated가 처음 배포될 버전은 아직 미정**이며 `#[deprecated]`의 `since`를 임의의 0.4.0으로 표시하지 않습니다.
- 대체 경로: 위 `new` 생성자와 `ascii`/`padding` 설정 메서드. Unicode, padding=1이 기본값이며 메뉴 바에는 추가 설정이 없습니다.
- 기존 구조체 리터럴은 계속 컴파일되지만 해당 필드를 지정하면 Deprecated 경고가 납니다. `deny(deprecated)`나 경고를 오류로 처리하는 앱은 새 경로로 전환해야 합니다. 필드를 제거하거나 실제 입력 포커스 동작을 바꾸지는 않습니다.
- 제거 계획: **미정**. 현재 릴리스나 다음 릴리스에서 자동 제거하지 않습니다.

```rust
// 이전 코드: 미배포 소스에서는 focused 필드에 경고가 남
let popup = MenuPopupWidget {
    model: &mut menu,
    styles: &styles,
    title: "Menu",
    ascii: true,
    focused: true,
    padding: 1,
};

// 권장 코드: 미배포 소스의 새 생성자, deprecated 경고 없음
let popup = MenuPopupWidget::new(&mut menu, &styles, "Menu")
    .ascii(true)
    .padding(1);
```

위 두 블록은 전환 전/후의 대안입니다. 앱이 기존처럼 메뉴 모델의 선택과 열림 상태, 입력 포커스·배경 차단·원래 호출 위치 복귀를 연결합니다. 생성자가 앱의 전역 포커스 정책을 결정하지 않습니다.

## 코드·문서·릴리스 갱신 절차

1. 사용 중단 이유와 경고 없이 사용할 대체 API를 먼저 마련합니다. 필요한 설정·동작·성능을 보존하고 기존 사용 경로도 검증합니다.
2. [상태 목록](../design/api-lifecycle.json)에 대상·상태·대체 API·사유·지정 시점·제거 계획을 기록하고 이 한영 사용 문서를 함께 수정합니다.
3. Go는 해당 공개 선언의 GoDoc 문단에 `Deprecated: ...`를, Rust는 해당 심볼에 `#[deprecated(note = "...")]`를 붙입니다. 타입 전체를 중단하지 않는다면 필드/메서드에만 표시합니다. 이번 미배포 작업에서는 위 Go 메서드/필드 6개에 GoDoc 표시를 추가했습니다. Go 컴파일러 자체는 Deprecated 경고를 내지 않으며 GoDoc·IDE·분석 도구가 이 정보를 사용합니다.
4. 미배포 항목을 릴리스할 때 `availability`를 `released`로 바꾸고 `deprecated_since`를 첫 배포 버전으로 기록합니다. Rust의 `since`와 한영 문서에도 같은 버전을 반영합니다. 기존 태그와 과거 도입 버전을 바꾸지 않습니다.
5. 제거가 승인되면 실제 제거 릴리스·전환 방법을 안내하고 목록을 `removed`로 갱신합니다. 제거 이력도 보존합니다. 현재는 제거 항목이 없습니다.
6. 자체 예제와 독립 적용 앱은 경고 없는 경로를 사용합니다. 호환 회귀를 위한 오래된 호출만 좁은 범위에서 경고를 허용하며 라이브러리/프로젝트 전체의 Deprecated 경고를 숨기지 않습니다.

```sh
python3 tools/check_api_lifecycle.py
```

이 검사는 Go/Rust 소스의 Deprecated 표시와 목록·한영 문서·대체 선언을 대조합니다. CI의 validate 단계에도 연결합니다. 새 API 사용법은 [Go](go-package.md), [Rust](../rust/README.md), [메뉴](menus.md)를 참고하세요. 로컬 검증과 원격 CI/게시 상태는 작업 결과에서 구분합니다.

## 중복 기능의 전환과 차이

단순 이름 유사성이 아니라 반환 스타일·표면·옵션·입력·데이터 소유권을 비교합니다. [전체 API 영역별 중복 점검](api-overlap-audit.md)에 각 판단의 근거를 기록합니다. 현재 미배포 Deprecated 대상은 Go 메서드/필드 6개와 Rust 메서드/필드 4개, 총 10개입니다. 지정/첫 배포 버전·제거 계획은 모두 위와 같이 미배포/미정입니다.

```go
// 이전 -> 권장: 동일한 스타일/Canvas 표면
field := styles.TextStyle(tuivory.Field, tuivory.Body)   // FieldStyle() 대체
footer := styles.TextStyle(tuivory.Footer, tuivory.Body) // FooterButtonStyle() 대체
card := styles.TextStyle(tuivory.Panel, tuivory.Body)    // PopupCardStyle() 대체
styler.TableOn(table, tuivory.Canvas)                  // Table(table) 대체
```

기존 스타일 메서드는 동작을 유지합니다. `TableOn`에는 기존과 같은 `Canvas`를 지정해야 하며 `Panel`로 바꾸면 배경도 달라집니다. 위 Go 대체 경로와 Grid 포인터 API는 공개 0.4.0에서도 사용할 수 있습니다.

```go
// 마우스 좌표는 그리드 내부 셀 좌표로 변환해서 전달
// 기존 Grid.Click(rowID, kind, x, width, height) 대신:
event := grid.Pointer("click", localX, localY, width, height, false)
// 영역 밖 move/up도 드래그 캡처 중 전달해야 함
```

```rust
let event = grid.pointer("click", local_x, local_y, width, height, false);
```

`Grid.Click/click`은 행 ID·x 좌표·`@header` 구분값을 섞은 이전 마우스 진입점입니다. `Pointer/pointer`는 행 좌표·헤더·여백·드래그·범위·휠·마우스 비활성 옵션을 같은 경로에서 처리합니다. 이전 메서드는 호환을 위해 원래 동작(직접 호출 시 DisableMouse를 적용하지 않음)도 유지합니다. 따라서 무조건 인수만 바꾸는 전환이 아닙니다. 직접 행/열 ID를 지정하려는 앱은 `Focus/focus` 뒤 `Handle/handle("select")` 또는 `"sort"`를 호출합니다. 포인터 경로는 마우스 비활성 설정을 따릅니다.

`Colors.SelectionText`(Styles에 승격된 같은 필드 포함)는 기존 팔레트 값 보존용 사본입니다. 이 필드에 쓰더라도 선택 색상을 바꾸지 않습니다. 실제 설정은 `styles.SelectionFG = color`이며, `SelectionStyle()`에서 사용합니다. 기존 필드의 값·순서·구조체 리터럴 호환성은 유지합니다.
