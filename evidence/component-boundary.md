# TVR-7 책임 범위 정정 검증

**한국어 (기본)** · [English](component-boundary.en.md)

2026-10-29, 기준 `e34b824`, 작업 브랜치 `codex/TVR-7-component-boundary`. 이번 변경은 로컬 커밋에 포함하며 GitHub에는 미게시입니다. TVR-17 커밋과 기존 v0.2.0 태그를 변경하지 않았으며 TVR-7 에픽은 열린 상태를 유지합니다.

## 변경과 경계

- 프로젝트 소개를 TUI 컴포넌트 라이브러리로 맞추고 Go/Rust 공개 패키지 설명·한영 책임 범위·현재 지원 점검표·설계·로드맵·작업 규칙을 현행화했습니다.
- 평면 메뉴 제공/중첩 메뉴 전용 API 미제공, 이미 구현한 탭 넘침·Help와 앱 전용 화면을 구분했습니다. 새 메뉴 구현·새 일감·전체 화면 이전을 추가하지 않았습니다.
- 기존 Go/Rust workspace 호스트에 `--layout`, `--focus-order`, `--quit-key`를 추가했습니다. 라이브러리의 공개 타입·시그니처·기능 구현은 바꾸지 않았습니다. Go 패키지/Rust crate 소개 주석과 Cargo 설명만 수정했습니다.
- 기본 열 분할/탭→트리→내용/Ctrl+Q와 대체 행 분할/내용→트리→탭/Ctrl+X는 같은 공개 컴포넌트를 사용합니다. 앱의 이벤트 루프와 화면 배치 코드는 호스트에 남습니다.

## 로컬 결과

| 검사 | 결과와 한계 |
| --- | --- |
| Go | `go -C go test ./...`, `go -C go vet ./...` 통과. 공개 기능의 새 회귀/경쟁 조건을 추가한 작업은 아니므로 race 전체 재실행은 이번에 하지 않음 |
| Rust | Rust 1.88.0의 `make check-rust-ui test-rust-ui` 통과: 전체 기능/타깃/문서 예제/fmt/Clippy 경고 0 |
| 실제 PTY | Go/Rust × 기본/대체 × 한국어/영어 = 8개 통과. 수정 탭 닫기 보류, 호스트 포커스/역순, 키 교체, 분할 전환·리사이즈, 테마/프로필, 정상 종료·대체 화면 복원 |
| 잘못된 호스트 설정 | layout/quit 키/누락·중복·알 수 없는 포커스 항목 5종을 단말 진입 전에 거부 |
| 참조 이미지 | Rust 대체 구성 한영 2장 생성·언어 검사와 한국어 화면 시각 확인. 기존 기본 구성 8장은 재생성 후 파일 바이트 동일 |
| 정적 ELF | Go CGO 비활성/Rust musl, ARM64/x86_64 workspace 4개에 PT_INTERP/DT_NEEDED 없음 |
| CentOS 7.4 | 실제 7.4.1708 사용자 공간·3.10.0-693.el7.x86_64 커널·glibc 2.17-196을 QEMU TCG로 부팅. Go/Rust 기본 구성 한영 시작·Ctrl+Q 종료 4회 통과. 대체 정책의 조작은 호스트 ARM64 PTY 검사이며 VM에서 확대 주장하지 않음 |
| 데이터·도구·문서 | 공통 토큰/검사 데이터 동등성, Python 도구 검사 7개, 로컬 Markdown 링크·diff 공백 검사 통과 |

한글 PTY 문자는 ANSI 커서 이동으로 여러 조각에 나뉘므로 원시 바이트의 연속 문자열 대신 해석한 화면에서 닫기 보류 문구를 검사합니다. 외부 패키지 import/배포 태그·원격 CI·실제 LazyOra/LazyBeaver/고객 SSH는 이번에 다시 검사하지 않았습니다. 새 호스트 옵션은 기존 v0.2.0 태그에 없습니다.

## 재현

```sh
go -C go test ./...
go -C go vet ./...
make check-rust-ui test-rust-ui
python3 tools/smoke_workspace.py /PATH/TO/workspace --host-policy default --lang ko
python3 tools/smoke_workspace.py /PATH/TO/workspace --host-policy alternate --lang en
python3 tools/snapshot_workspace.py /PATH/TO/RUST/workspace --host-policy alternate
python3 tools/check_links.py
python3 tools/export_tokens.py --check
python3 tools/export_tree_cases.py --check
python3 -m unittest discover -s tests -v
```

PTY 명령은 양 언어 실행파일과 양 언어 UI에 각각 실행합니다. 정적 검사·구형 커널 재현은 [정적 배포](../docs/static-build.md) 절차를 따릅니다. 임시 산출물/로그는 Git 제외 `bin/validation/`에 있으며 [환경·해시 기록](component-boundary-results.json)으로 소스를 식별합니다.

[책임 범위와 사용 예](../docs/component-boundary.md)
