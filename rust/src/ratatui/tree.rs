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
    drag: Option<&'a mut crate::drag::DragState>,
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
            drag: None,
        })
    }
    pub fn with_drag(mut self, drag: &'a mut crate::drag::DragState) -> Self {
        self.drag = Some(drag);
        self
    }
}
fn clean(text: &str) -> String {
    text.chars()
        .map(|c| if c.is_control() { ' ' } else { c })
        .collect()
}
impl StatefulWidget for TreeWidget<'_> {
    type State = TreeState;
    fn render(mut self, area: Rect, buf: &mut Buffer, state: &mut TreeState) {
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
        let (rows, scroll) = if let Some(d) = self.drag.as_deref_mut() {
            d.render_key(format!(
                "{area:?}/{:?}/{}",
                self.styles.palette.styles(),
                self.ascii
            ));
            self.tree.drag_rows(state, d, usize::from(area.height))
        } else {
            let rows = self.tree.reconcile(state, usize::from(area.height));
            (rows, state.scroll)
        };
        let feedback = self
            .drag
            .as_ref()
            .filter(|d| d.phase == "dragging")
            .map(|d| (d.target_id.clone(), d.position, d.allowed));
        for (line, row) in rows
            .iter()
            .skip(scroll)
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
            if let Some((target, position, allowed)) = &feedback {
                if *target == node.id && area.width > 0 {
                    let marker = if !allowed {
                        "!"
                    } else {
                        match (self.ascii, position) {
                            (true, Some(crate::drag::DropPosition::Before)) => "^",
                            (true, Some(crate::drag::DropPosition::Inside)) => "+",
                            (true, _) => "v",
                            (false, Some(crate::drag::DropPosition::Before)) => "↑",
                            (false, Some(crate::drag::DropPosition::Inside)) => "↳",
                            _ => "↓",
                        }
                    };
                    buf.set_stringn(area.x, y, marker, 1, self.styles.drag_feedback(*allowed));
                }
            }
        }
        if feedback.as_ref().is_some_and(|f| f.0.is_empty()) && area.width > 0 && area.height > 0 {
            buf.set_stringn(area.x, area.y, "!", 1, self.styles.drag_feedback(false));
        }
    }
}
