use tuivory::{
    layout::CellRect,
    popup::{ShadowOptions, popup_placement},
};
fn rect(v: &serde_json::Value) -> CellRect {
    let a = v.as_array().unwrap();
    CellRect {
        x: a[0].as_u64().unwrap() as usize,
        y: a[1].as_u64().unwrap() as usize,
        width: a[2].as_u64().unwrap() as usize,
        height: a[3].as_u64().unwrap() as usize,
    }
}
#[test]
fn shared_footprint_geometry() {
    let data: serde_json::Value =
        serde_json::from_str(include_str!("data/popup-shadow-cases.json")).unwrap();
    for c in data["cases"].as_array().unwrap() {
        let options: ShadowOptions = serde_json::from_value(c["options"].clone()).unwrap();
        let l = popup_placement(
            rect(&c["anchor"]),
            rect(&c["viewport"]),
            c["width"].as_u64().unwrap() as usize,
            c["height"].as_u64().unwrap() as usize,
            options,
        );
        assert_eq!(l.bounds, rect(&c["expected"]["bounds"]), "{}", c["name"]);
        assert_eq!(l.card, rect(&c["expected"]["card"]));
        assert_eq!(l.shadow, rect(&c["expected"]["shadow"]));
        for r in l.shadow_regions() {
            for y in r.y..r.y + r.height {
                for x in r.x..r.x + r.width {
                    assert!(
                        !(x >= l.card.x
                            && x < l.card.x + l.card.width
                            && y >= l.card.y
                            && y < l.card.y + l.card.height)
                    );
                    assert!(
                        x >= l.bounds.x
                            && x < l.bounds.x + l.bounds.width
                            && y >= l.bounds.y
                            && y < l.bounds.y + l.bounds.height
                    );
                }
            }
        }
    }
}
#[test]
fn extreme_offsets_and_coordinates_do_not_wrap() {
    let options = ShadowOptions {
        mode: tuivory::popup::ShadowMode::Auto,
        offset_x: usize::MAX,
        offset_y: usize::MAX,
    };
    let l = popup_placement(
        CellRect {
            x: usize::MAX,
            y: usize::MAX,
            width: usize::MAX,
            height: usize::MAX,
        },
        CellRect {
            x: 100,
            y: 50,
            width: 10,
            height: 10,
        },
        usize::MAX,
        usize::MAX,
        options,
    );
    assert_eq!(
        l.bounds,
        CellRect {
            x: 100,
            y: 50,
            width: 10,
            height: 10
        }
    );
    assert_eq!(l.card.width, 1);
    assert_eq!(l.card.height, 1);
}
#[cfg(feature = "ratatui")]
mod rendering {
    use super::*;
    use ratatui::{Terminal, backend::TestBackend, layout::Rect, style::Modifier};
    use tuivory::{
        ColorProfile, Theme,
        menu::{Menu, MenuItem},
        popup::ShadowMode,
        ratatui::{MenuPopupWidget, Styles},
    };
    #[test]
    fn modes_preserve_card_and_repair_wide_edges() {
        for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
            for profile in [
                ColorProfile::Ansi8,
                ColorProfile::Ansi16,
                ColorProfile::Indexed256,
                ColorProfile::Truecolor,
            ] {
                for mode in [
                    ShadowMode::Off,
                    ShadowMode::Auto,
                    ShadowMode::Solid,
                    ShadowMode::Dim,
                ] {
                    for glyph in ["界", "한", "😀", "é"] {
                        let styles = Styles::new(theme, profile).unwrap();
                        let base = styles
                            .role("surface")
                            .unwrap()
                            .add_modifier(Modifier::ITALIC);
                        let options = ShadowOptions {
                            mode,
                            ..Default::default()
                        };
                        let layout = options.layout(CellRect {
                            x: 4,
                            y: 3,
                            width: 16,
                            height: 8,
                        });
                        let mut menu = Menu::new(vec![MenuItem {
                            id: "item".into(),
                            label: "Card".into(),
                            ..Default::default()
                        }])
                        .unwrap();
                        menu.open("", "origin");
                        let mut t = Terminal::new(TestBackend::new(40, 14)).unwrap();
                        let mut outside_before = None;
                        t.draw(|f| {
                            for y in 0..14 {
                                for x in 0..40 {
                                    f.buffer_mut()[(x, y)].set_symbol("R").set_style(base);
                                }
                            }
                            for (x, y) in [(19, 5), (5, 10), (18, 10)] {
                                f.buffer_mut().set_string(x, y, glyph, base);
                            }
                            outside_before = Some(f.buffer_mut()[(20, 5)].style());
                            f.render_widget(
                                MenuPopupWidget::new(&mut menu, &styles, "Menu").shadow(options),
                                Rect::new(4, 3, 16, 8),
                            );
                        })
                        .unwrap();
                        let b = t.backend().buffer();
                        assert_eq!(b[(4, 3)].symbol(), "┌");
                        assert!(
                            !b[(6, 5)].modifier.contains(Modifier::DIM),
                            "shadow leaked into popup {theme:?}/{profile:?}/{mode:?}"
                        );
                        assert_eq!(b[(1, 1)].symbol(), "R");
                        assert!(b[(1, 1)].modifier.contains(Modifier::ITALIC));
                        let r = layout.shadow_regions()[0];
                        if r.width > 0 && r.height > 0 {
                            let c = &b[(r.x as u16, r.y as u16)];
                            if mode == ShadowMode::Dim {
                                assert_eq!(c.symbol(), "R");
                                assert!(c.modifier.contains(Modifier::DIM));
                            } else if mode == ShadowMode::Solid {
                                assert_eq!(c.symbol(), " ");
                            } else {
                                assert!(c.symbol() == " " || c.symbol() == "░");
                            }
                        }
                        if mode != ShadowMode::Off && tuivory::components::cells(glyph) == 2 {
                            assert_eq!(b[(20, 5)].symbol(), " ");
                            assert_eq!(b[(20, 5)].style(), outside_before.unwrap());
                            assert!(!b[(20, 5)].modifier.contains(Modifier::DIM));
                            assert_eq!(b[(5, 10)].symbol(), " ");
                            assert!(!b[(5, 10)].modifier.contains(Modifier::DIM));
                        }
                        assert_eq!(menu.return_id(), "origin");
                        assert_eq!(menu.focused_id(), "item");
                        // Closing repaints through the host, without restoring stale saved cells.
                        t.draw(|f| {
                            for y in 0..14 {
                                for x in 0..40 {
                                    f.buffer_mut()[(x, y)].set_symbol("N").set_style(base);
                                }
                            }
                        })
                        .unwrap();
                        assert_eq!(t.backend().buffer()[(6, 5)].symbol(), "N");
                        assert!(
                            !t.backend().buffer()[(6, 5)]
                                .modifier
                                .contains(Modifier::DIM)
                        );
                    }
                }
            }
        }
    }
    #[test]
    fn default_off_matches_plain_popup_and_ascii_pattern() {
        let s = Styles::new(Theme::Blackwhite, ColorProfile::Ansi8).unwrap();
        let mut m = Menu::new(vec![]).unwrap();
        m.open("", "host");
        let mut t = Terminal::new(TestBackend::new(30, 12)).unwrap();
        t.draw(|f| f.render_widget(MenuPopupWidget::new(&mut m, &s, "Menu"), f.area()))
            .unwrap();
        let plain = t.backend().buffer().clone();
        t.draw(|f| {
            f.render_widget(
                MenuPopupWidget::new(&mut m, &s, "Menu").shadow(ShadowOptions::default()),
                f.area(),
            )
        })
        .unwrap();
        assert_eq!(t.backend().buffer(), &plain);
        let options = ShadowOptions {
            mode: ShadowMode::Auto,
            ..Default::default()
        };
        t.draw(|f| {
            f.render_widget(
                MenuPopupWidget::new(&mut m, &s, "Menu")
                    .ascii(true)
                    .shadow(options),
                f.area(),
            )
        })
        .unwrap();
        let l = options.layout(CellRect {
            x: 0,
            y: 0,
            width: 30,
            height: 12,
        });
        let r = l.shadow_regions()[0];
        assert_eq!(t.backend().buffer()[(r.x as u16, r.y as u16)].symbol(), ".");
    }
}

