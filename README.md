# Tuivory — TUI 컴포넌트 라이브러리

**한국어 (기본)** · [English](README.en.md)

**Go/tview와 Rust/Ratatui**를 위한 TUI 컴포넌트 라이브러리입니다. 앱이 화면 구성·데이터·업무 동작을 연결합니다. Python·JavaScript는 현재 토큰 읽기 예제를 제공하며 UI 패키지는 계획 단계입니다.

**0.5.0** · [릴리스](docs/release-0.5.0.md) · [문서](docs/README.md) · [API](docs/api/README.md)

## 설치

```sh
go get github.com/leechis7/tuivory/go@v0.5.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.5.0", features = ["ratatui"] }
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

[출처·라이선스](NOTICE.md)
