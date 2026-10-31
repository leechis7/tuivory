use super::{Styles, shadow::repair_edges};
use ratatui::{
    buffer::Buffer,
    layout::{Margin, Rect},
    widgets::Widget,
};

/// Opaque borderless surface. The host supplies placement and routes input.
pub struct SurfaceWidget<'a, W> {
    child: W,
    styles: &'a Styles,
    padding: u16,
}
impl<'a, W> SurfaceWidget<'a, W> {
    pub fn new(child: W, styles: &'a Styles) -> Self {
        Self {
            child,
            styles,
            padding: 0,
        }
    }
    pub fn padding(mut self, cells: u16) -> Self {
        self.padding = cells;
        self
    }
}
impl<W: Widget> Widget for SurfaceWidget<'_, W> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let area = area.intersection(buf.area);
        if area.is_empty() {
            return;
        }
        let style = self.styles.role("surface").expect("surface role");
        for y in area.y..area.bottom() {
            repair_edges(buf, area, y);
            for x in area.x..area.right() {
                buf[(x, y)].reset();
                buf[(x, y)].set_style(style);
            }
        }
        self.child
            .render(area.inner(Margin::new(self.padding, self.padding)), buf);
    }
}

/// Executes a language-neutral layout and clips each child to its viewport.
/// The factory chooses widgets by stable ID; it does not compute placement.
pub struct ContainerWidget<'a, F> {
    pub items: &'a [crate::containers::LayoutItem],
    pub options: &'a crate::containers::ContainerOptions,
    pub styles: &'a Styles,
    pub scroll_x: usize,
    pub scroll_y: usize,
    pub render_child: F,
}
impl<F: FnMut(&str, Rect, &mut Buffer)> Widget for ContainerWidget<'_, F> {
    fn render(mut self, area: Rect, buf: &mut Buffer) {
        let area = area.intersection(buf.area);
        if area.is_empty() {
            return;
        }
        let bounds = crate::layout::CellRect {
            x: area.x.into(),
            y: area.y.into(),
            width: (area.width as usize).max(self.options.virtual_width),
            height: (area.height as usize).max(self.options.virtual_height),
        };
        let Ok(rects) = crate::containers::compute_container(bounds, self.items, self.options)
        else {
            return;
        };
        let sx = self.scroll_x.min(bounds.width - area.width as usize);
        let sy = self.scroll_y.min(bounds.height - area.height as usize);
        if bounds.x + bounds.width > u16::MAX as usize
            || bounds.y + bounds.height > u16::MAX as usize
            || bounds.width.saturating_mul(bounds.height) > 1000000
        {
            return;
        }
        let canvas_area = Rect::new(area.x, area.y, bounds.width as u16, bounds.height as u16);
        let mut canvas = Buffer::empty(canvas_area);
        let style = self.styles.role("surface").expect("surface role");
        canvas.set_style(canvas_area, style);
        for r in rects {
            let clip = Rect::new(
                r.rect.x as u16,
                r.rect.y as u16,
                r.rect.width as u16,
                r.rect.height as u16,
            )
            .intersection(canvas_area);
            if clip.is_empty() {
                continue;
            }
            for y in clip.y..clip.bottom() {
                repair_edges(&mut canvas, clip, y)
            }
            let mut child = Buffer::empty(clip);
            for y in clip.y..clip.bottom() {
                for x in clip.x..clip.right() {
                    child[(x, y)] = canvas[(x, y)].clone();
                }
            }
            (self.render_child)(&r.id, clip, &mut child);
            for y in clip.y..clip.bottom() {
                repair_edges(&mut child, clip, y);
                for x in clip.x..clip.right() {
                    canvas[(x, y)] = child[(x, y)].clone();
                }
            }
        }
        let source = Rect::new(
            area.x + sx as u16,
            area.y + sy as u16,
            area.width,
            area.height,
        );
        for y in source.y..source.bottom() {
            repair_edges(&mut canvas, source, y)
        }
        for y in area.y..area.bottom() {
            repair_edges(buf, area, y);
            for x in area.x..area.right() {
                buf[(x, y)] = canvas[(x + sx as u16, y + sy as u16)].clone();
            }
        }
    }
}
