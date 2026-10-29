use tuivory::{
    collections::{ListItem, ListModel},
    forms::{Form, FormField, FormOption},
    interaction::ControlState,
    layout::{Help, Shortcut},
};
#[test]
fn disabled_presentation_uses_roles_without_extra_markers() {
    let help = Help::new(vec![Shortcut {
        key: "Ctrl+S".into(),
        text: "Save".into(),
        disabled: true,
        priority: 0,
    }])
    .unwrap();
    let rows = help.layout(40, 1);
    assert_eq!(rows[0].text, "[Ctrl+S] Save");
    assert_eq!(rows[0].role, "disabled");
    let mut list = ListModel::new(vec![
        ListItem {
            id: "off".into(),
            label: "Unavailable".into(),
            secondary: "Reason".into(),
            disabled: true,
            ..Default::default()
        },
        ListItem {
            id: "on".into(),
            label: "Enabled".into(),
            ..Default::default()
        },
    ])
    .unwrap();
    assert!(!list.focus("off"));
    let rows = list.layout(50, 10, false);
    assert!(!rows[0].text.contains("[-]"));
    assert_eq!(rows[1].role, "disabled");
    let form = Form::new(vec![
        FormField {
            id: "text".into(),
            kind: "text".into(),
            label: "Name".into(),
            value: "Retained".into(),
            state: ControlState {
                disabled: true,
                ..Default::default()
            },
            ..Default::default()
        },
        FormField {
            id: "button".into(),
            kind: "button".into(),
            label: "Save".into(),
            state: ControlState {
                disabled: true,
                ..Default::default()
            },
            ..Default::default()
        },
        FormField {
            id: "choice".into(),
            kind: "radio".into(),
            label: "Choice".into(),
            options: vec![
                FormOption {
                    id: "no".into(),
                    label: "Unavailable".into(),
                    disabled: true,
                },
                FormOption {
                    id: "yes".into(),
                    label: "Available".into(),
                    disabled: false,
                },
            ],
            ..Default::default()
        },
    ])
    .unwrap();
    let rows = form.layout(60, 20);
    for row in &rows {
        if row.id == "text" || row.id == "button" {
            assert_eq!(row.role, "disabled");
        }
        if row.value == "no" {
            assert!(!row.text.contains("[-]"));
            assert_eq!(row.role, "disabled");
        }
    }
    assert!(!rows[0].text.starts_with("[-]"));
    assert!(rows[1].text.contains("Retained"));
}

#[test]
fn disabled_menu_bar_label_and_hit_region() {
    use tuivory::menu::{Menu, MenuItem};
    let mut menu = Menu::new(vec![
        MenuItem {
            id: "on".into(),
            label: "File".into(),
            ..Default::default()
        },
        MenuItem {
            id: "off".into(),
            label: "Edit".into(),
            disabled: true,
            ..Default::default()
        },
    ])
    .unwrap();
    let bar = menu.bar_layout(40);
    let cell = bar.cells.iter().find(|c| c.id == "off").unwrap();
    assert!(!cell.text.contains("- Edit"));
    assert_eq!(cell.width, 6);
    assert!(menu.bar_click(cell.start, 40).is_none());
}

#[test]
fn disabled_notice_action_cue() {
    use tuivory::feedback::{Notice, NoticeAction, NoticeQueue};
    let mut q = NoticeQueue::new(2).unwrap();
    q.push(Notice {
        id: "n".into(),
        text: "Ready".into(),
        severity: "info".into(),
        actions: vec![NoticeAction {
            id: "save".into(),
            label: "Save".into(),
            disabled: true,
        }],
        ..Default::default()
    })
    .unwrap();
    let rows = q.layout(60, 2, 0);
    assert!(!rows[0].text.contains("[-]"));
    assert_eq!(rows[0].spans[0].role, "disabled");
}

#[test]
fn disabled_click_does_not_move_focus_or_activate() {
    let mut form = Form::new(vec![
        FormField {
            id: "on".into(),
            kind: "button".into(),
            label: "Run".into(),
            ..Default::default()
        },
        FormField {
            id: "off".into(),
            kind: "button".into(),
            label: "Unavailable".into(),
            state: ControlState {
                disabled: true,
                ..Default::default()
            },
            ..Default::default()
        },
        FormField {
            id: "options".into(),
            kind: "radio".into(),
            label: "Options".into(),
            options: vec![
                FormOption {
                    id: "no".into(),
                    label: "Unavailable".into(),
                    disabled: true,
                },
                FormOption {
                    id: "yes".into(),
                    label: "Available".into(),
                    disabled: false,
                },
            ],
            ..Default::default()
        },
    ])
    .unwrap();
    let before = form.focused().to_owned();
    for (id, option) in [("off", ""), ("options", "no")] {
        assert!(form.click(id, option).kind.is_empty());
        assert_eq!(form.focused(), before);
    }
}

#[cfg(feature = "ratatui")]
#[test]
fn disabled_style_distinct_in_every_palette() {
    use ratatui::{Terminal, backend::TestBackend, style::Modifier};
    use tuivory::{
        ColorProfile, Theme,
        forms::ComponentLine,
        ratatui::{RowsWidget, Styles},
    };
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let styles = Styles::new(theme, profile).unwrap();
            let rows = vec![
                ComponentLine {
                    text: "Enabled".into(),
                    role: "body".into(),
                    ..Default::default()
                },
                ComponentLine {
                    text: "Disabled".into(),
                    role: "disabled".into(),
                    ..Default::default()
                },
            ];
            let mut terminal = Terminal::new(TestBackend::new(30, 2)).unwrap();
            terminal
                .draw(|f| {
                    f.render_widget(
                        RowsWidget {
                            rows: &rows,
                            styles: &styles,
                            focused: false,
                        },
                        f.area(),
                    )
                })
                .unwrap();
            let buf = terminal.backend().buffer();
            let active = &buf[(0, 0)];
            let disabled = &buf[(0, 1)];
            assert_eq!(active.bg, disabled.bg);
            assert!(active.fg != disabled.fg || active.modifier != disabled.modifier);
            if profile == ColorProfile::Ansi8 {
                assert!(disabled.modifier.contains(Modifier::DIM));
            }
        }
    }
}
