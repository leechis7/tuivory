# 변경 이력

**한국어 (기본)** · [English](CHANGELOG.en.md)

## 미배포

- 한국어 기본 문서를 유지하며 영어 README·Go 사용법·기여 안내와 언어 전환 링크를 추가했습니다.
- 견본 UI에 `--lang ko|en`을 추가했습니다. 하나의 바이너리에서 기본 한국어와 선택 영어 UI를 제공하며, 영어 문서에는 영어 UI 참조 이미지를 사용합니다.

- 위 변경은 [PR #1](https://github.com/leechis7/tuivory/pull/1)로 `main`·`dev`에 병합했으며 새 버전 태그는 아직 없습니다.
- 후속 문서 작업은 현재 사용법·게시 상태를 현행화하고 영어판과 문서 색인을 추가하며 원출처는 고지에 보존합니다.

## 0.0.1 — 2026-10-24

- Tuivory(TUI + ivory)의 첫 배포. 언어 중립 저장소 구조와 Go 스타일 패키지를 제공합니다.
- 공통 테마·색상 프로필·상태 규칙과 JSON·CSV·스키마는 `design/`에서 관리합니다.
- Go 모듈 `github.com/leechis7/tuivory/go`는 `tuivory` 하나의 공개 패키지로 스타일 API와 tview 적용 함수를 제공합니다.
- dark/light/blackwhite × 8/16/256/truecolor, DB 없는 대화형 견본 및 상태 보존 검사를 포함합니다.
- Python·JavaScript는 공통 토큰 읽기 예제, Shell은 ANSI 출력 예제를 제공합니다. 해당 언어의 UI 스타일 패키지는 후속 범위입니다.
- 배포는 이 저장소의 태그·Release를 기준으로 기록합니다. [설치·사용 안내](docs/installation.md)와 [출처 고지](NOTICE.md)를 참고하세요.
