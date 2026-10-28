//! Notices and progress accept host clocks; they spawn no timer/event loop.
use crate::{Error, components::cell_text, forms::ComponentLine};
#[derive(Clone, Debug, Default)]
pub struct NoticeAction {
    pub id: String,
    pub label: String,
    pub disabled: bool,
}
#[derive(Clone, Debug, Default)]
pub struct Notice {
    pub id: String,
    pub text: String,
    pub detail: String,
    pub severity: String,
    pub priority: i32,
    pub persistent: bool,
    pub expires_at: u64,
    pub actions: Vec<NoticeAction>,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct NoticeEvent {
    pub kind: String,
    pub id: String,
    pub action: String,
}
fn severity(s: &str) -> i32 {
    match s {
        "error" => 3,
        "warning" => 2,
        "success" => 1,
        "info" => 0,
        _ => -1,
    }
}
fn pinned(n: &Notice) -> bool {
    n.persistent || n.severity == "error" || !n.actions.is_empty()
}
fn expired(n: &Notice, now: u64) -> bool {
    !pinned(n) && n.expires_at > 0 && now >= n.expires_at
}
#[derive(Clone, Debug)]
pub struct NoticeQueue {
    items: Vec<Notice>,
    capacity: usize,
    pub focused: String,
}
impl NoticeQueue {
    pub fn new(capacity: usize) -> Result<Self, Error> {
        if capacity == 0 {
            return Err(Error::Invalid("positive notice capacity required".into()));
        }
        Ok(Self {
            items: vec![],
            capacity,
            focused: String::new(),
        })
    }
    pub fn push(&mut self, n: Notice) -> Result<(), Error> {
        if n.id.is_empty() || severity(&n.severity) < 0 {
            return Err(Error::Invalid("invalid notice ID or severity".into()));
        }
        let mut seen = std::collections::BTreeSet::new();
        for a in &n.actions {
            if a.id.is_empty() || !seen.insert(&a.id) {
                return Err(Error::Invalid("invalid notice action".into()));
            }
        }
        if let Some(old) = self.items.iter_mut().find(|old| old.id == n.id) {
            *old = n;
            return Ok(());
        }
        if self.items.len() >= self.capacity {
            let candidate = self
                .items
                .iter()
                .enumerate()
                .filter(|(_, old)| !pinned(old))
                .min_by_key(|(_, old)| (severity(&old.severity), old.priority))
                .map(|(i, _)| i);
            let Some(index) = candidate else {
                return Err(Error::Invalid(
                    "notice queue full; important notices retained".into(),
                ));
            };
            if severity(&self.items[index].severity) > severity(&n.severity)
                || severity(&self.items[index].severity) == severity(&n.severity)
                    && self.items[index].priority > n.priority
            {
                return Err(Error::Invalid("notice queue full".into()));
            }
            self.items.remove(index);
        }
        if self.focused.is_empty() || n.severity == "error" {
            self.focused = n.id.clone()
        }
        self.items.push(n);
        Ok(())
    }
    pub fn visible(&self, now: u64) -> Vec<Notice> {
        let mut items: Vec<_> = self
            .items
            .iter()
            .filter(|n| !expired(n, now))
            .cloned()
            .collect();
        items.sort_by(|a, b| {
            severity(&b.severity)
                .cmp(&severity(&a.severity))
                .then(b.priority.cmp(&a.priority))
        });
        items
    }
    pub fn dismiss(&mut self, id: &str) -> bool {
        if let Some(index) = self.items.iter().position(|n| n.id == id) {
            self.items.remove(index);
            if self.focused == id {
                self.focused.clear()
            }
            true
        } else {
            false
        }
    }
    pub fn expire(&mut self, now: u64) -> Vec<NoticeEvent> {
        let mut out = vec![];
        self.items.retain(|n| {
            if expired(n, now) {
                out.push(NoticeEvent {
                    kind: "expired".into(),
                    id: n.id.clone(),
                    ..Default::default()
                });
                false
            } else {
                true
            }
        });
        out
    }
    pub fn handle(&mut self, action: &str, now: u64, height: usize) -> NoticeEvent {
        let mut items = self.visible(now);
        let limit = if items.len() > height {
            if height > 0 {
                height.saturating_sub(1).max(1)
            } else {
                0
            }
        } else {
            height
        };
        items.truncate(limit);
        if items.is_empty() {
            return NoticeEvent::default();
        }
        let mut at = items.iter().position(|n| n.id == self.focused).unwrap_or(0);
        if action == "next" {
            at = (at + 1).min(items.len() - 1)
        }
        if action == "previous" {
            at = at.saturating_sub(1)
        }
        let n = &items[at];
        self.focused = n.id.clone();
        if action == "dismiss" {
            return NoticeEvent {
                kind: "dismiss".into(),
                id: n.id.clone(),
                ..Default::default()
            };
        }
        if action == "activate" {
            if let Some(a) = n.actions.iter().find(|a| !a.disabled) {
                return NoticeEvent {
                    kind: "action".into(),
                    id: n.id.clone(),
                    action: a.id.clone(),
                };
            }
        }
        NoticeEvent::default()
    }
    pub fn layout(&self, width: usize, height: usize, now: u64) -> Vec<ComponentLine> {
        let items = self.visible(now);
        let limit = if items.len() > height {
            if height > 0 {
                height.saturating_sub(1).max(1)
            } else {
                0
            }
        } else {
            height
        };
        let mut out = vec![];
        for n in items.iter().take(limit) {
            let mark = match n.severity.as_str() {
                "error" => "[!]",
                "warning" => "[?]",
                "success" => "[+]",
                _ => "[i]",
            };
            let mut value = format!(
                "{}{mark} {}",
                if self.focused == n.id { "> " } else { "  " },
                n.text
            );
            if !n.detail.is_empty() {
                value.push_str(&format!(" / {}", n.detail))
            }
            for a in &n.actions {
                value.push_str(&format!(" [{}]", a.label))
            }
            out.push(ComponentLine {
                id: n.id.clone(),
                text: cell_text(&value, width),
                role: n.severity.clone(),
                focused: n.id == self.focused,
                ..Default::default()
            })
        }
        if items.len() > limit && height > out.len() {
            out.push(ComponentLine {
                text: cell_text(&format!("+{}", items.len() - limit), width),
                role: "hint".into(),
                ..Default::default()
            })
        }
        out
    }
}
#[derive(Clone, Debug, Default)]
pub struct Progress {
    pub id: String,
    pub label: String,
    pub status: String,
    pub message: String,
    pub cancel_label: String,
    pub current: u64,
    pub total: u64,
    pub cancellable: bool,
}
impl Progress {
    pub fn request_cancel(&self) -> NoticeEvent {
        if !self.id.is_empty()
            && self.cancellable
            && (self.status.is_empty() || self.status == "loading")
        {
            NoticeEvent {
                kind: "cancel".into(),
                id: self.id.clone(),
                ..Default::default()
            }
        } else {
            NoticeEvent::default()
        }
    }
    pub fn layout(&self, width: usize, frame: u64) -> Vec<ComponentLine> {
        let status = if self.status.is_empty() {
            "loading"
        } else {
            &self.status
        };
        let role = match status {
            "error" => "error",
            "success" => "success",
            "empty" | "cancelled" => "hint",
            "ready" => "body",
            "loading" => "info",
            _ => "error",
        };
        let mut value = status.to_owned();
        if status == "loading" {
            if self.total == 0 {
                value = ["|", "/", "-", "\\"][(frame % 4) as usize].into()
            } else {
                let ratio = self.current.min(self.total) as f64 / self.total as f64;
                let size = width.saturating_sub(10).min(30);
                let done = (ratio * size as f64) as usize;
                value = format!(
                    "[{}{}] {}%",
                    "#".repeat(done),
                    "-".repeat(size - done),
                    (ratio * 100.0) as usize
                )
            }
        }
        if !self.message.is_empty() {
            value.push_str(&format!(" {}", self.message))
        }
        let mut rows = vec![
            ComponentLine {
                id: self.id.clone(),
                text: cell_text(&self.label, width),
                role: role.into(),
                ..Default::default()
            },
            ComponentLine {
                id: self.id.clone(),
                text: cell_text(&value, width),
                role: role.into(),
                ..Default::default()
            },
        ];
        if !self.request_cancel().kind.is_empty() && !self.cancel_label.is_empty() {
            rows.push(ComponentLine {
                id: self.id.clone(),
                text: cell_text(&self.cancel_label, width),
                role: "hint".into(),
                ..Default::default()
            })
        }
        rows
    }
}
#[derive(Clone, Debug, Default)]
pub struct DataState {
    pub kind: String,
    pub text: String,
    pub detail: String,
}
impl DataState {
    pub fn layout(&self, width: usize) -> Vec<ComponentLine> {
        let role = match self.kind.as_str() {
            "ready" => "body",
            "loading" => "info",
            "empty" => "hint",
            _ => "error",
        };
        vec![
            ComponentLine {
                text: cell_text(&self.text, width),
                role: role.into(),
                ..Default::default()
            },
            ComponentLine {
                text: cell_text(&self.detail, width),
                role: "hint".into(),
                ..Default::default()
            },
        ]
    }
}
