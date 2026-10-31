//! Language-neutral input values and editor action mapping. No terminal I/O.
use serde::{Deserialize, Serialize};
fn zero<T: Default + PartialEq>(value: &T) -> bool {
    value == &T::default()
}
/// Screen-cell coordinates, original UTF-8 text and ordered modifier names.
/// Hosts consume global keys before forwarding editing actions to a model.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default)]
pub struct InputEvent {
    pub kind: String,
    #[serde(skip_serializing_if = "String::is_empty")]
    pub key: String,
    #[serde(skip_serializing_if = "String::is_empty")]
    pub text: String,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub modifiers: Vec<String>,
    #[serde(skip_serializing_if = "String::is_empty")]
    pub phase: String,
    #[serde(skip_serializing_if = "zero")]
    pub x: isize,
    #[serde(skip_serializing_if = "zero")]
    pub y: isize,
    #[serde(skip_serializing_if = "String::is_empty")]
    pub button: String,
    #[serde(skip_serializing_if = "zero")]
    pub width: usize,
    #[serde(skip_serializing_if = "zero")]
    pub height: usize,
}
impl InputEvent {
    pub fn paste(text: &str) -> Self {
        Self {
            kind: "paste".into(),
            text: text.into(),
            ..Default::default()
        }
    }
    pub fn resize(width: usize, height: usize) -> Self {
        Self {
            kind: "resize".into(),
            width,
            height,
            ..Default::default()
        }
    }
    /// Returns requests only. Enter is newline; form hosts map it to activation.
    pub fn editing_action(&self) -> (String, String) {
        if self.kind == "paste" {
            return ("paste".into(), self.text.clone());
        }
        if self.kind != "key" || self.phase == "release" {
            return Default::default();
        }
        let has = |name: &str| self.modifiers.iter().any(|m| m == name);
        if has("ctrl") {
            return (
                match self.key.to_lowercase().as_str() {
                    "a" => "select_all",
                    "c" => "copy",
                    "x" => "cut",
                    "z" => "undo",
                    "y" => "redo",
                    _ => "",
                }
                .into(),
                String::new(),
            );
        }
        let mut action = match self.key.as_str() {
            "enter" => "newline",
            "backspace" => "backspace",
            "delete" => "delete",
            "left" => "left",
            "right" => "right",
            "up" => "up",
            "down" => "down",
            "home" => "home",
            "end" => "end",
            "page_up" => "page_up",
            "page_down" => "page_down",
            _ => "",
        }
        .to_string();
        if has("alt") && ["left", "right"].contains(&action.as_str()) {
            return (format!("scroll_{action}"), String::new());
        }
        if has("shift") && ["left", "right", "up", "down", "home", "end"].contains(&action.as_str())
        {
            action = format!("select_{action}");
        }
        if !action.is_empty() {
            return (action, String::new());
        }
        if !self.text.is_empty() {
            return ("insert".into(), self.text.clone());
        }
        Default::default()
    }

    #[cfg(feature = "terminal")]
    pub fn from_key(event: crate::ui::terminal::event::KeyEvent) -> Self {
        use crate::ui::terminal::event::{KeyCode, KeyEventKind, KeyModifiers};
        let mut modifiers = event.modifiers;
        let (mut key, mut text) = match event.code {
            KeyCode::Char(c) => (c.to_string(), c.to_string()),
            KeyCode::F(n) => (format!("f{n}"), String::new()),
            code => (
                (match code {
                    KeyCode::Tab => "tab",
                    KeyCode::BackTab => {
                        modifiers |= KeyModifiers::SHIFT;
                        "tab"
                    }
                    KeyCode::Enter => "enter",
                    KeyCode::Esc => "escape",
                    KeyCode::Backspace => "backspace",
                    KeyCode::Delete => "delete",
                    KeyCode::Insert => "insert",
                    KeyCode::Left => "left",
                    KeyCode::Right => "right",
                    KeyCode::Up => "up",
                    KeyCode::Down => "down",
                    KeyCode::Home => "home",
                    KeyCode::End => "end",
                    KeyCode::PageUp => "page_up",
                    KeyCode::PageDown => "page_down",
                    _ => "unknown",
                })
                .into(),
                String::new(),
            ),
        };
        if modifiers.contains(KeyModifiers::CONTROL) {
            key = key.to_lowercase();
            text.clear();
        }
        let mut names = vec![];
        for (flag, name) in [
            (KeyModifiers::SHIFT, "shift"),
            (KeyModifiers::CONTROL, "ctrl"),
            (KeyModifiers::ALT, "alt"),
        ] {
            if modifiers.contains(flag) {
                names.push(name.into());
            }
        }
        if modifiers.intersects(KeyModifiers::META | KeyModifiers::SUPER) {
            names.push("meta".into());
        }
        Self {
            kind: "key".into(),
            key,
            text,
            modifiers: names,
            phase: (match event.kind {
                KeyEventKind::Press => "press",
                KeyEventKind::Repeat => "repeat",
                KeyEventKind::Release => "release",
            })
            .into(),
            ..Default::default()
        }
    }

    #[cfg(feature = "terminal")]
    pub fn from_terminal(event: crate::ui::terminal::event::Event) -> Self {
        use crate::ui::terminal::event::{Event, KeyCode, KeyEvent, MouseButton, MouseEventKind};
        match event {
            Event::Key(key) => Self::from_key(key),
            Event::Paste(text) => Self::paste(&text),
            Event::Resize(w, h) => Self::resize(w.into(), h.into()),
            Event::FocusGained => Self {
                kind: "focus".into(),
                phase: "gained".into(),
                ..Default::default()
            },
            Event::FocusLost => Self {
                kind: "focus".into(),
                phase: "lost".into(),
                ..Default::default()
            },
            Event::Mouse(m) => {
                let (phase, button) = match m.kind {
                    MouseEventKind::Down(b) => ("down", Some(b)),
                    MouseEventKind::Up(b) => ("up", Some(b)),
                    MouseEventKind::Drag(b) => ("drag", Some(b)),
                    MouseEventKind::Moved => ("move", None),
                    MouseEventKind::ScrollUp => ("scroll_up", None),
                    MouseEventKind::ScrollDown => ("scroll_down", None),
                    MouseEventKind::ScrollLeft => ("scroll_left", None),
                    MouseEventKind::ScrollRight => ("scroll_right", None),
                };
                let button = match button {
                    Some(MouseButton::Left) => "left",
                    Some(MouseButton::Right) => "right",
                    Some(MouseButton::Middle) => "middle",
                    None => "none",
                };
                Self {
                    kind: "pointer".into(),
                    phase: phase.into(),
                    button: button.into(),
                    x: m.column as isize,
                    y: m.row as isize,
                    modifiers: Self::from_key(KeyEvent::new(KeyCode::Null, m.modifiers)).modifiers,
                    ..Default::default()
                }
            }
        }
    }
}
