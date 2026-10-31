# Tuivory만 import하는 UI 구성

**한국어 (기본)** · [English](ui-facade.en.md)

0.7.0 TVR-26은 `go/ui`, `go/terminal`, `tuivory::ui`, 공통 입력·바이트 span 변환을 제공합니다. [릴리스·설치](release-0.7.0.md) · [공통 규칙](../design/ui-facade.md) · [API 안내](api/README.md).

## 제공 경로

| 용도 | Go | Rust |
| --- | --- | --- |
| 공통 모델·컴포넌트 | github.com/leechis7/tuivory/go | tuivory의 forms/text/containers 등 |
| 앱·기존 위젯 | go/ui | ui::Terminal/Frame, ui::widgets/layout/buffer/style/text 등 |
| 의미별 렌더러 | 루트 New…View | ui::components의 기존 위젯·Styles |
| 이벤트·화면 | go/terminal | ui::terminal::{event,cursor,terminal,execute,…} |
| 공통 입력·편집 요청 | InputEvent, InputFromKey/InputFromMouse, EditingAction | input::InputEvent, from_key/from_terminal, editing_action |
| 터미널 수명 | ui.NewApplication의 Run/Stop/SetScreen | ui::Session, SessionOptions, finish/Drop |

Go는 SDK의 세 패키지를 사용하며 tview/tcell을 추가 import할 필요가 없습니다. Rust 외부 프로젝트는 Cargo 의존성에 **tuivory만** 선언하고 필요한 기능을 켭니다. 기존 루트 API와 `tuivory::ratatui` 경로는 유지합니다. SDK 내부 호환 별칭은 현재 backend의 타입·메서드·trait 정체성을 보존합니다. backend를 바꿔도 기존 코드/ABI가 무조건 유지된다는 의미는 아닙니다.

Rust 기능은 기본 core(1.85+), 그리기용 ratatui(1.88+), 터미널 I/O용 terminal(1.88+)로 나뉩니다. 기존 playground 기능은 terminal을 포함하는 호환 경로입니다. DB·전역 키·클립보드 실행 정책은 앱에 남습니다.

## 기존 Go 코드 전환

```go
import (
    tuivory "github.com/leechis7/tuivory/go"
    tview "github.com/leechis7/tuivory/go/ui"
    tcell "github.com/leechis7/tuivory/go/terminal"
)
```

기존 변수 이름을 유지하면서 import부터 바꿀 수 있습니다. `NewApplication`, `Primitive`, `Box`, `Form`, `InputField`, `TextArea`, `TextView`, `Flex`, `Pages`, `Grid`, `Table`, `TreeView`, 생성자·상수·정렬·콜백·화면/테스트 화면을 연결합니다. 루트 `tuivory.NewForm/NewButton/NewGrid`는 공통 의미 모델이고 `tview.NewForm/NewButton/NewGrid`는 SDK 호환 위젯이므로 이름 충돌 없이 단계적으로 옮깁니다. 새 코드의 Surface/Editor/배치는 [공통 컴포넌트](controls.md)를 우선 사용합니다.

호환 입력의 Ctrl+C 종료 등 원래 Application 동작은 유지합니다. Ctrl+C를 복사로 쓸 앱은 [controls 예제](../go/examples/controls/main.go)처럼 앱 입력 캡처에서 먼저 처리합니다. 키/마우스/붙여넣기·드래그 전달은 컨테이너가 담당하고 전역 동작은 앱이 선택합니다.

### 전역 설정

패키지 변수는 Go에서 다른 패키지 변수의 별칭으로 만들 수 없습니다. `Borders`/`Styles`는 시작 시점 값이며 직접 재할당해도 내부 전역이 바뀌지 않습니다. 아래 setter를 **이벤트 루프 시작 전** 사용합니다. 실행 중 동시 전역 변경은 지원하지 않습니다.

```go
theme := tview.GetStyles()
theme.PrimitiveBackgroundColor = tcell.ColorBlack
tview.SetStyles(theme)
borders := tview.GetBorders()
borders.TopLeft = '+'
tview.SetBorders(borders)
```

DoubleClickInterval, NewLine, TabSize, DefaultFormFieldWidth/Height도 Get…/Set…로 제공합니다. SemigraphicJoints는 공유 map 항목을 사용할 수 있고 map 교체는 SetSemigraphicJoints로 연결합니다. terminal의 기본값/색 이름 map 등도 시작값 또는 공유 map이며 변수 재바인딩을 backend 전역 재바인딩으로 간주하지 않습니다. 모든 패키지 심볼 대응은 [고정 버전 목록](../design/go-facade-symbols.json)에 기록하며 생성 결과를 CI에서 검사합니다.

## Rust의 단일 의존성

공개 Git 태그를 단일 의존성으로 연결합니다. 로컬 개발은 rust/의 path 의존성도 사용할 수 있습니다.

```toml
[dependencies]
tuivory = { git = "https://github.com/leechis7/tuivory", tag = "rust/v0.7.0", features = ["terminal"] }
```

