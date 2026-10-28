//! Shared tabs, split geometry, breadcrumbs, and priority status layout.
//! Models return requests and literal cell ranges; hosts own application data.
use unicode_segmentation::UnicodeSegmentation;
use unicode_width::UnicodeWidthStr;

pub fn clean(text: &str) -> String {
    text.chars()
        .map(|c| if c.is_control() { ' ' } else { c })
        .collect()
}
pub fn cells(text: &str) -> usize {
    UnicodeWidthStr::width(text)
}
pub fn cell_text(text: &str, width: usize) -> String {
    let text = clean(text);
    if cells(&text) <= width {
        return text;
    }
    if width == 0 {
        return String::new();
    }
    let mut result = String::new();
    let mut used = 0;
    for cluster in text.graphemes(true) {
        let w = cells(cluster);
        if used + w > width - 1 {
            break;
        }
        result.push_str(cluster);
        used += w
    }
    result.push('~');
    result
}
pub(crate) fn tail_cells(text: &str, width: usize) -> String {
    let text = clean(text);
    if cells(&text) <= width {
        return text;
    }
    if width == 0 {
        return String::new();
    }
    let clusters: Vec<_> = text.graphemes(true).collect();
    let mut start = clusters.len();
    let mut used = 0;
    while start > 0 {
        let w = cells(clusters[start - 1]);
        if used + w > width - 1 {
            break;
        }
        used += w;
        start -= 1
    }
    format!("~{}", clusters[start..].concat())
}
#[derive(Clone, Debug, Default)]
pub struct TabItem {
    pub id: String,
    pub title: String,
    pub edited: bool,
    pub closable: bool,
    pub disabled: bool,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct TabState {
    pub active: String,
    pub focused: String,
    pub first: usize,
}
#[derive(Clone, Copy, Debug)]
pub enum TabAction {
    Previous,
    Next,
    First,
    Last,
    Activate,
    Close,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TabEvent {
    Focus(String),
    Activate(String),
    Close(String),
}
#[derive(Clone, Debug)]
pub struct TabCell {
    pub id: String,
    pub text: String,
    pub start: usize,
    pub width: usize,
    pub active: bool,
    pub focused: bool,
    pub disabled: bool,
}
#[derive(Clone, Debug, Default)]
pub struct TabLayout {
    pub cells: Vec<TabCell>,
    pub previous: bool,
    pub next: bool,
}
#[derive(Clone, Debug)]
pub struct Tabs {
    items: Vec<TabItem>,
}
impl Tabs {
    pub fn new(items: Vec<TabItem>) -> Result<Self, String> {
        let mut seen = std::collections::BTreeSet::new();
        for item in &items {
            if item.id.is_empty() || !seen.insert(item.id.clone()) {
                return Err(format!("tabs: empty/duplicate ID {:?}", item.id));
            }
        }
        Ok(Self { items })
    }
    pub fn reconcile(&self, state: &mut TabState) {
        let enabled: Vec<_> = self.items.iter().filter(|t| !t.disabled).collect();
        if !enabled.iter().any(|t| t.id == state.active) {
            state.active = enabled.first().map(|t| t.id.clone()).unwrap_or_default()
        }
        if !enabled.iter().any(|t| t.id == state.focused) {
            state.focused = state.active.clone()
        }
        state.first = state.first.min(self.items.len().saturating_sub(1));
    }
    pub fn handle(&self, state: &mut TabState, action: TabAction) -> Option<TabEvent> {
        self.reconcile(state);
        let enabled: Vec<_> = self.items.iter().filter(|t| !t.disabled).collect();
        let mut index = enabled.iter().position(|t| t.id == state.focused)?;
        let item = enabled[index];
        match action {
            TabAction::Activate => {
                state.active = item.id.clone();
                return Some(TabEvent::Activate(item.id.clone()));
            }
            TabAction::Close => return item.closable.then(|| TabEvent::Close(item.id.clone())),
            TabAction::Previous => index = index.saturating_sub(1),
            TabAction::Next => index = (index + 1).min(enabled.len() - 1),
            TabAction::First => index = 0,
            TabAction::Last => index = enabled.len() - 1,
        }
        let target = &enabled[index].id;
        if *target != state.focused {
            state.focused = target.clone();
            return Some(TabEvent::Focus(target.clone()));
        }
        None
    }
    fn item_width(item: &TabItem) -> usize {
        (cells(&clean(&item.title)) + 5).clamp(6, 24)
    }
    pub fn layout(&self, state: &mut TabState, width: usize) -> TabLayout {
        self.reconcile(state);
        let mut result = TabLayout::default();
        if width <= 2 || self.items.is_empty() {
            return result;
        }
        let target = self
            .items
            .iter()
            .position(|t| t.id == state.focused)
            .unwrap_or(0);
        state.first = state.first.min(target);
        while state.first < target
            && self.items[state.first..=target]
                .iter()
                .map(Self::item_width)
                .sum::<usize>()
                > width - 2
        {
            state.first += 1
        }
        while state.first > 0
            && self.items[state.first - 1..=target]
                .iter()
                .map(Self::item_width)
                .sum::<usize>()
                <= width - 2
        {
            state.first -= 1;
        }
        let mut x = 1;
        for item in self.items.iter().skip(state.first) {
            if x >= width - 1 {
                break;
            }
            let w = Self::item_width(item).min(width - 1 - x);
            if w < 4 && !result.cells.is_empty() {
                break;
            }
            let active = item.id == state.active;
            let focused = item.id == state.focused;
            let (left, right) = if active { ("[", "]") } else { (" ", " ") };
            let mark = if item.disabled {
                "-"
            } else if focused {
                ">"
            } else {
                " "
            };
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
            result.cells.push(TabCell {
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
        result.previous = state.first > 0;
        result.next = state.first + result.cells.len() < self.items.len();
        result
    }
    pub fn click(&self, state: &mut TabState, column: usize, width: usize) -> Option<TabEvent> {
        let layout = self.layout(state, width);
        if column == 0 && layout.previous {
            return self.handle(state, TabAction::Previous);
        }
        if width > 0 && column == width - 1 && layout.next {
            return self.handle(state, TabAction::Next);
        }
        for cell in layout.cells {
            if column >= cell.start && column < cell.start + cell.width && !cell.disabled {
                state.focused = cell.id.clone();
                let visible_close = cell.text.ends_with("x]") || cell.text.ends_with("x ");
                if visible_close
                    && self.items.iter().any(|t| t.id == cell.id && t.closable)
                    && column == cell.start + cells(&cell.text) - 2
                {
                    return Some(TabEvent::Close(cell.id));
                }
                state.active = cell.id.clone();
                return Some(TabEvent::Activate(cell.id));
            }
        }
        None
    }
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct SplitState {
    pub preferred: usize,
}
#[derive(Clone, Copy, Debug)]
pub struct SplitSpec {
    pub first_min: usize,
    pub second_min: usize,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct SplitLayout {
    pub first: usize,
    pub divider: usize,
    pub second: usize,
    pub compact: bool,
}
impl SplitSpec {
    pub fn layout(self, state: &SplitState, total: usize) -> SplitLayout {
        let a = self.first_min.max(1);
        let b = self.second_min.max(1);
        if total < a.saturating_add(b).saturating_add(1) {
            return SplitLayout {
                second: total,
                compact: true,
                ..Default::default()
            };
        }
        let preferred = if state.preferred == 0 {
            (total - 1) / 2
        } else {
            state.preferred
        };
        let first = preferred.clamp(a, total - 1 - b);
        SplitLayout {
            first,
            divider: 1,
            second: total - first - 1,
            compact: false,
        }
    }
    pub fn resize(self, state: &mut SplitState, total: usize, position: usize) -> bool {
        let layout = self.layout(state, total);
        if layout.compact {
            return false;
        }
        let next = position.clamp(self.first_min.max(1), total - 1 - self.second_min.max(1));
        let changed = next != layout.first;
        state.preferred = next;
        changed
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LineRun {
    pub text: String,
    pub role: String,
    pub id: String,
    pub start: usize,
    pub width: usize,
}
impl LineRun {
    fn new(text: &str, role: &str, id: &str, start: usize) -> Self {
        let text = clean(text);
        let width = cells(&text);
        Self {
            text,
            role: role.into(),
            id: id.into(),
            start,
            width,
        }
    }
}
#[derive(Clone, Debug)]
pub struct PathItem {
    pub id: String,
    pub label: String,
}
pub fn breadcrumbs(items: &[PathItem], width: usize) -> Vec<LineRun> {
    let mut result = Vec::new();
    if items.is_empty() || width == 0 {
        return result;
    }
    let mut x = 0;
    let mut add = |text: &str, id: &str, role: &str| {
        let run = LineRun::new(text, role, id, x);
        x += run.width;
        result.push(run)
    };
    let full = items.iter().map(|p| cells(&clean(&p.label))).sum::<usize>() + 3 * (items.len() - 1);
    if full <= width {
        for (i, item) in items.iter().enumerate() {
            if i > 0 {
                add(" / ", "", "hint")
            }
            add(
                &item.label,
                &item.id,
                if i == items.len() - 1 { "body" } else { "hint" },
            )
        }
        return result;
    }
    let last = items.last().unwrap();
    let mut used = 0;
    let prefix = if items.len() > 2
        && cells(&clean(&items[0].label)) + 9 + cells(&clean(&last.label)) <= width
    {
        add(&items[0].label, &items[0].id, "hint");
        used = cells(&clean(&items[0].label));
        " / ... / "
    } else if items.len() > 1 && width >= 7 {
        "... / "
    } else {
        ""
    };
    add(prefix, "", "hint");
    used += cells(prefix);
    add(&tail_cells(&last.label, width - used), &last.id, "body");
    result
}
#[derive(Clone, Debug)]
pub struct StatusItem {
    pub id: String,
    pub text: String,
    pub role: String,
    pub priority: i32,
}
#[derive(Clone, Debug, Default)]
pub struct StatusLayout {
    pub runs: Vec<LineRun>,
    pub omitted: usize,
}
pub fn status_line(items: &[StatusItem], width: usize) -> StatusLayout {
    let mut sorted: Vec<_> = items.iter().collect();
    sorted.sort_by_key(|i| std::cmp::Reverse(i.priority));
    let mut result = StatusLayout {
        runs: Vec::new(),
        omitted: sorted.len(),
    };
    if width == 0 {
        return result;
    }
    let mut x = 0;
    let mut included = 0;
    for (i, item) in sorted.iter().enumerate() {
        let reserve = if i + 1 < sorted.len() {
            format!(" +{}", sorted.len() - i - 1).len()
        } else {
            0
        };
        let mut separator = if included > 0 { " | " } else { "" };
        let prefix = match item.role.as_str() {
            "warning" | "error" => "! ",
            "edited" => "* ",
            "success" => "+ ",
            "info" => "i ",
            _ => "",
        };
        let mut text = format!("{prefix}{}", clean(&item.text));
        let needed = cells(separator) + cells(&text);
        if needed + reserve > width - x {
            if included > 0 {
                break;
            }
            let available = width
                .checked_sub(reserve)
                .filter(|w| *w > 0)
                .unwrap_or(width);
            text = if available == 1 && !prefix.is_empty() {
                prefix[..1].into()
            } else {
                cell_text(&text, available)
            };
            separator = "";
        }
        if !separator.is_empty() {
            result.runs.push(LineRun::new(separator, "hint", "", x));
            x += 3
        }
        let role = if item.role.is_empty() {
            "body"
        } else {
            &item.role
        };
        let run = LineRun::new(&text, role, &item.id, x);
        x += run.width;
        result.runs.push(run);
        included += 1;
        if needed + reserve > width {
            break;
        }
    }
    result.omitted = sorted.len() - included;
    if result.omitted > 0 {
        let marker = format!(" +{}", result.omitted);
        if x + marker.len() <= width {
            result.runs.push(LineRun::new(&marker, "hint", "", x))
        }
    }
    result
}
