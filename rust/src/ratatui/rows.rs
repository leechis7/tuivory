use super::Styles;
use crate::forms::{ComponentLine, Form};
use ratatui::{buffer::Buffer, layout::Rect, style::Modifier, widgets::Widget};
/// Literal semantic rows. Missing optional roles use body; token errors are not hidden.
pub struct RowsWidget<'a> {
    pub rows: &'a [ComponentLine],
    pub styles: &'a Styles,
    pub focused: bool,
}
impl Widget for RowsWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let base = self.styles.role("surface").expect("surface role");
        for y in area.y..area.bottom() {
            for x in area.x..area.right() {
                buf[(x, y)].set_symbol(" ").set_style(base);
            }
        }
        for (i, row) in self.rows.iter().take(usize::from(area.height)).enumerate() {
            let mut style = self
                .styles
                .role(&row.role)
                .expect("validated semantic row role");
            if row.focused && self.focused {
                style = style.add_modifier(Modifier::UNDERLINED)
            }
            buf.set_stringn(
                area.x,
                area.y + i as u16,
                crate::components::cell_text(&row.text, usize::from(area.width)),
                usize::from(area.width),
                style,
            );
        }
    }
}
pub struct FormWidget<'a> {
    pub form: &'a Form,
    pub styles: &'a Styles,
    pub focused: bool,
}
impl Widget for FormWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let rows = self
            .form
            .layout(usize::from(area.width), usize::from(area.height));
        RowsWidget {
            rows: &rows,
            styles: self.styles,
            focused: self.focused,
        }
        .render(area, buf);
    }
}