```rust
use tuivory::{
    input::InputEvent,
    text::TextDocument,
    ui::{Session, Terminal, backend::CrosstermBackend},
    ui::components::{Styles, TextWidget},
    ui::terminal::event::{self, Event, KeyCode, KeyModifiers},
    Theme, ColorProfile,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let session = Session::enter(Default::default())?;
    let mut terminal = Terminal::new(CrosstermBackend::new(std::io::stdout()))?;
    let styles = Styles::new(Theme::Light, ColorProfile::Indexed256)?;
    let mut text = TextDocument::editor("한글 é 😀");
    loop {
        terminal.draw(|f| f.render_widget(
            TextWidget { model: &mut text, styles: &styles, focused: true }, f.area()))?;
        if let Event::Key(key) = event::read()? {
            if key.code == KeyCode::Char('q') && key.modifiers.contains(KeyModifiers::CONTROL) { break; }
            let (action, value) = InputEvent::from_key(key).editing_action();
            text.handle(&action, &value);
        }
    }
    session.finish()?;
    Ok(())
}
```

이 최소 예제의 종료 키는 앱이 정합니다. 실제 paste/mouse/resize/모달·테마 조합은 [Rust controls](../rust/examples/controls/main.rs)에 있습니다. Session은 중복 진입과 다른 컨트롤러가 소유한 raw 모드 진입을 거부하고 초기화 실패·정상 finish·Drop·panic unwind에서 터미널 상태를 정리합니다. 강제 종료/abort는 복원을 보장하지 않습니다. 기존 직접 터미널 수명 코드를 유지할 앱도 SDK의 호환 event/command 경로를 사용할 수 있습니다.

## LazyOra의 fork 제거 경로

Tuivory에서 LazyOra 저장소를 수정하지 않습니다. 다음은 적용 앱에서 **0.7.0 패키지로** 진행할 전환입니다.

| 기존 사용 | SDK 전환 |
| --- | --- |
| tview/tcell 패키지 타입·생성자·상수·콜백 | go/ui 및 go/terminal 경로 |
| fork의 Borders.…Focus 여섯 필드와 Box 포커스 그리기 | 공통 PanelView/상태 기반 그리기; Rust는 Styles.panel |
| fork의 TextArea.SetTextStyleFunc 바이트별 스타일 | 공통 Editor/TextView + 호스트 span + SetByteSyntax/set_byte_syntax |
| 표준 TextArea/TextView의 기능을 당장 유지 | SDK ui 호환 위젯, upstream v0.42.0 동작 |
| third_party/tview replace | 확장 사용을 위 경로로 옮긴 뒤 제거하고 앱/테스트를 재검증 |

호환 TextArea는 upstream 타입이며 fork 전용 메서드를 추가한 것으로 주장하지 않습니다. byte 범위가 결합 문자/CJK/이모지 내부를 자르면 변환 오류이며 이전 강조를 보존합니다. 그리기 범위와 원문 UTF-8의 의미를 섞지 않습니다.

```go
err := editor.SetByteSyntax([]tuivory.ByteSyntaxSpan{
    {Start: 0, End: 6, Role: "info"}, // 앱 렉서가 반환한 원문 byte 범위
})
```

Rust는 `text_offsets::ByteSyntaxSpan`, `TextDocument::set_byte_syntax`와 `grapheme_index`를 사용합니다. 렉서·SQL 실행·Vim/Toad 키맵은 SDK로 옮기지 않습니다. 기존 Undo/Redo·원문·마스킹·복사·포커스와 DB 데이터 의미는 적용 앱의 회귀 검사로 확인해야 합니다.

## 검증과 제공 상태

Go 모든 공개 예제와 루트 외부 API 테스트, Rust 모든 예제 및 UI 적합성 테스트에 backend 직접 import가 없는지 `tools/check_ui_facade.py`로 검사합니다. Go 고정 버전 심볼·한영 API 명세·공통 입력/바이트 경계 시나리오, 격리 Go 모듈/실제 패키징 Rust crate의 SDK 전용 외부 프로젝트를 검증합니다. Rust Session은 비TTY 초기화 실패·중복 진입·정상 종료/재진입·panic 복원을 실제 PTY로 검사합니다.

한영 Unicode/ASCII, 12팔레트, 팝업·포커스·선택·Undo/Redo·클립보드 요청·resize 회귀와 ARM64 정적 산출물 검증을 유지합니다. [구현 당시 로컬 검증](../evidence/ui-facade-results.json)과 [릴리스 검증 manifest](https://github.com/leechis7/tuivory/releases/tag/go/v0.7.0)를 구분합니다. CentOS 검증은 수행하지 않습니다. Python·JS/TS·C·C++ 및 ABI 구현은 [후속 설계](../design/ui-facade.md)이며 제공 완료가 아닙니다.

[LazyOra의 패키지 심볼 대응 기록](../evidence/ui-facade-consumer-map.json)은 first-party Go 소스/테스트를 읽기 전용으로 점검한 결과입니다. 실제 앱 전환·빌드 결과가 아닙니다. 호환 위젯은 upstream의 진단 동작도 유지하므로 비밀값의 표시/진단 보호에는 공통 password 모델을 사용합니다.
