# Tuivory Go 스타일 패키지

**한국어 (기본)** · [English](go-package.en.md)

현재 제품 버전은 **0.2.0**입니다. [변경 범위·설치·배포 자산](release-0.2.0.md).

현재 Go 소스는 `go/`에 있는 독립 하위 모듈입니다. 모듈 경로는 **`github.com/leechis7/tuivory/go`**, 패키지 이름은 **`tuivory`**이며 Tuivory 관련 import는 하나입니다.

```go
import "github.com/leechis7/tuivory/go"
```

현재 버전은 `v0.2.0`이며 Go 하위 모듈 태그는 `go/v0.2.0`입니다.

```sh
go get github.com/leechis7/tuivory/go@v0.2.0
```

| Go 모듈 내부 | 책임 |
| --- | --- |
| `tuivory.go` | 단일 공개 API·역할·상태 타입 |
| `internal/style` | 테마·프로필·상태 계산 |
| `internal/widgets` | stock tview 적용·재적용 |
| `internal/tokens` | 공통 토큰 로더와 생성된 배포용 JSON |

하위 구현은 `internal`로 제한하며 앱에서는 import할 필요가 없습니다. 위젯 생성에 필요한 tview/tcell 같은 호스트 라이브러리는 앱에서 사용합니다.

## 시작하기

저장소의 [Go 템플릿](../go/examples/starter/main.go)은 DB 없이 실행할 수 있습니다.

```sh
go -C go run ./examples/starter
go -C go run ./cmd/tuivory --theme light --colors 16
```

이 실행 명령과 `--lang`은 `v0.2.0` 소스 기준입니다. 견본은 한국어가 기본이며 `--lang en`을 추가하면 영어 UI로 실행합니다. `--lang ko`는 한국어를 명시합니다. 언어 선택은 견본 UI에만 적용하며 공개 스타일 API에는 영향을 주지 않습니다. 시작 템플릿의 예시 문구는 한국어입니다.

```go
import "github.com/leechis7/tuivory/go"

styler, err := tuivory.New("dark", "256")
if err != nil { return err }
styler.Form(form)
styler.List(list)
styler.Editor(editor)
styler.Text(hint, tuivory.Panel, tuivory.Hint)
```

테마: `dark`, `light`, `blackwhite`. 프로필: `8`, `16`, `256`, `truecolor`. 앱이 단말을 소유한다면 `tuivory.ProfileForColors(screen.Colors(), limited)`로 프로필을 결정합니다. 감지와 스타일 계산은 분리되어 있으며 패키지가 stdin을 읽거나 단말 팔레트를 바꾸지 않습니다.

## 역할과 상태

`Styles`는 실제 팔레트 값과 아래 계산 메서드를 제공합니다. 테마·프로필은 `NewStyles`에서 정하고, 필요한 색상 필드는 앱이 별도 값으로 조정할 수 있습니다. 전역 테마 상태는 없습니다.

- 표면: `Canvas`, `Panel`, `Field`, `Footer`, `Editor`.
- 텍스트: `Body`, `Hint`, `Accent`, `Warning`.
- 기본 스타일: 입력·선택·버튼·버튼 포커스·비활성·변경됨·편집기.
- 확장 스타일: 드롭다운·활성 탭·푸터 버튼·비교표 헤더·분할선·팝업 카드·배경·그림자.
- 그리드: 기본/줄무늬/현재 행, NULL(기울임), 변경됨, 범위 선택, 활성 셀, 헤더, 구분선·행번호·상태줄.
- 구문색: 키워드·함수·타입·문자열·숫자·주석·매개변수. 호스트가 lexer 결과를 `SyntaxKind`로 전달합니다. SQL/Oracle parser와 DB 상태는 포함하지 않습니다.

```go
styler.Grid(table, func(row, col int) tuivory.CellState {
    return tuivory.CellState{
        Null: nullCells[row][col],
        Edited: changedCells[row][col],
        InRange: selectedCells[row][col],
    }
})
tokenStyle := styler.Styles.SyntaxStyle(tuivory.SyntaxKeyword, styler.Styles.EditorStyle())
```

`Grid`의 Row/CurrentRow는 표의 실제 선택에서 계산합니다. 그리드 스타일은 줄무늬 → 현재 행 → NULL → 변경됨 → 범위 선택 순으로 합성하며, 활성 셀/활성 헤더는 별도 스타일입니다. 원본처럼 변경됨·범위 선택이 NULL 기울임을 덮을 수 있습니다. `*` 같은 표식, 데이터·행번호·구분선의 실제 그리기와 입력 처리는 앱의 책임입니다.

## 테마 변경

새 Styler를 만든 뒤 기존 위젯에 적용합니다. `Apply`는 숨겨진 Pages, Flex, Form 자식, 트리 노드까지 처리하며 위젯을 새로 만들지 않습니다.

```go
roles := tuivory.Roles{
    Surfaces: map[*tview.Box]tuivory.Surface{hint.Box: tuivory.Panel},
    Text: map[*tview.TextView]tuivory.TextRole{hint: tuivory.Hint},
}
styler.Apply(roles, pages)
// 상태가 있는 그리드·탭·푸터 버튼은 앱이 아는 상태로 다시 적용합니다.
styler.Tab(tabButton, isActive)
styler.FooterButton(footerButton)
```

