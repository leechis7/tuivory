//! Terminal-cell spacing, geometry and supporting literal components.
use crate::{
    Error,
    components::{cell_text, cells},
    forms::ComponentLine,
    interaction::ControlState,
};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Density {
    Auto,
    Compact,
    Comfortable,
}
impl std::str::FromStr for Density {
    type Err = Error;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "auto" => Ok(Self::Auto),
            "compact" => Ok(Self::Compact),
            "comfortable" => Ok(Self::Comfortable),
            _ => Err(Error::Invalid("invalid density".into())),
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SpacingTokens {
    pub gap: usize,
    pub padding: usize,
    pub control_gap: usize,
    pub compact_below: usize,
}
impl SpacingTokens {
    pub fn for_width(density: Density, columns: usize) -> Self {
        let density = if density == Density::Auto {
            if columns < 80 {
                Density::Compact
            } else {
                Density::Comfortable
            }
        } else {
            density
        };
        match density {
            Density::Compact => Self {
                gap: 0,
                padding: 0,
                control_gap: 1,
                compact_below: 80,
            },
            _ => Self {
                gap: 2,
                padding: 1,
                control_gap: 2,
                compact_below: 80,
            },
        }
    }
}
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(default)]
pub struct CellRect {
    pub x: usize,
    pub y: usize,
    pub width: usize,
    pub height: usize,
}
impl CellRect {
    pub fn inset(self, padding: usize) -> Self {
        Self {
            x: self.x + padding.min(self.width),
            y: self.y + padding.min(self.height),
            width: self.width.saturating_sub(padding.saturating_mul(2)),
            height: self.height.saturating_sub(padding.saturating_mul(2)),
        }
    }
}
#[derive(Clone, Debug)]
pub struct StackItem {
    pub id: String,
    pub min: usize,
    pub preferred: usize,
    pub weight: usize,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StackSlot {
    pub id: String,
    pub start: usize,
    pub size: usize,
}
#[derive(Clone, Debug, Default)]
pub struct StackResult {
    pub slots: Vec<StackSlot>,
    pub hidden: Vec<String>,
    pub gap: usize,
}
pub fn stack_layout(
    items: &[StackItem],
    total: usize,
    mut gap: usize,
) -> Result<StackResult, Error> {
    let mut r = StackResult::default();
    if total > 1000000000 || gap > 1024 {
        return Err(Error::Invalid("invalid stack extent/gap".into()));
    }
    let mut seen = std::collections::BTreeSet::new();
    let mut minimum = 0;
    for item in items {
        if item.id.is_empty()
            || !seen.insert(&item.id)
            || item.min == 0
            || item.min > 1000000
            || item.preferred > 1000000
            || item.weight > 1000000
        {
            return Err(Error::Invalid("invalid stack item".into()));
        }
        minimum += item.min
    }
    if items.is_empty() {
        return Ok(r);
    }
    let gaps = gap.saturating_mul(items.len() - 1);
    let mut available = if gaps > total || total - gaps < minimum {
        gap = 0;
        total
    } else {
        total - gaps
    };
    r.gap = gap;
    let mut sizes = vec![0; items.len()];
    let mut active = vec![false; items.len()];
    for (i, item) in items.iter().enumerate() {
        if item.min > available && i > 0 {
            continue;
        }
        sizes[i] = item.min.min(available);
        available -= sizes[i];
        active[i] = true
    }
    for (i, item) in items.iter().enumerate() {
        if !active[i] {
            continue;
        }
        let add = item.preferred.saturating_sub(sizes[i]).min(available);
        sizes[i] += add;
        available -= add
    }
    let weights: usize = items
        .iter()
        .enumerate()
        .filter(|(i, _)| active[*i])
        .map(|(_, s)| s.weight)
        .sum();
    if weights > 0 {
        let extra = available;
        for (i, s) in items.iter().enumerate() {
            if !active[i] {
                continue;
            }
            let add = extra * s.weight / weights;
            sizes[i] += add;
            available -= add
        }
        for (i, s) in items.iter().enumerate() {
            if available == 0 {
                break;
            }
            if active[i] && s.weight > 0 {
                sizes[i] += 1;
                available -= 1
            }
        }
    }
    let mut start = 0;
    let mut visible = 0;
    for (i, s) in items.iter().enumerate() {
        if sizes[i] == 0 {
            r.hidden.push(s.id.clone());
            r.slots.push(StackSlot {
                id: s.id.clone(),
                start,
                size: 0,
            });
            continue;
        }
        if visible > 0 {
            start += gap
        }
        r.slots.push(StackSlot {
            id: s.id.clone(),
            start,
            size: sizes[i],
        });
        start += sizes[i];
        visible += 1
    }
    Ok(r)
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NamedRect {
    pub id: String,
    pub rect: CellRect,
}
pub fn stack_rects(
    parent: CellRect,
    items: &[StackItem],
    tokens: SpacingTokens,
    vertical: bool,
) -> Result<(Vec<NamedRect>, Vec<String>), Error> {
    if tokens.padding > 1024 {
        return Err(Error::Invalid("invalid padding".into()));
    }
    let inner = parent.inset(tokens.padding);
    let result = stack_layout(
        items,
        if vertical { inner.height } else { inner.width },
        tokens.gap,
    )?;
    let rects: Vec<NamedRect> = result
        .slots
        .into_iter()
        .map(|s| {
            let mut rect = inner;
            if vertical {
                rect.y += s.start;
                rect.height = s.size
            } else {
                rect.x += s.start;
                rect.width = s.size
            }
            NamedRect { id: s.id, rect }
        })
        .collect();
    let hidden = rects
        .iter()
        .filter(|r| r.rect.width == 0 || r.rect.height == 0)
        .map(|r| r.id.clone())
        .collect();
    Ok((rects, hidden))
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DrawerPlacement {
    pub rect: CellRect,
    pub overlay: bool,
}
pub fn drawer_layout(parent: CellRect, preferred: usize, min_content: usize) -> DrawerPlacement {
    let mut rect = parent;
    rect.width = rect.width.min(preferred);
    DrawerPlacement {
        rect,
        overlay: parent.width < preferred.saturating_add(min_content),
    }
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct ComponentEvent {
    pub kind: String,
    pub id: String,
}
#[derive(Clone, Debug, Default)]
pub struct Badge {
    pub id: String,
    pub label: String,
    pub count: Option<u64>,
    pub limit: u64,
    pub state: ControlState,
}
impl Badge {
    pub fn line(&self, width: usize) -> ComponentLine {
        let mut text = self.label.clone();
        if let Some(count) = self.count {
            let limit = if self.limit == 0 { 99 } else { self.limit };
            text.push_str(&format!(
                " [{}]",
                if count > limit {
                    format!("{limit}+")
                } else {
                    count.to_string()
                }
            ))
        }
        let v = self.state.visual();
        ComponentLine {
            id: self.id.clone(),
            text: cell_text(
                &format!("{}{text}", v.markers.trim_start_matches('-')),
                width,
            ),
            role: v.role.into(),
            ..Default::default()
        }
    }
}
#[derive(Clone, Debug, Default)]
pub struct Chip {
    pub id: String,
    pub label: String,
    pub state: ControlState,
    pub removable: bool,
}
impl Chip {
    pub fn line(&self, width: usize) -> ComponentLine {
        let v = self.state.visual();
        let prefix = format!("{}[", v.markers.trim_start_matches('-'));
        let suffix = if self.removable { "] x" } else { "]" };
        ComponentLine {
            id: self.id.clone(),
            text: cell_text(
                &format!(
                    "{prefix}{}{suffix}",
                    cell_text(
                        &self.label,
                        width.saturating_sub(cells(&prefix) + cells(suffix))
                    )
                ),
                width,
            ),
            role: v.role.into(),
            value: "remove".into(),
            ..Default::default()
        }
    }
    pub fn request_remove(&self) -> ComponentEvent {
        if !self.id.is_empty() && self.removable && self.state.visual().editable {
            ComponentEvent {
                kind: "remove".into(),
                id: self.id.clone(),
            }
        } else {
            ComponentEvent::default()
        }
    }
}
#[derive(Clone, Debug, Default)]
pub struct Shortcut {
    pub key: String,
    pub text: String,
    pub priority: i32,
    pub disabled: bool,
}
#[derive(Clone, Debug)]
pub struct Help {
    items: Vec<Shortcut>,
}
impl Help {
    pub fn new(mut items: Vec<Shortcut>) -> Result<Self, Error> {
        let mut seen = std::collections::BTreeSet::new();
        for item in &items {
            let key = item.key.trim().to_lowercase();
            if key.is_empty() || !seen.insert(key) {
                return Err(Error::Invalid("empty or duplicate shortcut".into()));
            }
        }
        items.sort_by(|a, b| b.priority.cmp(&a.priority));
        Ok(Self { items })
    }
    pub fn layout(&self, width: usize, height: usize) -> Vec<ComponentLine> {
        let limit = if self.items.len() > height && height > 1 {
            height - 1
        } else {
            height
        };
        let mut rows: Vec<_> = self
            .items
            .iter()
            .take(limit)
            .map(|s| ComponentLine {
                text: cell_text(&format!("[{}] {}", s.key, s.text), width),
                role: if s.disabled { "disabled" } else { "body" }.into(),
                ..Default::default()
            })
            .collect();
        if self.items.len() > limit && height > rows.len() {
            rows.push(ComponentLine {
                text: cell_text(&format!("+{}", self.items.len() - limit), width),
                role: "hint".into(),
                ..Default::default()
            })
        }
        rows
    }
}
