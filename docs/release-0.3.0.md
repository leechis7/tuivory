# Tuivory 0.3.0 릴리스

**한국어 (기본)** · [English](release-0.3.0.en.md)

제품 `VERSION`과 Rust manifest/lock 버전은 **0.3.0**입니다. [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.3.0)에서 Linux ARM64/x86_64 정적 실행파일·독립 Rust crate·체크섬을 제공합니다. Go `go/v0.3.0`과 Rust `rust/v0.3.0` 태그는 같은 최종 커밋을 가리킵니다. TVR-7 에픽은 열린 상태를 유지합니다.

## 변경 범위

- [공통 메뉴](menus.md): Go·Rust 메뉴 막대, 계층 진입·뒤로 이동, 부모 선택과 원래 호출 위치 복원, 비활성·구분선·단축키·문자 탐색, 키보드·마우스·넘침·안전한 팝업 그리기.
- [그리드 옵션](grid.md): 같은 Grid의 simple/data 프리셋, 행 번호·여백·구분선·정렬·상태줄, 범위 선택·원문 복사·지연 응답 보호와 외부 앱 연결.
- [컴포넌트와 앱 책임](component-boundary.md): Tuivory는 TUI 컴포넌트 라이브러리입니다. 적용 앱이 화면 조합·전역 키·명령·DB/SQL·클립보드/파일 I/O를 담당합니다.
- 용어·한영 문서와 예제를 정리하고 Python·TypeScript·JavaScript의 일반 런타임 패키지 배포 예외를 명시합니다. 이 언어들의 UI 패키지는 아직 제공하지 않습니다.
- 사용자 지시에 따라 CentOS 검증을 중단하고 CI의 VM 단계를 제거합니다. 정적 배포와 ELF 검사는 유지합니다. 과거 CentOS 결과를 새 릴리스의 호환성 검증으로 확대하지 않습니다.

기존 0.2.0 컴포넌트는 유지합니다. [메뉴 화면](images/menu-dark.svg) · [영문 화면](images/menu-dark-en.svg).

## 설치

```sh
go get github.com/leechis7/tuivory/go@v0.3.0
```

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.3.0", features = ["ratatui"] }
```

Go 1.24 이상, Rust 코어 1.85 이상, Ratatui/실행 예제 1.88 이상입니다. Rust는 Git 배포이며 `publish = false`를 유지하고 crates.io에 게시하지 않습니다. 새 메뉴와 TVR-17 옵션은 이전 0.2.0 태그에 없습니다.

## 배포 자산

| 파일 | 내용 |
| --- | --- |
| `tuivory-go-v0.3.0-linux-arm64.tar.gz` | Go Linux ARM64 정적 playground·catalog·menu |
| `tuivory-go-v0.3.0-linux-x86_64.tar.gz` | Go Linux x86_64 정적 playground·catalog·menu |
| `tuivory-rust-v0.3.0-linux-arm64.tar.gz` | Rust Linux ARM64 musl playground·catalog·menu |
| `tuivory-rust-v0.3.0-linux-x86_64.tar.gz` | Rust Linux x86_64 musl playground·catalog·menu |
| `tuivory-0.3.0.crate` | 독립 Rust 소스·공개 API·예제·내장 데이터 |
| `SHA256SUMS` | 아카이브·crate·manifest 체크섬 |
| `RELEASE-MANIFEST.json` | 확정 소스 커밋·자산/바이너리 해시·검증 범위 |

압축파일 내부 실행파일은 `bin/<언어>/tuivory[-catalog|-menu]-linux-<아키텍처>`입니다. 각각 `--lang ko`/`--lang en`으로 실행하며, catalog는 `--mode grid --grid-preset data`로 새 그리드를 표시합니다. 메뉴는 F10으로 열고 Ctrl+Q로 종료합니다. 기본 `make build`는 Go Linux ARM64 하나만 생성하는 기존 정책을 유지합니다. 정적 실행파일은 동적 로더·공유 라이브러리·별도 언어 런타임을 요구하지 않습니다.

## 검증과 게시 근거

선행 구현과 dev 통합은 [PR #16](https://github.com/leechis7/tuivory/pull/16), [메뉴 검증](../evidence/menu.md), [그리드 검증](grid-validation.md)에 기록합니다. 릴리스 준비·main CI, 최종 커밋의 자산 빌드·정적 ELF, 한영 ARM64 PTY, 실제 공개 태그의 외부 Go/Rust 설치·API·렌더링, 업로드 자산 재다운로드/체크섬 결과는 Release의 `RELEASE-MANIFEST.json`과 [TVR-7](https://leechis7.atlassian.net/browse/TVR-7) 댓글을 기준으로 확인합니다. 미실행 항목을 통과로 간주하지 않습니다.

CentOS·고객 SSH·폰트별 물리 단말·실제 LazyOra/LazyBeaver·DB 편집 통합은 이번 릴리스 검증에 포함하지 않습니다. 기존 태그·릴리스 자산은 보존합니다.
