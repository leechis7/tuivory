# 변경 이력

**한국어 (기본)** · [English](CHANGELOG.en.md)

## 미배포

- Go·Rust 및 후속 언어에 정적 배포·호스트 정적 링크 원칙 적용. Rust musl/번들 LLD, Go CGO 비활성화·ELF 검사, 명시적 x86_64 빌드와 CentOS 7.4 커널 실행·외부 앱 검증을 추가합니다. 기존 v0.1.0 태그·자산은 변경하지 않습니다. [지원 범위](docs/static-build.md)

## 0.1.0 — 2026-10-27

- TVR-7 나머지 공통 UI 구현: 활성/포커스 분리·넘침·변경/닫기 탭, 패널 여백/포커스/ASCII, 열·행 분할과 키보드/드래그·좁은 화면 복원, 현재 경로 생략·이동 요청, 의미별 상태/단축키 우선순위·생략. Go/Rust 공개 API·외부 사용 검사·한영 통합 예제·8장 참조 이미지·PTY 입력 검사·문서를 함께 추가하고 v0.1.0으로 배포합니다.


- TVR-7 지원 범위 점검과 공통 Tree 추가: Go/tview·Rust/Ratatui의 안정 ID·펼침·선택·스크롤·노드 메타데이터·키보드/마우스·ASCII, 같은 탐색 계약·외부 import 검사·한영 예제와 이미지. 이번 Tree 변경은 v0.1.0에 포함하며 탭·패널·상태·경로는 아래 후속 구현에 포함했습니다.

- Rust 코어 crate 추가: 공통 후보 토큰·프로필·색상/스타일 값·엄격한 JSON 검증·내장 배포 데이터·외부 프로젝트 사용 검사. 선택적 Ratatui 0.30.2 어댑터와 Crossterm 0.29 한·영 대화형 예제, Linux ARM64 빌드, 언어별 참조 이미지와 PTY 검사를 추가했습니다. 코어는 Rust 1.85 이상, 어댑터·예제는 1.88 이상입니다. Rust Git 태그 `rust/v0.1.0`으로 배포하며 crates.io 배포는 없습니다.

- 견본 빌드 결과를 `bin/<언어>/`로 구분합니다. 기본 Go 출력 경로는 `bin/go/tuivory-linux-arm64`로 변경했으며 Linux ARM64 한 개를 만드는 정책은 유지합니다.
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
