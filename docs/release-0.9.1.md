# Tuivory 0.9.1 릴리스

**한국어 (기본)** · [English](release-0.9.1.en.md)

예제를 언어별 통합 실행파일 하나로 제공하고 저장소 폴더를 정리합니다. SDK 공개 API는 0.9.0과 호환됩니다.

```sh
go get github.com/leechis7/tuivory/go@v0.9.1
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.9.1", features = ["terminal", "syntax-sql"] }
```

Go는 기존처럼 `github.com/leechis7/tuivory/go` 하나를 import합니다. Rust는 Git 배포이며 crates.io에 게시하지 않습니다. Go 1.24+, Rust 코어 1.85+, UI/예제 1.88+입니다.

[배포 압축파일](https://github.com/leechis7/tuivory/releases/tag/go/v0.9.1)은 Go·Rust Linux ARM64/x86_64별로 제공하며 각각 `bin/<언어>/tuivory-linux-<아키텍처>` **하나**를 포함합니다. 별도 예제 실행파일이나 언어 런타임·공유 라이브러리가 필요 없습니다.

```sh
./bin/go/tuivory-linux-arm64 --list
./bin/go/tuivory-linux-arm64 --demo tree --lang ko
./bin/rust/tuivory-linux-arm64 --demo syntax --lang en
```

playground/tree/workspace/focus/catalog/menu/controls/syntax를 같은 파일에서 선택합니다. [예제 전체 안내](examples.md).

`make build`와 `make build-rust`는 실행 중인 Linux 서버의 아키텍처만 빌드합니다. ARM64는 로컬 서버, x86_64는 GitHub의 x86_64 서버에서 빌드합니다. `bin/`은 실행파일 전용이며 임시 빌드·검증·릴리스 보관은 Git 제외 `.cache/`를 사용합니다. 예제 안내는 이 문서군에 통합하고 검증 기록은 `docs/evidence/`로 옮겼습니다. [구조](architecture.md) · [정적 빌드](static-build.md).

최종 RELEASE-MANIFEST.json과 SHA256SUMS는 소스 커밋·네 실행파일의 ELF 검사·공개 태그 설치·다운로드 실행·GitHub CI 결과를 기록합니다. 구현 당시 [예제 검증](evidence/showcase-results.json)과 [폴더 정리 검증](evidence/layout-results.json)은 게시 전 이력으로 보존합니다. 기존 0.9.0 태그·자산은 변경하지 않습니다. CentOS 검증은 수행하지 않습니다.
