#![cfg(feature = "ratatui")]

use ratatui::{
    Terminal,
    backend::TestBackend,
    style::{Color as RColor, Modifier},
    widgets::Paragraph,
};
use tuivory::ratatui::Styles;
use tuivory::{Color, ColorProfile, Style, Theme, TokenDocument};

#[test]
fn converts_colors_and_weights_without_changing_indices() {
    for n in 0..=255 {
        assert_eq!(RColor::from(Color::Indexed(n)), RColor::Indexed(n));
    }
    assert_eq!(RColor::from(Color::Rgb(1, 2, 3)), RColor::Rgb(1, 2, 3));
    let converted: ratatui::style::Style = Style {
        foreground: Color::Indexed(7),
        background: Color::Indexed(0),
        bold: true,
    }
    .into();
    assert!(converted.add_modifier.contains(Modifier::BOLD));
}

#[test]
fn semantic_roles_render_in_all_twelve_palettes() {
    let doc = TokenDocument::candidate().unwrap();
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let styles = Styles::new(theme, profile).unwrap();
            let mut terminal = Terminal::new(TestBackend::new(32, 3)).unwrap();
            for role in doc.roles() {
                terminal
                    .draw(|f| {
                        f.render_widget(
                            Paragraph::new("Sample").style(styles.role(role).unwrap()),
                            f.area(),
                        )
                    })
                    .unwrap();
                let cell = &terminal.backend().buffer()[(0, 0)];
                let raw = doc.palette(theme, profile).unwrap().style(role).unwrap();
                assert_eq!(cell.fg, RColor::from(raw.foreground));
                assert_eq!(cell.bg, RColor::from(raw.background));
                assert_eq!(cell.modifier.contains(Modifier::BOLD), raw.bold);
            }
            assert!(styles.role("missing").is_err());
            terminal
                .draw(|f| f.render_widget(styles.block("Panel", true).unwrap(), f.area()))
                .unwrap();
            assert_eq!(terminal.backend().buffer()[(0, 0)].symbol(), "╔");
            for focused in [false, true] {
                for ascii in [false, true] {
                    terminal
                        .draw(|f| {
                            f.render_widget(
                                styles.panel("Area", focused, 0, ascii).unwrap(),
                                f.area(),
                            )
                        })
                        .unwrap();
                    let b = terminal.backend().buffer();
                    assert_eq!(
                        b[(0, 0)].symbol(),
                        if ascii {
                            "+"
                        } else if focused {
                            "╔"
                        } else {
                            "┌"
                        }
                    );
                    assert_eq!(
                        b[(31, 2)].symbol(),
                        if ascii {
                            "+"
                        } else if focused {
                            "╝"
                        } else {
                            "┘"
                        }
                    );
                    assert_eq!(
                        b[(0, 1)].symbol(),
                        if ascii {
                            "|"
                        } else if focused {
                            "║"
                        } else {
                            "│"
                        }
                    );
                    assert_eq!(
                        b[(1, 2)].symbol(),
                        if ascii {
                            "-"
                        } else if focused {
                            "═"
                        } else {
                            "─"
                        }
                    );
                    let border = styles
                        .role(if focused { "focus.border" } else { "hint" })
                        .unwrap();
                    assert_eq!(Some(b[(0, 0)].fg), border.fg);
                }
            }
        }
    }
}
