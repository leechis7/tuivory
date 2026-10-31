//! Host-owned forms; validation/submit/cancel are requests, never business I/O.
use crate::{
    Error,
    components::cell_text,
    interaction::{ControlState, FocusStack, FocusTarget},
};
use serde::{Deserialize, Serialize};
use unicode_segmentation::UnicodeSegmentation;
#[derive(Clone, Debug, Default, Deserialize, Serialize, PartialEq, Eq)]
#[serde(default)]
pub struct ComponentSpan {
    pub start: usize,
    pub width: usize,
    pub text: String,
    pub role: String,
    pub focused: bool,
}
#[derive(Clone, Debug, Default, Deserialize, Serialize, PartialEq, Eq)]
#[serde(default)]
pub struct ComponentLine {
    pub id: String,
    pub text: String,
    pub role: String,
    pub value: String,
    pub focused: bool,
    pub spans: Vec<ComponentSpan>,
}
#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(default)]
pub struct FormOption {
    pub id: String,
    pub label: String,
    pub disabled: bool,
}
#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(default)]
pub struct FormField {
    pub id: String,
    pub kind: String,
    pub label: String,
    pub help: String,
    pub error: String,
    pub value: String,
    pub choice: String,
    pub action: String,
    pub options: Vec<FormOption>,
    pub state: ControlState,
    pub required: bool,
    pub checked: bool,
    pub open: bool,
    pub pending: String,
    pub cursor: usize,
}
#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(default)]
pub struct FormEvent {
    pub kind: String,
    pub id: String,
    pub missing: Vec<String>,
    pub text: String,
}
#[derive(Clone, Debug)]
pub struct Form {
    fields: Vec<FormField>,
    focus: FocusStack,
    inputs: std::collections::BTreeMap<String, crate::text::TextBuffer>,
}
impl Form {
    pub fn new(mut fields: Vec<FormField>) -> Result<Self, Error> {
        let mut inputs = std::collections::BTreeMap::new();
        for field in &mut fields {
            if ![
                "text", "textarea", "password", "button", "checkbox", "radio", "select",
            ]
            .contains(&field.kind.as_str())
                || field.open
            {
                return Err(Error::Invalid(
                    "unknown field kind or initially open select".into(),
                ));
            }
            let mut seen = std::collections::BTreeSet::new();
            for option in &field.options {
                if option.id.is_empty() || !seen.insert(&option.id) {
                    return Err(Error::Invalid("invalid option ID".into()));
                }
            }
            if !field.choice.is_empty() && !field.options.iter().any(|o| o.id == field.choice) {
                return Err(Error::Invalid("unknown choice".into()));
            }
            field.cursor = field.value.graphemes(true).count();
            if ["text", "textarea", "password"].contains(&field.kind.as_str()) {
                let mut b = crate::text::TextBuffer::new(&field.value);
                b.secret = field.kind == "password";
                b.single_line = field.kind != "textarea";
                field.value = b.display();
                inputs.insert(field.id.clone(), b);
            }
        }
        let focus = FocusStack::new(
            "form",
            fields
                .iter()
                .map(|f| FocusTarget {
                    id: f.id.clone(),
                    state: f.state,
                    hidden: false,
                })
                .collect(),
        )?;
        Ok(Self {
            fields,
            focus,
            inputs,
        })
    }
    /// Explicit raw-value access, including password inputs.
    pub fn value(&self, id: &str) -> Option<&str> {
        self.inputs.get(id).map(|b| b.text()).or_else(|| {
            self.fields
                .iter()
                .find(|f| f.id == id)
                .map(|f| f.value.as_str())
        })
    }
    pub fn select_text(&mut self, id: &str, anchor: usize, cursor: usize) -> bool {
        let Some(b) = self.inputs.get_mut(id) else {
            return false;
        };
        b.select(anchor, cursor);
        if let Some(f) = self.fields.iter_mut().find(|f| f.id == id) {
            f.cursor = b.cursor
        }
        true
    }
    pub fn fields(&self) -> &[FormField] {
        &self.fields
    }
    pub fn at_tab_boundary(&self, previous: bool) -> bool {
        let ids: Vec<_> = self
            .fields
            .iter()
            .filter(|f| f.state.visual().focusable)
            .map(|f| f.id.as_str())
            .collect();
        if ids.is_empty() {
            return true;
        }
        self.focused() == if previous { ids[0] } else { ids[ids.len() - 1] }
    }
    pub fn focused(&self) -> &str {
        self.focus.focused()
    }
    pub fn focus(&mut self, id: &str) -> bool {
        for field in &mut self.fields {
            field.open = false
        }
        self.focus.focus(id)
    }
    pub fn set_state(&mut self, id: &str, state: ControlState) -> bool {
        let Some(field) = self.fields.iter_mut().find(|f| f.id == id) else {
            return false;
        };
        field.state = state;
        if !state.visual().editable {
            field.open = false
        }
        self.focus
            .update(
                "form",
                self.fields
                    .iter()
                    .map(|f| FocusTarget {
                        id: f.id.clone(),
                        state: f.state,
                        hidden: false,
                    })
                    .collect(),
            )
            .expect("validated IDs");
        true
    }
    pub fn set_feedback(&mut self, id: &str, help: &str, message: &str) -> bool {
        let Some(field) = self.fields.iter_mut().find(|f| f.id == id) else {
            return false;
        };
        field.help = help.into();
        field.error = message.into();
        field.state.invalid = !message.is_empty();
        true
    }
    pub fn missing(&self) -> Vec<String> {
        self.fields
            .iter()
            .filter(|f| {
                if f.state.disabled {
                    return false;
                }
                let empty = match f.kind.as_str() {
                    "text" | "textarea" | "password" => {
                        self.value(&f.id).unwrap_or("").trim().is_empty()
                    }
                    "checkbox" => !f.checked,
                    "radio" | "select" => f.choice.is_empty(),
                    _ => false,
                };
                f.state.invalid || !f.error.is_empty() || f.required && empty
            })
            .map(|f| f.id.clone())
            .collect()
    }
    pub fn handle(&mut self, action: &str, text: &str) -> FormEvent {
        let none = FormEvent::default;
        if action == "next" || action == "previous" {
            for f in &mut self.fields {
                f.open = false
            }
            self.focus.move_focus(action == "previous");
            return none();
        }
        if action == "submit" {
            let missing = self.missing();
            return FormEvent {
                kind: if missing.is_empty() {
                    "submit"
                } else {
                    "invalid"
                }
                .into(),
                missing,
                ..Default::default()
            };
        }
        let focused = self.focused().to_owned();
        let Some(field) = self.fields.iter_mut().find(|f| f.id == focused) else {
            return none();
        };
        let action = if action == "insert"
            && text == " "
            && !["text", "textarea", "password"].contains(&field.kind.as_str())
        {
            "toggle"
        } else {
            action
        };
        if action == "cancel" {
            if field.open {
                field.open = false;
                return none();
            }
            return FormEvent {
                kind: "cancel".into(),
                id: focused,
                ..Default::default()
            };
        }
        if field.kind == "button" && ["left", "right"].contains(&action) && !field.state.disabled {
            self.focus.move_focus(action == "left");
            return none();
        }
        if let Some(b) = self.inputs.get_mut(&field.id) {
            b.state = field.state;
            b.cursor = field.cursor;
            if action == "activate" && field.kind != "textarea" {
                if !field.state.visual().activatable {
                    return none();
                }
                return self.handle("submit", "");
            }
            let e = b.handle(
                if action == "activate" {
                    "newline"
                } else {
                    action
                },
                text,
            );
            field.value = b.display();
            field.cursor = b.cursor;
            field.state = b.state;
            return FormEvent {
                kind: e.kind,
                id: focused,
                text: e.text,
                ..Default::default()
            };
        }
        let navigate = ["text", "textarea"].contains(&field.kind.as_str())
            && ["left", "right", "home", "end"].contains(&action)
            && !field.state.disabled;
        if !field.state.visual().activatable && !navigate {
            return none();
        }
        if field.kind == "button" && (action == "activate" || action == "toggle") {
            return match field.action.as_str() {
                "submit" => self.handle("submit", ""),
                "cancel" => FormEvent {
                    kind: "cancel".into(),
                    id: focused,
                    ..Default::default()
                },
                _ => FormEvent {
                    kind: "activate".into(),
                    id: focused,
                    ..Default::default()
                },
            };
        }
        if !field.state.visual().editable && !navigate {
            return none();
        }
        let mut changed = false;
        if field.kind == "checkbox" && (action == "activate" || action == "toggle") {
            field.checked = !field.checked;
            changed = true
        } else if field.kind == "radio" || field.kind == "select" {
            if field.kind == "select" && (action == "activate" || action == "toggle") {
                if field.open {
                    field.choice = field.pending.clone();
                    field.open = false;
                    changed = true
                } else {
                    field.open = true;
                    field.pending = field.choice.clone();
                    if field.pending.is_empty() {
                        field.pending = field
                            .options
                            .iter()
                            .find(|o| !o.disabled)
                            .map(|o| o.id.clone())
                            .unwrap_or_default()
                    }
                    return none();
                }
            } else if ["left", "right", "up", "down", "activate", "toggle"].contains(&action) {
                if field.kind == "select" && !field.open {
                    return none();
                }
                let ids: Vec<_> = field
                    .options
                    .iter()
                    .filter(|o| !o.disabled)
                    .map(|o| o.id.clone())
                    .collect();
                if ids.is_empty() {
                    return none();
                }
                let current = if field.open {
                    &field.pending
                } else {
                    &field.choice
                };
                let at = ids.iter().position(|id| id == current);
                let next = if action == "left" || action == "up" {
                    (at.unwrap_or(0) + ids.len() - 1) % ids.len()
                } else {
                    at.map(|n| (n + 1) % ids.len()).unwrap_or(0)
                };
                if field.kind == "select" {
                    field.pending = ids[next].clone()
                } else {
                    field.choice = ids[next].clone();
                    changed = true
                }
            }
        } else if field.kind == "text" || field.kind == "textarea" {
            let mut g: Vec<String> = field.value.graphemes(true).map(str::to_owned).collect();
            field.cursor = field.cursor.min(g.len());
            let at = field.cursor;
            match action {
                "left" => field.cursor = at.saturating_sub(1),
                "right" => field.cursor = (at + 1).min(g.len()),
                "home" => field.cursor = 0,
                "end" => field.cursor = g.len(),
                "backspace" if at > 0 => {
                    g.remove(at - 1);
                    field.cursor -= 1;
                    changed = true
                }
                "delete" if at < g.len() => {
                    g.remove(at);
                    changed = true
                }
                "activate" if field.kind == "text" => return self.handle("submit", ""),
                "insert" | "activate" => {
                    let text = if action == "activate" { "\n" } else { text };
                    let text: String = text
                        .chars()
                        .filter(|c| !c.is_control() || *c == '\n' && field.kind == "textarea")
                        .collect();
                    if !text.is_empty() {
                        let addition: Vec<_> = text.graphemes(true).map(str::to_owned).collect();
                        field.cursor += addition.len();
                        g.splice(at..at, addition);
                        changed = true
                    }
                }
                _ => (),
            }
            if changed {
                field.value = g.concat()
            }
        }
        if changed {
            field.state.edited = true;
            FormEvent {
                kind: "change".into(),
                id: focused,
                ..Default::default()
            }
        } else {
            none()
        }
    }
    pub fn click(&mut self, id: &str, option: &str) -> FormEvent {
        if self.fields.iter().find(|f| f.id == id).is_some_and(|f| {
            f.state.disabled || f.options.iter().any(|o| o.id == option && o.disabled)
        }) {
            return FormEvent::default();
        }
        if self.focused() != id && !self.focus(id) {
            return FormEvent::default();
        }
        let Some(field) = self.fields.iter_mut().find(|f| f.id == id) else {
            return FormEvent::default();
        };
        if field.kind == "button" {
            if field.state.visual().activatable {
                return self.handle("activate", "");
            }
            return FormEvent::default();
        }
        if !field.state.visual().editable {
            return FormEvent::default();
        }
        if field.kind == "select" && !field.open {
            return self.handle("activate", "");
        }
        if !option.is_empty() && (field.kind == "radio" || field.kind == "select") {
            if field.options.iter().any(|o| o.id == option && !o.disabled) {
                field.choice = option.into();
                field.open = false;
                field.state.edited = true;
                return FormEvent {
                    kind: "change".into(),
                    id: id.into(),
                    ..Default::default()
                };
            }
            return FormEvent::default();
        }
        if ["button", "checkbox", "select"].contains(&field.kind.as_str()) {
            return self.handle("activate", "");
        }
        FormEvent::default()
    }
    pub fn layout(&self, width: usize, height: usize) -> Vec<ComponentLine> {
        let mut rows = Vec::new();
        let mut anchor = 0;
        for field in &self.fields {
            let focused = field.id == self.focused();
            let v = field.state.visual();
            if focused {
                anchor = rows.len()
            }
            let mut add = |text: String, role: &str, focus: bool, value: &str| {
                rows.push(ComponentLine {
                    id: field.id.clone(),
                    text,
                    role: role.into(),
                    focused: focus,
                    value: value.into(),
                    spans: vec![],
                })
            };
            add(
                format!(
                    "{}{}{} {}",
                    if focused { "> " } else { "  " },
                    field.label,
                    if field.required { " *" } else { "" },
                    if field.state.disabled {
                        v.markers.trim_start_matches('-')
                    } else {
                        &v.markers
                    }
                ),
                v.role,
                focused,
                "",
            );
            match field.kind.as_str() {
                "text" | "textarea" | "password" => {
                    let mut position = 0;
                    for line in field.value.split('\n') {
                        let count = line.graphemes(true).count();
                        let caret =
                            focused && field.cursor >= position && field.cursor <= position + count;
                        let value = edit_window(
                            line,
                            field.cursor.saturating_sub(position),
                            width.saturating_sub(2),
                            caret,
                        );
                        add(
                            format!("  {value}"),
                            if field.state.disabled {
                                "disabled"
                            } else {
                                "field"
                            },
                            false,
                            "",
                        );
                        position += count + 1
                    }
                }
                "checkbox" => add(
                    format!("  [{}]", if field.checked { "x" } else { " " }),
                    v.role,
                    false,
                    "",
                ),
                "radio" | "select" => {
                    for option in &field.options {
                        if field.kind == "select" && !field.open && option.id != field.choice {
                            continue;
                        }
                        let current = if field.open {
                            &field.pending
                        } else {
                            &field.choice
                        };
                        add(
                            format!(
                                "  ({}) {}",
                                if option.id == *current { "*" } else { " " },
                                option.label
                            ),
                            if option.disabled || field.state.disabled {
                                "disabled"
                            } else {
                                v.role
                            },
                            false,
                            &option.id,
                        )
                    }
                }
                "button" => add(
                    format!("  [ {} ]", field.label),
                    if field.state.disabled {
                        "disabled"
                    } else {
                        "button"
                    },
                    focused,
                    "",
                ),
                _ => (),
            }
            if !field.error.is_empty() {
                add(format!("! {}", field.error), "error", false, "")
            } else if !field.help.is_empty() {
                add(format!("  {}", field.help), "hint", false, "")
            }
        }
        for field in &self.fields {
            if let Some(buffer) = self.inputs.get(&field.id) {
                let (lo, hi) = buffer.selection();
                if lo != hi {
                    let mut doc = crate::text::TextDocument::viewer("");
                    doc.buffer = buffer.clone();
                    let selected = doc.layout(
                        width.saturating_sub(2),
                        field.value.graphemes(true).count() + 1,
                    );
                    let mut at = 0;
                    for row in &mut rows {
                        if row.id == field.id && (row.role == "field" || row.role == "disabled") {
                            if let Some(line) = selected.get(at) {
                                row.text = format!("  {}", line.text);
                                row.spans = line.spans.clone();
                                for span in &mut row.spans {
                                    span.start += 2
                                }
                            }
                            at += 1
                        }
                    }
                }
            }
        }
        let start = anchor
            .saturating_sub(height.saturating_sub(2))
            .min(rows.len().saturating_sub(height));
        rows.into_iter()
            .skip(start)
            .take(height)
            .map(|mut r| {
                r.text = cell_text(&r.text, width);
                r
            })
            .collect()
    }
}
pub(crate) fn edit_window(value: &str, cursor: usize, width: usize, focused: bool) -> String {
    if !focused {
        return cell_text(value, width);
    }
    let g: Vec<_> = value.graphemes(true).collect();
    let at = cursor.min(g.len());
    if width == 0 {
        return String::new();
    }
    let before = crate::components::tail_cells(&g[..at].concat(), width.saturating_sub(1));
    format!(
        "{before}|{}",
        cell_text(
            &g[at..].concat(),
            width.saturating_sub(crate::components::cells(&before) + 1)
        )
    )
}
