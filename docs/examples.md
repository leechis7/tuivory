# 통합 예제 실행파일

**한국어 (기본)** · [English](examples.en.md)

**0.10.2 TVR-29:** [팝업 그림자](popup-shadows.md)를 오른쪽 1칸·아래 반 줄로 통일하고 다크 대비를 개선했습니다. 0.10.2에서 제공합니다.

**0.9.1 TVR-27 변경:** Go·Rust 예제를 언어별 실행파일 하나로 통합합니다. 0.9.1 배포 압축파일부터 이 구성을 사용합니다.

```sh
make build                 # Go 하나
make build-rust            # Rust 하나
```

빌드는 Linux 서버의 CPU 아키텍처를 자동 감지합니다. ARM64 서버에서는 `bin/go/tuivory-linux-arm64`, `bin/rust/tuivory-linux-arm64`만 만듭니다. x86_64 서버에서는 같은 위치에 `tuivory-linux-x86_64`를 만듭니다. 다른 아키텍처를 교차 빌드하지 않으며, 새 실행파일의 정적 ELF 검사가 통과하면 해당 언어의 기존 예제·다른 아키텍처 바이너리를 정리합니다. 과거 릴리스 압축파일과 검증 이력은 보존합니다.

Go 1.24+, Rust 예제 1.88+, Python 3이 필요합니다. Rust는 **현재 호스트에 맞는** musl 표준 라이브러리와 rustup의 번들 rust-lld를 사용합니다. ARM64는 `rustup target add aarch64-unknown-linux-musl`, x86_64는 `rustup target add x86_64-unknown-linux-musl`을 한 번 실행합니다.

현재 ARM64 서버의 실행 예:

```sh
./bin/go/tuivory-linux-arm64 --list
./bin/go/tuivory-linux-arm64 --demo tree --lang ko
./bin/rust/tuivory-linux-arm64 --demo syntax --lang en
./bin/rust/tuivory-linux-arm64 --demo catalog --mode grid --grid-preset data
./bin/go/tuivory-linux-arm64 --demo menu --ascii --shadow auto
./bin/go/tuivory-linux-arm64 --demo controls --help
```

| `--demo` | 화면 |
| --- | --- |
| `playground` | 기존 테마·위젯 견본, 기본값 |
| `tree` | 트리 탐색 |
| `workspace` | 탭·패널·분할·상태 표시줄 |
| `focus` | 상태·포커스·중첩 팝업 |
| `catalog` | 폼·목록·그리드·알림·배치 (`--mode`로 선택) |
| `menu` | 메뉴·문맥 메뉴·그림자 |
| `controls` | 입력·버튼·Surface·편집기·컨테이너 |
| `syntax` | Oracle SQL/PLSQL 강조·편집 |

`--lang ko|en`으로 화면 언어를 정합니다. `--demo`가 없으면 기존 playground를 실행합니다. 예제별 옵션은 `--demo 이름 --help`로 확인합니다. 각 예제는 같은 실행파일에 포함되며 다른 예제 실행파일이나 소스·언어 런타임을 실행 시 요구하지 않습니다. DB·실제 클립보드 연결은 하지 않습니다.

소스별 `make run-tree-go`, `make run-syntax-rust` 같은 실행 명령도 유지합니다. `make run ARGS="--demo tree --lang ko"`, `make run-rust ARGS="--demo syntax --lang en"`은 통합 진입점을 소스로 실행합니다. Python·JavaScript·Shell 참조 예제는 기존처럼 소스로 실행합니다.

정적 ELF 검사와 한영 통합 실행 검증:

```sh
python3 tools/check_showcase.py bin/go/tuivory-linux-arm64 bin/rust/tuivory-linux-arm64
python3 tools/snapshot_tree.py bin/rust/tuivory-linux-arm64 --demo tree --output .cache/validation/tree-images
```

