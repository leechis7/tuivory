# Tuivory — TUI 컴포넌트 라이브러리

**한국어 (기본)** · [English](README.en.md)

Tuivory는 터미널 앱에 쓰는 트리, 메뉴, 폼, 대화상자, 텍스트 편집기, 데이터 그리드를 제공하는 TUI 컴포넌트 라이브러리입니다. 라이브러리가 각 컴포넌트의 그리기와 조작을 맡고, 앱이 화면을 구성하고 데이터와 동작을 연결합니다.

Go/tview와 Rust/Ratatui 패키지를 제공하며, Python, TypeScript/JavaScript, C, C++, Java도 각 언어에서 독립적으로 동작합니다. [언어 지원 현황](docs/languages.md)

## 설치

```sh
go get github.com/leechis7/tuivory/go@v0.12.1
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.12.1", features = ["ratatui"] }
```

Go 1.24+, Rust core 1.85+, Rust UI 1.88+. [설치 상세](docs/installation.md)

## 예제 실행

```sh
make run
make run-menu-go ARGS="--shadow auto"
make run-menu-rust ARGS="--shadow auto"
```

기본 UI는 한글이며 `--lang en`으로 영어를 선택합니다.

![Tuivory](docs/images/playground-dark.svg)

## 문서 안내

- [설치·빠른 시작](docs/installation.md)
- [컴포넌트 가이드](docs/components.md)
- [API 명세](docs/api/README.md)
- [디자인 가이드](docs/design-guide.md)
- [앱과 라이브러리의 책임](docs/component-boundary.md)
- [개발·검증·이력](docs/development.md)

- [릴리스](docs/release-0.12.1.md) · [변경 이력](CHANGELOG.md) · [회수 버전](docs/withdrawn-versions.md)

[출처·라이선스](NOTICE.md)
