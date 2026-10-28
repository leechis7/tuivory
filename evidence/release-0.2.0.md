# 0.2.0 릴리스 준비 검증

**한국어 (기본)** · [English](release-0.2.0.en.md)

이 문서는 게시 전 준비 기록입니다. 최종 자산·게시 검증은 [릴리스 안내](../docs/release-0.2.0.md)와 Release 첨부 manifest를 확인하세요.

2026-10-28, Linux ARM64에서 로컬 0.2.0 후보를 검사했습니다. [포함 범위·게시 경계](../docs/release-0.2.0.md) · [후보 버전·기준 커밋·SHA256·실행 결과](release-0.2.0-results.json).

## 결과

| 검사 | 결과 |
| --- | --- |
| 제품/Cargo/lock/crate 버전 | 모두 0.2.0. 의존성 버전은 유지 |
| `make test check` | Go race/vet·공통 데이터/명세·팔레트·링크·도구·Shell 통과 |
| Rust 1.85.1 core, 1.88.0 all-features | 테스트·rustdoc·fmt·clippy 통과 |
| 독립 Go 모듈·외부 import | 저장소 design/ 없이 공개 API·Show 이후 출력 검사 통과 |
| 독립 Rust crate·Ratatui 외부 앱 | 0.2.0 패키지·모델/렌더러·정적 외부 호스트 통과 |
| ARM64/x86_64 정적 ELF | Go/Rust playground·catalog 8개에 PT_INTERP/DT_NEEDED 없음. 외부 호스트도 정적 |
| 후보 압축파일·crate 5개 | SHA256SUMS 검사 및 실제 압축 해제·구성·실행 검사 통과 |
| 실제 아카이브 ARM64 PTY | 양 언어 playground×한영 4개, catalog×5모드×한영 20개, 총 24개 시작/조작·테마/리사이즈·종료/복원 검사 통과 |
| 실제 Rust 후보 참조 | 5모드×한영×3테마 30장 생성·문서와 일치. 이전 제목이 남은 forms 6장을 현행화 |
| 실제 아카이브 x86_64 CentOS 7.4 | 고정 공식 이미지·3.10.0-693 커널·glibc 2.17-196에서 Go/Rust playground/catalog 한영 8장면 및 외부 정적 앱 2개 실행 통과 |

Rust 외부 검사 첫 실행은 `/tmp`의 디스크 할당량 초과로 중단됐습니다. 저장소에서 무시하는 `bin/release-validation/`을 임시 경로로 사용해 재실행했고 통과했습니다. 소스 오류를 수정하거나 검사를 생략하지 않았습니다.

## 재현 명령

```sh
make test check
# RUSTUP_TOOLCHAIN=1.85.1
make test-rust check-rust
# RUSTUP_TOOLCHAIN=1.88.0
make test-rust-ui check-rust-ui
make build build-rust build-go-x86_64 build-rust-x86_64
python3 tools/build_rust.py --arch arm64 --examples
python3 tools/build_rust.py --arch x86_64 --examples
cargo package --manifest-path rust/Cargo.toml --locked --allow-dirty
python3 tools/check_go_module.py --static-output /tmp/go-host
python3 tools/check_rust_module.py --ratatui --static-output /tmp/rust-host
```

아카이브 내부의 실행파일을 직접 `smoke_playground.py`·`smoke_catalog.py`에 전달했습니다. `snapshot_catalog.py`로 참조를 생성했고 `check_centos74.py`에는 아카이브의 x86_64 실행파일과 외부 호스트를 전달했습니다. VM의 catalog 시작은 기본 forms 모드이며 다른 모드의 실제 입력은 native PTY, 모델·API는 외부 앱에서 검증합니다. 구체적인 바이너리 해시는 결과 JSON을 따릅니다.

## 남은 게시 단계

후보 파일은 로컬 `bin/releases/v0.2.0/`에 있으며 최종 배포 자산이 아닙니다. 커밋 전 소스(기준 dev `b9993d6`)의 dirty 빌드이며 게시 승인 후 확정 커밋에서 재빌드해야 합니다. 이번 준비 변경의 커밋·원격 CI·main 통합·새 태그·GitHub Release·실제 0.2.0 태그 설치는 아직 실행하지 않았습니다. 과거 dev CI를 이번 준비 브랜치의 결과로 간주하지 않습니다.

실제 고객 서버 SSH·폰트별 물리 단말·LazyOra/LazyBeaver 앱 통합은 별도입니다. 기존 0.1.0 태그/자산과 main/dev 원격 브랜치는 변경하지 않았습니다. 에픽은 열린 상태를 유지합니다.
