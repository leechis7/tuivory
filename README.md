# Tuivory — TUI 컴포넌트 라이브러리

**한국어 (기본)** · [English](README.en.md)

Tuivory는 터미널 앱에 쓰는 트리, 메뉴, 폼, 대화상자, 텍스트 편집기, 데이터 그리드를 제공하는 TUI 컴포넌트 라이브러리입니다. 라이브러리가 각 컴포넌트의 그리기와 조작을 맡고, 앱이 화면을 구성하고 데이터와 동작을 연결합니다.

Go/tview와 Rust/Ratatui 패키지를 제공하며, Python, TypeScript/JavaScript, C, C++, Java도 각 언어에서 독립적으로 동작합니다. [언어 지원 현황](docs/languages.md)

## 설치와 예제 실행

언어에 맞는 휠, npm 압축파일, SDK 또는 JAR을 현재 디렉터리에 내려받습니다. Linux SDK 명령은 ARM64 기준입니다. x86_64에서는 압축파일과 실행파일 이름의 `arm64`를 `x86_64`로 바꾸세요. [릴리스 파일 다운로드](https://github.com/leechis7/tuivory/releases/tag/go/v0.12.2)

### Go

Go 1.24+가 필요합니다. `github.com/leechis7/tuivory/go`를 import합니다. 예제 명령은 Tuivory 소스 저장소에서 실행합니다. [Go 안내](go/README.md)

```sh
go get github.com/leechis7/tuivory/go@v0.12.2
```

```sh
make run ARGS="--demo catalog --mode grid --grid-sample --grid-preset data --lang ko"
```

### Rust

Rust 코어는 1.85+, Ratatui UI와 예제는 1.88+가 필요합니다. 예제 명령은 Tuivory 소스 저장소에서 실행합니다. [Rust 안내](rust/README.md)

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.12.2", features = ["ratatui"] }
```

```sh
make run-rust ARGS="--demo catalog --mode grid --grid-sample --grid-preset data --lang ko"
```

### Python

Python 3.11+가 필요합니다. 가상 환경에 휠을 설치하고 앱에서 `import tuivory`로 가져옵니다. [Python 안내](python/README.md)

```sh
python -m pip install ./tuivory-0.12.2-py3-none-any.whl
python -m tuivory --demo grid --lang ko
```

### TypeScript / JavaScript

Node.js 22+가 필요합니다. ESM 앱에서 `import * as ui from "tuivory"`로 가져옵니다. 패키지에는 JavaScript와 TypeScript 타입 선언이 들어 있습니다. [TypeScript / JavaScript 안내](javascript/README.md)

```sh
npm install ./tuivory-0.12.2.tgz
npm exec -- tuivory --demo grid --lang ko
```

### C

앱을 빌드하려면 C11 컴파일러가 필요합니다. `tuivory.h`를 포함하고 SDK의 `lib/libtuivory.a`를 링크합니다. [C 안내](c/README.md)

```sh
tar -xzf tuivory-c-0.12.2-linux-arm64.tar.gz
./tuivory-c-0.12.2-linux-arm64/bin/c/tuivory-linux-arm64 --demo grid --lang ko
```

### C++

앱을 빌드하려면 C++17 컴파일러가 필요합니다. SDK의 `include/` 디렉터리를 추가하고 `tuivory.hpp`를 포함합니다. [C++ 안내](cpp/README.md)

```sh
tar -xzf tuivory-cpp-0.12.2-linux-arm64.tar.gz
./tuivory-cpp-0.12.2-linux-arm64/bin/cpp/tuivory-linux-arm64 --demo grid --lang ko
```

### Java

Java 17+가 필요합니다. JAR을 앱의 클래스패스에 추가하고 `import static io.tuivory.Tuivory.*;`로 컴포넌트 타입을 가져옵니다. [Java 안내](java/README.md)

```sh
java -jar tuivory-0.12.2.jar --demo grid --lang ko
```

예제 기본 UI는 한글이며 `--lang en`으로 영어를 선택합니다. [다른 예제 보기](docs/examples.md)

![Tuivory](docs/images/playground-dark.svg)

## 문서 안내

- [설치·빠른 시작](docs/installation.md)
- [컴포넌트 가이드](docs/components.md)
- [API 명세](docs/api/README.md)
- [디자인 가이드](docs/design-guide.md)
- [앱과 라이브러리의 책임](docs/component-boundary.md)
- [개발·검증·이력](docs/development.md)

- [릴리스](docs/release-0.12.2.md) · [변경 이력](CHANGELOG.md) · [회수 버전](docs/withdrawn-versions.md)

[출처·라이선스](NOTICE.md)
