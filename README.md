# Tuivory — 터미널 UI 스타일 패키지

Tuivory (TUI + ivory) provides reusable terminal UI styles across languages. Shared design data lives in `design/`; each language implementation has its own directory and packaging.

**Tuivory(투이보리)**는 Go·Python·JavaScript·Shell에서 일관된 터미널 UI를 만들기 위한 스타일 패키지 프로젝트입니다. 저장소 루트는 특정 언어에 종속하지 않습니다. 공통 테마·색상 프로필·상태 규칙은 `design/`에서 관리하고 실제 적용 코드는 언어별로 구현합니다.

| 경로 | 역할 | 현재 제공 범위 |
| --- | --- | --- |
| [design/](design/README.md) | 언어 독립 규칙·토큰·테마 후보 | 공통 명세, JSON·스키마, CSV 참조 데이터 |
| [go/](go/README.md) | Go 모듈·스타일 구현·견본 | 실제 스타일 API, tview 적용, 상태 보존·원본 비교 검사 |
| [python/](python/README.md) | Python 구현 영역 | 공통 토큰 소비 예제. UI 패키지 미구현 |
| [javascript/](javascript/README.md) | JavaScript 구현 영역 | Node.js 토큰 소비 예제. UI 패키지 미구현 |
| [shell/](shell/README.md) | Shell 구현 영역 | ANSI 참조 출력. 재사용 스타일 함수 패키지 미구현 |
| [examples/](examples/README.md) | 예제 안내 | 언어별 코드 위치와 공통 정적 배치 |
| [docs/](docs/architecture.md) | 사용법·구조·검증 기준 | 설계 원칙·API·지원 범위·출처 |

## Go 사용

Go 모듈의 경로는 `github.com/leechis7/tuivory/go`이며 패키지 이름은 `tuivory`입니다. Tuivory 관련 import는 하나입니다.

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
theme.Button(button)
```

첫 배포 버전은 **0.0.1**이며 Go 하위 모듈 태그는 `go/v0.0.1`입니다.

```sh
go get github.com/leechis7/tuivory/go@v0.0.1
```

[Go 사용법](docs/go-package.md) · [이전 TUIS에서 전환](docs/migration.md)

저장소를 체크아웃한 뒤 루트에서 실행합니다. Go 1.24 이상이 필요하며 DB나 서버가 필요 없습니다.

```sh
make run
make build
```

`make build`는 Linux ARM64 바이너리 하나를 `bin/tuivory-linux-arm64`에 만듭니다. Go 시작 템플릿은 `go/` 디렉터리에서 `go run ./examples/starter`로 실행합니다.

**F2 테마 · F3 색상 · F4 팝업 · F6 화면 전환 · Tab 이동 · Ctrl+Q 종료**

![Tuivory 대화형 견본](docs/images/playground-dark.svg)

실제 Go 위젯을 모의 화면에 그린 참조 이미지입니다. [라이트](docs/images/playground-light.svg) · [흑백](docs/images/playground-blackwhite.svg) · [팝업](docs/images/playground-popup.svg) · [견본 사용법](docs/playground.md)

## 검증

```sh
make test
make check
make check-consumers
python3 tools/check_go_module.py
```

Go 원본 스타일 비교·상태 보존, 공통 데이터와 언어별 소비 결과, 단독 Go 모듈 소비를 검사합니다. Python·Node.js 예제에는 외부 의존성이 없습니다. 생성된 Go 배포용 토큰은 공통 데이터와 일치하는지 검사하며 단말 사용자 팔레트·원격 환경 결과는 [별도 기록](evidence/README.md)과 [초기 이전 검증](evidence/initial-migration.md)으로 관리합니다.

LazyOra는 첫 적용 대상이며 앱·DB 내부 구현은 공통 코어에 넣지 않습니다. [출처](docs/sources.md) · [로드맵](docs/roadmap.md) · [기여 방법](CONTRIBUTING.md) · [변경 이력](CHANGELOG.md)

개발자: **이채강 (Chaekang Lee)** · leechis7@gmail.com

라이선스: [AGPL-3.0-only](LICENSE). 초기 자료·코드의 유래는 [NOTICE](NOTICE.md)에 기록합니다.
