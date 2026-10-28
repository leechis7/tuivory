use super::Styles;
use crate::forms::{ComponentLine, Form};
use ratatui::{buffer::Buffer, layout::Rect, style::Modifier, widgets::Widget};
/// Literal semantic rows; all semantic roles must exist in the supplied palette.
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
            for span in &row.spans {
                let start = span.start.min(usize::from(area.width));
                let width = span.width.min(usize::from(area.width) - start);
                let mut style = self.styles.role(&span.role).expect("span role");
                if span.focused && self.focused {
                    style = style.add_modifier(Modifier::UNDERLINED)
                }
                let x = area.x + start as u16;
                let y = area.y + i as u16;
                for offset in 0..width {
                    buf[(x + offset as u16, y)].set_symbol(" ").set_style(style);
                }
                buf.set_stringn(
                    x,
                    y,
                    crate::components::cell_text(&span.text, width),
                    width,
                    style,
                );
            }
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

pub struct ListWidget<'a> {
    pub model: &'a crate::collections::ListModel,
    pub styles: &'a Styles,
    pub focused: bool,
    pub ascii: bool,
}
impl Widget for ListWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let rows = self
            .model
            .layout(area.width.into(), area.height.into(), self.ascii);
        RowsWidget {
            rows: &rows,
            styles: self.styles,
            focused: self.focused,
        }
        .render(area, buf);
    }
}
pub struct SearchPickerWidget<'a> {
    pub model: &'a crate::collections::SearchPicker,
    pub styles: &'a Styles,
    pub focused: bool,
    pub ascii: bool,
}
impl Widget for SearchPickerWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let rows = self
            .model
            .layout(area.width.into(), area.height.into(), self.ascii);
        RowsWidget {
            rows: &rows,
            styles: self.styles,
            focused: self.focused,
        }
        .render(area, buf);
    }
}

pub struct GridWidget<'a> {
    pub model: &'a crate::grid::Grid,
    pub styles: &'a Styles,
    pub focused: bool,
}
impl Widget for GridWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let rows = self.model.layout(area.width.into(), area.height.into());
        RowsWidget {
            rows: &rows,
            styles: self.styles,
            focused: self.focused,
        }
        .render(area, buf);
    }
}
