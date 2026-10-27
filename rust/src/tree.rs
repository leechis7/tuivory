//! Framework-independent tree data, state, and actions. Hosts retain stable IDs
//! and handle returned events; no data loading or terminal I/O occurs here.
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, Default)]
pub struct TreeNode {
    pub id: String,
    pub parent: String,
    pub name: String,
    pub secondary: String,
    pub icon: String,
    pub ascii_icon: String,
    pub count: Option<u64>,
    /// Allows an unloaded branch to emit an expansion event.
    pub branch: bool,
}
#[derive(Clone, Debug)]
pub struct TreeRow {
    pub node: TreeNode,
    pub depth: usize,
}
#[derive(Clone, Debug)]
pub struct Tree {
    rows: Vec<TreeRow>,
    index: BTreeMap<String, usize>,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct TreeState {
    pub selected: String,
    pub expanded: BTreeSet<String>,
    pub scroll: usize,
    pub horizontal: usize,
}
#[derive(Clone, Copy, Debug)]
pub enum TreeAction {
    Up,
    Down,
    Left,
    Right,
    Toggle,
    Activate,
    Home,
    End,
    PageUp,
    PageDown,
    PanLeft,
    PanRight,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TreeEvent {
    Select(String),
    Expand(String),
    Collapse(String),
    Activate(String),
}

impl Tree {
    /// IDs must be nonempty/unique; a parent must precede its children.
    /// Nesting deeper than 128 levels is rejected rather than overflowing.
    pub fn new(nodes: Vec<TreeNode>) -> Result<Self, String> {
        let mut children: BTreeMap<String, Vec<TreeNode>> = BTreeMap::new();
        let mut seen = BTreeSet::new();
        for node in nodes {
            if node.id.is_empty()
                || seen.contains(&node.id)
                || (!node.parent.is_empty() && !seen.contains(&node.parent))
            {
                return Err(format!(
                    "tree: empty/duplicate ID or parent must precede child: {:?}",
                    node.id
                ));
            }
            seen.insert(node.id.clone());
            children.entry(node.parent.clone()).or_default().push(node);
        }
        let mut result = Self {
            rows: Vec::new(),
            index: BTreeMap::new(),
        };
        fn visit(
            parent: &str,
            depth: usize,
            children: &BTreeMap<String, Vec<TreeNode>>,
            result: &mut Tree,
        ) -> Result<(), String> {
            if let Some(nodes) = children.get(parent) {
                if depth > 128 {
                    return Err("tree: maximum depth is 128".into());
                }
                for node in nodes {
                    let mut node = node.clone();
                    node.branch |= children.contains_key(&node.id);
                    result.index.insert(node.id.clone(), result.rows.len());
                    result.rows.push(TreeRow {
                        node: node.clone(),
                        depth,
                    });
                    visit(&node.id, depth + 1, children, result)?;
                }
            }
            Ok(())
        }
        visit("", 0, &children, &mut result)?;
        Ok(result)
    }
    pub fn visible(&self, state: &TreeState) -> Vec<TreeRow> {
        let mut rows = Vec::new();
        let mut hidden = None;
        for row in &self.rows {
            if hidden.is_some_and(|depth| row.depth > depth) {
                continue;
            }
            hidden = None;
            rows.push(row.clone());
            if row.node.branch && !state.expanded.contains(&row.node.id) {
                hidden = Some(row.depth);
            }
        }
        rows
    }
    /// Reconcile stable state after data replacement or resize. Hidden selected
    /// children move to their nearest visible ancestor; removed IDs use row one.
    pub fn reconcile(&self, state: &mut TreeState, height: usize) -> Vec<TreeRow> {
        state.expanded.retain(|id| self.index.contains_key(id));
        let rows = self.visible(state);
        let visible: BTreeMap<&str, usize> = rows
            .iter()
            .enumerate()
            .map(|(i, r)| (r.node.id.as_str(), i))
            .collect();
        while !state.selected.is_empty() && !visible.contains_key(state.selected.as_str()) {
            state.selected = self
                .index
                .get(&state.selected)
                .map(|i| self.rows[*i].node.parent.clone())
                .unwrap_or_default();
        }
        if state.selected.is_empty() {
            state.selected = rows.first().map(|r| r.node.id.clone()).unwrap_or_default();
        }
        let height = height.max(1);
        state.horizontal = state.horizontal.min(u16::MAX as usize);
        state.scroll = state.scroll.min(rows.len().saturating_sub(height));
        if let Some(i) = visible.get(state.selected.as_str()) {
            if *i < state.scroll {
                state.scroll = *i;
            }
            if *i >= state.scroll + height {
                state.scroll = i - height + 1;
            }
        }
        rows
    }
    pub fn handle(
        &self,
        state: &mut TreeState,
        action: TreeAction,
        height: usize,
    ) -> Option<TreeEvent> {
        let rows = self.reconcile(state, height);
        let i = rows.iter().position(|r| r.node.id == state.selected)?;
        let node = &rows[i].node;
        let mut target = i;
        match action {
            TreeAction::Up => target = i.saturating_sub(1),
            TreeAction::Down => target = (i + 1).min(rows.len() - 1),
            TreeAction::Home => target = 0,
            TreeAction::End => target = rows.len() - 1,
            TreeAction::PageUp => target = i.saturating_sub(height.max(1)),
            TreeAction::PageDown => target = i.saturating_add(height.max(1)).min(rows.len() - 1),
            TreeAction::PanLeft => state.horizontal = state.horizontal.saturating_sub(4),
            TreeAction::PanRight => {
                state.horizontal = state.horizontal.saturating_add(4).min(u16::MAX as usize)
            }
            TreeAction::Activate => return Some(TreeEvent::Activate(node.id.clone())),
            TreeAction::Left => {
                if node.branch && state.expanded.remove(&node.id) {
                    self.reconcile(state, height);
                    return Some(TreeEvent::Collapse(node.id.clone()));
                }
                if !node.parent.is_empty() {
                    state.selected = node.parent.clone();
                }
            }
            TreeAction::Right | TreeAction::Toggle => {
                if node.branch {
                    if matches!(action, TreeAction::Toggle) && state.expanded.remove(&node.id) {
                        self.reconcile(state, height);
                        return Some(TreeEvent::Collapse(node.id.clone()));
                    }
                    if state.expanded.insert(node.id.clone()) {
                        self.reconcile(state, height);
                        return Some(TreeEvent::Expand(node.id.clone()));
                    }
                    if i + 1 < rows.len() && rows[i + 1].depth > rows[i].depth {
                        target += 1;
                    }
                }
            }
        }
        if target != i {
            state.selected = rows[target].node.id.clone();
        }
        self.reconcile(state, height);
        (state.selected != node.id).then(|| TreeEvent::Select(state.selected.clone()))
    }
    /// Coordinates are relative to the inner tree viewport. Clicking the
    /// disclosure toggles; other row clicks select without activation.
    pub fn click(
        &self,
        state: &mut TreeState,
        column: usize,
        row: usize,
        height: usize,
    ) -> Option<TreeEvent> {
        if row >= height {
            return None;
        }
        let rows = self.reconcile(state, height);
        let target = rows.get(state.scroll + row)?;
        let old = std::mem::replace(&mut state.selected, target.node.id.clone());
        if column >= 2 && column.checked_add(state.horizontal) == Some(2 + target.depth * 2) {
            if let Some(event) = self.handle(state, TreeAction::Toggle, height) {
                return Some(event);
            }
        }
        (old != state.selected).then(|| TreeEvent::Select(state.selected.clone()))
    }
}
