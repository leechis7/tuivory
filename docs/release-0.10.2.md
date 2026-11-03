# Tuivory 0.10.2 릴리스

**한국어 (기본)** · [English](release-0.10.2.en.md)

**0.10.1 사용 금지.** [회수·업그레이드 안내](withdrawn-versions.md)를 확인하세요. 0.10.2는 Windows에서 Tuivory 루트 import가 컴파일되지 않던 Go 파사드 결함을 수정합니다. 생성기가 backend의 빌드 조건·파일명 OS/아키텍처·서로 보완하는 구현을 반영하고 루트와 terminal 양쪽에서 조건부 API를 분리합니다. 공개 함수 이름과 기존 Unix 동작을 유지하며 Windows에는 backend와 동일하게 NewStdIoTty를 선언하지 않습니다.

```sh
go get github.com/leechis7/tuivory/go@v0.10.2
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.2", features = ["ratatui"] }
```

Windows AMD64·ARM64와 Linux/macOS AMD64·ARM64 단일 import 소비자를 검사합니다. 네이티브 Windows/macOS/Linux 생성·시뮬레이션 CI를 추가했으며 컴파일/시뮬레이션 검증은 물리 콘솔·폰트 검증과 구분합니다. [API 가용성](ui-facade.md) · [배포 전 로컬 이력](evidence/tvr26-windows-facade-results.json).

Go 1.24+, Rust 코어 1.85+, UI 1.88+입니다. Rust 구현 변경은 없고 제품 버전만 맞췄습니다. Linux 실행 예제는 ARM64/x86_64에서 각 실제 호스트로 빌드한 언어별 정적 실행파일 하나씩입니다. Windows/macOS 검사는 SDK 소비자 검증이며 새 배포 실행파일을 추가하지 않습니다.

[자산](https://github.com/leechis7/tuivory/releases/tag/go/v0.10.2)의 RELEASE-MANIFEST.json·SHA256SUMS는 최종 소스·main CI·Windows/macOS/Linux 검증·공개 태그 설치·회수 선언·다운로드 실행 근거를 제공합니다. CentOS와 실제 LazyOra 업무 연결은 검증하지 않습니다.
