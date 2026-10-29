# Tuivory 0.4.0 릴리스

**한국어 (기본)** · [English](release-0.4.0.en.md)

제품 `VERSION`과 Rust manifest/lock 버전은 **0.4.0**입니다. [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.4.0)에서 Linux ARM64/x86_64 정적 실행파일·독립 Rust crate·체크섬을 제공합니다. Go `go/v0.4.0`과 Rust `rust/v0.4.0` 태그는 같은 최종 커밋을 가리킵니다. TVR-7 에픽은 열린 상태를 유지합니다.

## 변경 범위

- 메뉴 팝업을 단일선으로 통일하고 별도 포커스 장식을 제거합니다. 일반 패널은 현재 조작 영역의 이중선·비활성 단일선 규칙을 유지합니다.
- Go 견본의 창 크기 변경 시 그리기 잠금과 포커스 변경이 겹치던 교착을 수정합니다.
- 평문 배경을 실제 표면에 맞추고 선택·편집·그리드의 명시적 배경을 보존합니다. Go `TextOnSurface`·`ControlStyleOnSurface`, Rust `Styles::text_on_surface`·`control_on_surface`, 행 배경 보존 API를 제공합니다.
- [비활성 표시](disabled-states.md): 12팔레트의 회색/Dim 전경을 보완하고 일반 비활성 접두사를 제거합니다. 체크박스·라디오의 선택 표식은 유지합니다. 비활성 옵션 클릭으로 부모 포커스가 이동하는 문제를 수정하며 포커스·실행 제외를 검사합니다. 8색 Dim은 단말 지원에 따라 표현이 달라집니다.
- 공개 컴포넌트로 그리는 Rust states 비교 예제, Go/Rust catalog의 비활성 입력·버튼, 한영 [디자인 가이드](../design/surfaces.md)와 UI 참조 104개를 제공합니다.

0.3.0의 메뉴·그리드·기존 컴포넌트를 포함합니다. 제품 major 버전은 바꾸지 않습니다. Python·TypeScript UI 패키지는 아직 제공하지 않습니다.

## 설치

```sh
go get github.com/leechis7/tuivory/go@v0.4.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.4.0", features = ["ratatui"] }
```

Go 1.24 이상, Rust 코어 1.85 이상, Ratatui/실행 예제 1.88 이상입니다. Rust는 Git 배포이며 `publish = false`를 유지하고 crates.io에 게시하지 않습니다. 새 표면 API·비활성 명암 보완은 이전 0.3.0 태그에 없습니다.

## 배포 자산

| 파일 | 내용 |
| --- | --- |
| `tuivory-go-v0.4.0-linux-arm64.tar.gz` | Go Linux ARM64 정적 playground·catalog·menu |
| `tuivory-go-v0.4.0-linux-x86_64.tar.gz` | Go Linux x86_64 정적 playground·catalog·menu |
| `tuivory-rust-v0.4.0-linux-arm64.tar.gz` | Rust Linux ARM64 musl playground·catalog·menu |
| `tuivory-rust-v0.4.0-linux-x86_64.tar.gz` | Rust Linux x86_64 musl playground·catalog·menu |
| `tuivory-0.4.0.crate` | 독립 Rust 소스·공개 API·예제·내장 데이터 |
| `SHA256SUMS` | 아카이브·crate·manifest 체크섬 |
| `RELEASE-MANIFEST.json` | 확정 소스 커밋·자산/바이너리 해시·검증 범위 |

압축파일 내부 실행파일은 `bin/<언어>/tuivory[-catalog|-menu]-linux-<아키텍처>`입니다. 각각 `--lang ko`/`--lang en`으로 실행하며, catalog는 `--mode grid --grid-preset data`로 새 그리드를 표시합니다. 메뉴는 F10으로 열고 Ctrl+Q로 종료합니다. 기본 `make build`는 Go Linux ARM64 하나만 생성하는 기존 정책을 유지합니다. 정적 실행파일은 동적 로더·공유 라이브러리·별도 언어 런타임을 요구하지 않습니다.

## 검증과 게시 근거

선행 구현과 dev 통합은 [PR #16](https://github.com/leechis7/tuivory/pull/16), [메뉴 검증](../evidence/menu.md), [그리드 검증](grid-validation.md)에 기록합니다. 릴리스 준비·main CI, 최종 커밋의 자산 빌드·정적 ELF, 한영 ARM64 PTY, 실제 공개 태그의 외부 Go/Rust 설치·API·렌더링, 업로드 자산 재다운로드/체크섬 결과는 Release의 `RELEASE-MANIFEST.json`과 [TVR-7](https://leechis7.atlassian.net/browse/TVR-7) 댓글을 기준으로 확인합니다. 미실행 항목을 통과로 간주하지 않습니다.

CentOS·고객 SSH·폰트별 물리 단말·실제 LazyOra/LazyBeaver·DB 편집 통합은 이번 릴리스 검증에 포함하지 않습니다. 기존 태그·릴리스 자산은 보존합니다.

0.4.0 표시·입력 검증의 상세 내역은 [비활성 상태](disabled-states.md), [배경 수정](../evidence/background-fix.md), [현재 결과 JSON](../evidence/disabled-colors-results.json)에 있습니다. 다운로드한 ARM64 실행파일은 로컬 PTY에서, x86_64 실행파일은 별도 GitHub Actions `Validate release assets`에서 실행합니다. 릴리스 자산 검증은 소스 커밋과 체크섬을 확인하며 CentOS를 사용하지 않습니다.
