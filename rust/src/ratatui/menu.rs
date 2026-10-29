use super::{RowsWidget, Styles};
use crate::{
    forms::{ComponentLine, ComponentSpan},
    menu::Menu,
};
use ratatui::{buffer::Buffer, layout::Rect, widgets::Widget};
/// Render a single menu level inside a host-owned panel; terminal/focus is host-owned.
pub struct MenuWidget<'a> {
    pub model: &'a mut Menu,
    pub styles: &'a Styles,
    pub ascii: bool,
    pub focused: bool,
}
impl Widget for MenuWidget<'_> {
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
pub struct MenuBarWidget<'a> {
    pub model: &'a mut Menu,
    pub styles: &'a Styles,
    pub focused: bool,
}
impl Widget for MenuBarWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        if area.height == 0 {
            return;
        }
        let l = self.model.bar_layout(area.width.into());
        let mut line = ComponentLine {
            role: "header".into(),
            ..Default::default()
        };
        if l.previous {
            line.text = "<".into()
        }
        for c in l.cells {
            line.spans.push(ComponentSpan {
                start: c.start,
                width: c.width,
                text: c.text,
                role: c.role,
                focused: c.focused,
            });
        }
        if l.next && area.width > 0 {
            line.spans.push(ComponentSpan {
                start: usize::from(area.width - 1),
                width: 1,
                text: ">".into(),
                role: "hint".into(),
                focused: false,
            });
        }
        RowsWidget {
            rows: &[line],
            styles: self.styles,
            focused: self.focused,
        }
        .render(Rect { height: 1, ..area }, buf);
    }
}
/// A reusable menu popup surface/border, clipped to the host-assigned area.
/// Pre-clearing through RowsWidget repairs background glyphs at both edges.
pub struct MenuPopupWidget<'a> {
    pub model: &'a mut Menu,
    pub styles: &'a Styles,
    pub title: &'a str,
    pub ascii: bool,
    pub focused: bool,
    pub padding: u16,
}
impl Widget for MenuPopupWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let area = area.intersection(buf.area);
        if area.is_empty() {
            return;
        }
        RowsWidget {
            rows: &[],
            styles: self.styles,
            focused: false,
        }
        .render(area, buf);
        let clean_title = crate::components::clean(self.title);
        let title = if self.focused {
            format!("> {clean_title}")
        } else {
            clean_title
        };
        // Build the title once; Styles::panel's focused title is additive.
        let mut block = self
            .styles
            .panel(&title, false, self.padding, self.ascii)
            .expect("menu panel roles");
        if self.focused {
            if !self.ascii {
                block = block.border_type(ratatui::widgets::BorderType::Double);
            }
            block = block.border_style(
                self.styles
                    .role("focus.border")
                    .expect("menu focus role")
                    .add_modifier(ratatui::style::Modifier::BOLD),
            );
        }
        let inner = block.inner(area);
        block.render(area, buf);
        MenuWidget {
            model: self.model,
            styles: self.styles,
            ascii: self.ascii,
            focused: self.focused,
        }
        .render(inner, buf);
    }
}
