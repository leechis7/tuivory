# 정적 배포와 CentOS 7.4

**한국어 (기본)** · [English](static-build.en.md)

현재 공개 릴리스는 **0.10.1**입니다. [자산과 검증](release-0.10.1.md). 아래 0.2.0/CentOS 내용은 과거 이력입니다.

2026-10-29 사용자 지시에 따라 앞으로 CentOS 검증을 수행하지 않습니다. CI의 CentOS VM 단계도 제거합니다. 정적 배포 조건·ELF 검사·사용 가능한 환경의 실행 검증은 유지합니다. 아래 CentOS 명령과 기존 결과는 과거 검증의 재현 이력이며 현재 필수 절차가 아닙니다.

정적 실행파일은 **0.2.0**에 포함합니다. 기존 0.1.0 자산은 유지합니다. [자산·설치·검증](release-0.2.0.md).

Go·Rust와 별도 예외가 없는 후속 언어의 배포 실행파일은 동적 로더·공유 라이브러리·별도 설치 언어 런타임 없이 실행해야 합니다. 이 정적 배포 대상 패키지도 적용 앱의 정적 링크를 막는 필수 네이티브 의존성을 추가하지 않습니다. 빌드 시 내려받는 Go 모듈·Rust crate는 허용하며 실행 시 외부 데이터 파일을 요구하지 않도록 공통 토큰을 내장합니다. OS 커널과 터미널은 실행 환경입니다.

Python·TypeScript·JavaScript 지원은 사용자 지정 예외입니다. 일반 Python/npm 패키지와 소스 예제는 해당 언어 런타임을 사용하며 정적 배포·독립 실행파일·ELF 정적 검사·CentOS 검증을 요구하지 않습니다. 지원 런타임·버전·의존성을 문서화하고 깨끗한 외부 환경의 설치·import·실행을 검증합니다. [Python TVR-15](https://leechis7.atlassian.net/browse/TVR-15) · [TypeScript·JavaScript TVR-16](https://leechis7.atlassian.net/browse/TVR-16).

Shell은 현재 인터프리터 기반 참조 예제입니다. 향후 독립 실행파일을 배포하는 경우에는 기본 정적 배포 조건을 따릅니다. 아래 빌드·ELF·CentOS 명령은 Go·Rust 정적 배포용입니다.

## 빌드

0.9.1 TVR-27 변경부터 현재 Linux 호스트 아키텍처만 대상으로 언어별 통합 실행파일 하나를 만듭니다. [통합 예제·아키텍처 감지·실행 옵션](examples.md)을 참고하세요. Go 1.24+, Rust 예제 1.88+, Python 3이 필요합니다.

```sh
make build                    # bin/go/tuivory-linux-<호스트 아키텍처>
make build-rust               # bin/rust/tuivory-linux-<호스트 아키텍처>
```

Rust는 호스트에 맞는 musl 표준 라이브러리와 rustup의 번들 `rust-lld`를 사용합니다. ARM64에서는 `rustup target add aarch64-unknown-linux-musl`, x86_64에서는 `rustup target add x86_64-unknown-linux-musl`이 필요합니다. 별도 GNU 링커나 대상 glibc는 필요하지 않습니다. 이 도구는 개발 환경에만 필요합니다.

빌드는 ELF 아키텍처를 검사하고 `PT_INTERP`와 `DT_NEEDED`를 거부합니다. Rust static PIE의 자체 재배치용 `PT_DYNAMIC`은 허용합니다. 파일 접근까지 ELF가 보장하지는 않으므로 실행 검사도 수행합니다. 적용 앱이 추가한 의존성은 최종 앱에서도 검사해야 합니다.

```sh
# 현재 ARM64 서버
python3 tools/check_static_elf.py --arch arm64 bin/go/tuivory-linux-arm64 bin/rust/tuivory-linux-arm64
python3 tools/check_showcase.py bin/go/tuivory-linux-arm64 bin/rust/tuivory-linux-arm64
```

기존 0.9.0 자산은 보존합니다. 0.10.0부터 언어·아키텍처별 압축파일 안에 통합 실행파일 하나를 제공합니다. 한 서버에서 다른 아키텍처를 교차 빌드하지 않습니다.

## 과거 CentOS 커널 검증 (현재 수행하지 않음)

Docker는 고정된 공식 CentOS 7.4.1708 AMD64 이미지에서 루트 파일시스템을 추출하는 데 사용합니다. QEMU는 CentOS 7.4의 실제 `3.10.0-693.el7.x86_64` 커널을 부팅합니다. 최신 호스트 커널을 공유하는 컨테이너 실행만으로 호환성을 판정하지 않습니다. 게스트 glibc는 `2.17-196.el7`입니다. VM은 네트워크·KVM·호스트 binfmt 등록 없이 실행합니다.

Docker, `qemu-system-x86_64`와 BIOS 파일이 필요합니다. 커널은 [CentOS 공식 보관소](https://vault.centos.org/7.4.1708/os/x86_64/isolinux/vmlinuz)에서 받으며 스크립트가 SHA256을 검사합니다. 이미지 다이제스트와 커널 해시는 `tools/check_centos74.py`에 고정되어 있습니다.

```sh
curl --fail --location https://vault.centos.org/7.4.1708/os/x86_64/isolinux/vmlinuz -o /tmp/tuivory-centos74-vmlinuz
python3 tools/check_centos74.py --kernel /tmp/tuivory-centos74-vmlinuz \
  --binary go=bin/go/tuivory-linux-x86_64 \
  --binary rust=bin/rust/tuivory-linux-x86_64 \
  --consumer go-host=/tmp/tuivory-go-consumer \
  --consumer rust-host=/tmp/tuivory-rust-consumer
```

검사는 한영 UI 시작·Ctrl+Q 종료·대체 화면 복원과 외부 앱의 API·렌더링을 확인합니다. `--binary`로 Tree·워크스페이스 예제도 추가합니다. 실제 서버·SSH·사용자 터미널·LazyOra/LazyBeaver 통합 검증과는 구분합니다. ARM64 정적 산출물은 별도로 검사하며 이 x86_64 결과를 ARM64 CentOS 검증으로 확대하지 않습니다. 결과는 [검증 기록](evidence/static-build.md)에 남깁니다.

## 과거 0.2.0 게시 이력

이 정적 빌드는 v0.2.0 태그 릴리스에 포함합니다. 기존 `v0.1.0` 릴리스의 Rust ARM64 바이너리는 GNU/glibc 2.39 의존성이 있으므로 이번 정적 산출물과 다릅니다. 기존 태그·릴리스 자산은 변경하지 않았습니다. Go의 기존 ARM64 자산은 이미 정적이지만 CentOS 7.4 x86_64용 자산은 아닙니다. 새 커밋·게시와 원격 CI 결과는 별도로 기록합니다.
