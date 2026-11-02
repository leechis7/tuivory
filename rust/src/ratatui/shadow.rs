use super::Styles;
use crate::{
    Color,
    layout::CellRect,
    popup::{PopupLayout, ShadowMode, ShadowOptions},
};
use ratatui::{
    buffer::Buffer,
    layout::Rect,
    style::{Modifier, Style},
    widgets::Widget,
};

/// Any widget with a visual-only shadow inside its assigned allocation.
/// The wrapped widget gets only the card rectangle. Hosts own hit testing/redraws.
pub struct ShadowWidget<'a, W> {
    widget: W,
    styles: &'a Styles,
    options: ShadowOptions,
    ascii: bool,
}
impl<'a, W> ShadowWidget<'a, W> {
    pub fn new(widget: W, styles: &'a Styles, options: ShadowOptions) -> Self {
        Self {
            widget,
            styles,
            options,
            ascii: false,
        }
    }
    pub fn ascii(mut self, ascii: bool) -> Self {
        self.ascii = ascii;
        self
    }
}
fn rect(r: CellRect) -> Rect {
    Rect::new(r.x as u16, r.y as u16, r.width as u16, r.height as u16)
}
impl<W: Widget> Widget for ShadowWidget<'_, W> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let area = area.intersection(buf.area);
        if area.is_empty() {
            return;
        }
        let layout: PopupLayout = self.options.layout(CellRect {
            x: area.x.into(),
            y: area.y.into(),
            width: area.width.into(),
            height: area.height.into(),
        });
        for region in layout.shadow_regions() {
            if matches!(self.options.mode, ShadowMode::Auto | ShadowMode::Solid) {
                draw_half_shadow(
                    buf,
                    rect(region),
                    layout,
                    self.styles,
                    self.options.mode,
                    self.ascii,
                );
            } else if self.options.mode == ShadowMode::Dim {
                draw_shadow(buf, rect(region));
            }
        }
        let card = rect(layout.card);
        if self.options.mode != ShadowMode::Off && !card.is_empty() {
            for y in card.y..card.bottom() {
                repair_edges(buf, card, y);
            }
        }
        self.widget.render(card, buf);
    }
}
fn rgb(c: Color) -> (u8, u8, u8) {
    match c {
        Color::Rgb(r, g, b) => (r, g, b),
        Color::Indexed(n) => {
            const ANSI: [(u8, u8, u8); 16] = [
                (0, 0, 0),
                (128, 0, 0),
                (0, 128, 0),
                (128, 128, 0),
                (0, 0, 128),
                (128, 0, 128),
                (0, 128, 128),
                (192, 192, 192),
                (128, 128, 128),
                (255, 0, 0),
                (0, 255, 0),
                (255, 255, 0),
                (0, 0, 255),
                (255, 0, 255),
                (0, 255, 255),
                (255, 255, 255),
            ];
            if n < 16 {
                ANSI[n as usize]
            } else if n >= 232 {
                let v = 8 + (n - 232) * 10;
                (v, v, v)
            } else {
                let n = n - 16;
                let s = [0, 95, 135, 175, 215, 255];
                (
                    s[(n / 36) as usize],
                    s[(n / 6 % 6) as usize],
                    s[(n % 6) as usize],
                )
            }
        }
    }
}

fn backdrop_color(c: ratatui::style::Color, styles: &Styles) -> Color {
    use ratatui::style::Color as C;
    let index = match c {
        C::Rgb(r, g, b) => return Color::Rgb(r, g, b),
        C::Indexed(n) => return Color::Indexed(n),
        C::Black => 0,
        C::Red => 1,
        C::Green => 2,
        C::Yellow => 3,
        C::Blue => 4,
        C::Magenta => 5,
        C::Cyan => 6,
        C::Gray => 7,
        C::DarkGray => 8,
        C::LightRed => 9,
        C::LightGreen => 10,
        C::LightYellow => 11,
        C::LightBlue => 12,
        C::LightMagenta => 13,
        C::LightCyan => 14,
        C::White => 15,
        C::Reset => {
            return styles
                .palette
                .style("surface")
                .expect("surface role")
                .background;
        }
    };
    Color::Indexed(index)
}

