# TVR-7 공통 메뉴 검증

**한국어 (기본)** · [English](menu.en.md)

2026-10-29, 기준 `50bf212`, 브랜치 `codex/TVR-7-menus`의 미커밋·미게시 작업 소스입니다. 선행 책임 범위 정정은 사용자 승인으로 `50bf212`에 커밋했으며 원격 게시하지 않았습니다. 메뉴 개선의 커밋·push·PR·병합·태그·Release·원격 CI는 수행하지 않았습니다. 기존 v0.2.0에는 새 Menu API가 없습니다. TVR-7 에픽은 열린 상태로 유지합니다.

## 출처와 변경

LazyOra 공개 커밋 `98a2f47e8621838101d5db781232a699dba382f3`의 [menu.go](https://github.com/leechis7/lazyora/blob/98a2f47e8621838101d5db781232a699dba382f3/internal/ui/menu.go), [menu_groups.go](https://github.com/leechis7/lazyora/blob/98a2f47e8621838101d5db781232a699dba382f3/internal/ui/menu_groups.go)를 읽었습니다. 같은 커밋의 로컬 메뉴 소스가 수정되지 않은 것도 확인했습니다. 그룹 진입/뒤로가기·부모 선택 보존·원래 호출 패널·영역 제한·구분선/비활성/단축키 표시 원칙을 참고했으며 SQL·트랜잭션·명령 분류 코드/임계값을 이전하지 않았습니다.

새 Go/Rust Menu 모델, 메뉴 바/내용 렌더러·팝업 배치, Rust 팝업 표면/테두리, DB 없는 호스트·한영 설명/이미지를 제공합니다. 기존 ListModel·SearchPicker·다른 컴포넌트 API를 변경하지 않습니다. 앱이 메뉴 그룹/항목/사용 가능 상태·전역 키·화면 조합·실제 명령 실행을 결정합니다.

## 검사 범위

- `design/menu-cases.json`의 같은 데이터·시나리오를 독립 Go/Rust 모듈 테스트 자산으로 복제합니다. 3단계 진입/복귀·부모 선택·루트 그룹 전환·문맥 루트·mnemonic·원래 ReturnID를 비교합니다.
- 빈 메뉴 메시지·32/33단계·10,000 초과 개수·누락/순환 부모·중복 ID/mnemonic·구분선 자식·비활성 차단, 잘못된 변경의 원자성·동적 조상 비활성 후 닫기/복귀를 검사합니다.
- 폭 0..89·높이 0..11과 Unicode/ASCII, 한글/CJK/이모지/결합 문자·긴 라벨·메뉴 바 넘침·단축키/태그 리터럴·팝업 뷰포트 경계를 확인합니다.
- dark/light/blackwhite × 8/16/256/True Color × Unicode/ASCII에서 Go Show 이후 실제 Runes/Bytes/스타일과 외부 영역, Rust TestBackend 전체 팝업의 좌우 두 칸 문자 경계·제목 단일 표시를 검사합니다. Go 메뉴 바는 클릭 후 캡처를 남기지 않습니다.
- Go 전체 race/vet, Rust 1.85.1 코어와 Rust 1.88.0 전체 기능/타깃/doctest/fmt/Clippy를 실행합니다.
- 실제 PTY는 Go/Rust × 한국어/영어 × 초기 Unicode/ASCII의 8개 장면입니다. F10/Shift+F10/Alt, 하위/뒤로/루트 전환·비활성 건너뛰기·원래 패널 복귀와 실제 문자 입력·붙여넣기/배경 차단·동적 사용 가능 상태·메뉴 바/바깥 클릭·테마/프로필/ASCII 왕복·리사이즈·정상 종료/단말 복원을 확인합니다. 한국어 메시지는 ANSI를 해석한 화면으로 확인합니다.
- design 디렉터리 없이 Go 모듈과 패키징한 Rust crate를 외부 앱에 설치/import해 모델 요청·호출 문맥과 실제 메뉴 렌더링을 확인합니다. Go는 Show 이후 물리 바이트, Rust는 TestBackend 팝업 테두리/내용을 확인합니다.
- Go CGO 비활성/Rust musl 메뉴 실행파일 ARM64/x86_64 4개 및 외부 x86_64 앱 2개는 PT_INTERP/DT_NEEDED가 없는 정적 ELF입니다.
- CentOS 7.4.1708 사용자 공간·커널 `3.10.0-693.el7.x86_64`·glibc `2.17-196.el7.x86_64`를 QEMU TCG로 부팅해 최종 x86_64 예제의 한영 시작·종료 4회와 외부 앱 2개를 확인합니다. VM 예제는 메뉴가 닫힌 기본 시작 장면이며 계층 조작은 ARM64 PTY에서 검사합니다.
- Rust 기본 메뉴 한영 8장과 하위 메뉴 한영 2장, 공통 토큰/테스트 데이터 동등성, Python 검사 도구 7개와 문서 링크/공백을 검사합니다. 참조 화면은 실제 Rust TestBackend이며 Go 캡처·물리/SSH 단말 결과가 아닙니다.

최종 상태·정확한 소스/이미지/실행파일 해시는 [결과 JSON](menu-results.json)에 기록합니다. 로그·임시 산출물은 Git 제외 `bin/validation/`에 둡니다. 실제 LazyOra/LazyBeaver 적용·고객 SSH·글꼴별 물리 단말·원격 CI·실제 공개 태그 설치는 이번 검증에 포함하지 않습니다.

## 재현

```sh
go -C go test -race ./...
go -C go vet ./...
make check-rust-ui test-rust-ui
# Rust 1.85.1 환경에서 코어 별도 검사
cargo test --manifest-path rust/Cargo.toml --locked
python3 tools/check_go_module.py --static-output bin/validation/go-menu-host-linux-x86_64
python3 tools/check_rust_module.py --ratatui --static-output bin/validation/rust-menu-host-linux-x86_64
python3 tools/smoke_menu.py /PATH/TO/menu --lang ko
python3 tools/smoke_menu.py /PATH/TO/menu --lang en --ascii
python3 tools/snapshot_menu.py /PATH/TO/RUST/menu
python3 tools/export_tree_cases.py --check
python3 tools/check_links.py
```

PTY 검사는 양 언어 실행파일과 두 UI 언어·초기 문자 모드를 각각 사용합니다. 정적 ELF/구형 커널 절차는 [정적 배포](../docs/static-build.md)를 따릅니다. 기본 제품 빌드 정책을 바꾸지 않으며 메뉴 예제 실행파일은 `bin/<언어>/menu-linux-<아키텍처>`입니다.

[공통 메뉴 사용법](../docs/menus.md) · [컴포넌트/앱 책임](../docs/component-boundary.md)
