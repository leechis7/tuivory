# 언어 중립 저장소 구조

**한국어 (기본)** · [English](architecture.en.md)

Tuivory는 여러 언어에서 사용할 터미널 UI 스타일 패키지 프로젝트입니다. 공통 디자인·검증 기준을 공유하고 각 언어의 구현과 패키징은 별도 디렉터리에서 관리합니다. 루트에 Go 소스·go.mod·go.sum을 두지 않습니다.

```text
tuivory/
├── design/       공통 명세·JSON 토큰·스키마·CSV 후보
├── docs/         공통 문서와 언어별 사용법
├── go/           Go 모듈·공개 API·내부 구현·Go 예제
├── python/       Python 토큰 읽기 예제
├── javascript/   Node.js 토큰 읽기 예제
├── shell/        POSIX ANSI 출력 예제
├── examples/     예제 색인과 공통 정적 배치
├── bin/          언어별 견본 실행파일. Git 제외, 현재 Go는 bin/go/
├── tools/        데이터 생성·검사·단독 모듈 검증
└── evidence/     검증 기록
```

현재 실제 스타일 패키지가 구현된 언어는 Go입니다. 다른 언어 디렉터리는 현재 제공하는 데이터 읽기·참조 예제를 보존하며 UI 패키지 미구현 상태를 각 README에 명시합니다. 다른 언어에서 Go를 호출하도록 강제하지 않습니다.

## 공통 데이터와 배포 자산

공통 후보 데이터는 `design/tokens/candidate.json`, 출처 CSV는 `design/themes/lazyora-candidate.csv`에 있습니다. Python과 JavaScript 예제는 이 공통 JSON을 읽습니다.

Go의 embed는 모듈 밖 파일을 포함할 수 없으므로 생성 도구가 같은 JSON을 `go/internal/tokens/candidate.json`에도 기록합니다. 이 파일은 배포 자산이며 별도 원본이 아닙니다. 수동 수정하지 않고 검사에서 바이트 단위로 일치를 확인합니다. Go 모듈만 다운로드해도 별도 생성 명령이나 레포 공통 디렉터리 없이 동작합니다.

```sh
python3 tools/export_tokens.py
python3 tools/export_tokens.py --check
python3 tools/check_go_module.py
```

단독 모듈 검사는 `go/`만 임시 디렉터리에 복사한 뒤 테스트하고 외부 프로젝트가 공개 API·embed된 토큰을 사용하는지 확인합니다. `design/`은 복사하지 않습니다.

## Go 공개 API

```go
import "github.com/leechis7/tuivory/go"

theme, err := tuivory.New("dark", "256")
if err != nil { return err }
theme.Form(form)
```

Go 하위 모듈 경로는 `github.com/leechis7/tuivory/go`, 패키지 이름은 `tuivory`입니다. 구현은 `go/internal/`에 두어 직접 공개하지 않습니다. 화면·이벤트·단말 능력 감지·DB 상태는 호스트 앱의 책임입니다.

첫 Go 배포 버전은 `v0.0.1`, 하위 모듈 태그는 `go/v0.0.1`입니다. [Go 사용법](go-package.md) · [설치·사용 안내](installation.md)

## 다음 구현

LazyOra 적용 검증과 Go 사용성을 유지하면서 Python·JavaScript·Shell의 각 환경에 맞는 API·배포·UI 템플릿을 별도 일감으로 확장합니다. [공통 명세](../design/README.md) · [언어별 예제](../examples/README.md) · [로드맵](roadmap.md)
