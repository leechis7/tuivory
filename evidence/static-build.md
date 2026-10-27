# 정적 배포 검증

**한국어 (기본)** · [English](static-build.en.md)

2026-10-28, TVR-5·TVR-6. `codex/TVR-5-centos74-musl`의 로컬 변경을 검증했습니다. 새 커밋·원격 게시·GitHub CI 실행 결과가 아닙니다. [재현 명령과 배포 정책](../docs/static-build.md)

| 항목 | 환경·결과 |
| --- | --- |
| CentOS 사용자 공간 | 공식 7.4.1708 AMD64 이미지, glibc `2.17-196.el7.x86_64` |
| 실제 게스트 커널 | 공식 CentOS `3.10.0-693.el7.x86_64`, QEMU TCG로 부팅 |
| Go x86_64 | CGO 비활성화, playground·Tree·workspace 한영 UI 시작·Ctrl+Q 종료·대체 화면 복원 통과 |
| Rust x86_64 | Rust 1.88.0 musl/static PIE, 같은 세 예제의 한영 UI·종료·복원 통과 |
| 외부 Go 앱 | 독립 go/ 모듈, 공통 디자인 디렉터리 없이 정적 빌드·게스트 API·렌더링 검사 통과 |
| 외부 Rust 앱 | 패키징된 crate+Ratatui, 공통 디자인 디렉터리 없이 정적 빌드·게스트 API·렌더링 검사 통과 |
| 기본 ARM64 | Go·Rust 정적 ELF 검사와 현재 Linux ARM64 호스트에서 한영 PTY 시작·종료·복원 통과 |
| 동적 의존성 거부 | ELF 아키텍처·로더·DT_NEEDED 검사, static PIE 허용·동적 의존성 거부 회귀 검사 통과 |
| 원격 CI·게시 | 로컬 검증 이후의 CI·PR·병합 결과는 TVR-5·TVR-6 댓글에서 추적. 기존 v0.1.0 태그·자산은 유지 |

Linux ARM64 호스트에서 QEMU 10.2.1로 x86_64 커널을 에뮬레이션했습니다. VM 네트워크와 KVM은 사용하지 않았습니다. Docker는 고정 이미지의 파일 추출에만 사용했습니다. 테스트 로그와 JSON 해시 목록은 실행 시 `--output` 경로에 생성합니다. 이 실행에서는 `/tmp/tuivory-centos74.log`, `/tmp/tuivory-centos74.json`을 사용했습니다. 임시 파일은 배포 자산이 아닙니다.

이미지 다이제스트: `sha256:78b63c089c40a2ca0d85db9125fb3193c6ff74814bba5f894c803e5ae02a4035`. 커널 SHA256: `8ede7f8d3c8f5e72f1a84713ad59b7b39211ea1af8887389cb50a189df937c6f`.

실제 대상 서버·SSH·폰트·사용자 터미널·LazyOra/LazyBeaver 통합은 미검증입니다. ARM64 결과는 CentOS 7.4 ARM64 검증이 아닙니다. 기존 v0.1.0의 Rust GNU ARM64 자산은 glibc 2.39 의존성이 있으므로 새 정적 산출물과 구분합니다. 화면 구성은 바뀌지 않아 기존 한영 UI 이미지를 유지합니다.

최종 통과 산출물 해시는 [JSON 기록](static-build-results.json)에 보존했습니다. Go race/vet, Python 7개 검사, Rust 전체 기능 테스트·rustdoc·fmt·clippy와 공통 토큰·문서 링크 검사도 통과했습니다. 문서 검사는 빌드로 생성한 target/bin 디렉터리를 제외합니다.
