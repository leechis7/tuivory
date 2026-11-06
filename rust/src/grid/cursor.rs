use super::*;
use crate::components::{cells, clean};
use unicode_segmentation::UnicodeSegmentation;
/// Local terminal-cell coordinates; adapters add their origin and focus policy.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct GridCursor {
    pub x: usize,
    pub y: usize,
    pub width: usize,
}
pub(super) fn editor_window(value: &str, cursor: usize, width: usize) -> (String, usize, usize) {
    let gs = value.graphemes(true).collect::<Vec<_>>();
    let at = cursor.min(gs.len());
    let mut start = at;
    let mut x = 0;
    let reserve = gs.get(at).map_or(1, |g| cells(&clean(g)).max(1)).min(width);
    while start > 0 {
        let w = cells(&clean(gs[start - 1]));
        if x + w > width.saturating_sub(reserve) {
            break;
        }
        start -= 1;
        x += w
    }
    let mut text = String::new();
    let mut used = 0;
    for g in &gs[start..] {
        let g = clean(g);
        let w = cells(&g);
        if used + w > width {
            break;
        }
        text.push_str(&g);
        used += w
    }
    (text, x, start)
}
impl Grid {
    /// Returns no caret for pending, NULL, invalidated, uneditable or clipped editors.
    /// The adapter owns focus and terminal visibility; no terminal I/O occurs here.
    pub fn edit_cursor(&self, width: usize, height: usize) -> Option<GridCursor> {
        let e = self.edit_session()?;
        if e.pending
            || e.value.null
            || self.work.detail.is_some()
            || self.work.find_buffer.is_some()
            || width == 0
            || height == 0
        {
            return None;
        }
        let row = self
            .source
            .index_of(&e.row_id)
            .filter(|r| *r < self.source.len())?;
        let col = self.column_index(&e.column_id)?;
        let record = self.source.row(row);
        if record.id != e.row_id
            || !self.editable(&record, &self.columns[col])
            || !self.prepared(&record, &self.columns[col])
        {
            return None;
        }
        let geo = self.geometry(width, height);
        if row < geo.top || row >= geo.top + geo.body_rows {
            return None;
        }
        let y = geo.header_rows + (row - geo.top) * geo.stride;
        if y >= height.saturating_sub(geo.footer_rows) {
            return None;
        }
        let span = geo.columns.iter().find(|s| s.id == e.column_id)?;
        let extra = if self.info(&record, &self.columns[col]).state.edited {
            2
        } else {
            0
        };
        let space = span
            .width
            .checked_sub(2 * self.options.padding + extra)
            .filter(|w| *w > 0)?;
        let b = self.work.buffer.as_ref()?;
        let (_, x, _) = editor_window(b.text(), b.cursor, space);
        let gs = b.text().graphemes(true).collect::<Vec<_>>();
        let glyph = gs.get(b.cursor).map_or(1, |g| cells(&clean(g)).max(1));
        let glyph = if glyph > space { 1 } else { glyph };
        Some(GridCursor {
            width: glyph,
            x: span.start + self.options.padding + extra + x,
            y,
        })
    }
}
