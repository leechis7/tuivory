# Tuivory Go

**한국어 (기본)** · [English](README.en.md)

0.11.0 TVR-7: [그리드 편집과 데이터 작업](../docs/grid-workspace.md). 루트 단일 import의 `Grid / NewGridView`를 확장하며 기존 편집 요청은 기본 동작으로 유지합니다.

**0.10.1 사용 금지:** [업그레이드·회수 안내](../docs/withdrawn-versions.md). 0.10.2 이상을 사용하세요.

**0.10.2 TVR-26:** [Windows Go 파사드](../docs/ui-facade.md)가 Unix 전용 API를 참조하는 결함을 수정했습니다. 0.10.2에서 제공하며 0.10.1은 사용 금지입니다.

**0.10.2 TVR-29:** [팝업 그림자](../docs/popup-shadows.md)를 오른쪽 1칸·아래 반 줄로 통일했습니다. 테두리와 기본 끄기는 유지합니다.

0.10.0 TVR-7: [Go 반응형 Modal](../docs/modals.md)은 좁은 단말 안에서 긴 버튼을 여러 행으로 배치합니다. Modal은 backend를 내장한 SDK 어댑터이며 원시 별칭 정체성의 예외입니다. 0.10.0에 포함합니다.
0.10.0 TVR-18: [Go/Rust 탭·트리 드래그 앤 드롭](../docs/drag-drop.md)은 기본 끄기이며 앱 승인 후 불변 모델 적용, 영역 밖 캡처·취소·키보드 대안을 제공합니다. 0.10.0부터 제공합니다.


**0.9.1 TVR-27:** [통합 예제 실행파일](../docs/examples.md)은 언어별 하나이며 현재 Linux 서버 아키텍처만 빌드합니다. `--demo tree`, `--demo menu`, `--demo syntax` 등으로 선택합니다.

**0.9.0 TVR-24:** [선택적 Oracle SQL/PLSQL 분석·공통 토큰·편집기 전환](../docs/syntax.md)을 제공합니다. Go는 루트 한 번만 import하고 Rust는 syntax-sql 기능으로 선택합니다.

**0.10.0:** Go UI를 `github.com/leechis7/tuivory/go` 하나로 구성합니다. 기존 하위 경로는 호환용으로 유지합니다. [단일 import·이름 대응](../docs/ui-facade.md).

[공개 API 명세](../docs/api/go.md)

컴포넌트의 표시·내부 조작은 라이브러리, 실제 화면 조합·전역 키·영역 간 포커스·업무 연결은 앱 책임입니다. 예제는 필수 화면 템플릿이 아닙니다. [컴포넌트와 앱의 책임](../docs/component-boundary.md).

제품 버전은 루트 `VERSION`의 **0.12.5**입니다. Go 모듈은 하위 디렉터리 태그 `go/v0.12.5`으로 배포합니다. [릴리스 안내](../docs/release-0.12.5.md).

Go 모듈과 모든 Go 구현은 이 디렉터리에 있습니다. 모듈 경로는 `github.com/leechis7/tuivory/go`, 패키지 이름은 `tuivory`이며 한 번만 import합니다.

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

현재 버전은 `v0.12.5`이며 Go 하위 모듈 태그는 `go/v0.12.5`입니다. 첫 배포 태그 `go/v0.0.1`도 보존합니다.

```sh
go get github.com/leechis7/tuivory/go@v0.12.5
```

저장소 루트에서:

```sh
make run
make build
make test
make check
```

이 디렉터리에서는 `go run ./cmd/tuivory`, `go run ./examples/starter`, `go test -race ./...`를 실행할 수 있습니다. `make build`는 현재 Linux 호스트 아키텍처의 통합 예제 하나를 저장소의 `bin/go/`에 만듭니다.

아래 언어 선택은 `v0.2.0`에 포함합니다. 견본 UI는 한국어가 기본이며, `go run ./cmd/tuivory --lang en` 또는 빌드한 바이너리의 `--lang en` 옵션으로 영어를 선택합니다. `--lang ko`로 한국어를 명시할 수 있습니다. 시작 템플릿의 예시 문구는 한국어입니다.

공통 후보 토큰의 원본은 [design/tokens](../design/tokens/README.md)에 있습니다. `internal/tokens/candidate.json`은 `tools/export_tokens.py`로 생성한 배포용 복사본입니다. 수동 수정하지 않습니다. Go 모듈을 단독 다운로드해도 이 파일을 embed하므로 레포 루트 데이터나 별도 생성 단계 없이 사용할 수 있습니다.

[API와 사용법](../docs/go-package.md) · [스타일 범위](../docs/go-style-coverage.md)

