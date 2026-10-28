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
pub struct ComponentLine {
    pub id: String,
    pub text: String,
    pub role: String,
    pub value: String,
    pub focused: bool,
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
}
#[derive(Clone, Debug)]
pub struct Form {
    fields: Vec<FormField>,
    focus: FocusStack,
}
impl Form {
    pub fn new(mut fields: Vec<FormField>) -> Result<Self, Error> {
        for field in &mut fields {
            if !["text", "textarea", "button", "checkbox", "radio", "select"]
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
        Ok(Self { fields, focus })
    }
    pub fn fields(&self) -> &[FormField] {
        &self.fields
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
                    "text" | "textarea" => f.value.trim().is_empty(),
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
        let navigate = ["text", "textarea"].contains(&field.kind.as_str())
            && ["left", "right", "home", "end"].contains(&action)
            && !field.state.disabled;
        if !field.state.visual().activatable && !navigate {
            return none();
        }
        if field.kind == "button" && action == "activate" {
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
        if self.focused() != id && !self.focus(id) {
            return FormEvent::default();
        }
        let Some(field) = self.fields.iter_mut().find(|f| f.id == id) else {
            return FormEvent::default();
        };
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
                })
            };
            add(
                format!(
                    "{}{}{} {}",
                    if focused { "> " } else { "  " },
                    field.label,
                    if field.required { " *" } else { "" },
                    v.markers
                ),
                v.role,
                focused,
                "",
            );
            match field.kind.as_str() {
                "text" | "textarea" => {
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
                        add(format!("  {value}"), "field", false, "");
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
                            if option.disabled { "disabled" } else { v.role },
                            false,
                            &option.id,
                        )
                    }
                }
                "button" => add(format!("  [ {} ]", field.label), "button", focused, ""),
                _ => (),
            }
            if !field.error.is_empty() {
                add(format!("! {}", field.error), "error", false, "")
            } else if !field.help.is_empty() {
                add(format!("  {}", field.help), "hint", false, "")
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
fn edit_window(value: &str, cursor: usize, width: usize, focused: bool) -> String {
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
