# Tuivory 설치·사용 안내

**한국어 (기본)** · [English](installation.en.md)

Tuivory(TUI + ivory)는 독립 터미널 UI 스타일 프로젝트입니다. 현재 모듈·명령·토큰 식별자는 모두 Tuivory 기준이며, 일감은 Jira TVR 프로젝트에서 관리합니다. 원출처 고지는 [NOTICE](../NOTICE.md)에 보존합니다.

## 배포 버전과 현재 소스

배포된 Go 버전은 `v0.0.1`, 저장소 태그는 `go/v0.0.1`입니다.

```sh
go get github.com/leechis7/tuivory/go@v0.0.1
```

모듈은 저장소의 `go/` 아래에 있습니다. 루트 Go 모듈은 없으며 패키지 이름은 `tuivory`입니다.

```go
import "github.com/leechis7/tuivory/go"

styler, err := tuivory.New("dark", "256")
```

현재 `main`에는 배포 태그 이후의 한·영 문서와 견본 언어 선택이 포함됩니다. 이 기능은 아직 새 태그로 배포하지 않았습니다. 현재 견본을 실행하려면 저장소를 체크아웃한 뒤 루트에서 실행하세요.

```sh
go -C go run ./cmd/tuivory --lang ko
go -C go run ./cmd/tuivory --lang en
make build
./bin/tuivory-linux-arm64 --lang en
```

Go 1.24 이상이 필요합니다. `make build`는 두 언어를 지원하는 Linux ARM64 바이너리 하나만 만듭니다. 소스 실행은 현재 호스트에서 동작합니다. 시작 템플릿은 `go -C go run ./examples/starter`이며 예시 라벨은 한국어입니다.

## 공통 데이터와 검증

토큰 초안 형식은 `tuivory.tokens.draft`, 공통 원본은 `design/tokens/`, Go 배포용 사본은 `go/internal/tokens/candidate.json`입니다. CLI 이름은 `tuivory`, 문서 이미지 생성 환경변수는 `TUIVORY_SNAPSHOT_DIR`입니다.

Go 프로젝트는 공개 모듈만으로 내장 토큰을 사용할 수 있습니다. Python·JavaScript는 공통 JSON 읽기 예제, Shell은 ANSI 참조 예제이며 해당 언어의 UI 패키지는 아직 제공하지 않습니다.

[Go API](go-package.md) · [저장소 구조](architecture.md) · [견본](playground.md) · [검증 기록](../evidence/README.md)
