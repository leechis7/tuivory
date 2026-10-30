# 공개 API 중복 점검

**한국어 (기본)** · [English](api-overlap-audit.en.md)

TVR-20의 0.5.0 배포 대상 점검입니다. 메뉴 필드뿐 아니라 아래 공개 API 영역 전체를 비교했습니다. Go 루트의 공개 선언과 `Styles`/`Styler` 등 공개 별칭으로 노출되는 내부 메서드·필드, Rust의 전체 기능 rustdoc 공개 항목을 바탕으로 살폈습니다. tview/Ratatui 자체에서 상속·구현되는 외부 API를 Tuivory의 중복 API로 세지 않습니다. 자동 선언 목록은 위치 탐색 자료이며 의미상 중복 여부는 아래 동작 비교로 판단합니다.

## 정리하는 중복

| 대상 | 겹치는 동작/문제 | 대체 경로와 검증 |
| --- | --- | --- |
| Go `Styles.FieldStyle` | Field/Body와 같은 색·속성 | `TextStyle(Field, Body)`; 12팔레트·사용자 색상 변경 비교 |
| Go `Styles.FooterButtonStyle` | Footer/Body와 같은 색·속성 | `TextStyle(Footer, Body)`; 12팔레트·사용자 색상 변경 비교 |
| Go `Styles.PopupCardStyle` | Panel/Body로 그대로 전달 | `TextStyle(Panel, Body)`; 12팔레트·사용자 색상 변경 비교 |
| Go `Styler.Table` | `TableOn(table, Canvas)`와 같은 테이블 표시 | 명시적 표면 API로 통합; Show 이후 한글·CJK·선택·헤더·테두리 비교 |
| Go `Colors.SelectionText` | 선택 전경의 과거 사본. SDK가 읽는 값은 별도 `Styles.SelectionFG` | 실제 설정 `SelectionFG`로 통합. 사본 쓰기가 렌더링에 영향을 주지 않고 실제 설정은 적용되는지 검증 |
| Go `Grid.Click` / Rust `Grid::click` | 행 ID와 x 좌표를 섞은 이전 마우스 진입점 | `Pointer/pointer`로 입력 통합. 직접 ID 제어는 `Focus/focus`+`Handle/handle`. DisableMouse 적용 차이는 전환 안내에 명시 |
| Rust 메뉴 3종 `focused` | 0.4.0부터 표시 효과가 없는 호환 필드 | `new`·`ascii`·`padding`. 기존 리터럴과 새 경로의 12팔레트 출력·메뉴 상태 일치 검증 |

총 **10개** 공개 메서드/필드를 0.5.0 소스에서 Deprecated로 표시합니다. 모두 기존 동작과 이름을 남겨 소스 호환성을 보존하며 제거 시점은 미정입니다. 정확한 대상·이유·대체 코드·배포 상태는 [API 전환 안내](api-lifecycle.md)와 [상태 목록](../design/api-lifecycle.json)을 기준으로 확인합니다.

## 나머지 영역과 통합 조건

