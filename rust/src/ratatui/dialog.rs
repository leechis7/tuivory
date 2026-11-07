use super::{RowsWidget, Styles};
use crate::{
    components::{cells, clean},
    dialog::{Dialog, DialogLayout},
    forms::{ComponentLine, ComponentSpan},
    layout::CellRect,
};
use ratatui::{buffer::Buffer, layout::Rect, widgets::Widget};

/// Draw a confirmation panel using the dialog's button rectangles.
pub struct DialogWidget<'a> {
    pub dialog: &'a Dialog,
    pub styles: &'a Styles,
    pub focused: bool,
    pub ascii: bool,
}

impl DialogWidget<'_> {
    /// Draw and return absolute hit rectangles for this frame.
    pub fn draw(self, area: Rect, buffer: &mut Buffer) -> DialogLayout {
        let area = area.intersection(buffer.area);
        let title = clean(self.dialog.title());
        let panel = self
            .styles
            .panel(&title, self.focused, 1, self.ascii)
            .expect("validated panel styles");
        let inner = panel.inner(area);
        panel.render(area, buffer);
        let layout = self.dialog.layout(CellRect {
            x: inner.x.into(),
            y: inner.y.into(),
            width: inner.width.into(),
            height: inner.height.into(),
        });
        let mut rows = vec![
            ComponentLine {
                role: "body".into(),
                ..Default::default()
            };
            inner.height.into()
        ];
        for (row, text) in rows.iter_mut().zip(&layout.body) {
            row.text.clone_from(text);
        }
        for button in &layout.buttons {
            let pad = button.rect.width.saturating_sub(cells(&button.text)) / 2;
            rows[button.rect.y - usize::from(inner.y)]
                .spans
                .push(ComponentSpan {
                    start: button.rect.x - usize::from(inner.x),
                    width: button.rect.width,
                    text: format!("{}{text}", " ".repeat(pad), text = button.text),
                    role: if button.disabled {
                        "disabled"
                    } else if button.focused && self.focused {
                        "button.focus"
                    } else {
                        "button"
                    }
                    .into(),
                    focused: false,
                });
        }
        RowsWidget {
            rows: &rows,
            styles: self.styles,
            focused: self.focused,
        }
        .render(inner, buffer);
        layout
    }
}

impl Widget for DialogWidget<'_> {
    fn render(self, area: Rect, buffer: &mut Buffer) {
        self.draw(area, buffer);
    }
}
