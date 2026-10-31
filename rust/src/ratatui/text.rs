use super::{RowsWidget, Styles};
use crate::text::TextDocument;
use ratatui::{buffer::Buffer, layout::Rect, widgets::Widget};
pub struct TextWidget<'a> {
    pub model: &'a mut TextDocument,
    pub styles: &'a Styles,
    pub focused: bool,
}
impl Widget for TextWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let rows = self.model.layout(area.width as usize, area.height as usize);
        RowsWidget {
            rows: &rows,
            styles: self.styles,
            focused: self.focused,
        }
        .render(area, buf)
    }
}
pub struct ControlWidget<'a> {
    pub model: &'a crate::controls::Control,
    pub styles: &'a Styles,
    pub focused: bool,
}
impl Widget for ControlWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let rows = self.model.layout(area.width as usize, area.height as usize);
        RowsWidget {
            rows: &rows,
            styles: self.styles,
            focused: self.focused,
        }
        .render(area, buf)
    }
}
