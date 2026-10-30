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
    /// Ignored since 0.4.0; input focus remains owned by the host.
    /// Deprecated in unreleased source after 0.4.0; removal is not scheduled.
    /// Construct with [`MenuWidget::new`] instead.
    #[deprecated(note = "Ignored: menus use selection/open state. Use MenuWidget::new instead.")]
    pub focused: bool,
}
impl<'a> MenuWidget<'a> {
    /// Create a menu renderer without an ineffective focus flag.
    #[allow(deprecated)] // Initialize the source-compatible, ignored legacy field only here.
    pub fn new(model: &'a mut Menu, styles: &'a Styles) -> Self {
        Self {
            model,
            styles,
            ascii: false,
            focused: false,
        }
    }
    /// Select ASCII presentation without changing menu state.
    pub fn ascii(mut self, ascii: bool) -> Self {
        self.ascii = ascii;
        self
    }
}
impl Widget for MenuWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let rows = self
            .model
            .layout(area.width.into(), area.height.into(), self.ascii);
        RowsWidget {
            rows: &rows,
            styles: self.styles,
            focused: false,
        }
        .render(area, buf);
    }
}
pub struct MenuBarWidget<'a> {
    pub model: &'a mut Menu,
    pub styles: &'a Styles,
    /// Ignored since 0.4.0; input focus remains owned by the host.
    /// Deprecated in unreleased source after 0.4.0; removal is not scheduled.
    /// Construct with [`MenuBarWidget::new`] instead.
    #[deprecated(
        note = "Ignored: menus use selection/open state. Use MenuBarWidget::new instead."
    )]
    pub focused: bool,
}
impl<'a> MenuBarWidget<'a> {
    /// Create a menu bar; the menu model determines open/selection state.
    #[allow(deprecated)] // Initialize the source-compatible, ignored legacy field only here.
    pub fn new(model: &'a mut Menu, styles: &'a Styles) -> Self {
        Self {
            model,
            styles,
            focused: false,
        }
    }
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
            focused: false,
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
    /// Ignored since 0.4.0; input focus remains owned by the host.
    /// Deprecated in unreleased source after 0.4.0; removal is not scheduled.
    /// Construct with [`MenuPopupWidget::new`] instead.
    #[deprecated(
        note = "Ignored: menus use selection/open state. Use MenuPopupWidget::new instead."
    )]
    pub focused: bool,
    pub padding: u16,
}
impl<'a> MenuPopupWidget<'a> {
    /// Create a single-border popup with one cell of padding and Unicode drawing.
    #[allow(deprecated)] // Initialize the source-compatible, ignored legacy field only here.
    pub fn new(model: &'a mut Menu, styles: &'a Styles, title: &'a str) -> Self {
        Self {
            model,
            styles,
            title,
            ascii: false,
            focused: false,
            padding: 1,
        }
    }
    /// Select ASCII presentation without changing menu state.
    pub fn ascii(mut self, ascii: bool) -> Self {
        self.ascii = ascii;
        self
    }
    /// Set padding inside the host-assigned popup rectangle.
    pub fn padding(mut self, padding: u16) -> Self {
        self.padding = padding;
        self
    }
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
        let title = crate::components::clean(self.title);
        let block = self
            .styles
            .panel(&title, false, self.padding, self.ascii)
            .expect("menu panel roles");
        let inner = block.inner(area);
        block.render(area, buf);
        MenuWidget::new(self.model, self.styles)
            .ascii(self.ascii)
            .render(inner, buf);
    }
}
