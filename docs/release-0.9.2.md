# Tuivory 0.9.2 릴리스

**한국어 (기본)** · [English](release-0.9.2.en.md)

WideSafeScreen과 Surface·그림자 안의 Go 표 재칠 시 한글·CJK·이모지가 사라지던 결함을 수정합니다. 분할선과 비교표 제목·구분선의 12팔레트 대비, 비활성 선택 필드와 8색 Dim을 보완합니다. Rust 견본의 탐색·팔레트·한영 도움말을 Go 기준으로 맞추고 Go 첫 화면 카드 배경을 수정합니다. 공개 API는 0.9.1과 호환됩니다.

```sh
go get github.com/leechis7/tuivory/go@v0.9.2
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.9.2", features = ["terminal", "syntax-sql"] }
```

Go는 기존처럼 `github.com/leechis7/tuivory/go` 하나를 import합니다. Rust는 Git 배포이며 crates.io에 게시하지 않습니다. Go 1.24+, Rust 코어 1.85+, UI/예제 1.88+입니다.

[배포 압축파일](https://github.com/leechis7/tuivory/releases/tag/go/v0.9.2)은 Go·Rust Linux ARM64/x86_64별로 제공하며 각각 `bin/<언어>/tuivory-linux-<아키텍처>` **하나**를 포함합니다. 별도 예제 실행파일이나 언어 런타임·공유 라이브러리가 필요 없습니다.

```sh
./bin/go/tuivory-linux-arm64 --list
./bin/go/tuivory-linux-arm64 --demo tree --lang ko
./bin/rust/tuivory-linux-arm64 --demo syntax --lang en
```

playground/tree/workspace/focus/catalog/menu/controls/syntax를 같은 파일에서 선택합니다. [예제 전체 안내](examples.md).

`make build`와 `make build-rust`는 실행 중인 Linux 서버의 아키텍처만 빌드합니다. ARM64는 로컬 서버, x86_64는 GitHub의 x86_64 서버에서 빌드합니다. `bin/`은 실행파일 전용이며 임시 빌드·검증·릴리스 보관은 Git 제외 `.cache/`를 사용합니다. 예제 안내는 이 문서군에 통합하고 검증 기록은 `docs/evidence/`로 옮겼습니다. [구조](architecture.md) · [정적 빌드](static-build.md).

RELEASE-MANIFEST.json과 SHA256SUMS에 최종 소스 커밋·정적 ELF·공개 태그 설치·다운로드 실행·CI 결과를 기록합니다. 기존 릴리스 자산은 보존하며 CentOS 검증은 수행하지 않습니다.

검증: Show/Sync 이후 실제 버퍼, 전체 grapheme 재칠과 덮어쓰기 복구, 12팔레트, 단일 import 독립 Go 적용 앱, Rust TestBackend, 한영 PTY 예제, API 생성과 정적 ELF를 검사합니다. 구현 당시 검증은 게시 전 이력으로 보존합니다: [TVR-7](evidence/tvr7-lazyora-rendering-results.json), [비활성 상태](evidence/go-disabled-followup-results.json), [예제 일치](evidence/example-parity-results.json). 최종 게시 근거는 릴리스 자산 명세에 기록합니다.
