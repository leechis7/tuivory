# Tuivory 설치·사용 안내

**한국어 (기본)** · [English](installation.en.md)

Tuivory(TUI + ivory)는 독립 터미널 UI 스타일 프로젝트입니다. 현재 모듈·명령·토큰 식별자는 모두 Tuivory 기준이며, 일감은 Jira TVR 프로젝트에서 관리합니다. 원출처 고지는 [NOTICE](../NOTICE.md)에 보존합니다.

## 배포 버전과 현재 소스

현재 Go 버전은 `v0.1.0`, 저장소 태그는 `go/v0.1.0`입니다.

```sh
go get github.com/leechis7/tuivory/go@v0.1.0
```

모듈은 저장소의 `go/` 아래에 있습니다. 루트 Go 모듈은 없으며 패키지 이름은 `tuivory`입니다.

```go
import "github.com/leechis7/tuivory/go"

styler, err := tuivory.New("dark", "256")
```

v0.1.0에는 한영 문서·견본 언어 선택·공통 UI가 포함됩니다. 태그를 체크아웃한 뒤 루트에서 실행하거나 [릴리스](https://github.com/leechis7/tuivory/releases/tag/go/v0.1.0)의 Linux ARM64 견본을 사용하세요.

```sh
go -C go run ./cmd/tuivory --lang ko
go -C go run ./cmd/tuivory --lang en
make build
./bin/go/tuivory-linux-arm64 --lang en
```

Go 1.24 이상이 필요합니다. `make build`는 두 언어를 지원하는 Linux ARM64 바이너리 하나만 만듭니다. 소스 실행은 현재 호스트에서 동작합니다. 시작 템플릿은 `go -C go run ./examples/starter`이며 예시 라벨은 한국어입니다.

## Rust 사용

Rust는 `rust/v0.1.0` Git 태그로 배포합니다. Rust 1.85 이상에서 `tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.1.0" }`를 사용하거나 로컬 rust/를 Cargo path 의존성으로 연결합니다. crates.io에는 게시하지 않습니다. 공통 후보 토큰·색상·스타일 값을 제공합니다. 선택적 Ratatui 0.30.2 어댑터와 Crossterm 0.29 대화형 예제는 Rust 1.88 이상입니다. `make run-rust ARGS="--lang ko"`로 실행하고 `make build-rust`로 `bin/rust/tuivory-linux-arm64`를 만듭니다. [Rust 화면·조작법](rust-playground.md)에서 단말·대상 링커 요구사항을 확인합니다. [Rust 사용법](../rust/README.md)

## 공통 데이터와 검증

토큰 초안 형식은 `tuivory.tokens.draft`, 공통 원본은 `design/tokens/`, 배포용 사본은 `go/internal/tokens/candidate.json`과 `rust/src/data/candidate.json`입니다. CLI 이름은 `tuivory`, 문서 이미지 생성 환경변수는 `TUIVORY_SNAPSHOT_DIR`입니다.

Go 프로젝트는 공개 모듈만으로 내장 토큰을 사용할 수 있습니다. Python·JavaScript는 공통 JSON 읽기 예제, Shell은 ANSI 참조 예제이며 해당 언어의 UI 패키지는 아직 제공하지 않습니다.

[Go API](go-package.md) · [저장소 구조](architecture.md) · [견본](playground.md) · [검증 기록](../evidence/README.md)

공통 컴포넌트의 신규 Tree API는 [Go·Rust Tree 사용법](tree.md)에서 설명합니다. 기존 Go 추출 스타일·stock `Styler.Tree`와 별도의 후보 팔레트 기반 구현이며 v0.1.0 태그에 포함합니다. [TVR-7 지원 범위 점검](component-audit.md)에서 상태·조작·앱 책임과 남은 단계를 구분합니다.

## 공통 워크스페이스 컴포넌트

[탭·패널·분할선·상태 표시줄·경로 사용법](workspace.md)에서 Go/Rust 공개 API와 같은 조작·색상·상태 원칙을 설명합니다. DB 없는 한영 통합 예제는 루트에서 `make run-workspace-go ARGS="--lang ko"`, `make run-workspace-rust ARGS="--lang en"`으로 실행합니다. Go `go/v0.1.0`과 Rust `rust/v0.1.0`에 포함합니다. CI 결과와 실제 앱 적용은 [작업 기록](https://leechis7.atlassian.net/browse/TVR-7)에서 구분합니다.

## 정적 실행파일과 구형 Linux

현재 소스는 Go CGO 비활성화·Rust musl 정적 빌드를 제공합니다. CentOS 7.4 x86_64용 명령은 `make build-go-x86_64`, `make build-rust-x86_64`입니다. Rust 대상은 먼저 `rustup target add aarch64-unknown-linux-musl x86_64-unknown-linux-musl`로 설치합니다. 기존 v0.1.0 Rust GNU ARM64 자산과 이번 미배포 정적 빌드는 다릅니다. [정적 배포·지원 범위·외부 앱 검증](static-build.md)
