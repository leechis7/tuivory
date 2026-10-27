# 언어별 예제 안내

**한국어 (기본)** · [English](README.en.md)

실제 코드는 각 언어 디렉터리 안에서 관리합니다. 이 디렉터리는 언어별 예제와 공통 정적 배치를 연결합니다.

| 언어 | 예제 | 제공 범위 |
| --- | --- | --- |
| Go | [시작 템플릿](../go/examples/starter/main.go), [토큰 읽기](../go/examples/tokens/main.go) | 동작하는 Go 스타일 API·실행형 견본 |
| Rust | [토큰 읽기](../rust/examples/tokens.rs), [대화형 견본](../docs/rust-playground.md) | JSON 검증·색상/스타일 코어·Ratatui 어댑터·한영 실행 예제 |
| Python | [토큰 읽기](../python/examples/read_tokens.py) | 데이터 읽기 예제. UI 패키지 미구현 |
| JavaScript | [토큰 읽기](../javascript/examples/read-tokens.mjs) | 데이터 읽기 예제. UI 패키지 미구현 |
| Shell | [ANSI 견본](../shell/examples/terminal-colors.sh) | 참조 출력. 스타일 함수 패키지 미구현 |

[공통 컴포넌트 정적 배치](components.txt)는 언어와 무관한 참고 예시입니다.

시작 템플릿과 정적 배치 예시의 라벨은 한국어이며, 현재 [견본](../docs/playground.md)은 `--lang en`으로 영어 UI를 제공합니다.

## 실행파일 위치

예제 소스는 각 언어 디렉터리에서 유지하고, 빌드한 견본 실행파일은 `bin/<언어>/`로 구분합니다. 파일명에는 OS·아키텍처를 넣습니다. 현재 `make build`는 `bin/go/tuivory-linux-arm64` 하나를 만듭니다. 실행은 저장소 루트에서 `./bin/go/tuivory-linux-arm64 --lang ko` 또는 `--lang en`을 사용합니다.

Rust 견본은 Rust 1.88 이상에서 `make run-rust ARGS="--lang ko"`로 실행합니다. `make build-rust`는 `bin/rust/tuivory-linux-arm64` 하나를 만듭니다. 기본 코어·JSON 예제는 Rust 1.85 이상에서 `cargo run --manifest-path rust/Cargo.toml --locked --example tokens -- dark 256`으로 실행합니다. Python·JavaScript·Shell 예제는 기본적으로 소스로 실행하며 별도 실행파일 패키징은 필요할 때 정합니다. `bin/`은 Git에서 제외합니다.

## 공통 Tree 예제

[Go 소스](../go/examples/tree/main.go) · [Rust 소스](../rust/examples/tree/main.rs) · [한영 사용법](../docs/tree.md). 루트의 `make run-tree-go ARGS="--lang ko"`, `make run-tree-rust ARGS="--lang en"`으로 실행합니다. DB 없는 동일 데이터·조작 예제이며 기본 제품 빌드에는 추가하지 않습니다.
