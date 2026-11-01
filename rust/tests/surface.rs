#![cfg(feature = "ratatui")]
use ratatui::{
    buffer::Buffer,
    layout::Rect,
    style::Modifier,
    widgets::{Paragraph, Widget},
};
use tuivory::{
    ColorProfile, Theme,
    ratatui::{Styles, SurfaceWidget},
};

#[test]
fn wrapped_tables_preserve_wide_text_across_selection_and_repaint() {
    use ratatui::{
        Terminal,
        backend::TestBackend,
        layout::Constraint,
        widgets::{Row, StatefulWidget, Table, TableState},
    };
    use tuivory::{
        popup::{ShadowMode, ShadowOptions},
        ratatui::ShadowWidget,
    };
    use unicode_segmentation::UnicodeSegmentation;
    use unicode_width::UnicodeWidthStr;
    struct SelectedTable<'a> {
        styles: &'a Styles,
        selected: usize,
    }
    impl Widget for SelectedTable<'_> {
        fn render(self, area: Rect, buffer: &mut Buffer) {
            let rows = ["한글 SQL 전체 선택", "界面 é 👩‍💻 🇰🇷 😀"].map(|text| Row::new([text]));
            StatefulWidget::render(
                Table::new(rows, [Constraint::Min(0)])
                    .style(self.styles.role("field").unwrap())
                    .row_highlight_style(self.styles.role("selection").unwrap()),
                area,
                buffer,
                &mut TableState::default().with_selected(Some(self.selected)),
            );
        }
    }
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let styles = Styles::new(theme, profile).unwrap();
            let mut terminal = Terminal::new(TestBackend::new(80, 18)).unwrap();
            for selected in [0, 1, 0] {
                terminal
                    .draw(|frame| {
                        frame.render_widget(
                            ShadowWidget::new(
                                SurfaceWidget::new(
                                    SelectedTable {
                                        styles: &styles,
                                        selected,
                                    },
                                    &styles,
                                ),
                                &styles,
                                ShadowOptions {
                                    mode: ShadowMode::Dim,
                                    ..ShadowOptions::default()
                                },
                            ),
                            Rect::new(3, 2, 60, 10),
                        )
                    })
                    .unwrap();
                let buffer = terminal.backend().buffer();
                for (row, text) in ["한글 SQL 전체 선택", "界面 é 👩‍💻 🇰🇷 😀"].iter().enumerate()
                {
                    let expected = styles
                        .role(if row == selected {
                            "selection"
                        } else {
                            "field"
                        })
                        .unwrap();
                    let mut x = 3;
                    for glyph in text.graphemes(true) {
                        let cell = &buffer[(x, 2 + row as u16)];
                        assert_eq!(cell.symbol(), glyph);
                        assert_eq!(Some(cell.fg), expected.fg);
                        assert_eq!(Some(cell.bg), expected.bg);
                        x += glyph.width() as u16;
                    }
                }
            }
        }
    }
}
#[test]
fn opaque_surface_preserves_wide_edges_and_fills_padding() {
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let styles = Styles::new(theme, profile).unwrap();
            let mut title = Buffer::empty(Rect::new(0, 0, 30, 4));
            styles
                .panel("Unique title", true, 0, false)
                .unwrap()
                .render(title.area, &mut title);
            let text: String = (0..30).map(|x| title[(x, 0)].symbol()).collect();
            assert_eq!(text.matches("Unique title").count(), 1);
            let mut b = Buffer::empty(Rect::new(0, 0, 20, 10));
            let outside = styles.role("hint").unwrap().add_modifier(Modifier::ITALIC);
            b.set_string(2, 3, "界", outside);
            b.set_string(9, 3, "한", outside);
            SurfaceWidget::new(Paragraph::new("A"), &styles)
                .padding(1)
                .render(Rect::new(3, 2, 7, 4), &mut b);
            assert_eq!(b[(3, 2)].symbol(), " ");
            assert_eq!(b[(4, 3)].symbol(), "A");
            assert_eq!(b[(2, 3)].symbol(), " ");
            assert_eq!(b[(10, 3)].symbol(), " ");
            assert!(b[(2, 3)].modifier.contains(Modifier::ITALIC));
            SurfaceWidget::new(Paragraph::new(""), &styles).render(Rect::new(3, 2, 0, 0), &mut b);
        }
    }
}
