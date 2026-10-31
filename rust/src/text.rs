//! Literal text editing; offsets are extended grapheme indices, not bytes.
use crate::{
    components::{cell_text, cells},
    forms::{ComponentLine, ComponentSpan},
    interaction::ControlState,
};
use std::fmt;
use unicode_segmentation::UnicodeSegmentation;
pub(crate) fn text_role(role: &str) -> bool {
    [
        "body",
        "hint",
        "info",
        "success",
        "warning",
        "error",
        "header",
        "field",
        "selection",
        "button",
        "disabled",
        "edited",
    ]
    .contains(&role)
}
fn text_break(s: &str) -> bool {
    ["\n", "\r\n", "\r"].contains(&s)
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct TextEvent {
    pub kind: String,
    pub text: String,
}
#[derive(Clone)]
struct Snapshot {
    text: String,
    cursor: usize,
    anchor: usize,
}
#[derive(Clone)]
pub struct TextBuffer {
    text: String,
    pub cursor: usize,
    pub anchor: usize,
    pub state: ControlState,
    pub secret: bool,
    pub single_line: bool,
    undo: Vec<Snapshot>,
    redo: Vec<Snapshot>,
}
impl fmt::Debug for TextBuffer {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("TextBuffer")
            .field("text", &self.display())
            .field("cursor", &self.cursor)
            .field("anchor", &self.anchor)
            .finish()
    }
}
impl TextBuffer {
    pub fn new(text: &str) -> Self {
        let n = text.graphemes(true).count();
        Self {
            text: text.into(),
            cursor: n,
            anchor: n,
            state: ControlState::default(),
            secret: false,
            single_line: false,
            undo: vec![],
            redo: vec![],
        }
    }
    pub fn text(&self) -> &str {
        &self.text
    }
    pub fn display(&self) -> String {
        if self.secret {
            "*".repeat(self.text.graphemes(true).count())
        } else {
            self.text.clone()
        }
    }
    pub fn set_text(&mut self, text: &str) {
        self.text = text.into();
        self.cursor = text.graphemes(true).count();
        self.anchor = self.cursor;
        self.undo.clear();
        self.redo.clear()
    }
    pub fn select(&mut self, anchor: usize, cursor: usize) {
        let n = self.text.graphemes(true).count();
        self.anchor = anchor.min(n);
        self.cursor = cursor.min(n)
    }
    pub fn selection(&self) -> (usize, usize) {
        let n = self.text.graphemes(true).count();
        (
            self.anchor.min(self.cursor).min(n),
            self.anchor.max(self.cursor).min(n),
        )
    }
    pub fn cursor_byte(&self) -> usize {
        self.text
            .graphemes(true)
            .take(self.cursor)
            .map(str::len)
            .sum()
    }
    fn snapshot(&self) -> Snapshot {
        Snapshot {
            text: self.text.clone(),
            cursor: self.cursor,
            anchor: self.anchor,
        }
    }
    fn restore(&mut self, s: Snapshot) {
        self.text = s.text;
        self.cursor = s.cursor;
        self.anchor = s.anchor
    }
    fn save(&mut self) {
        self.undo.push(self.snapshot());
        if self.undo.len() > 128 {
            self.undo.remove(0);
        }
        self.redo.clear()
    }
    fn clean(&self, text: &str) -> String {
        text.replace("\r\n", "\n")
            .replace('\r', "\n")
            .chars()
            .filter_map(|c| {
                if c == '\t' {
                    Some(' ')
                } else if !c.is_control() || c == '\n' && !self.single_line {
                    Some(c)
                } else {
                    None
                }
            })
            .collect()
    }
    fn bounds(g: &[String], at: usize) -> (usize, usize) {
        let (mut a, mut b) = (at, at);
        while a > 0 && !text_break(&g[a - 1]) {
            a -= 1
        }
        while b < g.len() && !text_break(&g[b]) {
            b += 1
        }
        (a, b)
    }
    pub fn handle(&mut self, action: &str, text: &str) -> TextEvent {
        let none = TextEvent::default;
        if self.state.disabled {
            return none();
        }
        self.select(self.anchor, self.cursor);
        let g: Vec<String> = self.text.graphemes(true).map(str::to_owned).collect();
        let (lo, hi) = self.selection();
        let at = self.cursor;
        let extend = action.starts_with("select_");
        let movement = action.strip_prefix("select_").unwrap_or(action);
        let (start, end) = Self::bounds(&g, at);
        let target = match movement {
            "left" => Some(if !extend && lo != hi {
                lo
            } else {
                at.saturating_sub(1)
            }),
            "right" => Some(if !extend && lo != hi {
                hi
            } else {
                (at + 1).min(g.len())
            }),
            "home" => Some(start),
            "end" => Some(end),
            "up" => Some(if start > 0 {
                let (p, _) = Self::bounds(&g, start - 1);
                (p + at - start).min(start - 1)
            } else {
                at
            }),
            "down" => Some(if end < g.len() {
                let (_, e) = Self::bounds(&g, end + 1);
                (end + 1 + at - start).min(e)
            } else {
                at
            }),
            "all" if extend => {
                self.select(0, g.len());
                return TextEvent {
                    kind: "select".into(),
                    text: String::new(),
                };
            }
            _ => None,
        };
        if let Some(to) = target {
            self.cursor = to;
            if !extend {
                self.anchor = to
            }
            return TextEvent {
                kind: "select".into(),
                text: String::new(),
            };
        }
        if action == "copy" || action == "cut" {
            if self.secret || lo == hi || action == "cut" && !self.state.visual().editable {
                return none();
            }
            let value = g[lo..hi].concat();
            if action == "cut" {
                self.save();
                self.text = [g[..lo].concat(), g[hi..].concat()].concat();
                self.select(lo, lo);
                self.state.edited = true
            }
            return TextEvent {
                kind: action.into(),
                text: value,
            };
        }
        if !self.state.visual().editable {
            return none();
        }
        if action == "undo" || action == "redo" {
            let snapshot = self.snapshot();
            let previous = if action == "undo" {
                self.undo.pop()
            } else {
                self.redo.pop()
            };
            let Some(previous) = previous else {
                return none();
            };
            if action == "undo" {
                self.redo.push(snapshot)
            } else {
                self.undo.push(snapshot)
            }
            self.restore(previous);
            self.state.edited = true;
            return TextEvent {
                kind: "change".into(),
                text: String::new(),
            };
        }
        let (mut lo, mut hi) = (lo, hi);
        let addition = match action {
            "backspace" => {
                if lo == hi && lo > 0 {
                    lo -= 1
                }
                String::new()
            }
            "delete" => {
                if lo == hi && hi < g.len() {
                    hi += 1
                }
                String::new()
            }
            "newline" => self.clean("\n"),
            "insert" | "paste" => self.clean(text),
            _ => return none(),
        };
        if lo == hi && addition.is_empty() {
            return none();
        }
        self.save();
        let prefix = g[..lo].concat() + &addition;
        self.text = prefix.clone() + &g[hi..].concat();
        let mut byte = 0;
        let mut cursor = 0;
        for c in self.text.graphemes(true) {
            if byte >= prefix.len() {
                break;
            }
            byte += c.len();
            cursor += 1
        }
        self.select(cursor, cursor);
        self.state.edited = true;
        TextEvent {
            kind: "change".into(),
            text: String::new(),
        }
    }
}
#[derive(Clone, Debug)]
pub struct SyntaxSpan {
    pub start: usize,
    pub end: usize,
    pub role: String,
}
#[derive(Clone, Debug)]
struct Hit {
    x: isize,
    index: usize,
}
#[derive(Clone, Debug)]
pub struct TextDocument {
    pub buffer: TextBuffer,
    pub wrap: bool,
    pub line_numbers: bool,
    pub ascii: bool,
    pub scroll_x: usize,
    pub scroll_y: usize,
    pub syntax: Vec<SyntaxSpan>,
    hits: Vec<Vec<Hit>>,
    reveal: bool,
    view_height: usize,
}
impl TextDocument {
    pub fn set_text(&mut self, text: &str) {
        self.buffer.set_text(text);
        self.syntax.clear();
        self.scroll_x = 0;
        self.scroll_y = 0;
        self.reveal = !self.buffer.state.read_only
    }
    pub fn reveal_cursor(&mut self) {
        self.reveal = true
    }
    pub fn set_syntax(&mut self, spans: Vec<SyntaxSpan>) -> Result<(), crate::Error> {
        let n = self.buffer.text().graphemes(true).count();
        if spans
            .iter()
            .any(|s| s.end < s.start || s.end > n || !text_role(&s.role))
        {
            return Err(crate::Error::Invalid("invalid syntax span".into()));
        }
        self.syntax = spans;
        Ok(())
    }
    pub fn editor(text: &str) -> Self {
        Self {
            buffer: TextBuffer::new(text),
            wrap: false,
            line_numbers: true,
            ascii: false,
            scroll_x: 0,
            scroll_y: 0,
            syntax: vec![],
            hits: vec![],
            reveal: true,
            view_height: 0,
        }
    }
    pub fn viewer(text: &str) -> Self {
        let mut d = Self::editor(text);
        d.buffer.state.read_only = true;
        d.line_numbers = false;
        d.reveal = false;
        d
    }
    pub fn handle(&mut self, action: &str, text: &str) -> TextEvent {
        if self.buffer.state.disabled {
            return TextEvent::default();
        }
        match action {
            "page_up" => self.scroll_y = self.scroll_y.saturating_sub(self.view_height.max(1)),
            "page_down" => self.scroll_y = self.scroll_y.saturating_add(self.view_height.max(1)),
            "scroll_up" => self.scroll_y = self.scroll_y.saturating_sub(1),
            "scroll_down" => self.scroll_y = self.scroll_y.saturating_add(1),
            "scroll_left" => self.scroll_x = self.scroll_x.saturating_sub(4),
            "scroll_right" => self.scroll_x = self.scroll_x.saturating_add(4),
            _ => {
                let event = self.buffer.handle(action, text);
                if ["select", "change", "cut"].contains(&event.kind.as_str()) {
                    self.reveal = true
                }
                return event;
            }
        };
        TextEvent::default()
    }
    pub fn layout(&mut self, width: usize, height: usize) -> Vec<ComponentLine> {
        self.view_height = height;
        self.buffer.select(self.buffer.anchor, self.buffer.cursor);
        if width == 0 || height == 0 {
            self.hits.clear();
            return vec![];
        }
        let display = self.buffer.display();
        let g: Vec<_> = display.graphemes(true).collect();
        self.scroll_x = self.scroll_x.min(cells(&display));
        if self.reveal && !self.wrap {
            let mut start = self.buffer.cursor.min(g.len());
            while start > 0 && !text_break(g[start - 1]) {
                start -= 1
            }
            let col = cells(&g[start..self.buffer.cursor.min(g.len())].concat());
            let number = 1 + g[..start].iter().filter(|c| **c == "\n").count();
            let prefix = if self.line_numbers {
                format!("{number} ").len()
            } else {
                0
            };
            let available = width.saturating_sub(prefix).max(1);
            if col < self.scroll_x {
                self.scroll_x = col
            }
            if col >= self.scroll_x.saturating_add(available) {
                self.scroll_x = col - available + 1
            }
        }
        let (lo, hi) = self.buffer.selection();
        let mut rows = vec![];
        let mut all_hits = vec![];
        let (mut line, mut at) = (1, 0);
        loop {
            let prefix = if self.line_numbers {
                format!("{line} ")
            } else {
                String::new()
            };
            let mut row = ComponentLine {
                role: "body".into(),
                text: cell_text(&prefix, width),
                ..Default::default()
            };
            let prefix_width = cells(&prefix);
            let mut col = prefix_width;
            let mut hits = vec![Hit {
                x: prefix_width as isize,
                index: at,
            }];
            while at < g.len() && !text_break(g[at]) {
                let c = if g[at].chars().any(char::is_control) {
                    " "
                } else {
                    g[at]
                };
                let w = cells(c);
                if self.wrap && col + w > width && col > prefix_width {
                    break;
                }
                let x = col as isize
                    - if self.wrap {
                        0
                    } else {
                        self.scroll_x.min(isize::MAX as usize) as isize
                    };
                hits.push(Hit { x, index: at });
                if x >= prefix_width as isize && (x as usize).saturating_add(w) <= width {
                    let x = x as usize;
                    let old = cells(&row.text);
                    if x > old {
                        row.text.push_str(&" ".repeat(x - old))
                    }
                    row.text.push_str(c);
                    let mut role = "body";
                    for s in &self.syntax {
                        if at >= s.start && at < s.end && text_role(&s.role) {
                            role = &s.role
                        }
                    }
                    if at >= lo && at < hi {
                        role = "selection"
                    }
                    if self.buffer.state.disabled {
                        role = "disabled"
                    }
                    if role != "body" || at == self.buffer.cursor && !self.buffer.state.read_only {
                        row.spans.push(ComponentSpan {
                            start: x,
                            width: w,
                            text: c.into(),
                            role: role.into(),
                            focused: at == self.buffer.cursor,
                        })
                    }
                }
                col += w;
                at += 1;
            }
            let x = col as isize
                - if self.wrap {
                    0
                } else {
                    self.scroll_x.min(isize::MAX as usize) as isize
                };
            if x >= prefix_width as isize && (x as usize) < width {
                hits.push(Hit { x, index: at });
                if at == self.buffer.cursor && !self.buffer.state.read_only {
                    row.spans.push(ComponentSpan {
                        start: x as usize,
                        width: 1,
                        text: " ".into(),
                        role: "body".into(),
                        focused: true,
                    })
                }
            }
            rows.push(row);
            all_hits.push(hits);
            if at == g.len() {
                break;
            }
            if text_break(g[at]) {
                at += 1;
                line += 1
            }
        }
        if self.reveal {
            for (row, hits) in all_hits.iter().enumerate() {
                for hit in hits {
                    if hit.index == self.buffer.cursor {
                        if row < self.scroll_y {
                            self.scroll_y = row
                        }
                        if row >= self.scroll_y.saturating_add(height) {
                            self.scroll_y = row - height + 1
                        }
                    }
                }
            }
            self.reveal = false
        }
        self.scroll_y = self.scroll_y.min(rows.len().saturating_sub(height));
        let end = rows.len().min(self.scroll_y + height);
        self.hits = all_hits[self.scroll_y..end].to_vec();
        rows[self.scroll_y..end].to_vec()
    }
    pub fn point(&mut self, x: isize, y: isize, width: usize, height: usize, extend: bool) {
        self.layout(width, height);
        if self.hits.is_empty() || self.buffer.state.disabled {
            return;
        }
        let y = y.max(0).min(self.hits.len() as isize - 1) as usize;
        let row = &self.hits[y];
        let mut at = row[0].index;
        for hit in row {
            if hit.x <= x {
                at = hit.index
            }
        }
        let anchor = if extend { self.buffer.anchor } else { at };
        self.buffer.select(anchor, at)
    }
}
