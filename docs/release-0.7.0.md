# Tuivory 0.7.0 릴리스

**한국어 (기본)** · [English](release-0.7.0.en.md)

TVR-26은 Go·Rust 앱이 Tuivory 경로만으로 UI를 구성하도록 SDK 호환 경로와 공통 입력 API를 제공합니다. [사용법·전환 예제](ui-facade.md) · [언어 중립 명세](../design/ui-facade.md) · [API 명세](api/README.md).

- Go `go/ui`, `go/terminal`: 고정 tview/tcell 타입·함수·상수와 설정 setter. 기존 타입·콜백의 호환성을 유지합니다.
- Rust `ui`, `ui::components`, `ui::terminal`: 렌더링·이벤트를 단일 Cargo 의존성으로 사용합니다. `terminal` 기능의 `Session`은 정상 종료·초기화 실패·panic unwind 시 터미널을 정리합니다.
- 공통 `InputEvent`와 편집 동작 변환, UTF-8 byte 범위에서 grapheme 경계로의 구문 강조 변환. 잘못된 경계는 이전 강조를 보존하며 오류로 반환합니다.
- 공개 Go·Rust 예제는 직접 backend import 없이 SDK 경로를 사용합니다. 화면·테마는 0.6.0과 동일합니다.

```sh
go get github.com/leechis7/tuivory/go@v0.7.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.7.0", features = ["terminal"] }
```

Go 1.24+, Rust 코어 1.85+, UI/터미널 1.88+입니다. 그리기만 필요한 Rust 앱은 `ratatui` 기능을 사용합니다. crates.io에는 게시하지 않습니다.

[GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.7.0)에서 Go·Rust Linux ARM64/x86_64 정적 playground/catalog/menu/controls 실행파일, Rust crate, SHA256SUMS와 RELEASE-MANIFEST.json을 제공합니다. manifest는 실제 소스 커밋·정적 ELF·공개 태그 설치·다운로드 실행·GitHub CI 결과를 기록합니다. [구현 당시 로컬 검증](../evidence/ui-facade-results.json)은 별도 이력입니다.

예제는 `make run-controls-go` / `make run-controls-rust`, 영어는 `ARGS="--lang en"`입니다. LazyOra의 실제 전환·DB 연결은 포함하지 않습니다. 호환 별칭은 고정 backend의 정체성을 유지하며 backend 교체나 ABI 호환을 보장하지 않습니다. Python·JS/TS·C·C++는 설계 대상이며 구현 완료가 아닙니다. CentOS 검증은 수행하지 않습니다. TVR-7 에픽은 열어둡니다.
