# TVR-17 로컬 검증

**한국어 (기본)** · [English](grid-validation.en.md)

2026-10-29, `codex/TVR-17-grid-options` 작업 소스 기준입니다. 선행 문서 변경은 `c1a9b9a`로 커밋했으며 TVR-17은 검증 당시 미커밋 소스였으며 이 로컬 커밋에 포함합니다. GitHub에는 미게시입니다. v0.2.0 태그/Release에는 TVR-17이 없습니다. 원격 CI·LazyOra 실제 연결·실제 DB 편집·SSH/SecureCRT/MobaXterm 확인과 아래 로컬 검증을 구분합니다.

## 검사 범위

- Go 기존 전체 race 검사와 최종 그리드 race 검사, `go vet ./...`.
- Rust 1.85.1 코어 테스트·문서 예제, Rust 1.88.0 전체 기능/타깃 테스트·문서 예제·fmt·Clippy 경고 0.
- 기본 API 회귀, 옵션 왕복 후 안정 ID·선택 범위·원문·열 폭·스크롤 보존, 잘못된 옵션의 원자적 거부.
- 한글/CJK/이모지/결합 문자와 폭 0..79·높이 0..11, 두 문자 모드·세 밀도·세 오버플로 정책의 경계.
- 범위 TSV 원문·대량 복사 위임, 100,000행 가상 소스의 뷰포트 행 읽기, 현재 뷰포트 자동 폭, 수동 폭 우선, 밀도별 페이지 이동·위로 이동할 때 뷰포트 유지.
- 읽기 전용 셀의 편집 차단·수정 표시 우선순위·셀 메타데이터, 범위 드래그·열 리사이즈·호버/미지원 이벤트 무시, 오래되거나 중복인 응답 거부.
- dark/light/blackwhite × 8/16/256/True Color × Unicode/ASCII에서 Go Show 이후 Runes/Bytes/스타일 및 Rust TestBackend의 가시 문자/스타일, 좌우 두 칸 문자 경계와 오버레이 후 재그리기. TestBackend의 두 칸 문자 아래 숨은 연속 셀은 단말 표시처럼 선행 문자 폭에 따라 건너뜁니다.
- Go/Rust 데이터 프리셋 한영 PTY: 편집·Shift 범위·원문 복사·상세·정렬·마우스 헤더·가로/세로 이동·리사이즈·종료 후 단말 복원. 영어 실행은 ASCII 대체 표시도 확인합니다.
- design 디렉터리 없이 Go 모듈과 패키징한 Rust crate를 각각 외부 앱에서 import·렌더링. Go는 Show 이후 구분선 바이트, Rust는 TestBackend 구분선 확인.
- Go CGO 비활성·Rust musl: ARM64/x86_64 정적 ELF에 PT_INTERP/DT_NEEDED 없음. 별도 x86_64 외부 앱도 동일 검사.
- 한영 비교 SVG 14장, 공통 토큰/테스트 데이터 동등성, Python 검사 도구 테스트 7개와 로컬 문서 링크.

실행 로그와 임시 산출물은 Git에서 제외한 `bin/release-validation/`에 둡니다. 기존 태그·자산은 변경하지 않습니다.

## 재현 명령

```sh
go -C go test -race ./...
go -C go vet ./...
make check-rust-ui test-rust-ui
# 코어는 Rust 1.85.1 환경에서 별도 실행
cargo test --manifest-path rust/Cargo.toml --locked
python3 tools/check_go_module.py --static-output bin/release-validation/go-grid-host-linux-x86_64
python3 tools/check_rust_module.py --ratatui --static-output bin/release-validation/rust-grid-host-linux-x86_64
make build build-go-x86_64
python3 tools/build_rust.py --arch x86_64 --examples
python3 tools/build_rust.py --arch arm64
python3 tools/smoke_catalog.py /PATH/TO/catalog --mode grid --lang ko --grid-preset data
python3 tools/smoke_catalog.py /PATH/TO/catalog --mode grid --lang en --ascii --grid-preset data
python3 tools/snapshot_catalog.py /PATH/TO/RUST/catalog --mode grid --grid-sample --grid-preset data --name grid-data
python3 tools/snapshot_catalog.py /PATH/TO/RUST/catalog --mode grid --grid-sample --grid-preset simple --name grid-simple
```

`/PATH/TO/catalog`은 각 언어의 호스트 아키텍처 검증 실행파일입니다. 임시 빌드 공간이 부족하면 `TMPDIR`와 Go 캐시를 여유 있는 작업 경로로 지정합니다. 정적 검사와 대상 커널 실행 방법은 [정적 배포](static-build.md)를 참고하세요.

CentOS 7.4.1708 x86_64 / 커널 `3.10.0-693.el7.x86_64` / glibc `2.17-196.el7.x86_64`에서 Go·Rust 정적 견본의 한영 시작·종료와 두 외부 그리드 앱 실행을 모두 통과했습니다. QEMU TCG로 실제 구형 커널/사용자 공간을 부팅한 결과이며 물리 서버·SSH 검증은 아닙니다. ARM64 CentOS 실행 검증으로 확대하지 않습니다. [환경·산출물 해시](../evidence/grid-options-results.json).

[그리드 API·지원 범위](grid.md)
