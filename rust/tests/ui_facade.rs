use tuivory::input::InputEvent;

#[test]
fn host_lexer_byte_offsets() {
    use tuivory::{
        text::TextDocument,
        text_offsets::{ByteSyntaxSpan, grapheme_index},
    };
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("data/ui-input-cases.json")).unwrap();
    let offsets = &fixture["byte_offsets"];
    let text = offsets["text"].as_str().unwrap();
    for pair in offsets["boundaries"].as_array().unwrap() {
        assert_eq!(
            grapheme_index(text, pair[0].as_u64().unwrap() as usize).unwrap(),
            pair[1].as_u64().unwrap() as usize
        );
    }
    let mut d = TextDocument::editor(text);
    d.set_byte_syntax(&[ByteSyntaxSpan {
        start: 1,
        end: 7,
        role: "info".into(),
    }])
    .unwrap();
    for offset in offsets["invalid"].as_array().unwrap() {
        let offset = offset.as_u64().unwrap() as usize;
        assert!(grapheme_index(text, offset).is_err());
        assert!(
            d.set_byte_syntax(&[ByteSyntaxSpan {
                start: offset,
                end: offset,
                role: "info".into()
            }])
            .is_err()
        );
        assert_eq!((d.syntax[0].start, d.syntax[0].end), (1, 3));
    }
}

#[test]
fn shared_input_actions() {
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("data/ui-input-cases.json")).unwrap();
    for case in fixture["cases"].as_array().unwrap() {
        let expected: InputEvent = serde_json::from_value(case["event"].clone()).unwrap();
        #[cfg(not(feature = "terminal"))]
        let event = expected.clone();
        #[cfg(feature = "terminal")]
        let event = {
            use tuivory::ui::terminal::event::{
                Event, KeyCode, KeyEvent, KeyModifiers, MouseButton, MouseEvent, MouseEventKind,
            };
            let key = |k, m| InputEvent::from_key(KeyEvent::new(k, m));
            match case["raw"].as_str().unwrap() {
                "unicode" => key(KeyCode::Char('한'), KeyModifiers::NONE),
                "ctrl_c" => key(KeyCode::Char('c'), KeyModifiers::CONTROL),
                "ctrl_shift_c" => key(
                    KeyCode::Char('C'),
                    KeyModifiers::CONTROL | KeyModifiers::SHIFT,
                ),
                "shift_left" => key(KeyCode::Left, KeyModifiers::SHIFT),
                "alt_right" => key(KeyCode::Right, KeyModifiers::ALT),
                "backtab" => key(KeyCode::BackTab, KeyModifiers::NONE),
                "enter" => key(KeyCode::Enter, KeyModifiers::NONE),
                "f10" => key(KeyCode::F(10), KeyModifiers::NONE),
                "paste" => InputEvent::from_terminal(Event::Paste(expected.text.clone())),
                "resize" => InputEvent::from_terminal(Event::Resize(8, 3)),
                "drag" => InputEvent::from_terminal(Event::Mouse(MouseEvent {
                    kind: MouseEventKind::Drag(MouseButton::Left),
                    column: 6,
                    row: 3,
                    modifiers: KeyModifiers::SHIFT,
                })),
                "wheel" => InputEvent::from_terminal(Event::Mouse(MouseEvent {
                    kind: MouseEventKind::ScrollDown,
                    column: 6,
                    row: 3,
                    modifiers: KeyModifiers::NONE,
                })),
                _ => expected.clone(),
            }
        };
        assert_eq!(event, expected, "{}", case["name"]);
        assert_eq!(
            event.editing_action(),
            (
                case["action"].as_str().unwrap().into(),
                case["text"].as_str().unwrap().into()
            )
        );
    }
}

#[cfg(feature = "ratatui")]
#[test]
fn sdk_only_composition_and_clipping() {
    use tuivory::ui::{
        Terminal,
        backend::TestBackend,
        components::{Styles, SurfaceWidget, TextWidget},
        widgets::Widget,
    };
    let styles = Styles::new(tuivory::Theme::Light, tuivory::ColorProfile::Ansi16).unwrap();
    let mut model = tuivory::text::TextDocument::viewer("[literal] 界é");
    let mut terminal = Terminal::new(TestBackend::new(20, 4)).unwrap();
    terminal
        .draw(|frame| {
            SurfaceWidget::new(
                TextWidget {
                    model: &mut model,
                    styles: &styles,
                    focused: true,
                },
                &styles,
            )
            .render(frame.area(), frame.buffer_mut());
        })
        .unwrap();
    assert_eq!(terminal.backend().buffer()[(0, 0)].symbol(), "[");
    model.buffer.handle("select_all", "");
    assert_eq!(model.handle("copy", "").text, "[literal] 界é");
}
