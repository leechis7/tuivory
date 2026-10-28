//! Literal lists/menus and query/pending-choice composition; no search I/O.
use crate::{Error, components::cell_text, forms::ComponentLine};
use unicode_segmentation::UnicodeSegmentation;
#[derive(Clone, Debug, Default)]
pub struct ListItem {
    pub id: String,
    pub label: String,
    pub secondary: String,
    pub shortcut: String,
    pub icon: String,
    pub ascii_icon: String,
    pub disabled: bool,
    pub separator: bool,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct ListEvent {
    pub kind: String,
    pub id: String,
    pub query: String,
}
#[derive(Clone, Debug)]
pub struct ListModel {
    items: Vec<ListItem>,
    pub focused: String,
    pub selected: String,
    pub query: String,
    pub empty: String,
}
impl ListModel {
    pub fn new(items: Vec<ListItem>) -> Result<Self, Error> {
        let mut m = Self {
            items: vec![],
            focused: String::new(),
            selected: String::new(),
            query: String::new(),
            empty: "(empty)".into(),
        };
        m.set_items(items)?;
        Ok(m)
    }
    pub fn items(&self) -> &[ListItem] {
        &self.items
    }
    pub fn set_items(&mut self, items: Vec<ListItem>) -> Result<(), Error> {
        let mut seen = std::collections::BTreeSet::new();
        for item in &items {
            if item.id.is_empty() || !seen.insert(&item.id) {
                return Err(Error::Invalid("empty or duplicate list ID".into()));
            }
        }
        if !items.iter().any(|i| i.id == self.selected) {
            self.selected.clear()
        }
        self.items = items;
        self.reconcile();
        Ok(())
    }
    fn visible(&self) -> Vec<&ListItem> {
        let q = self.query.to_lowercase();
        self.items
            .iter()
            .filter(|i| {
                q.is_empty()
                    || !i.separator
                        && format!("{} {}", i.label, i.secondary)
                            .to_lowercase()
                            .contains(&q)
            })
            .collect()
    }
    pub fn focus(&mut self, id: &str) -> bool {
        if self
            .visible()
            .iter()
            .any(|i| i.id == id && !i.disabled && !i.separator)
        {
            self.focused = id.into();
            true
        } else {
            false
        }
    }
    fn reconcile(&mut self) {
        let id = self.focused.clone();
        if !self.focus(&id) {
            self.focused = self
                .visible()
                .iter()
                .find(|i| !i.disabled && !i.separator)
                .map(|i| i.id.clone())
                .unwrap_or_default();
        }
    }
    pub fn set_query(&mut self, query: &str) -> ListEvent {
        self.query = query.chars().filter(|c| !c.is_control()).collect();
        self.reconcile();
        ListEvent {
            kind: "query".into(),
            query: self.query.clone(),
            ..Default::default()
        }
    }
    pub fn handle(&mut self, action: &str, height: usize) -> ListEvent {
        self.reconcile();
        let ids: Vec<_> = self
            .visible()
            .iter()
            .filter(|i| !i.disabled && !i.separator)
            .map(|i| i.id.clone())
            .collect();
        if ids.is_empty() {
            return ListEvent::default();
        }
        let mut at = ids.iter().position(|id| *id == self.focused).unwrap_or(0);
        match action {
            "activate" | "select" => {
                self.selected = self.focused.clone();
                return ListEvent {
                    kind: action.into(),
                    id: self.focused.clone(),
                    ..Default::default()
                };
            }
            "next" => at = (at + 1).min(ids.len() - 1),
            "previous" => at = at.saturating_sub(1),
            "first" => at = 0,
            "last" => at = ids.len() - 1,
            "page_down" => at = (at + height.saturating_sub(1).max(1)).min(ids.len() - 1),
            "page_up" => at = at.saturating_sub(height.saturating_sub(1).max(1)),
            _ => return ListEvent::default(),
        };
        self.focused = ids[at].clone();
        ListEvent {
            kind: "focus".into(),
            id: self.focused.clone(),
            ..Default::default()
        }
    }
    pub fn layout(&self, width: usize, height: usize, ascii: bool) -> Vec<ComponentLine> {
        let mut rows = vec![];
        let mut anchor = 0;
        for item in self.visible() {
            if item.id == self.focused {
                anchor = rows.len()
            }
            if item.separator {
                rows.push(ComponentLine {
                    id: item.id.clone(),
                    text: format!("--- {} ---", item.label),
                    role: "hint".into(),
                    ..Default::default()
                });
                continue;
            }
            let role = if item.disabled {
                "disabled"
            } else if item.id == self.selected {
                "selection"
            } else {
                "body"
            };
            let mut mark = if item.id == self.focused { "> " } else { "  " }.to_owned();
            if item.id == self.selected {
                mark.push_str("* ")
            }
            let icon = if ascii { &item.ascii_icon } else { &item.icon };
            let icon = if icon.is_empty() {
                String::new()
            } else {
                format!("{icon} ")
            };
            let shortcut = if item.shortcut.is_empty() {
                String::new()
            } else {
                format!(" [{}]", item.shortcut)
            };
            rows.push(ComponentLine {
                id: item.id.clone(),
                text: format!("{mark}{icon}{}{shortcut}", item.label),
                role: role.into(),
                focused: item.id == self.focused,
                value: item.id.clone(),
            });
            if !item.secondary.is_empty() {
                rows.push(ComponentLine {
                    id: item.id.clone(),
                    text: format!("    {}", item.secondary),
                    role: "hint".into(),
                    value: item.id.clone(),
                    ..Default::default()
                })
            }
        }
        if rows.is_empty() {
            rows.push(ComponentLine {
                text: self.empty.clone(),
                role: "hint".into(),
                ..Default::default()
            })
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
#[derive(Clone, Debug)]
pub struct SearchPicker {
    pub list: ListModel,
    pub open: bool,
    pub value: String,
}
impl SearchPicker {
    pub fn new(items: Vec<ListItem>) -> Result<Self, Error> {
        Ok(Self {
            list: ListModel::new(items)?,
            open: false,
            value: String::new(),
        })
    }
    pub fn handle(&mut self, action: &str, text: &str, height: usize) -> ListEvent {
        match action {
            "open" => {
                self.open = true;
                self.list.set_query("");
                self.list.focus(&self.value);
                return ListEvent {
                    kind: "open".into(),
                    ..Default::default()
                };
            }
            "cancel" => {
                self.open = false;
                return ListEvent {
                    kind: "cancel".into(),
                    ..Default::default()
                };
            }
            "insert" | "backspace" => {
                if !self.open {
                    self.handle("open", "", height);
                }
                let mut query = self.list.query.clone();
                if action == "insert" {
                    query.push_str(text)
                } else {
                    let mut g: Vec<_> = query.graphemes(true).collect();
                    g.pop();
                    query = g.concat()
                }
                return self.list.set_query(&query);
            }
            "activate" => {
                if !self.open {
                    return self.handle("open", "", height);
                }
                let mut event = self.list.handle("activate", height);
                if !event.id.is_empty() {
                    self.value = event.id.clone();
                    self.open = false;
                    event.kind = "change".into()
                }
                return event;
            }
            _ => (),
        };
        if !self.open {
            return ListEvent::default();
        }
        self.list.handle(action, height)
    }
    pub fn click(&mut self, id: &str) -> ListEvent {
        if !self.list.focus(id) {
            return ListEvent::default();
        }
        self.handle("activate", "", 1)
    }
    pub fn layout(&self, width: usize, height: usize, ascii: bool) -> Vec<ComponentLine> {
        if height == 0 {
            return vec![];
        }
        if !self.open {
            let label = self
                .list
                .items()
                .iter()
                .find(|i| i.id == self.value)
                .map(|i| i.label.as_str())
                .unwrap_or(&self.list.empty);
            return vec![ComponentLine {
                text: cell_text(&format!("v {label}"), width),
                role: "field".into(),
                ..Default::default()
            }];
        }
        let mut rows = vec![ComponentLine {
            text: cell_text(
                &format!(
                    "? {}",
                    crate::forms::edit_window(
                        &self.list.query,
                        self.list.query.graphemes(true).count(),
                        width.saturating_sub(2),
                        true
                    )
                ),
                width,
            ),
            role: "field".into(),
            ..Default::default()
        }];
        rows.extend(self.list.layout(width, height - 1, ascii));
        rows
    }
}
