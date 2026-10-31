# Tuivory 0.8.0 릴리스

**한국어 (기본)** · [English](release-0.8.0.en.md)

Go 앱은 **Tuivory를 한 번만 import**하여 전체 UI를 구성할 수 있습니다. 앱·위젯·화면·키/마우스·색상·설정 API를 루트에서 제공합니다.

```sh
go get github.com/leechis7/tuivory/go@v0.8.0
```

```go
import "github.com/leechis7/tuivory/go"
```

기존 의미 모델 생성자는 그대로 유지합니다. 이름이 겹치는 호환 위젯은 `WidgetForm`·`NewWidgetForm`, `WidgetButton`·`NewWidgetButton` 등으로 구분합니다. 기존 `/ui`·`/terminal` 경로도 유효하며 tview/tcell은 내부 의존성으로 유지합니다. [단일 import 예제·이름 대응·설정](ui-facade.md) · [Go API 명세](api/go.md).

TVR-26 후속 변경으로 공개 Go 예제를 단일 import로 전환하고 생성 심볼 대응·외부 앱 검증·한영 문서를 갱신합니다. 기존 타입·콜백 정체성과 UI 표현을 유지합니다. Rust 기능 변경은 없으며 제품 버전을 맞춥니다.

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.8.0", features = ["terminal"] }
```

Go 1.24+, Rust 코어 1.85+, UI/터미널 1.88+입니다. Rust의 그리기만 필요하면 `ratatui` 기능을 사용합니다. crates.io에는 게시하지 않습니다.

[GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.8.0)는 Go·Rust Linux ARM64/x86_64 정적 playground/catalog/menu/controls 실행파일, Rust crate, SHA256SUMS와 RELEASE-MANIFEST.json을 제공합니다. 최종 manifest는 소스 커밋·정적 ELF·공개 태그 설치·다운로드 실행·GitHub CI 결과를 기록합니다. [구현 당시 로컬 검증](../evidence/go-single-import-results.json)은 별도 이력입니다.

LazyOra의 실제 앱 전환·DB 연결과 후속 언어 구현은 포함하지 않습니다. CentOS 검증은 수행하지 않습니다. TVR-7 에픽은 열어둡니다.
