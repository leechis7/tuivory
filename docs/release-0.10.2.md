# Tuivory 0.10.2 릴리스

**한국어 (기본)** · [English](release-0.10.2.en.md)

**0.10.1 사용 금지.** [회수·업그레이드 안내](withdrawn-versions.md)를 확인하세요. 0.10.2는 Windows에서 Tuivory 루트 import가 컴파일되지 않던 Go 파사드 결함을 수정합니다. 생성기가 backend의 빌드 조건·파일명 OS/아키텍처·서로 보완하는 구현을 반영하고 루트와 terminal 양쪽에서 조건부 API를 분리합니다. 공개 함수 이름과 기존 Unix 동작을 유지하며 Windows에는 backend와 동일하게 NewStdIoTty를 선언하지 않습니다.

## 0.10.1의 개선도 모두 포함

**0.10.2는 0.10.1을 대체하는 누적 릴리스입니다.** 0.10.1의 사용 금지는 해당 버전에 적용되며, 아래 기능을 제거하거나 되돌린 것이 아닙니다.

- **Go·Rust 반 줄 팝업 그림자:** auto/solid를 오른쪽 1칸·아래 반 줄로 통일하고 테두리와 기본 끄기를 유지합니다.
- **테마별 대비:** 실제 뒤쪽 배경을 기준으로 다크·라이트 명암을 조절하며 검정 배경·8/16/256색 대체 표현과 ASCII 점을 제공합니다.
- **안전한 그리기·입력:** 한글·CJK·이모지 경계 복구, 원래 반 셀 배경색 보존, 카드에만 적용하는 입력 판정을 유지합니다.
- **한영 예제·문서·참조 화면:** 정돈된 실제 위젯 예제와 SVG 셀 틈 보정을 포함합니다. Dim은 기존 셀 전체 호환 모드로 유지합니다.

[그림자 API·예제](popup-shadows.md) · [누적 변경 이력](../CHANGELOG.md). 이 내용에 Windows 파사드 수정과 0.10.1 회수 처리를 더한 버전이 0.10.2입니다. 아래의 “Rust 구현 변경 없음”은 **0.10.1 대비 추가 수정**에 관한 설명이며, 위 Rust 그림자 기능은 그대로 포함됩니다.

## 설치와 검증

```sh
go get github.com/leechis7/tuivory/go@v0.10.2
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.10.2", features = ["ratatui"] }
```

Windows AMD64·ARM64와 Linux/macOS AMD64·ARM64 단일 import 소비자를 검사합니다. 네이티브 Windows/macOS/Linux 생성·시뮬레이션 CI를 추가했으며 컴파일/시뮬레이션 검증은 물리 콘솔·폰트 검증과 구분합니다. [API 가용성](ui-facade.md) · [배포 전 로컬 이력](evidence/tvr26-windows-facade-results.json).

Go 1.24+, Rust 코어 1.85+, UI 1.88+입니다. Rust 구현 변경은 없고 제품 버전만 맞췄습니다. Linux 실행 예제는 ARM64/x86_64에서 각 실제 호스트로 빌드한 언어별 정적 실행파일 하나씩입니다. Windows/macOS 검사는 SDK 소비자 검증이며 새 배포 실행파일을 추가하지 않습니다.

[자산](https://github.com/leechis7/tuivory/releases/tag/go/v0.10.2)의 RELEASE-MANIFEST.json·SHA256SUMS는 최종 소스·main CI·Windows/macOS/Linux 검증·공개 태그 설치·회수 선언·다운로드 실행 근거를 제공합니다. CentOS와 실제 LazyOra 업무 연결은 검증하지 않습니다.