TVR-7 0.9.2 보완: 표의 스타일 재칠에서 두 칸 문자를 보존하고, 분할선·비교표 구분선 대비를 보정합니다. [그리기 규칙](../docs/overlay-drawing.md) · [스타일 보완](../docs/lazyora-extraction.md).

## 공통 Tree

기존 `Styler.Tree`는 stock tview 트리의 스타일 API입니다. 신규 `NewTree`·`TreeState`·`NewTreeView`는 안정 ID, 펼침/선택/스크롤, 노드 아이콘·보조 설명·개수와 키보드/마우스를 제공합니다. 같은 후보 토큰과 조작 규칙의 Rust 구현도 있습니다. 기존 Go 추출 스타일 전체의 이식이나 배포 태그의 API는 아닙니다. [API·예제](../docs/tree.md) · [현재 점검표](../docs/component-audit.md). 루트에서 `make run-tree-go ARGS="--lang ko"`로 실행합니다.

## 공통 워크스페이스 컴포넌트

[탭·패널·분할선·상태 표시줄·경로 사용법](../docs/workspace.md)에서 Go/Rust 공개 API와 같은 조작·색상·상태 원칙을 설명합니다. DB 없는 한영 통합 예제는 루트에서 `make run-workspace-go ARGS="--lang ko"`, `make run-workspace-rust ARGS="--lang en"`으로 실행합니다. Go `go/v0.5.0`과 Rust `rust/v0.5.0`에 포함합니다. CI 결과와 실제 앱 적용은 [작업 기록](https://leechis7.atlassian.net/browse/TVR-7)에서 구분합니다.

[오버레이 그리기 API](../docs/overlay-drawing.md): 팝업·카드·그림자의 한글·CJK·이모지 경계와 Show 이후 출력 검사.

[공통 메뉴](../docs/menus.md): Go/Rust 계층·메뉴 바·뒤로가기·단축키/비활성·팝업·호출 문맥 요청과 DB 없는 한영 실행 예제. 0.5.0에 포함합니다.

0.5.0의 메뉴는 단일선 테두리와 항목 선택·열린 메뉴 표시를 사용합니다. 입력 차단·호출 위치 복귀는 유지합니다. [메뉴 표시 규칙](../docs/menus.md).

0.5.0의 TextOnSurface / Styles::text_on_surface 및 ControlStyleOnSurface / Styles::control_on_surface로 평문을 실제 바탕에 연결하고 대비를 보정합니다. 원본 토큰과 raw 스타일은 유지하며 명시적 상태/사용자 배경은 보존합니다. [한영 표면 디자인 가이드](../design/surfaces.md).

[비활성 상태와 12팔레트 비교](../docs/disabled-states.md): 일반 비활성 접두사 제거, 회색/Dim 전경, 입력 차단과 한영 실행 예제.

[API 지원 상태·Deprecated·전환 안내](../docs/api-lifecycle.md) · [공개 API 중복 점검](../docs/api-overlap-audit.md): 0.5.0 변경의 대상·대체 방법·배포/제거 계획을 구분합니다.

0.5.0의 TVR-19는 기본 끄기의 공통 팝업 그림자를 제공합니다. `off/auto/solid/dim`, 카드와 그림자를 포함한 위치 계산, 그림자를 제외한 입력 판정과 두 칸 문자 경계 보호를 지원합니다. 앱이 배경 다시 그리기와 열기·닫기를 결정합니다. [API·실행 예제·12팔레트 화면](../docs/popup-shadows.md).

0.6.0 TVR-22~25는 테두리 없는 Surface, 독립/암호 컨트롤, 텍스트 편집·뷰어와 행·열·격자·레이어 컨테이너를 제공합니다. [사용법·제공 상태·예제](../docs/controls.md).

0.7.0 TVR-26: Go·Rust에서 Tuivory 경로만 사용하는 UI 구성, 공통 입력·바이트 span 변환과 터미널 수명을 제공합니다. [API 대응·예제·현재 제공 상태](../docs/ui-facade.md).

TVR-8 0.9.2 후속은 Go 토큰 표의 8색 Dim 누락과 드롭다운 비활성 필드의 테마 적용 누락을 수정합니다. [Go 12팔레트 화면·검증](../docs/disabled-states.md).

0.9.2는 다크/8색 SQL 강조를 Go/Rust 공통 7종 전경·속성 조합으로 개선하고 참조 본문 대비 >=4.5:1을 유지합니다. [규칙·단말 제약](../docs/syntax.md).

TVR-7 0.12.4: [실제 그리드 커서·backend 연결](../docs/grid-workspace.md). 0.12.4에서 실제 커서를 사용하려면 Go NewCursorScreen/NewGridView, Rust GridWidget::render_frame을 사용합니다.