[예제 소스](examples.md) · [정적 배포](static-build.md) · [로컬 검증 기록](evidence/showcase-results.json). 언어별 24개 한영 PTY 시나리오와 정적 ELF 검사, 20개 참조 화면 일치를 확인했습니다. 원격 CI·게시·x86_64 실행·CentOS 검증은 수행하지 않았습니다.

Go를 예제 기준으로 사용합니다. 기본 playground의 탐색·테마/색상 선택·암호·비활성 버튼과 조작 순서를 Rust에도 제공합니다. 트리 제목/버튼 정렬과 SQL 편집기의 여백·마우스 좌표도 Go 기준으로 맞춥니다. `--lang=en`, `--theme=light`, `--colors=16` 같은 값 지정 옵션은 두 통합 실행파일에서 사용할 수 있습니다. 터미널 백엔드와 자동 색상 감지는 언어별 구현을 사용하며 실제 단말 출력은 달라질 수 있습니다. [Rust 화면·조작](rust-playground.md).

## 예제 소스·컴포넌트 안내

컴포넌트의 표시·내부 조작은 라이브러리, 실제 화면 조합·전역 키·영역 간 포커스·업무 연결은 앱 책임입니다. 예제는 필수 화면 템플릿이 아닙니다. [컴포넌트와 앱의 책임](component-boundary.md).

실제 코드는 각 언어 디렉터리 안에서 관리합니다. 이 안내는 언어별 예제와 공통 정적 배치를 연결합니다.

| 언어 | 예제 | 제공 범위 |
| --- | --- | --- |
| Go | [시작 템플릿](../go/examples/starter/main.go), [토큰 읽기](../go/examples/tokens/main.go) | 동작하는 Go 스타일 API·실행형 견본 |
| Rust | [토큰 읽기](../rust/examples/tokens.rs), [대화형 견본](rust-playground.md) | JSON 검증·색상/스타일 코어·Ratatui 어댑터·한영 실행 예제 |
| Python | [토큰 읽기](../python/examples/read_tokens.py) | 데이터 읽기 예제. UI 패키지 미구현 |
| JavaScript | [토큰 읽기](../javascript/examples/read-tokens.mjs) | 데이터 읽기 예제. UI 패키지 미구현 |
| Shell | [ANSI 견본](../shell/examples/terminal-colors.sh) | 참조 출력. 스타일 함수 패키지 미구현 |

[공통 컴포넌트 정적 배치](examples-components.txt)는 언어와 무관한 참고 예시입니다.

시작 템플릿과 정적 배치 예시의 라벨은 한국어이며, 현재 [견본](playground.md)은 `--lang en`으로 영어 UI를 제공합니다.

## 공통 Tree 예제

[Go 소스](../go/examples/tree/main.go) · [Rust 소스](../rust/examples/tree/main.rs) · [한영 사용법](tree.md). 루트의 `make run-tree-go ARGS="--lang ko"`, `make run-tree-rust ARGS="--lang en"`으로 실행합니다. DB 없는 동일 데이터·조작 예제이며 통합 실행파일의 `--demo tree`에 포함합니다.

## 공통 워크스페이스 컴포넌트

[탭·패널·분할선·상태 표시줄·경로 사용법](workspace.md)에서 Go/Rust 공개 API와 같은 조작·색상·상태 원칙을 설명합니다. DB 없는 한영 통합 예제는 루트에서 `make run-workspace-go ARGS="--lang ko"`, `make run-workspace-rust ARGS="--lang en"`으로 실행합니다. Go `go/v0.1.0`과 Rust `rust/v0.1.0`에 포함합니다. CI 결과와 실제 앱 적용은 [작업 기록](https://leechis7.atlassian.net/browse/TVR-7)에서 구분합니다.

## 상태·포커스·중첩 팝업 예제

[Go 소스](../go/examples/focus/main.go) · [Rust 소스](../rust/examples/focus/main.rs) · [사용법](focus.md). `make run-focus-go ARGS="--lang ko"`, `make run-focus-rust ARGS="--lang en"`으로 실행합니다. 읽기 전용·처리 중·비활성 탐색, 중첩 팝업·입력 차단·포커스 복귀·한영 표시를 검증하는 호스트입니다. 통합 실행파일의 `--demo focus`에 포함합니다.

[TVR-9: 입력·폼](forms.md): `Form / FormField / FormWidget`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-10: 목록·메뉴·검색 선택](collections.md): `ListModel / SearchPicker / ListWidget / SearchPickerWidget`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-11: 표·데이터 그리드](grid.md): `Grid / GridSource / GridWidget`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-12: 알림·진행·데이터 상태](feedback.md): `NoticeQueue / Progress / DataState`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-13: 배치·밀도·부가 컴포넌트](layout.md): `SpacingTokens / StackLayout / Badge / Chip / Help`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

