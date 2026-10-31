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