fn half_shadow_color(backdrop: Color, styles: &Styles) -> Color {
    let (r, g, b) = rgb(backdrop);
    let colors = styles
        .palette
        .styles()
        .values()
        .flat_map(|p| [p.foreground, p.background]);
    let has_rgb = colors.clone().any(|c| matches!(c, Color::Rgb(..)));
    let has_256 = colors
        .into_iter()
        .any(|c| matches!(c, Color::Indexed(16..=255)));
    if r.max(g).max(b) <= 16 {
        return if has_rgb {
            Color::Rgb(64, 64, 64)
        } else if has_256 {
            Color::Indexed(238)
        } else {
            Color::Indexed(7)
        };
    }
    let factor = if r.max(g).max(b) <= 96 { 2 } else { 4 };
    if has_rgb {
        Color::Rgb(
            (r as u16 * factor / 5) as u8,
            (g as u16 * factor / 5) as u8,
            (b as u16 * factor / 5) as u8,
        )
    } else if has_256 {
        let gray = (r as i32 + g as i32 + b as i32) * factor as i32 / 15;
        Color::Indexed((232 + ((gray - 8 + 5) / 10).clamp(0, 23)) as u8)
    } else {
        Color::Indexed(0)
    }
}

fn draw_half_shadow(
    buf: &mut Buffer,
    region: Rect,
    layout: PopupLayout,
    styles: &Styles,
    mode: ShadowMode,
    ascii: bool,
) {
    let area = region.intersection(buf.area);
    if area.is_empty() {
        return;
    }
    for y in area.y..area.bottom() {
        // Ratatui resets wide continuation cells. A terminal still shows the
        // leading cell's background across both columns; capture it before
        // repairing/overwriting either half of the grapheme.
        let backgrounds: Vec<_> = (area.x..area.right())
            .map(|x| {
                let source =
                    if x > buf.area.x && crate::components::cells(buf[(x - 1, y)].symbol()) > 1 {
                        x - 1
                    } else {
                        x
                    };
                backdrop_color(buf[(source, y)].bg, styles)
            })
            .collect();
        repair_edges(buf, area, y);
        for x in area.x..area.right() {
            let bg: ratatui::style::Color = backgrounds[(x - area.x) as usize].into();
            let shade: ratatui::style::Color = if mode == ShadowMode::Solid {
                Color::Indexed(0)
            } else {
                half_shadow_color(backdrop_color(bg, styles), styles)
            }
            .into();
            let (mut symbol, mut style) = (" ", Style::default().bg(shade));
            if ascii {
                symbol = ".";
                style = Style::default().fg(shade).bg(bg);
            } else if layout.shadow.height > layout.card.height {
                if y as usize == layout.shadow.y {
                    symbol = "▄";
                    style = Style::default().fg(shade).bg(bg);
                } else if y as usize == layout.shadow.y.saturating_add(layout.shadow.height) - 1 {
                    symbol = "▀";
                    style = Style::default().fg(shade).bg(bg);
                }
            }
            buf[(x, y)].reset();
            buf[(x, y)].set_symbol(symbol).set_style(style);
        }
    }
}
// Clear an intersected whole grapheme, retaining every cell's original style.
fn clear_wide(buf: &mut Buffer, x: u16, y: u16) {
    let width = crate::components::cells(buf[(x, y)].symbol());
    for n in 0..width {
        if (x as usize) + n >= buf.area.right() as usize {
            break;
        };
        buf[(x + n as u16, y)].set_symbol(" ");
    }
}
pub(super) fn repair_edges(buf: &mut Buffer, area: Rect, y: u16) {
    if area.x > buf.area.x && crate::components::cells(buf[(area.x - 1, y)].symbol()) > 1 {
        clear_wide(buf, area.x - 1, y)
    }
    let last = area.right() - 1;
    if crate::components::cells(buf[(last, y)].symbol()) > 1 {
        clear_wide(buf, last, y)
    }
}
fn draw_shadow(buf: &mut Buffer, area: Rect) {
    let area = area.intersection(buf.area);
    if area.is_empty() {
        return;
    }
    for y in area.y..area.bottom() {
        repair_edges(buf, area, y);
        for x in area.x..area.right() {
            buf[(x, y)].modifier.insert(Modifier::DIM);
        }
    }
}
