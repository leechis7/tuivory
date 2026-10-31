# API 명세

**한국어 (기본)** · [English](README.en.md)

이 명세는 0.6.0 소스를 따르며 **TVR-22~25 API를 포함합니다.** [제공 범위·전환 안내](../controls.md).

기준 버전은 **0.6.0**입니다. Go 모듈은 `github.com/leechis7/tuivory/go`, Rust crate는 `tuivory`입니다. Rust 렌더러는 `ratatui`, 대화형 예제는 `playground` 기능을 켭니다.

- [Go 공개 선언](go.md)
- [Rust 공개 선언](rust.md)
- [Deprecated·전환 안내](../api-lifecycle.md)

[Go 스타일·팔레트 사용법](../go-package.md) · [Rust 패키지·기능 설정](../../rust/README.md)

## 명세 읽기

선언부에서 매개변수·반환 타입을 확인하고, 아래 가이드에서 허용 값·기본값·오류·상태/이벤트 규칙을 확인합니다. 생성자의 error/Result를 처리해야 합니다. 이벤트는 앱에 보내는 요청이며 DB나 업무 명령을 직접 실행하지 않습니다. Go 뷰는 tview 입력을 연결하고, Rust 모델은 동작을 받으며 위젯은 그립니다. 전역 키·컴포넌트 사이 포커스·배경 다시 그리기는 앱 책임입니다. 기본값과 오류 정책은 컴포넌트별로 다르므로 공통 동작으로 추측하지 마세요.

| 컴포넌트 | 내용 |
| --- | --- |
| [Tree](../tree.md) | 노드·선택·펼침·스크롤 |
| [Menu](../menus.md) | 메뉴 바·문맥 메뉴 |
| [Workspace](../workspace.md) | 탭·패널·분할·경로·상태줄 |
| [Focus](../focus.md) | 상태·포커스·팝업 |
| [Forms](../forms.md) | 입력·검증·제출 |
| [Collections](../collections.md) | 목록·검색 선택 |
| [Grid](../grid.md) | 표·편집·범위 선택 |
| [Feedback](../feedback.md) | 알림·진행·데이터 상태 |
| [Layout](../layout.md) | 배치·밀도·배지·단축키 안내 |
| [Shadows](../popup-shadows.md) | 팝업 그림자·위치·입력 범위 |
| [Drawing](../overlay-drawing.md) | 두 칸 문자·영역 그리기 |

## 갱신 방법

공개 선언과 원문 주석은 소스에서 생성합니다. 동작 설명은 한영으로 함께 수정합니다. Rust 추출에는 Rust 1.88.0의 JSON 형식 45를 사용하며 아래 RUSTC_BOOTSTRAP은 문서 추출에만 필요합니다. CARGO_TARGET_DIR을 별도로 설정했다면 JSON 경로도 맞추세요.

```sh
RUSTC_BOOTSTRAP=1 cargo +1.88.0 rustdoc --manifest-path rust/Cargo.toml --locked --all-features --lib -- -Z unstable-options --output-format json
python3 tools/generate_api_reference.py --rust-json rust/target/doc/tuivory.json
python3 tools/generate_api_reference.py --rust-json rust/target/doc/tuivory.json --check
python3 tools/check_links.py
```

Go 별칭의 원 선언에 internal 패키지 이름이 보여도 앱에서는 공개 tuivory 이름으로 사용합니다. Rust의 Default·Widget 등 trait 구현 전체는 cargo doc으로 확인합니다.

```sh
cargo doc --manifest-path rust/Cargo.toml --locked --all-features --no-deps --open
```