#[cfg(feature = "ratatui")]
#[test]
fn general_popup_widget_repairs_its_card_edges() {
    use ratatui::{Terminal, backend::TestBackend, layout::Rect, widgets::Paragraph};
    use tuivory::{
        ColorProfile, Theme,
        popup::ShadowMode,
        ratatui::{ShadowWidget, Styles},
    };
    let styles = Styles::new(Theme::Dark, ColorProfile::Indexed256).unwrap();
    let base = styles.role("body").unwrap();
    let mut terminal = Terminal::new(TestBackend::new(30, 14)).unwrap();
    terminal
        .draw(|f| {
            f.buffer_mut().set_string(3, 5, "界", base);
            f.buffer_mut().set_string(17, 5, "界", base);
            f.render_widget(
                ShadowWidget::new(
                    Paragraph::new("General").block(styles.block("Card", false).unwrap()),
                    &styles,
                    ShadowOptions {
                        mode: ShadowMode::Auto,
                        ..Default::default()
                    },
                ),
                Rect::new(4, 3, 16, 8),
            );
        })
        .unwrap();
    let b = terminal.backend().buffer();
    assert_eq!(b[(3, 5)].symbol(), " ");
    assert_eq!(b[(3, 5)].fg, base.fg.unwrap());
    assert_eq!(b[(4, 5)].symbol(), "│");
    assert_eq!(b[(17, 5)].symbol(), "│");
}
