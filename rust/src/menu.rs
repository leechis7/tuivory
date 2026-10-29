//! Hierarchical menu state and requests; hosts supply content, global keys and actions.
use crate::{
    Error,
    components::{cell_text, cells, clean},
    forms::{ComponentLine, ComponentSpan},
    layout::CellRect,
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(default, rename_all = "camelCase")]
pub struct MenuItem {
    pub id: String,
    pub parent: String,
    pub label: String,
    pub secondary: String,
    pub shortcut: String,
    pub mnemonic: String,
    pub icon: String,
    pub ascii_icon: String,
    pub disabled: bool,
    pub separator: bool,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct MenuEvent {
    pub kind: String,
    pub id: String,
    pub return_id: String,
}
#[derive(Clone, Debug)]
pub struct MenuBarCell {
    pub id: String,
    pub text: String,
    pub role: String,
    pub start: usize,
    pub width: usize,
    pub focused: bool,
}
#[derive(Clone, Debug, Default)]
pub struct MenuBarLayout {
    pub cells: Vec<MenuBarCell>,
    pub previous: bool,
    pub next: bool,
}
pub struct Menu {
    items: Vec<MenuItem>,
    index: BTreeMap<String, usize>,
    children: BTreeMap<String, Vec<String>>,
    opened: bool,
    context: bool,
    path: Vec<String>,
    focus: BTreeMap<String, String>,
    top: BTreeMap<String, usize>,
    caller: String,
    bar: String,
    bar_first: usize,
    pub back_label: String,
    pub empty_label: String,
}
type MenuData = (BTreeMap<String, usize>, BTreeMap<String, Vec<String>>);
fn validate(items: &[MenuItem]) -> Result<MenuData, Error> {
    if items.len() > 10000 {
        return Err(Error::Invalid("too many menu items".into()));
    }
    let mut index = BTreeMap::new();
    let mut children: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut keys = BTreeSet::new();
    for (n, i) in items.iter().enumerate() {
        if i.id.is_empty() || i.id.starts_with('@') || index.insert(i.id.clone(), n).is_some() {
            return Err(Error::Invalid("invalid/duplicate menu ID".into()));
        }
        if !i.mnemonic.is_empty() {
            let k = i.mnemonic.to_ascii_lowercase();
            if k.len() != 1
                || !k.as_bytes()[0].is_ascii_alphanumeric()
                || i.separator
                || !keys.insert((i.parent.clone(), k))
            {
                return Err(Error::Invalid("invalid/duplicate sibling mnemonic".into()));
            }
        }
        children
            .entry(i.parent.clone())
            .or_default()
            .push(i.id.clone());
    }
    for i in items {
        if i.separator && children.contains_key(&i.id) {
            return Err(Error::Invalid("separator cannot have children".into()));
        }
        let mut at = i.parent.as_str();
        let mut seen = BTreeSet::from([i.id.as_str()]);
        let mut depth = 1;
        while !at.is_empty() {
            let Some(n) = index.get(at) else {
                return Err(Error::Invalid("missing parent".into()));
            };
            if !seen.insert(at) || items[*n].separator {
                return Err(Error::Invalid("invalid parent/cycle".into()));
            }
            depth += 1;
            if depth > 32 {
                return Err(Error::Invalid("menu depth exceeds 32".into()));
            }
            at = &items[*n].parent;
        }
    }
    Ok((index, children))
}
fn label(i: &MenuItem) -> String {
    if i.mnemonic.is_empty() {
        i.label.clone()
    } else {
        format!("{} ({})", i.label, i.mnemonic.to_ascii_uppercase())
    }
}
impl Menu {
    pub fn new(items: Vec<MenuItem>) -> Result<Self, Error> {
        let mut m = Self {
            items: vec![],
            index: BTreeMap::new(),
            children: BTreeMap::new(),
            opened: false,
            context: false,
            path: vec![],
            focus: BTreeMap::new(),
            top: BTreeMap::new(),
            caller: String::new(),
            bar: String::new(),
            bar_first: 0,
            back_label: "Back".into(),
            empty_label: "(empty)".into(),
        };
        m.set_items(items)?;
        Ok(m)
    }
    pub fn items(&self) -> &[MenuItem] {
        &self.items
    }
    pub fn set_items(&mut self, items: Vec<MenuItem>) -> Result<Option<MenuEvent>, Error> {
        let (index, children) = validate(&items)?;
        self.items = items;
        self.index = index;
        self.children = children;
        self.focus
            .retain(|p, _| p.is_empty() || self.index.contains_key(p));
        self.top
            .retain(|p, _| p.is_empty() || self.index.contains_key(p));
        if !self.usable(&self.bar, "") {
            self.bar = self.first("")
        }
        for (n, id) in self.path.iter().enumerate() {
            let parent = if n > 0 { &self.path[n - 1] } else { "" };
            if !self.usable(id, parent) || self.child_ids(id).is_empty() {
                return Ok(self.close());
            }
        }
        if self.opened {
            self.reconcile()
        }
        Ok(None)
    }
    fn child_ids(&self, p: &str) -> Vec<String> {
        self.children.get(p).cloned().unwrap_or_default()
    }
    fn usable(&self, id: &str, p: &str) -> bool {
        self.index.get(id).is_some_and(|n| {
            let i = &self.items[*n];
            i.parent == p && !i.disabled && !i.separator
        })
    }
    fn first(&self, p: &str) -> String {
        self.child_ids(p)
            .into_iter()
            .find(|id| self.usable(id, p))
            .unwrap_or_default()
    }
    fn parent(&self) -> &str {
        self.path.last().map(String::as_str).unwrap_or("")
    }
    fn back_allowed(&self) -> bool {
        self.path.len() > 1 || (self.context && !self.path.is_empty())
    }
    fn reconcile(&mut self) {
        let p = self.parent().to_string();
        let id = self.focus.get(&p).map(String::as_str).unwrap_or("");
        if id == "@back" && self.back_allowed() {
            return;
        }
        if !self.usable(id, &p) {
            let mut first = self.first(&p);
            if first.is_empty() && self.back_allowed() {
                first = "@back".into()
            }
            self.focus.insert(p, first);
        }
    }
    pub fn opened(&self) -> bool {
        self.opened
    }
    pub fn path(&self) -> &[String] {
        &self.path
    }
    pub fn focused_id(&self) -> &str {
        self.focus
            .get(self.parent())
            .map(String::as_str)
            .unwrap_or("")
    }
    pub fn return_id(&self) -> &str {
        &self.caller
    }
    pub fn bar_focused_id(&self) -> &str {
        &self.bar
    }
    pub fn title(&self) -> String {
        self.path
            .iter()
            .map(|id| clean(&self.items[self.index[id]].label))
            .collect::<Vec<_>>()
            .join(" / ")
    }
    pub fn open(&mut self, id: &str, return_id: &str) -> Option<MenuEvent> {
        let mut path = vec![];
        let mut at = id.to_string();
        while !at.is_empty() {
            let n = *self.index.get(&at)?;
            let i = &self.items[n];
            if i.disabled || i.separator {
                return None;
            }
            path.insert(0, at);
            at = i.parent.clone();
        }
        self.caller = return_id.into();
        self.path = path;
        for (n, child) in self.path.iter().enumerate() {
            let parent = if n > 0 {
                self.path[n - 1].clone()
            } else {
                String::new()
            };
            self.focus.insert(parent, child.clone());
        }
        self.context = id.is_empty();
        self.opened = true;
        if let Some(root) = self.path.first() {
            self.bar = root.clone()
        }
        if !id.is_empty() && self.child_ids(id).is_empty() {
            return self.finish("activate", id);
        }
        self.reconcile();
        Some(self.event("open", id))
    }
    fn event(&self, kind: &str, id: &str) -> MenuEvent {
        MenuEvent {
            kind: kind.into(),
            id: id.into(),
            return_id: self.caller.clone(),
        }
    }
    fn finish(&mut self, kind: &str, id: &str) -> Option<MenuEvent> {
        self.opened = false;
        self.path.clear();
        Some(self.event(kind, id))
    }
    pub fn close(&mut self) -> Option<MenuEvent> {
        if !self.opened {
            return None;
        }
        self.finish("close", "")
    }
    pub fn back(&mut self) -> Option<MenuEvent> {
        if !self.opened {
            return None;
        }
        if !self.back_allowed() {
            return self.close();
        }
        self.path.pop();
        self.reconcile();
        Some(self.event("back", self.parent()))
    }
    pub fn focus(&mut self, id: &str) -> bool {
        if !self.opened {
            return false;
        }
        if (id == "@back" && self.back_allowed()) || self.usable(id, self.parent()) {
            self.focus.insert(self.parent().into(), id.into());
            return true;
        }
        false
    }
    pub fn click(&mut self, id: &str) -> Option<MenuEvent> {
        if !self.focus(id) {
            return None;
        }
        self.handle("activate", "", 1)
    }
    fn choices(&self) -> Vec<String> {
        let mut ids = vec![];
        if self.back_allowed() {
            ids.push("@back".into())
        }
        ids.extend(
            self.child_ids(self.parent())
                .into_iter()
                .filter(|id| self.usable(id, self.parent())),
        );
        ids
    }
    fn enter(&mut self, id: &str) -> Option<MenuEvent> {
        self.path.push(id.into());
        self.reconcile();
        Some(self.event("open", id))
    }
    pub fn handle(&mut self, action: &str, value: &str, height: usize) -> Option<MenuEvent> {
        if !self.opened {
            return None;
        }
        self.reconcile();
        let p = self.parent().to_string();
        let id = self.focused_id().to_string();
        match action {
            "cancel" | "back" => return self.back(),
            "left" => {
                return if self.back_allowed() {
                    self.back()
                } else if self.context {
                    None
                } else {
                    self.switch_root(false)
                };
            }
            "right" => {
                return if self.usable(&id, &p) && !self.child_ids(&id).is_empty() {
                    self.enter(&id)
                } else if !self.back_allowed() && !self.context {
                    self.switch_root(true)
                } else {
                    None
                };
            }
            "activate" => {
                if id == "@back" {
                    return self.back();
                }
                if !self.usable(&id, &p) {
                    return None;
                }
                return if !self.child_ids(&id).is_empty() {
                    self.enter(&id)
                } else {
                    self.finish("activate", &id)
                };
            }
            "mnemonic" => {
                for candidate in self.child_ids(&p) {
                    let i = &self.items[self.index[&candidate]];
                    if self.usable(&candidate, &p)
                        && !i.mnemonic.is_empty()
                        && i.mnemonic.eq_ignore_ascii_case(value)
                    {
                        self.focus.insert(p, candidate);
                        return self.handle("activate", "", height);
                    }
                }
                return None;
            }
            _ => (),
        }
        let ids = self.choices();
        if ids.is_empty() {
            return None;
        }
        let mut at = ids.iter().position(|c| c == &id).unwrap_or(0);
        match action {
            "previous" | "up" => at = (at + ids.len() - 1) % ids.len(),
            "next" | "down" => at = (at + 1) % ids.len(),
            "first" => at = 0,
            "last" => at = ids.len() - 1,
            "page_up" => at = at.saturating_sub(height.saturating_sub(1).max(1)),
            "page_down" => at = (at + height.saturating_sub(1).max(1)).min(ids.len() - 1),
            _ => return None,
        };
        self.focus.insert(p, ids[at].clone());
        Some(self.event("focus", &ids[at]))
    }
    fn switch_root(&mut self, next: bool) -> Option<MenuEvent> {
        let ids = self
            .child_ids("")
            .into_iter()
            .filter(|id| self.usable(id, ""))
            .collect::<Vec<_>>();
        if ids.is_empty() {
            return None;
        }
        let mut at = ids.iter().position(|id| id == &self.bar).unwrap_or(0);
        let step = if next { 1 } else { ids.len() - 1 };
        at = (at + step) % ids.len();
        for _ in 0..ids.len() {
            if ids[at] != self.bar && !self.child_ids(&ids[at]).is_empty() {
                return self.open(&ids[at], &self.caller.clone());
            }
            at = (at + step) % ids.len();
        }
        None
    }
    pub fn handle_bar(&mut self, action: &str, value: &str) -> Option<MenuEvent> {
        let ids = self
            .child_ids("")
            .into_iter()
            .filter(|id| self.usable(id, ""))
            .collect::<Vec<_>>();
        if ids.is_empty() {
            return None;
        }
        let mut at = ids.iter().position(|id| id == &self.bar).unwrap_or(0);
        match action {
            "previous" | "left" => at = (at + ids.len() - 1) % ids.len(),
            "next" | "right" => at = (at + 1) % ids.len(),
            "first" => at = 0,
            "last" => at = ids.len() - 1,
            "activate" | "down" => {
                return Some(MenuEvent {
                    kind: "open_request".into(),
                    id: ids[at].clone(),
                    return_id: String::new(),
                });
            }
            "mnemonic" => {
                for id in ids {
                    let i = &self.items[self.index[&id]];
                    if !i.mnemonic.is_empty() && i.mnemonic.eq_ignore_ascii_case(value) {
                        self.bar = id.clone();
                        return Some(MenuEvent {
                            kind: "open_request".into(),
                            id,
                            return_id: String::new(),
                        });
                    }
                }
                return None;
            }
            _ => return None,
        };
        self.bar = ids[at].clone();
        Some(MenuEvent {
            kind: "focus".into(),
            id: self.bar.clone(),
            return_id: String::new(),
        })
    }
    fn rows(&self) -> Vec<MenuItem> {
        let mut rows = vec![];
        if self.back_allowed() {
            rows.push(MenuItem {
                id: "@back".into(),
                label: self.back_label.clone(),
                ..Default::default()
            });
            rows.push(MenuItem {
                separator: true,
                ..Default::default()
            });
        }
        rows.extend(
            self.child_ids(self.parent())
                .iter()
                .map(|id| self.items[self.index[id]].clone()),
        );
        rows
    }
    pub fn content_size(&self) -> (usize, usize) {
        let rows = self.rows();
        let mut w = 12;
        for i in &rows {
            w = w.max(
                cells(&clean(&label(i)))
                    + cells(&clean(&i.secondary))
                    + cells(&clean(&i.shortcut))
                    + cells(&clean(&i.icon))
                    + 8,
            )
        }
        (w.min(4096), rows.len().max(1))
    }
    pub fn layout(&mut self, width: usize, height: usize, ascii: bool) -> Vec<ComponentLine> {
        if !self.opened || width == 0 || height == 0 {
            return vec![];
        }
        let width = width.min(65535);
        let height = height.min(4096);
        self.reconcile();
        let rows = self.rows();
        if rows.is_empty() {
            return vec![ComponentLine {
                text: cell_text(&self.empty_label, width),
                role: "hint".into(),
                ..Default::default()
            }];
        }
        let at = rows
            .iter()
            .position(|i| i.id == self.focused_id())
            .unwrap_or(0);
        let mut top = (*self.top.get(self.parent()).unwrap_or(&0)).min(at);
        if at >= top + height {
            top = at - height + 1
        }
        top = top.min(rows.len().saturating_sub(height));
        self.top.insert(self.parent().into(), top);
        rows.iter()
            .skip(top)
            .take(height)
            .map(|i| {
                if i.separator {
                    return ComponentLine {
                        text: if ascii { "-" } else { "─" }.repeat(width),
                        role: "hint".into(),
                        value: "@separator".into(),
                        ..Default::default()
                    };
                }
                let focused = i.id == self.focused_id();
                let role = if i.disabled {
                    "disabled"
                } else if focused {
                    "selection"
                } else {
                    "surface"
                };
                let mut prefix = if focused { "> " } else { "  " }.to_string();
                let icon = if ascii {
                    if i.ascii_icon.is_empty() && !i.icon.is_empty() {
                        "*"
                    } else {
                        &i.ascii_icon
                    }
                } else {
                    &i.icon
                };
                if !icon.is_empty() {
                    prefix.push_str(icon);
                    prefix.push(' ')
                }
                let mut text = if i.id == "@back" {
                    format!("{prefix}< {}", i.label)
                } else {
                    format!("{prefix}{}", label(i))
                };
                if !i.secondary.is_empty() {
                    text.push_str(&format!("  {}", i.secondary))
                }
                let suffix = if !self.child_ids(&i.id).is_empty() {
                    if ascii { " >" } else { " ›" }
                } else {
                    ""
                };
                let shortcut = clean(&i.shortcut);
                let reserve = (width / 3).min(cells(&shortcut));
                let tail = if reserve > 0 {
                    format!(" {}{suffix}", clip(&shortcut, reserve))
                } else {
                    suffix.into()
                };
                let tw = width.min(cells(&tail));
                let mut spans = vec![ComponentSpan {
                    start: 0,
                    width,
                    text: cell_text(&text, width - tw),
                    role: role.into(),
                    focused,
                }];
                if tw > 0 {
                    spans.push(ComponentSpan {
                        start: width - tw,
                        width: tw,
                        text: clip(&tail, tw),
                        role: if role == "surface" { "hint" } else { role }.into(),
                        focused,
                    });
                }
                ComponentLine {
                    id: i.id.clone(),
                    role: role.into(),
                    focused,
                    spans,
                    ..Default::default()
                }
            })
            .collect()
    }
    pub fn bar_layout(&mut self, width: usize) -> MenuBarLayout {
        let mut out = MenuBarLayout::default();
        let width = width.min(65535);
        if width < 3 {
            return out;
        }
        let ids = self.child_ids("");
        if ids.is_empty() {
            return out;
        }
        let target = ids.iter().position(|id| id == &self.bar).unwrap_or(0);
        self.bar_first = self.bar_first.min(target);
        let size = |n: usize| (cells(&clean(&label(&self.items[self.index[&ids[n]]]))) + 2).min(24);
        while self.bar_first < target
            && (self.bar_first..=target).map(size).sum::<usize>() > width - 2
        {
            self.bar_first += 1;
        }
        while self.bar_first > 0
            && (self.bar_first - 1..=target).map(size).sum::<usize>() <= width - 2
        {
            self.bar_first -= 1;
        }
        let mut x = 1;
        let mut last = self.bar_first;
        for (n, id) in ids.iter().enumerate().skip(self.bar_first) {
            if x >= width - 1 {
                break;
            }
            let i = &self.items[self.index[id]];
            if i.separator {
                continue;
            }
            let w = size(n).min(width - 1 - x);
            let focused = i.id == self.bar;
            let role = if i.disabled {
                "disabled"
            } else if focused {
                "selection"
            } else {
                "header"
            };
            out.cells.push(MenuBarCell {
                id: i.id.clone(),
                text: cell_text(&format!(" {} ", label(i)), w),
                role: role.into(),
                start: x,
                width: w,
                focused,
            });
            x += w;
            last = n + 1;
        }
        out.previous = self.bar_first > 0;
        out.next = last < ids.len();
        out
    }
    pub fn bar_click(&mut self, x: usize, width: usize) -> Option<MenuEvent> {
        let l = self.bar_layout(width);
        if x == 0 && l.previous {
            return self.handle_bar("previous", "");
        }
        if x + 1 == width && l.next {
            return self.handle_bar("next", "");
        }
        for c in l.cells {
            if x >= c.start && x < c.start + c.width && self.usable(&c.id, "") {
                self.bar = c.id.clone();
                return Some(MenuEvent {
                    kind: "open_request".into(),
                    id: c.id,
                    return_id: String::new(),
                });
            }
        }
        None
    }
}
fn clip(s: &str, width: usize) -> String {
    use unicode_segmentation::UnicodeSegmentation;
    let mut out = String::new();
    let mut used = 0;
    for g in s.graphemes(true) {
        let w = cells(g);
        if used + w > width {
            break;
        }
        out.push_str(g);
        used += w;
    }
    out
}
/// Pure popup geometry; the host owns its anchor, visibility and panel padding.
pub fn menu_placement(
    anchor: CellRect,
    viewport: CellRect,
    width: usize,
    height: usize,
) -> CellRect {
    let w = width.min(viewport.width);
    let h = height.min(viewport.height);
    let x = anchor.x.clamp(
        viewport.x,
        viewport.x.saturating_add(viewport.width).saturating_sub(w),
    );
    let mut y = anchor.y.saturating_add(anchor.height);
    if y.saturating_add(h) > viewport.y.saturating_add(viewport.height) {
        y = anchor.y.saturating_sub(h)
    }
    y = y.clamp(
        viewport.y,
        viewport.y.saturating_add(viewport.height).saturating_sub(h),
    );
    CellRect {
        x,
        y,
        width: w,
        height: h,
    }
}
