# 언어 중립 저장소 구조

**한국어 (기본)** · [English](architecture.en.md)

Tuivory는 여러 언어에서 사용할 TUI 컴포넌트 라이브러리입니다. 공통 디자인·검증 기준을 공유하고 각 언어의 구현과 패키징은 별도 디렉터리에서 관리합니다. 루트에 Go 소스·go.mod·go.sum을 두지 않습니다.

```text
tuivory/
├── design/       공통 명세·JSON 토큰·스키마·CSV 후보
├── docs/         공통 문서와 언어별 사용법
├── go/           Go 모듈·공개 API·내부 구현·Go 예제
├── rust/         Rust 코어·Ratatui 어댑터·독립 Cargo 패키지·예제
├── python/       Python 토큰 읽기 예제
├── javascript/   Node.js 토큰 읽기 예제
├── shell/        POSIX ANSI 출력 예제
├── examples/     예제 색인과 공통 정적 배치
├── bin/          언어별 견본 실행파일. Git 제외, Go는 bin/go/, Rust는 bin/rust/
├── tools/        데이터 생성·검사·단독 모듈 검증
└── evidence/     검증 기록
```

Go·Rust는 공통 컴포넌트 모델·토큰·스타일과 tview/Ratatui 렌더러를 제공합니다. Rust 코어는 1.85 이상, Ratatui 어댑터·대화형 예제는 1.88 이상입니다. 공통 모델은 내부 상태·선택·스크롤·요청을 계산하고, 앱은 단말·이벤트 루프·화면 조합·전역 포커스·업무 동작을 연결합니다. [책임 범위](component-boundary.md). 다른 언어는 현재 토큰 읽기·참조 예제이며 UI 패키지 미구현 범위를 각 README에 명시합니다. 다른 언어에서 Go를 호출하도록 강제하지 않습니다.

## 공통 데이터와 배포 자산

공통 후보 데이터는 `design/tokens/candidate.json`, 출처 CSV는 `design/themes/lazyora-candidate.csv`에 있습니다. Python과 JavaScript 예제는 이 공통 JSON을 읽습니다.

Go의 embed는 모듈 밖 파일을 포함할 수 없으므로 생성 도구가 같은 JSON을 `go/internal/tokens/candidate.json`에도 기록합니다. Rust도 같은 JSON을 `rust/src/data/candidate.json`에 포함하고 `include_str!`로 읽습니다. Cargo.toml과 Rust 소스는 rust/ 안에 둡니다. 두 생성 사본은 배포 자산이며 별도 원본이 아닙니다. 수동 수정하지 않고 검사에서 바이트 단위로 일치를 확인합니다. Go 모듈만 다운로드해도 별도 생성 명령이나 레포 공통 디렉터리 없이 동작합니다.

```sh
python3 tools/export_tokens.py
python3 tools/export_tokens.py --check
python3 tools/check_go_module.py
python3 tools/check_rust_module.py
```

단독 모듈 검사는 `go/`만 임시 디렉터리에 복사한 뒤 테스트하고 외부 프로젝트가 공개 API·embed된 토큰을 사용하는지 확인합니다. `design/`은 복사하지 않습니다.

## Go 공개 API

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

Go 하위 모듈 경로는 `github.com/leechis7/tuivory/go`, 패키지 이름은 `tuivory`입니다. 공개 컴포넌트 API는 `go/`의 패키지 소스에 두며 추출 스타일·내장 자산 등의 비공개 구현은 `go/internal/`에 둡니다. 화면·이벤트·단말 능력 감지·DB 상태는 호스트 앱의 책임입니다.

첫 Go 배포 버전은 `v0.0.1`, 하위 모듈 태그는 `go/v0.0.1`입니다. [Go 사용법](go-package.md) · [설치·사용 안내](installation.md)

Rust 검사는 rust/만 복사해 Cargo 패키지를 검증하고 외부 path 의존성 프로젝트에서 실행합니다. 공통 원본이나 Go 체크아웃이 필요하지 않습니다. [Rust 범위와 API](../rust/README.md)

## 다음 구현

LazyOra 적용 검증과 Go 사용성을 유지하면서 Python·JavaScript·Shell의 각 환경에 맞는 API·배포·UI 템플릿을 별도 일감으로 확장합니다. [공통 명세](../design/README.md) · [언어별 예제](../examples/README.md) · [로드맵](roadmap.md)

공통 컴포넌트의 신규 Tree API는 [Go·Rust Tree 사용법](tree.md)에서 설명합니다. 기존 Go 추출 스타일·stock `Styler.Tree`와 별도의 후보 팔레트 기반 구현이며 v0.1.0 태그에 포함합니다. [TVR-7 지원 범위 점검](component-audit.md)에서 상태·조작·앱 책임과 남은 단계를 구분합니다.

## 공통 워크스페이스 컴포넌트

[탭·패널·분할선·상태 표시줄·경로 사용법](workspace.md)에서 Go/Rust 공개 API와 같은 조작·색상·상태 원칙을 설명합니다. DB 없는 한영 통합 예제는 루트에서 `make run-workspace-go ARGS="--lang ko"`, `make run-workspace-rust ARGS="--lang en"`으로 실행합니다. Go `go/v0.1.0`과 Rust `rust/v0.1.0`에 포함합니다. CI 결과와 실제 앱 적용은 [작업 기록](https://leechis7.atlassian.net/browse/TVR-7)에서 구분합니다.

## 배포 경계

Go·Rust 및 후속 언어의 실행파일은 정적으로 배포하며, 라이브러리는 호스트 앱의 정적 링크를 막는 필수 네이티브 의존성을 추가하지 않습니다. 공통 자산은 모듈 내부에 내장합니다. 인터프리터 기반 참조 예제와 독립 배포 실행파일을 구분합니다. [정적 배포 정책과 검증](static-build.md)

워크스페이스 예제의 행/열 분할·포커스 순서·종료 키는 호스트 설정으로 바꿀 수 있습니다. [구성 예제](component-boundary.md#같은-컴포넌트-다른-앱-정책).
