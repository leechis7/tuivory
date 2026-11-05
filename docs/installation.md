# 설치·빠른 시작

**한국어 (기본)** · [English](installation.en.md)

**0.10.1 사용 금지:** [업그레이드·회수 안내](withdrawn-versions.md). 0.10.2 이상을 사용하세요.

소스의 예제 빌드는 0.9.1 TVR-27 변경으로 [언어별 통합 실행파일 하나·호스트 아키텍처 자동 감지](examples.md)를 사용합니다.

현재 버전은 **0.11.0**입니다. Go 1.24+, Rust 코어 1.85+, Rust UI/예제 1.88+가 필요합니다.

## Go

```sh
go get github.com/leechis7/tuivory/go@v0.11.0
```

```go
import "github.com/leechis7/tuivory/go"

styler, err := tuivory.New("dark", "256")
if err != nil { return err }
styler.Button(button)
```

button은 앱이 만든 tview 버튼입니다. Go 모듈은 저장소 루트가 아닌 go/에 있습니다.

## Rust

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.11.0", features = ["ratatui"] }
```

Rust는 crates.io 대신 Git 태그로 배포합니다. 모델·토큰만 사용할 때는 ratatui 기능을 생략할 수 있고, 로컬 체크아웃은 rust/를 path 의존성으로 연결합니다.

## 예제 실행

릴리스 태그를 체크아웃한 저장소 루트에서 실행합니다:

```sh
make run
make run-rust ARGS="--lang en"
make run-menu-go ARGS="--shadow auto"
make run-menu-rust ARGS="--shadow auto"
```

기본 UI는 한글이고 --lang en으로 영어를 선택합니다. 예제는 DB가 필요 없습니다. 앱이 단말 수명·전역 키·업무 동작을 소유합니다.

## 정적 실행파일

릴리스는 Linux ARM64/x86_64의 Go·Rust 정적 실행파일을 제공합니다. 로컬 `make build`와 `make build-rust`는 각각 현재 Linux 호스트 아키텍처의 통합 실행파일 하나를 만듭니다. 산출물은 bin/<언어>/ 아래에 OS·아키텍처를 포함한 이름으로 저장합니다. CentOS는 검증하지 않습니다. Python·JavaScript는 현재 토큰 읽기 예제를 제공하며 UI 패키지는 아직 없습니다.

[API](api/README.md) · [컴포넌트](components.md) · [릴리스](release-0.11.0.md) · [정적 배포](static-build.md)
