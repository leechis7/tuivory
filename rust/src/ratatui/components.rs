use super::Styles;
use crate::components::{
    LineRun, SplitControl, SplitLayout, SplitSide, SplitSpec, SplitState, TabState, Tabs,
    split_glyph,
};
use ::ratatui::{
    buffer::Buffer,
    layout::Rect,
    style::Modifier,
    widgets::{StatefulWidget, Widget},
};

pub struct TabsWidget<'a> {
    tabs: &'a Tabs,
    styles: &'a Styles,
    pub focused: bool,
    drag: Option<&'a mut crate::drag::DragState>,
    ascii: bool,
}
impl<'a> TabsWidget<'a> {
    pub fn new(tabs: &'a Tabs, styles: &'a Styles) -> Result<Self, crate::Error> {
        for role in ["surface", "body", "header", "hint", "selection", "disabled"] {
            styles.role(role)?;
        }
        Ok(Self {
            tabs,
            styles,
            focused: false,
            drag: None,
            ascii: false,
        })
    }
    /// Use ASCII outlines when the terminal cannot display box drawing.
    pub fn with_ascii(mut self, ascii: bool) -> Self {
        self.ascii = ascii;
        self
    }
    pub fn with_drag(mut self, drag: &'a mut crate::drag::DragState, ascii: bool) -> Self {
        self.drag = Some(drag);
        self.ascii = ascii;
        self
    }
}
fn fill(area: Rect, buf: &mut Buffer, styles: &Styles) {
    let style = styles.role("surface").expect("validated component palette");
    for y in area.y..area.bottom() {
        for x in area.x..area.right() {
            buf[(x, y)].set_symbol(" ").set_style(style);
        }
    }
}
impl StatefulWidget for TabsWidget<'_> {
    type State = TabState;
    fn render(mut self, area: Rect, buf: &mut Buffer, state: &mut TabState) {
        fill(area, buf, self.styles);
        let layout = if let Some(d) = self.drag.as_deref_mut() {
            d.render_key(format!(
                "{area:?}/{:?}/{}",
                self.styles.palette.styles(),
                self.ascii
            ));
            self.tabs.drag_layout(state, d, usize::from(area.width))
        } else {
            self.tabs.layout(state, usize::from(area.width))
        };
        if area.height == 0 {
            return;
        }
        let feedback = self
            .drag
            .as_ref()
            .filter(|d| d.phase == "dragging")
            .map(|d| (d.target_id.clone(), d.position, d.allowed));
        let y = area.y + u16::from(area.height >= 3);
        let (edge, dash, tl, tr, bl, br) = if self.ascii {
            ("|", "-", "+", "+", "+", "+")
        } else {
            ("│", "─", "┌", "┐", "┘", "└")
        };
        let border = self.styles.text_on_surface("hint", "surface").unwrap();
        if area.height >= 2 {
            buf.set_stringn(
                area.x,
                y + 1,
                dash.repeat(usize::from(area.width)),
                usize::from(area.width),
                border,
            );
        }
        if layout.previous {
            buf.set_stringn(
                area.x,
                y,
                "<",
                usize::from(area.width),
                self.styles.role("hint").unwrap(),
            );
        }
        if layout.next && area.width > 0 {
            buf.set_stringn(
                area.right() - 1,
                y,
                ">",
                1,
                self.styles.role("hint").unwrap(),
            );
        }
        for cell in layout.cells {
            let role = if cell.disabled { "disabled" } else { "body" };
            let mut style = if cell.active {
                self.styles.role("selection")
            } else {
                self.styles.text_on_surface(role, "surface")
            }
            .unwrap();
            if self.focused && cell.focused {
                style = style.add_modifier(Modifier::UNDERLINED)
            }
            let x = area.x + cell.start as u16;
            buf.set_style(Rect::new(x, y, cell.width as u16, 1), style);
            if cell.width < 4 {
                buf.set_stringn(x, y, &cell.text, cell.width, style);
            } else {
                let mark = if cell.focused { ">" } else { " " };
                let label = cell.text.get(2..).unwrap_or("");
                let label = label
                    .strip_suffix(if cell.active { ']' } else { ' ' })
                    .unwrap_or(label);
                buf.set_stringn(x, y, edge, 1, style);
                buf.set_stringn(x + 1, y, format!("{mark}{label}"), cell.width - 2, style);
                buf.set_stringn(x + cell.width as u16 - 1, y, edge, 1, style);
                if area.height >= 3 {
                    buf.set_stringn(
                        x,
                        area.y,
                        format!("{tl}{}{tr}", dash.repeat(cell.width - 2)),
                        cell.width,
                        border,
                    );
                }
                if area.height >= 2 && cell.active {
                    let surface = self.styles.role("surface").unwrap();
                    buf.set_stringn(x, y + 1, " ".repeat(cell.width), cell.width, surface);
                    buf.set_stringn(x, y + 1, bl, 1, border);
                    buf.set_stringn(x + cell.width as u16 - 1, y + 1, br, 1, border);
                }
            }
            if let Some((target, position, allowed)) = &feedback {
                if *target == cell.id {
                    let column = if *position == Some(crate::drag::DropPosition::After) {
                        x + cell.width.saturating_sub(1) as u16
                    } else {
                        x
                    };
                    let marker = if !allowed {
                        "!"
                    } else if self.ascii {
                        "|"
                    } else {
                        "│"
                    };
                    buf.set_stringn(column, y, marker, 1, self.styles.drag_feedback(*allowed));
                }
            }
        }
        if feedback.as_ref().is_some_and(|f| f.0.is_empty()) && area.width > 0 {
            buf.set_stringn(area.x, y, "!", 1, self.styles.drag_feedback(false));
        }
    }
}