| 비교한 API 영역 | 판단과 근거 |
| --- | --- |
| `New` / `NewStyles`, `Styler` / `Styles` / `Colors` | 객체 위젯 적용·스타일 계산·값 데이터라는 층위가 다름. 하나의 결과 타입으로 통합하려면 실제 사용 경로·사용자 색상 설정을 먼저 설계해야 함 |
| Candidate 토큰 `Parse`/`Candidate`/`Resolve` / 기존 파생 스타일 | 팔레트 값과 역할 체계가 다름. 지금 같은 함수로 바꾸면 화면이 달라짐. 팔레트 통합이 선행되어야 함 |
| JSON 문자열 / 파싱된 토큰 / 해석된 팔레트 | 직렬화·검증·tcell/Ratatui 색상 표현이 다름. 반환값만 같은 의미라고 간주하지 않음 |
| 원래 역할 스타일 / 실제 표면 지정 스타일 / 배경 보존 Rows | 명시적 선택·편집·필드·사용자 배경과 평문 표면 보정의 동작이 다름. 한 가지 설정 API로 모두 표현할 수 있을 때 통합 검토 |
| 기존 `Styler.Form/Input/List/Tree/Grid/Comparison` / 공통 모델·뷰 | 기존 tview 객체·상태·셀 스타일을 유지하는 적용기와, 데이터를 받아 내부 조작을 제공하는 새 컴포넌트임. 자동 치환이 아님. 기존 앱의 객체/콜백·사용자 스타일을 이전할 경로가 준비되면 정리 범위를 재검토 |
| 선택·버튼·버튼 포커스·탭·비교 헤더 스타일 | 현재 일부 프로필에서 색이 같아도 전체 테마와 사용자 색상·속성·상태 합성이 다름. 색이 우연히 같다는 이유로 같은 API로 판정하지 않음 |
| `Styles.Disabled` / `DisabledStyle`, `GridColors.RangeBG` / 실제 범위 스타일 | 과거 값·커스텀 설정·실제 렌더링 사이 정리가 필요한 후보. 읽기/쓰기 및 사용자 조합을 대체할 설정·조회 경로를 마련한 뒤 Deprecated 여부 결정 |
| `PopupShadowStyle` / `DimRegion` / TVR-19 팝업 옵션 | 스타일 생성·지정 영역 그리기·전체 팝업 조합으로 범위가 다름. **저수준이므로 영구 유지하는 것은 아님**. 0.5.0 `ShadowView`는 팝업 전체를 감싸며 앞의 두 API를 내부 사용한다. 임의 영역 스타일/Dim 적용·경계 보호는 대체하지 않으므로 지원 유지 |
| 모델 `Handle` / 개별 `Open/Close/Focus/Resize` | 입력 액션 라우팅과 프로그램 제어 역할. 동작 일부를 공유해도 모델 조작 경로가 다름 |
| `FormKey`·`NavigationKey`·`MenuKey` / 모델 액션 | tcell 이벤트 번역과 프레임워크 독립 모델 조작. Rust/crossterm 연결과 같은 어댑터 층으로 구분 |
| Grid `SetSource` / `ApplySource`·revision | 즉시 데이터 교체와 오래된 비동기 응답 차단이 다름. 변경 시 원본 데이터/정렬/선택 복원 규칙까지 비교 필요 |
| Tree·Tabs 모델 / Go·Rust 렌더러 / 기존 stock-widget 스타일 | 안정 ID·탐색 상태·이벤트 요청과 실제 프레임워크 그리기/스타일 적용이 다름 |
| `StackLayout` / `StackRects` / Ratatui `stack_rects`, Split 모델/뷰 | 길이 배분·셀 좌표·Ratatui Rect 변환·실제 입력/그리기라는 역할이 다름. 기반 계산을 공유하며 별도 렌더러를 중복 구현으로 보지 않음 |
| 경로·상태·Notice·Progress·DataState·Badge·Chip·Help의 모델/행/뷰 | 레이아웃 계산·앱에 대한 요청과 그리기를 나눈 구조. 모델만 사용하는 앱도 있어 렌더러 하나로 강제 통합하지 않음 |
| 노출된 Go 별칭 / 내부 패키지 선언, Rust re-export | 같은 심볼을 하나의 public import로 노출하는 구조. 별칭 수를 별개의 기능 구현 수로 세지 않음 |

이 점검은 현재 기능을 무조건 영구 지원하겠다는 약속이 아닙니다. 새 대체 API가 마련되거나 실제 적용 앱의 이전 가능성이 확인되면 상태 목록과 이 판단을 함께 갱신합니다. TVR-19 옵션은 0.5.0 소스에 구현되었으며 일반 팝업 조합에 사용합니다. 임의 영역 그리기나 앱별 화면 코드를 모두 대체하지 않습니다.

검증 범위·공개 선언/문서 항목 목록·소스 해시는 [TVR-20 결과](../evidence/api-lifecycle-results.json)에 기록합니다. Go 751개 공개 선언과 Rust 159개 공개 문서 항목은 서로 다른 집계 단위이며 같은 API 수로 비교하지 않습니다. 로컬 검증만 완료했으며 커밋·게시·원격 CI는 실행하지 않았습니다.
