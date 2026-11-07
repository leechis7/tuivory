//! Confirmation dialog state and button geometry. The host handles requests.
use crate::{
    Error,
    components::{cell_text, cells, clean},
    layout::CellRect,
};
use std::collections::HashSet;
use unicode_segmentation::UnicodeSegmentation;

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct DialogButton {
    pub id: String,
    pub label: String,
    pub disabled: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DialogButtonCell {
    pub id: String,
    pub rect: CellRect,
    pub text: String,
    pub disabled: bool,
    pub focused: bool,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct DialogLayout {
    pub body: Vec<String>,
    pub buttons: Vec<DialogButtonCell>,
    pub hidden_buttons: usize,
    pub body_truncated: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DialogEvent {
    Activate(String),
    Cancel(String),
    Focus(String),
}

#[derive(Clone, Debug)]
pub struct Dialog {
    title: String,
    message: String,
    buttons: Vec<DialogButton>,
    cancel: String,
    focused: String,
}

impl Dialog {
    pub fn new(
        title: impl Into<String>,
        message: impl Into<String>,
        buttons: Vec<DialogButton>,
        cancel: &str,
    ) -> Result<Self, Error> {
        let mut dialog = Self {
            title: title.into(),
            message: message.into(),
            buttons: Vec::new(),
            cancel: String::new(),
            focused: String::new(),
        };
        dialog.set_buttons(buttons, cancel)?;
        Ok(dialog)
    }

    pub fn title(&self) -> &str {
        &self.title
    }

    pub fn focused(&self) -> &str {
        &self.focused
    }

    pub fn set_text(&mut self, title: impl Into<String>, message: impl Into<String>) {
        self.title = title.into();
        self.message = message.into();
    }

    pub fn set_buttons(&mut self, buttons: Vec<DialogButton>, cancel: &str) -> Result<(), Error> {
        let mut ids = HashSet::new();
        if buttons.len() > 1024
            || buttons
                .iter()
                .any(|button| button.id.is_empty() || !ids.insert(&button.id))
            || (!cancel.is_empty() && !ids.iter().any(|id| id.as_str() == cancel))
        {
            return Err(Error::Invalid("invalid dialog buttons or cancel ID".into()));
        }
        let enabled = |id: &str| {
            buttons
                .iter()
                .find(|button| button.id == id && !button.disabled)
        };
        self.focused = enabled(&self.focused)
            .or_else(|| enabled(cancel))
            .or_else(|| buttons.iter().find(|button| !button.disabled))
            .map(|button| button.id.clone())
            .unwrap_or_default();
        self.cancel = cancel.into();
        self.buttons = buttons;
        Ok(())
    }

    pub fn focus(&mut self, id: &str) -> bool {
        if !self
            .buttons
            .iter()
            .any(|button| button.id == id && !button.disabled)
        {
            return false;
        }
        self.focused = id.into();
        true
    }

    pub fn handle(&mut self, action: &str) -> Option<DialogEvent> {
        match action {
            "activate" if !self.focused.is_empty() => {
                Some(DialogEvent::Activate(self.focused.clone()))
            }
            "cancel" => self
                .buttons
                .iter()
                .find(|b| b.id == self.cancel && !b.disabled)
                .map(|b| DialogEvent::Cancel(b.id.clone())),
            "next" | "previous" | "left" | "right" | "up" | "down" => {
                let enabled: Vec<_> = self.buttons.iter().filter(|b| !b.disabled).collect();
                let current = enabled.iter().position(|b| b.id == self.focused)?;
                if enabled.len() == 1 {
                    return None;
                }
                let next = if matches!(action, "previous" | "left" | "up") {
                    (current + enabled.len() - 1) % enabled.len()
                } else {
                    (current + 1) % enabled.len()
                };
                self.focused.clone_from(&enabled[next].id);
                Some(DialogEvent::Focus(self.focused.clone()))
            }
            _ => None,
        }
    }

    /// Route a click against the button rectangles returned by the last draw.
    pub fn click(&mut self, layout: &DialogLayout, x: usize, y: usize) -> Option<DialogEvent> {
        let button = layout.buttons.iter().find(|button| {
            !button.disabled
                && button.rect.y == y
                && x.checked_sub(button.rect.x)
                    .is_some_and(|offset| offset < button.rect.width)
        })?;
        self.focus(&button.id)
            .then(|| DialogEvent::Activate(button.id.clone()))
    }

    /// Lay out body and button cells inside the provided content area.
    pub fn layout(&self, area: CellRect) -> DialogLayout {
        let labels: Vec<_> = self
            .buttons
            .iter()
            .map(|button| {
                clean(if button.label.is_empty() {
                    &button.id
                } else {
                    &button.label
                })
            })
            .collect();
        let positions = popup_button_rects(
            area.width,
            labels.iter().map(|label| cells(label).saturating_add(4)),
        );
        let total_rows = positions.last().map_or(0, |rect| rect.y + 1);
        let visible = total_rows.min(area.height);
        let focus_row = self
            .buttons
            .iter()
            .position(|button| button.id == self.focused)
            .and_then(|index| positions.get(index))
            .map_or(0, |rect| rect.y);
        let start = (focus_row + 1).saturating_sub(visible);
        let available = area.height - visible;
        let gap = usize::from(!self.message.is_empty() && visible > 0 && available >= 2);
        let (body, body_truncated) = wrap(&self.message, area.width, available - gap);
        let buttons: Vec<_> = self
            .buttons
            .iter()
            .zip(labels)
            .zip(positions)
            .filter(|(_, rect)| (start..start + visible).contains(&rect.y))
            .map(|((button, label), rect)| {
                let text = if rect.width >= 6 {
                    format!("[ {} ]", cell_text(&label, rect.width - 4))
                } else {
                    cell_text(&label, rect.width)
                };
                DialogButtonCell {
                    id: button.id.clone(),
                    rect: CellRect {
                        x: area.x.saturating_add(rect.x),
                        y: area
                            .y
                            .saturating_add(area.height - visible + rect.y - start),
                        ..rect
                    },
                    text,
                    disabled: button.disabled,
                    focused: button.id == self.focused,
                }
            })
            .collect();
        DialogLayout {
            body,
            hidden_buttons: self.buttons.len() - buttons.len(),
            buttons,
            body_truncated,
        }
    }
}

/// Wrap button widths with a one-cell gap and center each row in the content width.
/// Rectangles are local to the content area and use contiguous row indices.
pub fn popup_button_rects(width: usize, widths: impl IntoIterator<Item = usize>) -> Vec<CellRect> {
    if width == 0 {
        return Vec::new();
    }
    let mut rects: Vec<CellRect> = Vec::new();
    let (mut start, mut used, mut row) = (0, 0, 0);
    for requested in widths {
        let w = requested.clamp(1, width);
        if used > 0 && w >= width - used {
            for rect in &mut rects[start..] {
                rect.x += (width - used) / 2;
            }
            start = rects.len();
            used = 0;
            row += 1;
        }
        used += usize::from(used > 0);
        rects.push(CellRect {
            x: used,
            y: row,
            width: w,
            height: 1,
        });
        used += w;
    }
    for rect in &mut rects[start..] {
        rect.x += (width - used) / 2;
    }
    rects
}

fn wrap(text: &str, width: usize, limit: usize) -> (Vec<String>, bool) {
    if text.is_empty() || width == 0 || limit == 0 {
        return (Vec::new(), !text.is_empty());
    }
    let mut rows = Vec::new();
    let mut line = String::new();
    let mut used = 0;
    let mut truncated = false;
    for grapheme in text.graphemes(true) {
        let newline = matches!(grapheme, "\n" | "\r" | "\r\n");
        let glyph = cell_text(grapheme, width);
        let glyph_width = cells(&glyph);
        if newline || used > width - glyph_width {
            rows.push(std::mem::take(&mut line));
            used = 0;
            if rows.len() == limit {
                truncated = true;
                break;
            }
        }
        if !newline {
            line.push_str(&glyph);
            used += glyph_width;
        }
    }
    if truncated {
        let last = rows.last_mut().expect("positive row limit");
        let clipped = cell_text(last, width - 1);
        *last = if width > 1 && cells(last) > width - 1 {
            clipped
        } else {
            format!("{clipped}~")
        };
    } else {
        rows.push(line);
    }
    (rows, truncated)
}
