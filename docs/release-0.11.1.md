# Tuivory 0.11.1 릴리스

**한국어 (기본)** · [English](release-0.11.1.en.md)

그리드 셀 편집의 `|` 문자 표시를 실제 터미널 커서로 대체한 패치 릴리스입니다. [0.11.0의 그리드 기능](release-0.11.0.md)과 이전 수정도 모두 포함합니다. **0.10.1 사용 금지** 정책은 유지합니다. [회수 안내](withdrawn-versions.md).

## 변경과 적용 방법

- Go `NewGridView`가 실제 커서 위치·가시성을 관리합니다. `NewCursorScreen`을 생성해 Application에 연결하면 backend의 커서 모양·깜빡임 강제 명령을 걸러 터미널 사용자 설정을 보존합니다. 기존 `NewScreen`과 Application 자동 생성 화면은 기존 동작을 유지합니다.
- Rust는 `GridWidget::render_frame(frame, area)`로 그리기와 실제 커서 등록을 함께 합니다. 기존 버퍼 전용 `Widget` 그리기도 유지하며 그 방식은 터미널 커서를 등록하지 않습니다.
- 한글·CJK·이모지·결합 문자, 긴 값, 마우스 위치, 변경 표식과 여백이 같은 셀 뷰포트를 사용합니다. 입력 값의 `|`는 일반 데이터로 유지합니다.
- 포커스 해제·NULL·승인 대기·클리핑·편집 종료 시 커서를 숨기고 거절 후 재시도 시 복원합니다. 앱은 전역 포커스와 레이어 순서를 결정합니다.

[Go/Rust 연결 코드와 API](grid-workspace.md) · [디자인 가이드](design-guide.md) · [예제](examples.md).

## 설치·예제

```sh
go get github.com/leechis7/tuivory/go@v0.11.1
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.11.1", features = ["ratatui"] }
```

Go 1.24+, Rust 코어 1.85+, UI/예제 1.88+. Rust는 Git/.crate 배포이며 crates.io 게시가 아닙니다. Linux ARM64/x86_64 정적 예제는 각 네이티브 호스트에서 언어별 하나로 빌드합니다. `--demo catalog --mode grid --grid-sample --grid-edit-preview`로 편집을 미리 볼 수 있습니다.

## 검증과 범위

로컬 Go race/vet, Rust 코어·전체 기능 테스트/doctest/fmt/clippy, 외부 모듈·crate 사용, 6개 OS/아키텍처 Go 컴파일, 공유 커서 사례 11개, 언어별 24개 실제 버퍼 커서 조합, 실제 커서·표시 명령을 확인하는 PTY 96개와 통합 예제 62개를 통과했습니다. [배포 전 기록](evidence/tvr7-grid-cursor-results.json)은 당시 미커밋·미게시 상태를 보존합니다.

실제 SecureCRT 및 Windows/macOS 물리 콘솔의 깜빡임 동작은 로컬에서 검증하지 않았습니다. 커서 모양·깜빡임 강제 명령 부재와 좌표·가시성을 검사했습니다. 폼·찾기 입력의 기존 표시는 이번 수정 범위가 아닙니다. SVG는 실제 깜빡임이나 커서 메타데이터를 표현하지 않습니다. CentOS 검증은 수행하지 않습니다.

최종 소스·원격 CI·공개 태그 설치·다운로드 실행·체크섬 결과는 [릴리스](https://github.com/leechis7/tuivory/releases/tag/go/v0.11.1)의 RELEASE-MANIFEST.json/SHA256SUMS에 기록합니다.
