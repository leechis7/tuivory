# Tuivory 0.11.0 릴리스

**한국어 (기본)** · [English](release-0.11.0.en.md)

Go·Rust 공통 그리드의 편집과 데이터 작업을 확장한 기능 릴리스입니다. 0.10.2의 Windows 파사드 수정과 반 줄 팝업 그림자·대비·두 칸 문자 보호도 모두 포함합니다. **0.10.1 사용 금지** 정책은 유지합니다. [회수 안내](withdrawn-versions.md).

## 그리드 개선

- 앱 승인형 셀 내 편집: Enter·더블클릭·선택적 타이핑 시작, NULL, 커서/마우스·클리핑, 승인 대기·거절/재시도·취소와 오래된 응답 차단.
- 변경 셀과 행 표식 분리: 선택·오류·비활성에서도 변경 셀의 `*`를 유지하고 행 번호 집계 표식은 독립 설정.
- 열 좌우 고정·숨김·순서 변경, 머리글 드래그·키보드 조작과 좁은 화면 처리.
- Tab/Shift+Tab 제출 승인 후 편집 가능한 다음/이전 셀 이동.
- 인용 TSV 범위 붙여넣기 요청: 원자적 사전 검사, 명시적 NULL, 안정 ID와 승인 직전 권한 재검사.
- 로드된 데이터 찾기·일치 강조·다음/이전 이동 및 앱 전체 검색 요청.
- 열·선택·정렬·위치의 보기 상태 저장/복원(Go JSON/Rust serde), 선택적 원문 상세 뷰어.

[API·옵션·단축키·화면](grid-workspace.md) · [그리드 기본](grid.md) · [변경 이력](../CHANGELOG.md).

## 호환성과 앱 책임

셀 내 편집 UI는 기본 끄기이며 기존 `activate → edit` 이벤트를 유지합니다. 상세 보기 역시 기본 요청만 반환하고 `SetDetailsEnabled`로 기본 UI를 켭니다. **행 `State.Edited`는 행 표식만 제어합니다.** 셀 변경색은 `GridCellInfo.State.Edited`로 공급하세요. 행 전체 색 상속에 의존한 앱은 이 설정을 조정해야 합니다.

Go 호환 Application의 붙여넣기는 `EnablePaste(true)`와 `PasteSafeScreen`을 연결해야 LF/CRLF가 보존됩니다. 일반 Ctrl+J는 바꾸지 않습니다. DB 검증·SQL·트랜잭션·클립보드·파일 저장·전역 키는 앱 책임입니다. 새 필수 네이티브 의존성은 없습니다.

## 설치·예제와 검증

```sh
go get github.com/leechis7/tuivory/go@v0.11.0
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.11.0", features = ["ratatui"] }
```

Go 1.24+, Rust 코어 1.85+, UI/예제 1.88+. Rust는 Git/.crate 배포이며 crates.io 게시가 아닙니다. Linux ARM64/x86_64 정적 예제는 각 아키텍처의 네이티브 호스트에서 언어별 실행파일 하나로 빌드합니다. `--demo catalog --mode grid --grid-sample --grid-preset data`로 실행하세요.

배포 전 로컬 검증: Go race/vet·Rust 전체 기능 테스트/doctest/fmt/clippy, 독립 모듈·crate 외부 사용, 공유 TSV 14개, 언어별 1,536개 상태 조합의 실제 출력, 한영·테마/색상/문자 모드의 96개 그리드 PTY와 기존 통합 예제 62개를 통과했습니다. 한영 API·디자인·예제·참조 화면 28장을 갱신했습니다. [배포 전 기록](evidence/tvr7-grid-workspace-results.json)은 당시 미게시 상태를 보존합니다.

최종 소스·원격 CI·공개 태그 설치·다운로드 실행·체크섬 결과는 [릴리스](https://github.com/leechis7/tuivory/releases/tag/go/v0.11.0)의 RELEASE-MANIFEST.json/SHA256SUMS에 기록합니다. CentOS·실제 LazyOra DB 연결 검증은 수행하지 않습니다.
