//! Request-only tab/tree movement. Hosts approve requests before applying an
//! immutable replacement; gestures own only temporary scroll/expansion previews.
use crate::{
    components::{TabCell, TabItem, TabLayout, TabState, Tabs, cell_text, cells, clean},
    tree::{Tree, TreeNode, TreeRow, TreeState},
};
use std::collections::BTreeSet;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DropPosition {
    Before,
    After,
    Inside,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DropRequest {
    pub source_id: String,
    pub target_id: String,
    pub position: DropPosition,
    pub revision: u64,
}
#[derive(Clone, Debug, Default)]
pub struct DragOptions {
    pub threshold: usize,
    pub auto_scroll: bool,
    pub hover_expand: bool,
    pub locked: Vec<String>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DragAction {
    Down,
    Move,
    Up,
    Cancel,
}
#[derive(Clone, Copy, Debug)]
pub struct DragPointer {
    pub action: DragAction,
    pub x: i32,
    pub y: i32,
    pub width: usize,
    pub height: usize,
}
#[derive(Clone, Copy, Debug)]
pub enum DragMove {
    Previous,
    Next,
    Inside,
    Outside,
}
pub type DropPolicy<'a> = Option<&'a dyn Fn(&DropRequest) -> bool>;
#[derive(Clone, Debug, Default)]
pub struct DragState {
    pub phase: String,
    pub result: String,
    pub source_id: String,
    pub target_id: String,
    pub position: Option<DropPosition>,
    pub allowed: bool,
    pub reason: String,
    revision: u64,
    state_revision: u64,
    x: i32,
    y: i32,
    width: usize,
    height: usize,
    first: usize,
    scroll: usize,
    expanded: BTreeSet<String>,
    request: Option<DropRequest>,
    render_key: String,
}
impl DragState {
    pub fn captured(&self) -> bool {
        matches!(self.phase.as_str(), "armed" | "dragging")
    }
    pub fn cancel(&mut self) {
        let key = std::mem::take(&mut self.render_key);
        *self = Self {
            result: "cancel".into(),
            render_key: key,
            ..Self::default()
        };
    }
    /// Widgets call this every frame to cancel gestures on move/resize/restyle.
    pub fn render_key(&mut self, key: String) {
        if self.captured() && !self.render_key.is_empty() && self.render_key != key {
            self.cancel();
            self.result = "stale".into();
        }
        self.render_key = key;
    }
    fn begin(&mut self, id: String, revision: u64, p: DragPointer) {
        let key = std::mem::take(&mut self.render_key);
        *self = Self {
            phase: "armed".into(),
            source_id: id,
            revision,
            x: p.x,
            y: p.y,
            width: p.width,
            height: p.height,
            render_key: key,
            ..Self::default()
        };
    }
    fn prepare(&mut self, revision: u64, p: DragPointer, o: &DragOptions) -> bool {
        if !self.captured() {
            return false;
        }
        if self.revision != revision || self.width != p.width || self.height != p.height {
            self.cancel();
            self.result = "stale".into();
            return false;
        }
        if p.action == DragAction::Cancel {
            self.cancel();
            return false;
        }
        let threshold = if o.threshold == 0 { 2 } else { o.threshold };
        if self.x.abs_diff(p.x).max(self.y.abs_diff(p.y)) as usize >= threshold {
            self.phase = "dragging".into();
        }
        true
    }
    fn preview(&mut self, r: Option<DropRequest>, error: Option<String>) {
        self.target_id = r.as_ref().map(|r| r.target_id.clone()).unwrap_or_default();
        self.position = r.as_ref().map(|r| r.position);
        self.allowed = error.is_none();
        self.reason = error.unwrap_or_default();
        self.request = r;
    }
    fn finish(&mut self, p: DragPointer) -> Option<DropRequest> {
        if p.action != DragAction::Up {
            return None;
        }
        let active = self.phase == "dragging";
        let request = if active && self.allowed {
            self.request.clone()
        } else {
            None
        };
        self.cancel();
        self.result = if request.is_some() {
            "drop"
        } else if active {
            "reject"
        } else {
            ""
        }
        .into();
        request
    }
}
fn revision(parts: Vec<String>) -> u64 {
    let mut hash = 14695981039346656037u64;
    for s in parts {
        for b in format!("{}:{s}", s.len()).bytes() {
            hash ^= u64::from(b);
            hash = hash.wrapping_mul(1099511628211);
        }
    }
    hash
}
fn locked(o: &DragOptions, id: &str) -> bool {
    o.locked.iter().any(|v| v == id)
}
fn tab_state_revision(s: &TabState) -> u64 {
    revision(vec![
        s.active.clone(),
        s.focused.clone(),
        s.first.to_string(),
    ])
}
fn tree_state_revision(s: &TreeState) -> u64 {
    let mut parts = vec![
        s.selected.clone(),
        s.scroll.to_string(),
        s.horizontal.to_string(),
    ];
    parts.extend(s.expanded.iter().cloned());
    revision(parts)
}
impl Tabs {
    fn drag_revision(&self) -> u64 {
        revision(
            self.items
                .iter()
                .flat_map(|i| {
                    [
                        i.id.clone(),
                        i.title.clone(),
                        i.edited.to_string(),
                        i.closable.to_string(),
                        i.disabled.to_string(),
                    ]
                })
                .collect(),
        )
    }
    pub fn items(&self) -> &[TabItem] {
        &self.items
    }
    pub fn request_drop(
        &self,
        source: &str,
        target: &str,
        position: DropPosition,
        o: &DragOptions,
        allow: DropPolicy<'_>,
    ) -> Result<DropRequest, String> {
        if locked(o, source) || locked(o, target) {
            return Err("locked".into());
        }
        let r = DropRequest {
            source_id: source.into(),
            target_id: target.into(),
            position,
            revision: self.drag_revision(),
        };
        self.apply_drop(&r)?;
        if allow.is_some_and(|f| !f(&r)) {
            return Err("policy".into());
        }
        Ok(r)
    }
    /// Apply only after host approval. The source model is never mutated.
    pub fn apply_drop(&self, r: &DropRequest) -> Result<Self, String> {
        if r.revision != self.drag_revision() {
            return Err("stale".into());
        }
        if r.source_id == r.target_id {
            return Err("self".into());
        }
        if r.position == DropPosition::Inside {
            return Err("position".into());
        }
        let source = self
            .items
            .iter()
            .position(|i| i.id == r.source_id)
            .ok_or("missing")?;
        let mut target = self
            .items
            .iter()
            .position(|i| i.id == r.target_id)
            .ok_or("missing")?;
        if self.items[source].disabled || self.items[target].disabled {
            return Err("disabled".into());
        }
        let mut items = self.items.clone();
        let item = items.remove(source);
        if source < target {
            target -= 1
        }
        if r.position == DropPosition::After {
            target += 1
        }
        if source == target {
            return Err("unchanged".into());
        }
        items.insert(target, item);
        Self::new(items)
    }
    pub fn keyboard_drop(
        &self,
        s: &TabState,
        m: DragMove,
        o: &DragOptions,
        allow: DropPolicy<'_>,
    ) -> Result<DropRequest, String> {
        let i = self
            .items
            .iter()
            .position(|v| v.id == s.focused)
            .ok_or("missing")?;
        let (target, pos) = match m {
            DragMove::Previous => (i.checked_sub(1).ok_or("missing")?, DropPosition::Before),
            DragMove::Next => (i + 1, DropPosition::After),
            _ => return Err("position".into()),
        };
        let target = self.items.get(target).ok_or("missing")?;
        self.request_drop(&s.focused, &target.id, pos, o, allow)
    }
    pub fn drag_layout(&self, s: &mut TabState, d: &mut DragState, width: usize) -> TabLayout {
        if !d.captured() {
            return self.layout(s, width);
        }
        if d.revision != self.drag_revision()
            || d.width != width
            || d.state_revision != tab_state_revision(s)
        {
            d.cancel();
            d.result = "stale".into();
            return self.layout(s, width);
        }
        let first = d.first.min(self.items.len().saturating_sub(1));
        let mut out = TabLayout {
            previous: first > 0,
            ..TabLayout::default()
        };
        if width <= 2 {
            return out;
        }
        let mut x = 1;
        for item in self.items.iter().skip(first) {
            if x >= width - 1 {
                break;
            }
            let w = (width - 1 - x).min((cells(&clean(&item.title)) + 5).clamp(6, 24));
            let active = item.id == s.active;
            let focused = item.id == s.focused;
            let (left, right) = if active { ("[", "]") } else { (" ", " ") };
            let mark = if focused { ">" } else { " " };
            let suffix = format!(
                "{}{}",
                if item.edited { " *" } else { "" },
                if item.closable { " x" } else { "" }
            );
            let text = cell_text(
                &format!(
                    "{mark}{left}{}{suffix}{right}",
                    cell_text(&item.title, w.saturating_sub(3 + suffix.len()))
                ),
                w,
            );
            out.cells.push(TabCell {
                id: item.id.clone(),
                text,
                start: x,
                width: w,
                active,
                focused,
                disabled: item.disabled,
            });
            x += w;
        }
        out.next = first + out.cells.len() < self.items.len();
        out
    }
    /// Route captured move/up even outside the viewport; up rechecks policy.
    pub fn drag(
        &self,
        s: &mut TabState,
        d: &mut DragState,
        p: DragPointer,
        o: &DragOptions,
        allow: DropPolicy<'_>,
    ) -> Option<DropRequest> {
        if p.action == DragAction::Down {
            d.cancel();
            if p.x < 0 || p.x as usize >= p.width || p.y != 0 || p.height == 0 {
                return None;
            }
            let layout = self.layout(s, p.width);
            for c in layout.cells {
                if p.x as usize >= c.start
                    && (p.x as usize) < c.start + c.width
                    && !c.disabled
                    && !locked(o, &c.id)
                {
                    d.begin(c.id, self.drag_revision(), p);
                    d.first = s.first;
                    d.state_revision = tab_state_revision(s);
                    break;
                }
            }
            return None;
        }
        if d.captured() && d.state_revision != tab_state_revision(s) {
            d.cancel();
            d.result = "stale".into();
            return None;
        }
        if !d.prepare(self.drag_revision(), p, o) {
            return None;
        }
        if d.phase == "dragging" {
            if o.auto_scroll && p.action == DragAction::Move {
                if p.x <= 0 {
                    d.first = d.first.saturating_sub(1)
                } else if p.x as usize >= p.width.saturating_sub(1) {
                    d.first = (d.first + 1).min(self.items.len().saturating_sub(1))
                }
            }
            let mut request = None;
            let mut error = Some("outside".into());
            if p.x >= 0 && (p.x as usize) < p.width && p.y == 0 {
                let layout = self.drag_layout(s, d, p.width);
                for c in layout.cells {
                    if p.x as usize >= c.start && (p.x as usize) < c.start + c.width {
                        let pos = if p.x as usize - c.start >= c.width / 2 {
                            DropPosition::After
                        } else {
                            DropPosition::Before
                        };
                        let raw = DropRequest {
                            source_id: d.source_id.clone(),
                            target_id: c.id.clone(),
                            position: pos,
                            revision: d.revision,
                        };
                        let result = self.request_drop(&d.source_id, &c.id, pos, o, allow);
                        error = result.err();
                        request = Some(raw);
                        break;
                    }
                }
            }
            d.preview(request, error);
        }
        d.finish(p)
    }
}
impl Tree {
    fn drag_revision(&self) -> u64 {
        revision(
            self.rows
                .iter()
                .flat_map(|r| {
                    let n = &r.node;
                    [
                        n.id.clone(),
                        n.parent.clone(),
                        n.name.clone(),
                        n.secondary.clone(),
                        n.icon.clone(),
                        n.ascii_icon.clone(),
                        n.count.map(|n| n.to_string()).unwrap_or_default(),
                        n.branch.to_string(),
                    ]
                })
                .collect(),
        )
    }
    pub fn nodes(&self) -> Vec<TreeNode> {
        self.rows.iter().map(|r| r.node.clone()).collect()
    }
    pub fn request_drop(
        &self,
        source: &str,
        target: &str,
        position: DropPosition,
        o: &DragOptions,
        allow: DropPolicy<'_>,
    ) -> Result<DropRequest, String> {
        if locked(o, source) || locked(o, target) {
            return Err("locked".into());
        }
        let r = DropRequest {
            source_id: source.into(),
            target_id: target.into(),
            position,
            revision: self.drag_revision(),
        };
        self.apply_drop(&r)?;
        if allow.is_some_and(|f| !f(&r)) {
            return Err("policy".into());
        }
        Ok(r)
    }
    pub fn apply_drop(&self, r: &DropRequest) -> Result<Self, String> {
        if r.revision != self.drag_revision() {
            return Err("stale".into());
        }
        let si = *self.index.get(&r.source_id).ok_or("missing")?;
        let ti = *self.index.get(&r.target_id).ok_or("missing")?;
        if si == ti {
            return Err("self".into());
        }
        let mut id = r.target_id.as_str();
        while !id.is_empty() {
            if id == r.source_id {
                return Err("cycle".into());
            }
            id = &self.rows[self.index[id]].node.parent;
        }
        if r.position == DropPosition::Inside && !self.rows[ti].node.branch {
            return Err("leaf".into());
        }
        let mut end = si + 1;
        while end < self.rows.len() && self.rows[end].depth > self.rows[si].depth {
            end += 1
        }
        let mut all = self.nodes();
        let mut block: Vec<_> = all.drain(si..end).collect();
        let mut pos = all
            .iter()
            .position(|n| n.id == r.target_id)
            .ok_or("missing")?;
        let parent = if r.position == DropPosition::Inside {
            all[pos].id.clone()
        } else {
            all[pos].parent.clone()
        };
        if r.position != DropPosition::Before {
            let depth = self.rows[ti].depth;
            pos += 1;
            while pos < all.len() && self.rows[self.index[&all[pos].id]].depth > depth {
                pos += 1
            }
        }
        block[0].parent = parent;
        all.splice(pos..pos, block);
        if all
            .iter()
            .zip(&self.rows)
            .all(|(n, r)| n.id == r.node.id && n.parent == r.node.parent)
        {
            return Err("unchanged".into());
        }
        Self::new(all)
    }
    pub fn keyboard_drop(
        &self,
        s: &TreeState,
        m: DragMove,
        o: &DragOptions,
        allow: DropPolicy<'_>,
    ) -> Result<DropRequest, String> {
        let i = *self.index.get(&s.selected).ok_or("missing")?;
        let n = &self.rows[i].node;
        if matches!(m, DragMove::Outside) && !n.parent.is_empty() {
            return self.request_drop(&n.id, &n.parent, DropPosition::After, o, allow);
        }
        let siblings: Vec<_> = self
            .rows
            .iter()
            .filter(|r| r.node.parent == n.parent)
            .collect();
        let current = siblings
            .iter()
            .position(|r| r.node.id == n.id)
            .ok_or("missing")?;
        let (target, pos) = match m {
            DragMove::Previous => (
                current.checked_sub(1).ok_or("missing")?,
                DropPosition::Before,
            ),
            DragMove::Next => (current + 1, DropPosition::After),
            DragMove::Inside => (
                current.checked_sub(1).ok_or("missing")?,
                DropPosition::Inside,
            ),
            _ => return Err("position".into()),
        };
        let target = siblings.get(target).ok_or("missing")?;
        self.request_drop(&n.id, &target.node.id, pos, o, allow)
    }
    pub fn drag_rows(
        &self,
        s: &mut TreeState,
        d: &mut DragState,
        height: usize,
    ) -> (Vec<TreeRow>, usize) {
        if !d.captured() {
            let rows = self.reconcile(s, height);
            return (rows, s.scroll);
        }
        if d.revision != self.drag_revision()
            || d.height != height
            || d.state_revision != tree_state_revision(s)
        {
            d.cancel();
            d.result = "stale".into();
            let rows = self.reconcile(s, height);
            return (rows, s.scroll);
        }
        let preview = TreeState {
            expanded: d.expanded.clone(),
            ..s.clone()
        };
        let rows = self.visible(&preview);
        d.scroll = d.scroll.min(rows.len().saturating_sub(height.max(1)));
        (rows, d.scroll)
    }
    pub fn drag(
        &self,
        s: &mut TreeState,
        d: &mut DragState,
        p: DragPointer,
        o: &DragOptions,
        allow: DropPolicy<'_>,
    ) -> Option<DropRequest> {
        if p.action == DragAction::Down {
            d.cancel();
            if p.x < 0 || p.x as usize >= p.width || p.y < 0 || p.y as usize >= p.height {
                return None;
            }
            let rows = self.visible(s);
            let target = rows.get(s.scroll + p.y as usize)?;
            if locked(o, &target.node.id) {
                return None;
            }
            d.begin(target.node.id.clone(), self.drag_revision(), p);
            d.scroll = s.scroll;
            d.state_revision = tree_state_revision(s);
            d.expanded = s.expanded.clone();
            return None;
        }
        if d.captured() && d.state_revision != tree_state_revision(s) {
            d.cancel();
            d.result = "stale".into();
            return None;
        }
        if !d.prepare(self.drag_revision(), p, o) {
            return None;
        }
        if d.phase == "dragging" {
            let (rows, scroll) = self.drag_rows(s, d, p.height);
            if o.auto_scroll && p.action == DragAction::Move {
                if p.y <= 0 {
                    d.scroll = scroll.saturating_sub(1)
                } else if p.y as usize >= p.height.saturating_sub(1) {
                    d.scroll = (scroll + 1).min(rows.len().saturating_sub(p.height.max(1)))
                }
            }
            let mut request = None;
            let mut error = Some("outside".into());
            if p.x >= 0 && (p.x as usize) < p.width && p.y >= 0 && (p.y as usize) < p.height {
                if let Some(target) = rows.get(d.scroll + p.y as usize) {
                    let position = if p.x as usize <= 2 + target.depth * 2 {
                        DropPosition::Before
                    } else if target.node.branch && (p.x as usize) < p.width.saturating_sub(2) {
                        DropPosition::Inside
                    } else {
                        DropPosition::After
                    };
                    let raw = DropRequest {
                        source_id: d.source_id.clone(),
                        target_id: target.node.id.clone(),
                        position,
                        revision: d.revision,
                    };
                    let result =
                        self.request_drop(&d.source_id, &target.node.id, position, o, allow);
                    error = result.err();
                    if error.is_none() && o.hover_expand && position == DropPosition::Inside {
                        d.expanded.insert(target.node.id.clone());
                    }
                    request = Some(raw);
                }
            }
            d.preview(request, error);
        }
        d.finish(p)
    }
}
