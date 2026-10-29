# Tuivory Go

**한국어 (기본)** · [English](README.en.md)

컴포넌트의 표시·내부 조작은 라이브러리, 실제 화면 조합·전역 키·영역 간 포커스·업무 연결은 앱 책임입니다. 예제는 필수 화면 템플릿이 아닙니다. [컴포넌트와 앱의 책임](../docs/component-boundary.md).

제품 버전은 루트 `VERSION`의 **0.3.0**입니다. Go 모듈은 하위 디렉터리 태그 `go/v0.3.0`으로 배포합니다. [릴리스 안내](../docs/release-0.3.0.md).

Go 모듈과 모든 Go 구현은 이 디렉터리에 있습니다. 모듈 경로는 `github.com/leechis7/tuivory/go`, 패키지 이름은 `tuivory`이며 한 번만 import합니다.

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

현재 버전은 `v0.3.0`이며 Go 하위 모듈 태그는 `go/v0.3.0`입니다. 첫 배포 태그 `go/v0.0.1`도 보존합니다.

```sh
go get github.com/leechis7/tuivory/go@v0.3.0
```

저장소 루트에서:

```sh
make run
make build
make test
make check
```

이 디렉터리에서는 `go run ./cmd/tuivory`, `go run ./examples/starter`, `go test -race ./...`를 실행할 수 있습니다. `make build`는 Linux ARM64 제품 바이너리 하나를 저장소의 `bin/go/`에 만듭니다.

아래 언어 선택은 `v0.2.0`에 포함합니다. 견본 UI는 한국어가 기본이며, `go run ./cmd/tuivory --lang en` 또는 빌드한 바이너리의 `--lang en` 옵션으로 영어를 선택합니다. `--lang ko`로 한국어를 명시할 수 있습니다. 시작 템플릿의 예시 문구는 한국어입니다.

공통 후보 토큰의 원본은 [design/tokens](../design/tokens/README.md)에 있습니다. `internal/tokens/candidate.json`은 `tools/export_tokens.py`로 생성한 배포용 복사본입니다. 수동 수정하지 않습니다. Go 모듈을 단독 다운로드해도 이 파일을 embed하므로 레포 루트 데이터나 별도 생성 단계 없이 사용할 수 있습니다.

[API와 사용법](../docs/go-package.md) · [스타일 범위](../docs/go-style-coverage.md)

## 공통 Tree

기존 `Styler.Tree`는 stock tview 트리의 스타일 API입니다. 신규 `NewTree`·`TreeState`·`NewTreeView`는 안정 ID, 펼침/선택/스크롤, 노드 아이콘·보조 설명·개수와 키보드/마우스를 제공합니다. 같은 후보 토큰과 조작 규칙의 Rust 구현도 있습니다. 기존 Go 추출 스타일 전체의 이식이나 배포 태그의 API는 아닙니다. [API·예제](../docs/tree.md) · [현재 점검표](../docs/component-audit.md). 루트에서 `make run-tree-go ARGS="--lang ko"`로 실행합니다.

## 공통 워크스페이스 컴포넌트

[탭·패널·분할선·상태 표시줄·경로 사용법](../docs/workspace.md)에서 Go/Rust 공개 API와 같은 조작·색상·상태 원칙을 설명합니다. DB 없는 한영 통합 예제는 루트에서 `make run-workspace-go ARGS="--lang ko"`, `make run-workspace-rust ARGS="--lang en"`으로 실행합니다. Go `go/v0.3.0`과 Rust `rust/v0.3.0`에 포함합니다. CI 결과와 실제 앱 적용은 [작업 기록](https://leechis7.atlassian.net/browse/TVR-7)에서 구분합니다.

[오버레이 그리기 API](../docs/overlay-drawing.md): 팝업·카드·그림자의 한글·CJK·이모지 경계와 Show 이후 출력 검사.

[공통 메뉴](../docs/menus.md): Go/Rust 계층·메뉴 바·뒤로가기·단축키/비활성·팝업·호출 문맥 요청과 DB 없는 한영 실행 예제. 0.3.0에 포함합니다.
