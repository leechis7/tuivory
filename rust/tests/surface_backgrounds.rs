#![cfg(feature = "ratatui")]
use ratatui::{
    Terminal,
    backend::TestBackend,
    style::{Color, Modifier},
};
use tuivory::{
    ColorProfile, Theme,
    components::{PathItem, StatusItem, breadcrumbs, status_line},
    forms::{ComponentLine, ComponentSpan},
    interaction::ControlState,
    ratatui::{LineWidget, RowsWidget, Styles},
};
#[test]
fn plain_text_inherits_surface_without_flattening_explicit_backgrounds() {
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let styles = Styles::new(theme, profile).unwrap();
            let roles = [
                "body",
                "hint",
                "disabled",
                "info",
                "success",
                "warning",
                "error",
                "field",
                "button",
                "selection",
                "edited",
            ];
            let rows: Vec<_> = roles
                .iter()
                .map(|role| ComponentLine {
                    text: "Label".into(),
                    role: (*role).into(),
                    spans: vec![ComponentSpan {
                        start: 10,
                        width: 8,
                        text: "Span".into(),
                        role: (*role).into(),
                        ..Default::default()
                    }],
                    ..Default::default()
                })
                .collect();
            let mut terminal = Terminal::new(TestBackend::new(40, 16)).unwrap();
            for preserve in [false, true] {
                terminal
                    .draw(|f| {
                        let widget = RowsWidget {
                            rows: &rows,
                            styles: &styles,
                            focused: false,
                        };
                        if preserve {
                            f.render_widget(widget.preserve_backgrounds(), f.area())
                        } else {
                            f.render_widget(widget, f.area())
                        }
                    })
                    .unwrap();
                for (y, role) in roles.iter().enumerate() {
                    let expected = styles
                        .role(if !preserve && y < 7 { "surface" } else { role })
                        .unwrap()
                        .bg
                        .unwrap();
                    for x in [0, 10, 17] {
                        assert_eq!(
                            terminal.backend().buffer()[(x, y as u16)].bg,
                            expected,
                            "{theme:?}/{profile:?} {role} preserve={preserve}"
                        );
                    }
                }
            }
            for runs in [
                breadcrumbs(
                    &[
                        PathItem {
                            id: "r".into(),
                            label: "Root".into(),
                        },
                        PathItem {
                            id: "c".into(),
                            label: "Current".into(),
                        },
                    ],
                    40,
                ),
                status_line(
                    &[StatusItem {
                        id: "s".into(),
                        text: "Success".into(),
                        role: "success".into(),
                        priority: 1,
                    }],
                    40,
                )
                .runs,
            ] {
                terminal
                    .draw(|f| {
                        f.render_widget(LineWidget::new(runs.clone(), &styles).unwrap(), f.area())
                    })
                    .unwrap();
                for x in 0..40 {
                    assert_eq!(
                        terminal.backend().buffer()[(x, 0)].bg,
                        styles.role("surface").unwrap().bg.unwrap()
                    );
                }
            }
            let bound = styles.text_on_surface("success", "surface").unwrap();
            assert_eq!(bound.bg, styles.role("surface").unwrap().bg);
            if theme == Theme::Light && profile == ColorProfile::Ansi16 {
                assert_eq!(bound.fg, Some(Color::Indexed(0)));
                assert_eq!(styles.role("success").unwrap().fg, Some(Color::Indexed(2)));
            }
            assert_eq!(
                styles.text_on_surface("body", "body").unwrap().bg,
                styles.role("body").unwrap().bg
            );
            for state in [
                ControlState {
                    selected: true,
                    ..Default::default()
                },
                ControlState {
                    edited: true,
                    ..Default::default()
                },
            ] {
                assert_eq!(
                    styles.control_on_surface(state, true, "surface").unwrap(),
                    styles.control(state, true).unwrap()
                );
            }
            let control = styles
                .control_on_surface(ControlState::default(), true, "surface")
                .unwrap();
            assert_eq!(control.bg, styles.role("surface").unwrap().bg);
            assert!(control.add_modifier.contains(Modifier::UNDERLINED));
        }
    }
}
#[test]
fn invalid_surface_roles_report_errors() {
    let s = Styles::new(Theme::Dark, ColorProfile::Indexed256).unwrap();
    assert!(s.text_on_surface("missing", "surface").is_err());
    assert!(s.text_on_surface("body", "missing").is_err());
}