사용자 래퍼는 `StyleChildren() []tview.Primitive`로 자식을 노출할 수 있습니다. 포커스 이동 후 `RefreshBorders`를 호출하면 현재 배경과 포커스에 맞게 경계색을 다시 결정합니다. 앱의 포커스·이벤트 콜백을 교체하지 않습니다.

폼에서는 `NewChoice`로 만든 선택 필드를 권장합니다. 폼의 공통 입력색 덮어쓰기를 방지하고 열린 목록 아래 한글의 반쪽 문자가 남는 문제를 처리합니다. `Form`은 입력·읽기 전용 설명·stock DropDown의 DrawFunc를 소유합니다. 기존 DrawFunc가 있는 앱은 개별 스타일 함수를 쓰거나 훅을 합성해야 합니다.

`Apply`는 값을 변경하지 않지만 단순 표의 셀 스타일을 재설정합니다. 사용자 셀 상태는 이후 `Grid` 또는 개별 API로 재적용합니다. 모달 포커스 순환·배경 입력 차단·앱 작업 실행은 호스트의 책임입니다.

## 원본 동등성

[출처 기록](lazyora-extraction.md)과 [스타일 범위표](go-style-coverage.md)를 참조하세요. Go 테스트는 LazyOra 원본 함수를 독립 실행해 캡처한 240개 팔레트 값과 1,572개 스타일 사례를 비교합니다. 실제 단말 관찰과 모의 화면 검사는 구분합니다.

## 배포와 독립 사용

이 저장소는 Go 외의 언어도 포함하므로 `go.mod`는 `go/`에 둡니다. Go 버전 조회·설치는 `github.com/leechis7/tuivory/go@v0.2.0`을 사용합니다. 루트 모듈은 제공하지 않습니다.

[설치·사용 안내](installation.md)에서 현재 모듈·명령·토큰 식별자를 확인할 수 있습니다. 원출처와 라이선스는 [NOTICE](../NOTICE.md)에 보존합니다.

공통 원본은 `design/tokens/`에 있습니다. 생성된 `go/internal/tokens/candidate.json`을 모듈 안에 포함하므로 Go 프로젝트는 레포 루트·Python·Shell·생성 도구 없이 사용할 수 있습니다. `tools/export_tokens.py --check`가 공통 원본과 Go 복사본 일치를 확인합니다.

공통 컴포넌트의 신규 Tree API는 [Go·Rust Tree 사용법](tree.md)에서 설명합니다. 기존 Go 추출 스타일·stock `Styler.Tree`와 별도의 후보 팔레트 기반 구현이며 v0.2.0 태그에 포함합니다. [TVR-7 지원 범위 점검](component-audit.md)에서 상태·조작·앱 책임과 남은 단계를 구분합니다.

## 공통 워크스페이스 컴포넌트

[탭·패널·분할선·상태 표시줄·경로 사용법](workspace.md)에서 Go/Rust 공개 API와 같은 조작·색상·상태 원칙을 설명합니다. DB 없는 한영 통합 예제는 루트에서 `make run-workspace-go ARGS="--lang ko"`, `make run-workspace-rust ARGS="--lang en"`으로 실행합니다. Go `go/v0.2.0`과 Rust `rust/v0.2.0`에 포함합니다. CI 결과와 실제 앱 적용은 [작업 기록](https://leechis7.atlassian.net/browse/TVR-7)에서 구분합니다.

## 정적 링크

Tuivory는 적용 앱에 필수 공유 라이브러리 의존성을 추가하지 않습니다. Linux 배포 앱은 `CGO_ENABLED=0`으로 빌드하고 최종 ELF와 대상 커널 실행을 검사합니다. 다른 앱 의존성이 추가하는 네이티브 런타임도 앱에서 확인해야 합니다. [정적 배포·외부 앱 검증](static-build.md)

## 공통 컨트롤 상태와 포커스

미배포 공개 API `ControlState.Visual`, `ControlStyle`, `NewFocusStack`으로 상태 표현·안정 ID 탐색·중첩 팝업의 입력 차단과 복귀를 제공합니다. [Go/Rust 공통 계약·실행 예제](focus.md). 실제 위젯·데이터·업무 동작·단말 수명주기는 앱이 연결합니다.

[TVR-9: 입력·폼](forms.md): `Form / FormField / FormWidget`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-10: 목록·메뉴·검색 선택](collections.md): `ListModel / SearchPicker / ListWidget / SearchPickerWidget`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-11: 표·데이터 그리드](grid.md): `Grid / GridSource / GridWidget`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-12: 알림·진행·데이터 상태](feedback.md): `NoticeQueue / Progress / DataState`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-13: 배치·밀도·부가 컴포넌트](layout.md): `SpacingTokens / StackLayout / Badge / Chip / Help`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

`WideSafeScreen(screen)`으로 카드 전체 Draw를 감싸고, 그림자는 `DimRegion(screen, CellRect{...})`으로 그립니다. 좌우 경계 보정·Show 이후 검사는 [오버레이 그리기](overlay-drawing.md)를 보세요. 0.2.0 태그에 포함한 API입니다.
