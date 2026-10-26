# 언어별 예제 안내

**한국어 (기본)** · [English](README.en.md)

실제 코드는 각 언어 디렉터리 안에서 관리합니다. 이 디렉터리는 언어별 예제와 공통 정적 배치를 연결합니다.

| 언어 | 예제 | 제공 범위 |
| --- | --- | --- |
| Go | [시작 템플릿](../go/examples/starter/main.go), [토큰 읽기](../go/examples/tokens/main.go) | 동작하는 Go 스타일 API·실행형 견본 |
| Python | [토큰 읽기](../python/examples/read_tokens.py) | 데이터 읽기 예제. UI 패키지 미구현 |
| JavaScript | [토큰 읽기](../javascript/examples/read-tokens.mjs) | 데이터 읽기 예제. UI 패키지 미구현 |
| Shell | [ANSI 견본](../shell/examples/terminal-colors.sh) | 참조 출력. 스타일 함수 패키지 미구현 |

[공통 컴포넌트 정적 배치](components.txt)는 언어와 무관한 참고 예시입니다.

시작 템플릿과 정적 배치 예시의 라벨은 한국어이며, 현재 [견본](../docs/playground.md)은 `--lang en`으로 영어 UI를 제공합니다.

## 실행파일 위치

예제 소스는 각 언어 디렉터리에서 유지하고, 빌드한 견본 실행파일은 `bin/<언어>/`로 구분합니다. 파일명에는 OS·아키텍처를 넣습니다. 현재 `make build`는 `bin/go/tuivory-linux-arm64` 하나를 만듭니다. 실행은 저장소 루트에서 `./bin/go/tuivory-linux-arm64 --lang ko` 또는 `--lang en`을 사용합니다.

향후 Rust 견본도 빌드 결과를 `bin/rust/`에 둡니다. Rust 빌드 명령과 실행파일은 아직 제공하지 않습니다. Python·JavaScript·Shell 예제는 기본적으로 소스로 실행하며 별도 실행파일 패키징은 필요할 때 정합니다. `bin/`은 Git에서 제외합니다.
