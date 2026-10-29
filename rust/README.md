# Tuivory Rust 패키지

**한국어 (기본)** · [English](README.en.md)

컴포넌트의 표시·내부 조작은 라이브러리, 실제 화면 조합·전역 키·영역 간 포커스·업무 연결은 앱 책임입니다. 예제는 필수 화면 템플릿이 아닙니다. [컴포넌트와 앱의 책임](../docs/component-boundary.md).

crate 버전은 **0.4.0**이며 루트 `VERSION`과 일치합니다. `rust/v0.4.0` Git 태그로 사용합니다. [릴리스 안내](../docs/release-0.4.0.md).

공통 컴포넌트 모델·후보 토큰·스타일 코어, 선택적 Ratatui 렌더러와 DB 없는 대화형 예제를 제공합니다. 기본 코어는 Rust 1.85 이상(1.85.1 검증), Ratatui 0.30.2 어댑터와 Crossterm 0.29 예제는 Rust 1.88 이상(1.88.0 검증)입니다. 코어와 어댑터는 Go 코드·단말 I/O·DB에 의존하지 않습니다.

## 사용

버전 0.4.0은 `rust/v0.4.0` Git 태그로 배포하며 crates.io에는 게시하지 않습니다. 외부 프로젝트의 Cargo.toml에서 Git 의존성을 지정하거나 로컬 체크아웃의 rust/를 path 의존성으로 사용합니다.

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.4.0" }
# Ratatui 사용 시 features = ["ratatui"] 추가
```

```toml
[dependencies]
tuivory = { path = "/path/to/tuivory/rust" }
```

```rust
use tuivory::{Color, ColorProfile, Theme, TokenDocument};

fn main() -> Result<(), tuivory::Error> {
    let document = TokenDocument::candidate()?;
    let palette = document.palette(Theme::Dark, ColorProfile::Indexed256)?;
    let selection = palette.style("selection")?;
    assert!(matches!(selection.foreground, Color::Indexed(_)));
    Ok(())
}
```

## 현재 제공 범위

- `Theme`: dark/light/blackwhite. `ColorProfile`: 8/16/256/truecolor.
- `profile_for_colors(count, limited)`: 호스트가 전달한 색상 수로 프로필 선택. Go의 같은 함수와 동일한 경계 규칙이며 단말 감지는 하지 않습니다.
- `TokenDocument::candidate()`: crate 내부에 포함한 공통 JSON 읽기.
- `TokenDocument::from_json()`: 형식·역할·프로필·색상 범위·참조 RGB·굵기·필드와 중복 키 검사.
- `tokens()`: 독립된 원시 팔레트. `palette()`와 `style(role)`: ANSI 인덱스와 RGB를 구분한 전경·배경·굵기 값.
- 12팔레트·192쌍·16개 의미별 역할. 선택·버튼 포커스·비활성·변경·경고·오류 등의 역할 값을 사용할 수 있습니다. 없는 역할이나 팔레트는 오류를 반환하며 임의 대체하지 않습니다.

공통 후보 JSON은 Go의 실제 LazyOra 추출 스타일과 별도 데이터입니다. 이 crate의 값이 Go 위젯 스타일 전체와 같다는 의미는 아닙니다. 앱 데이터·포커스·선택·스크롤·이벤트는 호스트가 소유합니다. 공통 트리·탭 등 복합 컴포넌트 개선은 TVR-7에서 관리하며 실제 LazyBeaver 앱 적용은 아직 검증하지 않았습니다.

## Ratatui 연동

Rust 1.88 이상에서 선택적 기능을 켭니다. 기본 기능에는 프레임워크 의존성이 없습니다. `ratatui` 기능은 터미널 백엔드를 강제하지 않습니다.

```toml
[dependencies]
tuivory = { path = "/path/to/tuivory/rust", features = ["ratatui"] }
ratatui = { version = "0.30.2", default-features = false }
```

```rust
use tuivory::{ColorProfile, Theme};
use tuivory::ratatui::Styles;

