use tuivory::layer_input::LayerInput;

#[test]
fn shared_layer_routes() {
    let fixture: Vec<Vec<serde_json::Value>> =
        serde_json::from_str(include_str!("data/layer-input-cases.json")).unwrap();
    let mut gate = LayerInput::default();
    for row in fixture {
        let word = |i: usize| row[i].as_str().unwrap();
        match word(0) {
            "front" => {
                let expected: Vec<_> = [word(2)].into_iter().filter(|s| !s.is_empty()).collect();
                assert_eq!(gate.set_front(word(1)), expected);
            }
            "invalidate" => assert_eq!(gate.invalidate(), [word(1)]),
            "key" => assert_eq!(gate.keyboard_target(word(1)), word(2)),
            "pointer" => {
                let got = gate.pointer(
                    word(1),
                    row[2].as_u64().unwrap() as u8,
                    word(3),
                    row[4].as_bool().unwrap(),
                );
                assert_eq!(
                    (got.target.as_str(), got.action.as_str()),
                    (word(5), word(6)),
                    "{row:?}"
                );
            }
            _ => panic!("unknown case: {row:?}"),
        }
    }
}

#[cfg(feature = "ratatui")]
#[test]
fn ratatui_front_layer_restricts_input_and_restores_prior_focus() {
    use ratatui::{Terminal, backend::TestBackend, layout::Rect, widgets::Paragraph};
    use tuivory::containers::{ContainerState, LayoutItem};
    use tuivory::input::InputEvent;

    let editor = LayoutItem {
        id: "editor".into(),
        ..Default::default()
    };
    let tabs = LayoutItem {
        id: "tabs".into(),
        modal: true,
        ..Default::default()
    };
    let popup = LayoutItem {
        id: "popup".into(),
        modal: true,
        ..Default::default()
    };
    let mut focus = ContainerState::default();
    let mut gate = LayerInput::default();
    let mut terminal = Terminal::new(TestBackend::new(20, 7)).unwrap();

    focus.reconcile(std::slice::from_ref(&editor));
    gate.pointer("down", 1, "editor", false);
    assert_eq!(gate.set_front("tabs"), ["editor"]);
    focus.reconcile(&[editor.clone(), tabs.clone()]);
    assert_eq!(gate.pointer("up", 1, "tabs", false).target, "");
    gate.set_front("popup");
    focus.reconcile(&[editor.clone(), tabs.clone(), popup]);
    terminal
        .draw(|frame| {
            frame.render_widget(Paragraph::new("editor"), Rect::new(0, 0, 20, 7));
            frame.render_widget(Paragraph::new("tabs"), Rect::new(1, 1, 13, 5));
            frame.render_widget(Paragraph::new("popup"), Rect::new(2, 2, 7, 3));
        })
        .unwrap();
    assert_eq!(terminal.backend().buffer()[(2, 2)].symbol(), "p");
    let paste = InputEvent::paste("한글");
    assert!(gate.keyboard_target("tabs").is_empty());
    assert_eq!(gate.keyboard_target(&focus.focused), "popup");
    assert_eq!(paste.editing_action(), ("paste".into(), "한글".into()));
    gate.set_front("tabs");
    focus.reconcile(&[editor.clone(), tabs]);
    assert_eq!(gate.keyboard_target(&focus.focused), "tabs");
    gate.set_front("");
    focus.reconcile(&[editor]);
    assert_eq!(gate.keyboard_target(&focus.focused), "editor");
}
