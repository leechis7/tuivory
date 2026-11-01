# Tuivory 0.9.0 릴리스

**한국어 (기본)** · [English](release-0.9.0.en.md)

Go·Rust에서 선택적으로 사용할 Oracle SQL/PLSQL 문법 분석기와 공통 강조 역할을 제공합니다. Go는 루트 패키지 하나를 import하고, Rust는 `syntax-sql` 기능을 켭니다. 앱 자체 분석기도 연결할 수 있습니다.

```sh
go get github.com/leechis7/tuivory/go@v0.9.0
```

```go
import "github.com/leechis7/tuivory/go"
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.9.0", features = ["terminal", "syntax-sql"] }
```

UTF-8 바이트 범위 선택·교체, Undo/Redo, 편집 후 분석 갱신과 오래된 결과 제거를 지원합니다. 비활성·선택·검색·문법 강조 순서를 공통으로 적용하고 컴포넌트 바탕색을 유지합니다. [문법 분석 사용법·전환·실행 예제](syntax.md) · [공통 규격](../design/syntax.md) · [API 명세](api/README.md).

Go 1.24+, Rust 코어 1.85+, UI/터미널 1.88+입니다. Rust의 기본 기능에는 SQL 분석기가 포함되지 않으며 새 네이티브 의존성은 없습니다. crates.io에는 게시하지 않습니다.

[GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.9.0)는 Go·Rust Linux ARM64/x86_64용 playground/catalog/menu/controls/syntax 실행파일 **20개**, Rust crate, SHA256SUMS와 RELEASE-MANIFEST.json을 제공합니다. 각 언어·아키텍처 압축파일의 `bin/<언어>/tuivory-syntax-linux-<아키텍처>`로 SQL 예제를 실행합니다. `--lang ko` 또는 `--lang en`, `--ascii`를 사용할 수 있습니다.

최종 manifest는 소스 커밋, 정적 ELF 검사, 공개 태그 설치, 다운로드 실행 및 GitHub CI 결과를 기록합니다. [구현 당시 로컬 검증](../evidence/syntax-results.json)은 게시 전 이력입니다. 긴 문서는 전체 분석하므로 증분 분석기의 지연 시간을 보장하지 않습니다.

SQL 실행·안전성 판단·DB 연결, 실제 LazyOra 앱 전환, Go/Rust 소스 분석기는 포함하지 않습니다. CentOS 검증은 수행하지 않습니다. TVR-7 에픽은 열어둡니다.