fn main() -> Result<(), tuivory::Error> {
    let styles = Styles::new(Theme::Dark, ColorProfile::Indexed256)?;
    let selection = styles.role("selection")?;
    let panel = styles.block("Panel", true)?;
    Ok(())
}
```

`Styles::from_palette()`로 검증된 사용자 팔레트를 사용할 수 있습니다. `role()`은 Ratatui Style을 반환하고, `block(title, focused)`는 역할 색상과 포커스 시 이중 테두리를 적용합니다. 코어 Color/Style의 `Into` 변환은 ANSI 인덱스·RGB·굵기를 보존합니다. 테마 변경 시 호스트가 Styles만 교체하고 위젯 상태를 유지합니다.

기존 [playground](../docs/rust-playground.md)의 입력·목록·표·모달은 호스트 구현입니다. 별도로 0.2.0은 `forms`·`collections`·`grid`·`feedback`·`layout` 모델과 공개 Ratatui 위젯을 제공합니다. [카탈로그와 API](../docs/release-0.4.0.md)를 참고하세요.

## 예제와 검증

저장소 루트에서 실행합니다. 예제는 JSON만 출력하며 ANSI 제어 코드를 출력하거나 단말 설정을 바꾸지 않습니다.

```sh
cargo run --manifest-path rust/Cargo.toml --locked --example tokens -- dark 256
make test-rust
make check-rust
make check-rust-consumers
python3 tools/check_rust_module.py
```

어댑터·대화형 예제는 Rust 1.88 이상에서 별도 실행합니다.

```sh
make test-rust-ui check-rust-ui
python3 tools/check_rust_module.py --ratatui
make run-rust ARGS="--lang ko"
make build-rust
./bin/rust/tuivory-linux-arm64 --lang en
```

`rustup target add aarch64-unknown-linux-musl` 후 `make build-rust`로 Linux ARM64 정적 실행파일 하나를 만듭니다. rustup의 musl 표준 라이브러리와 번들 `rust-lld`를 사용합니다. x86_64 대상은 `rustup target add x86_64-unknown-linux-musl` 후 `make build-rust-x86_64`입니다. 패키지는 적용 앱의 정적 링크를 막는 필수 네이티브 의존성을 추가하지 않습니다. [정적 배포·CentOS 검증·기존 자산과의 차이](../docs/static-build.md) 기본 `make build`는 계속 Go 하나만 만듭니다. [한국어 화면·조작법](../docs/rust-playground.md)

`make check-rust-consumers`는 Go·Python·Node.js·Rust가 같은 공통 토큰을 읽는지 비교하므로 각 도구가 필요합니다. `make check-consumers`는 기존 Go·Python·Node.js 검사입니다. Rust fmt/clippy 컴포넌트는 `rustup component add rustfmt clippy`로 설치합니다.

독립 모듈 검사는 rust/만 임시 복사해 Cargo 패키지를 만든 뒤 그 패키지를 외부 프로젝트에서 path 의존성으로 빌드·실행합니다. `--ratatui`는 외부 프로젝트의 TestBackend 렌더링도 확인합니다. 실제 crates.io 다운로드 검증은 아닙니다. 검증용 실행파일은 임시 디렉터리에 둡니다. 로컬 상태·렌더링 검사와 한·영 PTY 시작·Ctrl+Q 종료·화면 복원은 통과했으며, 원격 단말과 GitHub CI는 아직 실행하지 않았습니다.

공통 원본은 [design/tokens](https://github.com/leechis7/tuivory/blob/main/design/tokens/README.md)입니다. `src/data/candidate.json`은 `python3 tools/export_tokens.py`로 생성한 배포용 사본이며 수동 편집하지 않습니다. `include_str!`로 포함하므로 외부 Rust 프로젝트에 design/이나 생성 도구가 필요하지 않습니다.

현재 Cargo 버전은 0.2.0이며 Git 배포를 위해 `publish = false`를 유지합니다. crates.io 게시는 수행하지 않았습니다. [라이선스](LICENSE) · [출처 고지](NOTICE.md)

## 공통 Tree

`tuivory::tree::{Tree, TreeNode, TreeState, TreeAction, TreeEvent}`는 Rust 1.85 이상에서 프레임워크 없이 사용합니다. 선택적 `tuivory::ratatui::TreeWidget`은 Rust 1.88 이상입니다. Go와 같은 안정 ID·펼침·선택·스크롤·이벤트 처리 규칙을 따르며 아이콘·보조 설명·개수·Unicode/ASCII를 렌더링합니다. [Tree 사용법](../docs/tree.md) · [지원 범위 점검](../docs/component-audit.md). 루트에서 `make run-tree-rust ARGS="--lang ko"`로 실행합니다. 이 TVR-7 변경은 `rust/v0.4.0`에 포함합니다.

## 공통 워크스페이스 컴포넌트

[탭·패널·분할선·상태 표시줄·경로 사용법](../docs/workspace.md)에서 Go/Rust 공개 API와 같은 조작·색상·상태 원칙을 설명합니다. DB 없는 한영 통합 예제는 루트에서 `make run-workspace-go ARGS="--lang ko"`, `make run-workspace-rust ARGS="--lang en"`으로 실행합니다. Go `go/v0.4.0`과 Rust `rust/v0.4.0`에 포함합니다. CI 결과와 실제 앱 적용은 [작업 기록](https://leechis7.atlassian.net/browse/TVR-7)에서 구분합니다.

## 공통 컨트롤 상태와 포커스

0.2.0의 `interaction::{ControlState, FocusTarget, FocusStack}`과 Ratatui `Styles::control`을 제공합니다. [공통 명세·한영 예제](../docs/focus.md)를 참조하고 루트에서 `make run-focus-rust ARGS="--lang ko"`로 실행합니다. 이 API는 rust/v0.4.0에 포함합니다.

[TVR-9: 입력·폼](../docs/forms.md): `Form / FormField / FormWidget`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-10: 목록·메뉴·검색 선택](../docs/collections.md): `ListModel / SearchPicker / ListWidget / SearchPickerWidget`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-11: 표·데이터 그리드](../docs/grid.md): `Grid / GridSource / GridWidget`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-12: 알림·진행·데이터 상태](../docs/feedback.md): `NoticeQueue / Progress / DataState`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-13: 배치·밀도·부가 컴포넌트](../docs/layout.md): `SpacingTokens / StackLayout / Badge / Chip / Help`. Go/Rust 공개 API와 한영 실행 예제. 0.2.0에 포함합니다.

[TVR-17 그리드 옵션](../docs/grid.md): simple/data 프리셋·범위·열 구성·상태줄·응답 세대 검사와 5행 비교 예제. 0.4.0에 포함합니다.

[공통 메뉴](../docs/menus.md): Go/Rust 계층·메뉴 바·뒤로가기·단축키/비활성·팝업·호출 문맥 요청과 DB 없는 한영 실행 예제. 0.4.0에 포함합니다.

0.4.0의 메뉴는 단일선 테두리와 항목 선택·열린 메뉴 표시를 사용합니다. 입력 차단·호출 위치 복귀는 유지합니다. [메뉴 표시 규칙](../docs/menus.md).

0.4.0의 TextOnSurface / Styles::text_on_surface 및 ControlStyleOnSurface / Styles::control_on_surface로 평문을 실제 바탕에 연결하고 대비를 보정합니다. 원본 토큰과 raw 스타일은 유지하며 명시적 상태/사용자 배경은 보존합니다. [한영 표면 디자인 가이드](../design/surfaces.md).

[비활성 상태와 12팔레트 비교](../docs/disabled-states.md): 일반 비활성 접두사 제거, 회색/Dim 전경, 입력 차단과 한영 실행 예제.