pub struct LineWidget<'a> {
    runs: Vec<LineRun>,
    styles: &'a Styles,
}
impl<'a> LineWidget<'a> {
    pub fn new(runs: Vec<LineRun>, styles: &'a Styles) -> Result<Self, crate::Error> {
        styles.role("surface")?;
        for run in &runs {
            styles.role(&run.role)?;
        }
        Ok(Self { runs, styles })
    }
}
impl Widget for LineWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        fill(area, buf, self.styles);
        if area.height == 0 {
            return;
        }
        for run in self.runs {
            if run.start >= usize::from(area.width) {
                continue;
            }
            buf.set_stringn(
                area.x + run.start as u16,
                area.y,
                &run.text,
                usize::from(area.width) - run.start,
                self.styles.component_role(&run.role).unwrap(),
            );
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct SplitRects {
    pub first: Rect,
    pub divider: Rect,
    pub second: Rect,
    pub compact: bool,
}
pub fn split_rects(
    area: Rect,
    spec: SplitSpec,
    state: &SplitState,
    rows: bool,
    active_second: bool,
) -> SplitRects {
    let layout = spec.layout(
        state,
        usize::from(if rows { area.height } else { area.width }),
    );
    split_layout_rects(area, layout, rows, active_second)
}

/// Compute panel and accessible divider rectangles for an optionally collapsed split.
pub fn split_controlled_rects(
    area: Rect,
    spec: SplitSpec,
    state: &SplitState,
    control: &SplitControl,
    rows: bool,
    active_second: bool,
) -> SplitRects {
    let total = usize::from(if rows { area.height } else { area.width });
    split_layout_rects(
        area,
        control.layout(spec, state, total),
        rows,
        control.visible_focus(active_second),
    )
}

fn split_layout_rects(
    area: Rect,
    layout: SplitLayout,
    rows: bool,
    active_second: bool,
) -> SplitRects {
    let empty = Rect::new(area.x, area.y, 0, 0);
    if layout.compact {
        return SplitRects {
            first: if active_second { empty } else { area },
            second: if active_second { area } else { empty },
            divider: empty,
            compact: true,
        };
    }
    let first = layout.first as u16;
    let second = layout.second as u16;
    if rows {
        SplitRects {
            first: Rect::new(area.x, area.y, area.width, first),
            divider: Rect::new(area.x, area.y.saturating_add(first), area.width, 1),
            second: Rect::new(
                area.x,
                area.y.saturating_add(first).saturating_add(1),
                area.width,
                second,
            ),
            compact: false,
        }
    } else {
        SplitRects {
            first: Rect::new(area.x, area.y, first, area.height),
            divider: Rect::new(area.x.saturating_add(first), area.y, 1, area.height),
            second: Rect::new(
                area.x.saturating_add(first).saturating_add(1),
                area.y,
                second,
                area.height,
            ),
            compact: false,
        }
    }
}

/// Paint the divider and centered action arrow, clipped to the output buffer.
pub fn draw_split_divider(
    area: Rect,
    buf: &mut Buffer,
    styles: &Styles,
    control: &SplitControl,
    rows: bool,
    ascii: bool,
    side: SplitSide,
) -> Result<(), crate::Error> {
    let style = styles.role(if control.dragging() {
        "focus.border"
    } else {
        "hint"
    })?;
    let clip = area.intersection(buf.area);
    let grip = if rows {
        area.x.saturating_add(area.width / 2)
    } else {
        area.y.saturating_add(area.height / 2)
    };
    for y in clip.y..clip.bottom() {
        for x in clip.x..clip.right() {
            let glyph = split_glyph(
                rows,
                ascii,
                if rows { x == grip } else { y == grip },
                side,
                control.collapsed(),
            );
            buf[(x, y)].set_char(glyph).set_style(style);
        }
    }
    Ok(())
}
