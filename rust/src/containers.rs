//! Backend-neutral layout execution and scoped input routing. Cells, stable IDs.
use crate::{
    Error,
    layout::{CellRect, NamedRect},
};
use serde::{Deserialize, Serialize};
#[derive(Clone, Copy, Debug, Default, Serialize, Deserialize)]
#[serde(default)]
pub struct Track {
    pub min: usize,
    pub max: usize,
    pub fixed: usize,
    pub weight: usize,
}
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
#[serde(default)]
pub struct LayoutItem {
    pub id: String,
    pub track: Track,
    pub row: usize,
    pub column: usize,
    pub row_span: usize,
    pub column_span: usize,
    pub hidden: bool,
    pub disabled: bool,
    pub drawer: String,
    pub modal: bool,
    pub centered: bool,
    pub area: CellRect,
}
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
#[serde(default)]
pub struct ContainerOptions {
    pub kind: String,
    pub gap: usize,
    pub padding: usize,
    pub rows: Vec<Track>,
    pub columns: Vec<Track>,
    pub virtual_width: usize,
    pub virtual_height: usize,
}
fn invalid() -> Error {
    Error::Invalid("invalid container constraints or items".into())
}
fn valid(t: Track) -> bool {
    t.min.max(t.max).max(t.fixed).max(t.weight) <= 1000000
        && (t.max == 0 || t.max >= t.min)
        && (t.max == 0 || t.fixed <= t.max)
}
fn allocate(tracks: &[Track], total: usize, gap: usize) -> Result<(Vec<usize>, usize), Error> {
    if tracks.len() > 1024 || tracks.iter().any(|t| !valid(*t)) {
        return Err(invalid());
    }
    if tracks.is_empty() {
        return Ok((vec![], 0));
    }
    let tracks: Vec<_> = tracks
        .iter()
        .map(|t| {
            let mut t = *t;
            if t.min == 0 && t.max == 0 && t.fixed == 0 && t.weight == 0 {
                t.weight = 1
            }
            t
        })
        .collect();
    let mut gap = gap.min(total / tracks.len());
    let mut available = total.saturating_sub(gap * (tracks.len() - 1));
    let minimum: usize = tracks.iter().map(|t| t.min.max(t.fixed)).sum();
    if minimum > available {
        gap = 0;
        available = total
    }
    let mut sizes = vec![0; tracks.len()];
    for (i, t) in tracks.iter().enumerate() {
        sizes[i] = available.min(t.min.max(t.fixed));
        available -= sizes[i]
    }
    while available > 0 {
        let weight: usize = tracks
            .iter()
            .enumerate()
            .filter(|(i, t)| t.fixed == 0 && t.weight > 0 && (t.max == 0 || sizes[*i] < t.max))
            .map(|(_, t)| t.weight)
            .sum();
        if weight == 0 {
            break;
        }
        let budget = available;
        let mut changed = false;
        for (i, t) in tracks.iter().enumerate() {
            if t.fixed > 0 || t.weight == 0 || t.max > 0 && sizes[i] >= t.max {
                continue;
            }
            let mut add = available
                .min(((budget as u64 * t.weight as u64) / weight as u64) as usize)
                .max(1)
                .min(available);
            if t.max > 0 {
                add = add.min(t.max - sizes[i])
            }
            sizes[i] += add;
            available -= add;
            changed |= add > 0
        }
        if !changed {
            break;
        }
    }
    Ok((sizes, gap))
}
pub fn compute_container(
    bounds: CellRect,
    items: &[LayoutItem],
    options: &ContainerOptions,
) -> Result<Vec<NamedRect>, Error> {
    if options.gap > 1024
        || options.padding > 1024
        || bounds
            .x
            .max(bounds.y)
            .max(bounds.width)
            .max(bounds.height)
            .max(options.virtual_width)
            .max(options.virtual_height)
            > 1000000
        || items.len() > 1024
        || !["row", "column", "grid", "layers"].contains(&options.kind.as_str())
    {
        return Err(invalid());
    }
    let mut seen = std::collections::BTreeSet::new();
    for item in items {
        if !item.drawer.is_empty()
            && (options.kind != "layers"
                || item.centered
                || !["left", "right"].contains(&item.drawer.as_str()))
        {
            return Err(invalid());
        }
        if item.id.is_empty()
            || !seen.insert(&item.id)
            || !valid(item.track)
            || item
                .area
                .x
                .max(item.area.y)
                .max(item.area.width)
                .max(item.area.height)
                > 1000000
        {
            return Err(invalid());
        }
    }
    let visible: Vec<_> = items.iter().filter(|i| !i.hidden).collect();
    let inner = bounds.inset(options.padding);
    let mut out = vec![];
    match options.kind.as_str() {
        "row" | "column" => {
            let tracks: Vec<_> = visible.iter().map(|i| i.track).collect();
            let total = if options.kind == "row" {
                inner.width
            } else {
                inner.height
            };
            let (sizes, gap) = allocate(&tracks, total, options.gap)?;
            let mut at = 0;
            for (i, item) in visible.iter().enumerate() {
                let mut r = inner;
                if options.kind == "row" {
                    r.x += at;
                    r.width = sizes[i]
                } else {
                    r.y += at;
                    r.height = sizes[i]
                }
                out.push(NamedRect {
                    id: item.id.clone(),
                    rect: r,
                });
                at += sizes[i] + gap
            }
        }
        "grid" => {
            let (widths, gx) = allocate(&options.columns, inner.width, options.gap)?;
            let (heights, gy) = allocate(&options.rows, inner.height, options.gap)?;
            for item in visible {
                let (rs, cs) = (item.row_span.max(1), item.column_span.max(1));
                if item.row >= heights.len()
                    || item.column >= widths.len()
                    || rs > heights.len() - item.row
                    || cs > widths.len() - item.column
                {
                    return Err(invalid());
                }
                let r = CellRect {
                    x: inner.x + widths[..item.column].iter().map(|w| w + gx).sum::<usize>(),
                    y: inner.y + heights[..item.row].iter().map(|h| h + gy).sum::<usize>(),
                    width: widths[item.column..item.column + cs].iter().sum::<usize>()
                        + gx * (cs - 1),
                    height: heights[item.row..item.row + rs].iter().sum::<usize>() + gy * (rs - 1),
                };
                out.push(NamedRect {
                    id: item.id.clone(),
                    rect: r,
                })
            }
        }
        "layers" => {
            for item in visible {
                let mut r = inner;
                r.x += item.area.x;
                r.y += item.area.y;
                r.width = r.width.saturating_sub(item.area.x);
                r.height = r.height.saturating_sub(item.area.y);
                if item.area.width > 0 {
                    r.width = r.width.min(item.area.width)
                }
                if item.area.height > 0 {
                    r.height = r.height.min(item.area.height)
                }
                if item.centered {
                    r.x = inner.x + (inner.width - r.width) / 2;
                    r.y = inner.y + (inner.height - r.height) / 2
                }
                if !item.drawer.is_empty() {
                    let preferred = if item.area.width == 0 {
                        inner.width
                    } else {
                        item.area.width
                    };
                    let placement = crate::layout::drawer_layout(inner, preferred, 0);
                    r.width = placement.rect.width;
                    r.x = if item.drawer == "right" {
                        inner.x + inner.width - r.width
                    } else {
                        inner.x
                    };
                }
                out.push(NamedRect {
                    id: item.id.clone(),
                    rect: r,
                })
            }
        }
        _ => unreachable!(),
    }
    Ok(out)
}
#[derive(Clone, Debug, Default)]
pub struct ContainerState {
    pub focused: String,
    pub captured: String,
    modal: String,
    restore: std::collections::BTreeMap<String, String>,
}
impl ContainerState {
    pub fn eligible<'a>(&self, items: &'a [LayoutItem]) -> Vec<&'a str> {
        let start = items
            .iter()
            .rposition(|i| !i.hidden && i.modal)
            .unwrap_or(0);
        items[start..]
            .iter()
            .filter(|i| !i.hidden && !i.disabled)
            .map(|i| i.id.as_str())
            .collect()
    }
    pub fn reconcile(&mut self, items: &[LayoutItem]) {
        let ids = self.eligible(items);
        let modal = items
            .iter()
            .rfind(|i| i.modal && !i.hidden)
            .map(|i| i.id.as_str())
            .unwrap_or("");
        if modal != self.modal {
            let old_visible = items
                .iter()
                .any(|i| i.id == self.modal && i.modal && !i.hidden);
            if !self.modal.is_empty() && !old_visible {
                if let Some(mut previous) = self.restore.remove(&self.modal) {
                    for _ in 0..=items.len() {
                        if ids.contains(&previous.as_str()) {
                            self.focused = previous;
                            break;
                        }
                        let Some(next) = self.restore.remove(&previous) else {
                            break;
                        };
                        previous = next;
                    }
                }
            }
            if !modal.is_empty() {
                self.restore
                    .entry(modal.into())
                    .or_insert_with(|| self.focused.clone());
            }
            self.modal = modal.into();
        }
        if !ids.contains(&self.focused.as_str()) {
            self.focused = ids.first().unwrap_or(&"").to_string()
        }
        if !ids.contains(&self.captured.as_str()) {
            self.captured.clear()
        }
    }
    pub fn move_focus(&mut self, items: &[LayoutItem], previous: bool) -> &str {
        self.reconcile(items);
        let ids = self.eligible(items);
        if let Some(at) = ids.iter().position(|id| *id == self.focused) {
            let delta = if previous { ids.len() - 1 } else { 1 };
            self.focused = ids[(at + delta) % ids.len()].into()
        }
        &self.focused
    }
    pub fn hit<'a>(
        &self,
        items: &[LayoutItem],
        rects: &'a [NamedRect],
        x: usize,
        y: usize,
    ) -> Option<&'a str> {
        let ids = self.eligible(items);
        rects
            .iter()
            .rev()
            .find(|r| {
                ids.contains(&r.id.as_str())
                    && x >= r.rect.x
                    && y >= r.rect.y
                    && x < r.rect.x + r.rect.width
                    && y < r.rect.y + r.rect.height
            })
            .map(|r| r.id.as_str())
    }
    /// Call on pointer press/drag/release. Hosts deliver input to the returned ID.
    pub fn pointer(
        &mut self,
        items: &[LayoutItem],
        rects: &[NamedRect],
        x: usize,
        y: usize,
        press: bool,
        release: bool,
    ) -> Option<String> {
        self.reconcile(items);
        let id = if self.captured.is_empty() {
            self.hit(items, rects, x, y).unwrap_or("").to_string()
        } else {
            self.captured.clone()
        };
        if press && !id.is_empty() {
            self.focused = id.clone();
            self.captured = id.clone()
        }
        if release {
            self.captured.clear()
        }
        if id.is_empty() { None } else { Some(id) }
    }
}
