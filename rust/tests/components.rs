use serde_json::Value;
use tuivory::components::*;
fn fixture() -> Value {
    serde_json::from_str(include_str!("data/components-cases.json")).unwrap()
}
fn items(f: &Value) -> Vec<TabItem> {
    f["tabs"]["items"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| TabItem {
            id: v["id"].as_str().unwrap().into(),
            title: v["title"].as_str().unwrap().into(),
            edited: v["edited"].as_bool().unwrap_or(false),
            closable: v["closable"].as_bool().unwrap_or(false),
            disabled: v["disabled"].as_bool().unwrap_or(false),
        })
        .collect()
}
#[test]
fn shared_workspace_contract() {
    let f = fixture();
    let tabs = Tabs::new(items(&f)).unwrap();
    let mut state = TabState::default();
    for step in f["tabs"]["steps"].as_array().unwrap() {
        let action = match step["action"].as_str().unwrap() {
            "next" => TabAction::Next,
            "previous" => TabAction::Previous,
            "first" => TabAction::First,
            "last" => TabAction::Last,
            "activate" => TabAction::Activate,
            "close" => TabAction::Close,
            _ => panic!(),
        };
        let e = tabs.handle(&mut state, action).unwrap();
        let (kind, id) = match e {
            TabEvent::Focus(id) => ("focus", id),
            TabEvent::Activate(id) => ("activate", id),
            TabEvent::Close(id) => ("close", id),
        };
        assert_eq!(kind, step["event"].as_str().unwrap());
        assert_eq!(id, step["id"].as_str().unwrap());
        assert_eq!(state.active, step["active"].as_str().unwrap());
        assert_eq!(state.focused, step["focused"].as_str().unwrap());
    }
    for test in f["tabs"]["layouts"].as_array().unwrap() {
        let width = test["width"].as_u64().unwrap() as usize;
        let mut state = TabState {
            active: "a".into(),
            focused: "c".into(),
            first: 0,
        };
        let layout = tabs.layout(&mut state, width);
        assert_eq!(state.first, test["first"].as_u64().unwrap() as usize);
        assert_eq!(
            layout
                .cells
                .iter()
                .map(|c| c.id.as_str())
                .collect::<Vec<_>>(),
            test["ids"]
                .as_array()
                .unwrap()
                .iter()
                .map(|v| v.as_str().unwrap())
                .collect::<Vec<_>>()
        );
        for cell in layout.cells {
            assert!(cell.start + cell.width <= width);
            assert!(cells(&cell.text) <= cell.width);
        }
    }
    let path = vec![
        PathItem {
            id: "r".into(),
            label: "root".into(),
        },
        PathItem {
            id: "f".into(),
            label: "folder".into(),
        },
        PathItem {
            id: "c".into(),
            label: "현재.sql".into(),
        },
    ];
    for test in f["paths"].as_array().unwrap() {
        let width = test["width"].as_u64().unwrap() as usize;
        let runs = breadcrumbs(&path, width);
        assert_eq!(
            runs.iter().map(|r| r.text.as_str()).collect::<String>(),
            test["text"].as_str().unwrap()
        );
        for run in runs {
            assert!(run.start + run.width <= width)
        }
    }
    let status = vec![
        StatusItem {
            id: "help".into(),
            text: "F1 Help".into(),
            role: "hint".into(),
            priority: 1,
        },
        StatusItem {
            id: "err".into(),
            text: "Failure".into(),
            role: "error".into(),
            priority: 100,
        },
        StatusItem {
            id: "draft".into(),
            text: "Draft".into(),
            role: "edited".into(),
            priority: 30,
        },
    ];
    for test in f["status"].as_array().unwrap() {
        let width = test["width"].as_u64().unwrap() as usize;
        let layout = status_line(&status, width);
        assert_eq!(
            layout
                .runs
                .iter()
                .map(|r| r.text.as_str())
                .collect::<String>(),
            test["text"].as_str().unwrap()
        );
        assert_eq!(layout.omitted, test["omitted"].as_u64().unwrap() as usize);
        for run in layout.runs {
            assert!(run.start + run.width <= width)
        }
    }
}
#[test]
fn close_requests_and_split_state_survive_reflow() {
    assert!(
        Tabs::new(vec![
            TabItem {
                id: "a".into(),
                ..Default::default()
            },
            TabItem {
                id: "a".into(),
                ..Default::default()
            }
        ])
        .is_err()
    );
    let tabs = Tabs::new(vec![TabItem {
        id: "a".into(),
        title: "Long 한글 document".into(),
        edited: true,
        closable: true,
        ..Default::default()
    }])
    .unwrap();
    let mut state = TabState::default();
    let layout = tabs.layout(&mut state, 24);
    let before = state.clone();
    let cell = &layout.cells[0];
    assert!(cell.text.contains("* x"));
    assert_eq!(
        tabs.click(&mut state, cell.start + cells(&cell.text) - 2, 24),
        Some(TabEvent::Close("a".into()))
    );
    assert_eq!(state, before);
    Tabs::new(vec![]).unwrap().reconcile(&mut state);
    assert!(state.active.is_empty() && state.focused.is_empty());
    let spec = SplitSpec {
        first_min: 10,
        second_min: 15,
    };
    let mut state = SplitState { preferred: 20 };
    let initial = spec.layout(&state, 60);
    assert_eq!((initial.first, initial.second), (20, 39));
    assert!(spec.layout(&state, 20).compact);
    assert_eq!(state.preferred, 20);
    assert_eq!(spec.layout(&state, 60), initial);
    spec.resize(&mut state, 60, 99);
    assert_eq!(state.preferred, 44);
    assert_eq!(spec.layout(&state, 40).first, 24);
    assert_eq!(state.preferred, 44);
    for total in 0..100 {
        let l = spec.layout(&state, total);
        assert_eq!(l.first + l.divider + l.second, total)
    }
}
#[cfg(feature = "ratatui")]
#[test]
fn twelve_palette_widgets_geometry_and_literal_text() {
    use ratatui::{Terminal, backend::TestBackend, layout::Rect, style::Modifier};
    use tuivory::{
        ColorProfile, Theme,
        ratatui::{LineWidget, Styles, TabsWidget, split_rects},
    };
    let tabs = Tabs::new(items(&fixture())).unwrap();
    let mut state = TabState {
        active: "a".into(),
        focused: "b".into(),
        first: 0,
    };
    let split = SplitState { preferred: 20 };
    let spec = SplitSpec {
        first_min: 10,
        second_min: 10,
    };
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let styles = Styles::new(theme, profile).unwrap();
            let mut terminal = Terminal::new(TestBackend::new(80, 20)).unwrap();
            let before = state.clone();
            terminal
                .draw(|f| {
                    let mut widget = TabsWidget::new(&tabs, &styles).unwrap();
                    widget.focused = true;
                    f.render_stateful_widget(widget, Rect::new(0, 0, 60, 1), &mut state);
                    let panel = styles.panel("[red] Literal", true, 1, true).unwrap();
                    f.render_widget(panel, Rect::new(0, 2, 30, 8));
                    let layout = status_line(
                        &[StatusItem {
                            id: "e".into(),
                            text: "Failure".into(),
                            role: "error".into(),
                            priority: 9,
                        }],
                        30,
                    );
                    f.render_widget(
                        LineWidget::new(layout.runs, &styles).unwrap(),
                        Rect::new(0, 15, 30, 1),
                    );
                })
                .unwrap();
            assert_eq!(state.active, before.active);
            assert_eq!(state.focused, before.focused);
            let layout = tabs.layout(&mut state, 60);
            let cell = &terminal.backend().buffer()[(layout.cells[1].start as u16, 0)];
            assert!(cell.modifier.contains(Modifier::UNDERLINED));
            assert_eq!(terminal.backend().buffer()[(0, 2)].symbol(), "+");
            let style = styles.role("error").unwrap();
            assert_eq!(terminal.backend().buffer()[(0, 15)].fg, style.fg.unwrap());
            assert_eq!(terminal.backend().buffer()[(0, 15)].bg, style.bg.unwrap());
            for rows in [false, true] {
                for width in 0..60 {
                    let r = split_rects(Rect::new(0, 0, width, 20), spec, &split, rows, true);
                    assert!(r.first.right() <= width && r.second.right() <= width);
                    assert!(r.first.bottom() <= 20 && r.second.bottom() <= 20);
                    if r.compact {
                        assert_eq!(r.second, Rect::new(0, 0, width, 20));
                    }
                }
            }
            terminal
                .draw(|f| {
                    f.render_stateful_widget(
                        TabsWidget::new(&tabs, &styles).unwrap(),
                        Rect::default(),
                        &mut state,
                    );
                    f.render_widget(LineWidget::new(vec![], &styles).unwrap(), Rect::default());
                })
                .unwrap();
            assert!(
                LineWidget::new(
                    vec![LineRun {
                        text: "bad".into(),
                        role: "missing".into(),
                        id: "".into(),
                        start: 0,
                        width: 3
                    }],
                    &styles
                )
                .is_err()
            );
        }
    }
}
