//! A stateful Ratatui tree renderer. The host routes keys/mouse into Tree actions.
use super::Styles;
use crate::tree::{Tree, TreeState};
use ::ratatui::{
    buffer::Buffer,
    layout::Rect,
    style::{Modifier, Style},
    text::{Line, Span},
    widgets::{Paragraph, StatefulWidget, Widget},
};

pub struct TreeWidget<'a> {
    tree: &'a Tree,
    styles: &'a Styles,
    pub focused: bool,
    pub ascii: bool,
}
impl<'a> TreeWidget<'a> {
    pub fn new(tree: &'a Tree, styles: &'a Styles) -> Result<Self, crate::Error> {
        for role in ["surface", "hint", "selection"] {
            styles.role(role)?;
        }
        Ok(Self {
            tree,
            styles,
            focused: false,
            ascii: false,
        })
    }
}
fn clean(text: &str) -> String {
    text.chars()
        .map(|c| if c.is_control() { ' ' } else { c })
        .collect()
}
impl StatefulWidget for TreeWidget<'_> {
    type State = TreeState;
    fn render(self, area: Rect, buf: &mut Buffer, state: &mut TreeState) {
        let surface = self.styles.role("surface").expect("validated tree palette");
        let hint = self
            .styles
            .role("hint")
            .expect("validated tree palette")
            .bg(surface.bg.unwrap());
        let selection = self
            .styles
            .role("selection")
            .expect("validated tree palette");
        buf.set_style(area, surface);
        for y in area.y..area.bottom() {
            for x in area.x..area.right() {
                buf[(x, y)].set_symbol(" ");
            }
        }
        let rows = self.tree.reconcile(state, usize::from(area.height));
        for (line, row) in rows
            .iter()
            .skip(state.scroll)
            .take(usize::from(area.height))
            .enumerate()
        {
            let selected = row.node.id == state.selected;
            let style = if selected {
                if self.focused {
                    selection.add_modifier(Modifier::UNDERLINED)
                } else {
                    selection
                }
            } else {
                surface
            };
            let y = area.y + line as u16;
            buf.set_style(Rect::new(area.x, y, area.width, 1), style);
            buf.set_stringn(
                area.x,
                y,
                if selected { "> " } else { "  " },
                usize::from(area.width),
                style,
            );
            let node = &row.node;
            let arrow = if node.branch {
                match (self.ascii, state.expanded.contains(&node.id)) {
                    (true, true) => "v",
                    (true, false) => ">",
                    (false, true) => "▾",
                    (false, false) => "▸",
                }
            } else if self.ascii {
                "."
            } else {
                "·"
            };
            let icon = if self.ascii {
                &node.ascii_icon
            } else {
                &node.icon
            };
            let mut primary = format!("{}{arrow} ", " ".repeat(row.depth * 2));
            if !icon.is_empty() {
                primary.push_str(&clean(icon));
                primary.push(' ');
            }
            primary.push_str(&clean(&node.name));
            if let Some(count) = node.count {
                primary.push_str(&format!(" ({count})"));
            }
            let secondary = if selected { style } else { hint };
            let text = Line::from(vec![
                Span::styled(primary, style),
                Span::styled(format!("  {}", clean(&node.secondary)), secondary),
            ]);
            Paragraph::new(text)
                .style(Style::default())
                .scroll((0, state.horizontal.min(u16::MAX as usize) as u16))
                .render(
                    Rect::new(
                        area.x + area.width.min(2),
                        y,
                        area.width.saturating_sub(2),
                        1,
                    ),
                    buf,
                );
        }
    }
}
