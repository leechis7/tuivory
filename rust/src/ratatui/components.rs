use super::Styles;
use crate::components::{LineRun, SplitSpec, SplitState, TabState, Tabs};
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
        })
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
    fn render(self, area: Rect, buf: &mut Buffer, state: &mut TabState) {
        fill(area, buf, self.styles);
        if area.height == 0 {
            return;
        }
        let layout = self.tabs.layout(state, usize::from(area.width));
        if layout.previous {
            buf.set_stringn(
                area.x,
                area.y,
                "<",
                usize::from(area.width),
                self.styles.role("hint").unwrap(),
            );
        }
        if layout.next && area.width > 0 {
            buf.set_stringn(
                area.right() - 1,
                area.y,
                ">",
                1,
                self.styles.role("hint").unwrap(),
            );
        }
        for cell in layout.cells {
            let role = if cell.disabled {
                "disabled"
            } else if cell.active {
                "header"
            } else {
                "body"
            };
            let mut style = self.styles.role(role).unwrap();
            if self.focused && cell.focused {
                style = self
                    .styles
                    .role("selection")
                    .unwrap()
                    .add_modifier(Modifier::UNDERLINED)
            }
            let x = area.x + cell.start as u16;
            buf.set_style(Rect::new(x, area.y, cell.width as u16, 1), style);
            buf.set_stringn(x, area.y, &cell.text, cell.width, style);
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
                self.styles.role(&run.role).unwrap(),
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
            divider: Rect::new(area.x, area.y + first, area.width, 1),
            second: Rect::new(area.x, area.y + first + 1, area.width, second),
            compact: false,
        }
    } else {
        SplitRects {
            first: Rect::new(area.x, area.y, first, area.height),
            divider: Rect::new(area.x + first, area.y, 1, area.height),
            second: Rect::new(area.x + first + 1, area.y, second, area.height),
            compact: false,
        }
    }
}