Go 팝업·외부 카드의 적용 코드는 [오버레이 그리기](overlay-drawing.md)를 참고합니다. 기존 견본의 팝업·Choice와 focus 예제의 PanelView에 공통 보정이 적용됩니다.

[TVR-17 그리드 비교](grid.md): `make run-catalog-go ARGS="--mode grid --grid-sample --grid-preset data --lang ko"`. Rust는 `run-catalog-rust`, 간결 구성은 `--grid-preset simple`을 사용합니다. 같은 5행 데이터와 2번 행 이름 선택입니다. TVR-17은 공개 배포에 포함됩니다.

[호스트 구성 예제](component-boundary.md): 기존 workspace에 `--layout rows --focus-order content,tree,tabs --quit-key ctrl-x`를 주어 앱이 선택하는 배치·포커스·전역 키를 확인합니다. 기본 화면과 새 구성은 같은 Go/Rust 공개 컴포넌트를 사용하며 호스트 옵션은 공개 배포에 포함됩니다.

[공통 메뉴](menus.md): Go/Rust 계층·메뉴 바·뒤로가기·단축키/비활성·팝업·호출 문맥 요청과 DB 없는 한영 실행 예제. 0.5.0부터 공개 배포에 포함됩니다.

[컨트롤·Surface·편집기·배치](controls.md): 0.6.0부터 제공하는 Go·Rust controls 예제입니다.

0.7.0 TVR-26의 Go·Rust 공개 예제는 backend 직접 import 없이 Tuivory SDK 경로를 사용합니다. 실행 명령과 화면은 유지합니다. [새 API·전환·배포 상태](ui-facade.md).

0.9.1 TVR-28 폴더 정리: 검증 로그·참조 화면 생성물은 `.cache/validation/`, 로컬 릴리스 보관은 `.cache/releases/`를 사용합니다. [저장소 구조](architecture.md).

0.10.0 TVR-18: [Go/Rust 탭·트리 드래그 앤 드롭](drag-drop.md)은 기본 끄기이며 앱 승인 후 불변 모델 적용, 영역 밖 캡처·취소·키보드 대안을 제공합니다. 0.10.0부터 제공합니다.

## 0.11.0 그리드 데이터 작업

기존 통합 실행파일에서 `--demo catalog --mode grid --grid-sample --grid-preset data`로 실행합니다. `--grid-edit-preview`는 편집 중 화면으로 시작합니다. 합성 데이터의 앱 승인·거절/재시도·NULL·붙여넣기·찾기·열 관리·메모리 보기 복원·원문 상세를 한 예제에 모으며 실행파일을 추가하지 않습니다. [키와 화면](grid-workspace.md).

TVR-7 0.11.1: [실제 그리드 커서·backend 연결](grid-workspace.md). 0.11.1에서 실제 커서를 사용하려면 Go NewCursorScreen/NewGridView, Rust GridWidget::render_frame을 사용합니다.

[Python·TypeScript/JavaScript·C·C++·Java 독립 지원](languages.md): 미배포 패키지·Tree 검증 작업입니다. 구현과 런타임은 언어별로 독립적이며 기존 공개 0.11.1은 유지합니다.
