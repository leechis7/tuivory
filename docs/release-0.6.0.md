# Tuivory 0.6.0 릴리스

**한국어 (기본)** · [English](release-0.6.0.en.md)

Go·Rust의 공통 Surface·입력·편집·배치 API를 추가합니다. [사용법·API 대응표·실행 화면](controls.md)과 [언어 중립 명세](../design/controls.md)를 제공합니다.

- **TVR-22:** 테두리 없는 불투명 Surface, `PanelView.SetBorder(false)` 수정, 두 칸 문자 경계 보호와 그림자 조합.
- **TVR-23:** 암호 마스킹·명시적 원문 조회, 독립 Input/Button/Check/Select, 선택·붙여넣기·복사 요청, 비활성·Busy 처리.
- **TVR-24:** 다중행 Editor/Buffer와 TextView, grapheme/UTF-8 위치·선택·Undo/Redo·읽기 전용·행 번호·스크롤·호스트 구문 span·명시적 마크업.
- **TVR-25:** Row/Column/Grid/Layer/Drawer, 크기 제약·가상 스크롤·클리핑·입력 전달·모달 격리와 포커스 복원.
- **TVR-21:** 문서 탐색 구조와 소스에서 생성하는 Go·Rust API 명세. Rust 포커스 패널의 제목 중복도 수정합니다.

```sh
go get github.com/leechis7/tuivory/go@v0.6.0
```

```toml
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.6.0", features = ["ratatui"] }
```

Go 1.24+, Rust 코어 1.85+, UI/예제 1.88+입니다. Go·Rust Linux ARM64/x86_64 정적 playground/catalog/menu/**controls** 실행파일, Rust crate, SHA256SUMS와 RELEASE-MANIFEST.json을 제공합니다. crates.io에는 게시하지 않습니다. 실제 빌드·태그·CI 검증 결과는 [GitHub Release](https://github.com/leechis7/tuivory/releases/tag/go/v0.6.0)의 manifest에서 확인하세요. [구현 당시 로컬 검증](../evidence/controls-results.json)은 배포 검증과 구분합니다.

새 예제는 `make run-controls-go` / `make run-controls-rust`, 영어는 `ARGS="--lang en"`입니다. TVR-26 전체 backend 파사드는 포함하지 않으며 현재 언어별 렌더러 타입은 공개 API에 남습니다. Python·JS/TS·C·C++ 구현은 이번 릴리스에 포함하지 않습니다. Text Layout은 원문 전체를 순회하며 1만 줄 회귀 검사를 제공합니다. CentOS 검증은 수행하지 않았고 TVR-7 에픽은 열어둡니다.
