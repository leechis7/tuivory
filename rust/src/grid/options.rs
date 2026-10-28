use super::*;
use std::cell::Cell;

/// Options on the existing grid; defaults retain the simple v0.2 presentation.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct GridOptions {
    pub row_numbers: bool,
    pub hide_markers: bool,
    pub vertical_lines: bool,
    pub horizontal_lines: bool,
    pub striped: bool,
    pub use_surface: bool,
    pub hide_header: bool,
    pub scroll_header: bool,
    pub status_bar: bool,
    pub ascii: bool,
    pub highlight_cell: bool,
    pub highlight_row: bool,
    pub preserve_edited: bool,
    pub hide_selection_marker: bool,
    pub show_cell_markers: bool,
    pub disable_keyboard: bool,
    pub disable_mouse: bool,
    pub disable_editing: bool,
    pub disable_copy: bool,
    pub disable_resize: bool,
    pub disable_header_sort: bool,
    pub padding: usize,
    pub row_spacing: usize,
    pub gutter_width: usize,
    pub max_copy_cells: usize,
    pub selection: String,
    pub status_fields: Option<Vec<String>>,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct GridColumnOptions {
    pub align: String,
    pub min_width: usize,
    pub max_width: usize,
    pub auto_fit: bool,
    pub expand: usize,
    pub overflow: String,
}
#[derive(Clone, Debug, Default)]
pub struct GridCellInfo {
    pub display: String,
    pub has_display: bool,
    pub null: bool,
    pub numeric: bool,
    pub state: ControlState,
    pub metadata: String,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct GridRange {
    pub anchor_row: String,
    pub anchor_column: String,
    pub end_row: String,
    pub end_column: String,
}
#[derive(Clone, Debug, Default)]
pub struct GridDataStatus {
    pub total_rows: usize,
    pub metadata: String,
    pub filter: String,
    pub error: String,
    pub loading: bool,
    pub has_more: bool,
}
#[derive(Clone, Debug, Default)]
pub struct GridGeometry {
    pub top: usize,
    pub left: usize,
    pub gutter: usize,
    pub header_rows: usize,
    pub footer_rows: usize,
    pub body_rows: usize,
    pub stride: usize,
    pub columns: Vec<GridSpan>,
}
pub(super) type CellInfo = Box<dyn Fn(&GridRecord, &GridColumn) -> GridCellInfo>;

pub fn grid_preset(name: &str) -> Result<GridOptions, Error> {
    match name {
        "" | "simple" => Ok(GridOptions::default()),
        "data" => Ok(GridOptions {
            row_numbers: true,
            vertical_lines: true,
            use_surface: true,
            padding: 1,
            status_bar: true,
            highlight_cell: true,
            highlight_row: true,
            preserve_edited: true,
            hide_selection_marker: true,
            show_cell_markers: true,
            ..Default::default()
        }),
        _ => Err(Error::Invalid("unknown grid preset".into())),
    }
}
impl GridOptions {
    pub fn with_density(mut self, density: &str) -> Result<Self, Error> {
        match density {
            "compact" => {
                self.padding = 0;
                self.row_spacing = 0
            }
            "normal" => {
                self.padding = 1;
                self.row_spacing = 0
            }
            "comfortable" => {
                self.padding = 1;
                self.row_spacing = 1
            }
            _ => return Err(Error::Invalid("invalid grid density".into())),
        };
        Ok(self)
    }
}
pub(super) fn bounds(o: &GridColumnOptions) -> (usize, usize) {
    (
        o.min_width.max(1),
        if o.max_width == 0 { 4096 } else { o.max_width },
    )
}
pub(super) fn combine(a: ControlState, b: ControlState) -> ControlState {
    ControlState {
        disabled: a.disabled || b.disabled,
        read_only: a.read_only || b.read_only,
        busy: a.busy || b.busy,
        selected: a.selected || b.selected,
        edited: a.edited || b.edited,
        invalid: a.invalid || b.invalid,
    }
}
impl Grid {
    pub(super) fn page_rows(&self, height: usize) -> usize {
        if self.options.row_spacing > 0 || self.options.horizontal_lines {
            self.geometry(self.last_width.get().max(1), height)
                .body_rows
                .max(1)
        } else {
            height.saturating_sub(2).max(1)
        }
    }
    pub fn options(&self) -> &GridOptions {
        &self.options
    }
    pub fn set_options(&mut self, o: GridOptions) -> Result<(), Error> {
        if o.padding > 8
            || o.row_spacing > 4
            || o.gutter_width > 128
            || o.max_copy_cells > 1_000_000
            || !["", "cell", "row", "range"].contains(&o.selection.as_str())
        {
            return Err(Error::Invalid("invalid grid options".into()));
        }
        if let Some(fields) = &o.status_fields {
            let mut seen = std::collections::BTreeSet::new();
            for s in fields {
                if ![
                    "position",
                    "column",
                    "selection",
                    "sort",
                    "filter",
                    "loading",
                    "more",
                    "meta",
                    "error",
                ]
                .contains(&s.as_str())
                    || !seen.insert(s)
                {
                    return Err(Error::Invalid("invalid grid status field".into()));
                }
            }
        }
        if !o.selection.is_empty() {
            self.set_selection_mode(&o.selection)?;
        }
        self.options = o;
        Ok(())
    }
    pub fn set_column_options(&mut self, id: &str, o: GridColumnOptions) -> Result<(), Error> {
        let (lo, hi) = bounds(&o);
        if self.column_index(id).is_none()
            || !["", "left", "center", "right", "numeric"].contains(&o.align.as_str())
            || !["", "ellipsis", "clip", "scroll"].contains(&o.overflow.as_str())
            || lo > hi
            || hi > 4096
            || o.expand > 1_000_000
        {
            return Err(Error::Invalid("invalid grid column options".into()));
        }
        self.column_options.insert(id.into(), o);
        Ok(())
    }
    pub fn column_options(&self, id: &str) -> GridColumnOptions {
        self.column_options.get(id).cloned().unwrap_or_default()
    }
    pub fn set_cell_info(
        &mut self,
        info: impl Fn(&GridRecord, &GridColumn) -> GridCellInfo + 'static,
    ) {
        self.cell_info = Some(Box::new(info));
    }
    pub fn clear_cell_info(&mut self) {
        self.cell_info = None;
    }
    pub(super) fn info(&self, r: &GridRecord, c: &GridColumn) -> GridCellInfo {
        self.cell_info.as_ref().map(|f| f(r, c)).unwrap_or_default()
    }
    pub(super) fn label(&self, key: &str, fallback: &str) -> String {
        self.labels
            .get(key)
            .cloned()
            .unwrap_or_else(|| fallback.into())
    }
    pub fn selection_mode(&self) -> &str {
        if self.whole_row {
            "row"
        } else if self.range_mode {
            "range"
        } else {
            "cell"
        }
    }
    pub fn set_selection_mode(&mut self, mode: &str) -> Result<(), Error> {
        if !["cell", "row", "range"].contains(&mode) {
            return Err(Error::Invalid("invalid grid selection mode".into()));
        }
        self.whole_row = mode == "row";
        self.range_mode = mode == "range";
        Ok(())
    }
    pub(super) fn column_index(&self, id: &str) -> Option<usize> {
        self.columns.iter().position(|c| c.id == id)
    }
    pub(super) fn range_bounds(&self) -> Option<(usize, usize, usize, usize)> {
        let r = &self.selection;
        let ar = self.source.index_of(&r.anchor_row)?;
        let er = self.source.index_of(&r.end_row)?;
        let ac = self.column_index(&r.anchor_column)?;
        let ec = self.column_index(&r.end_column)?;
        if ar >= self.source.len() || er >= self.source.len() {
            return None;
        }
        Some((ar.min(er), ar.max(er), ac.min(ec), ac.max(ec)))
    }
    pub fn select_range(&mut self, r: GridRange) -> bool {
        let old = std::mem::replace(&mut self.selection, r);
        if self.range_bounds().is_none() {
            self.selection = old;
            return false;
        }
        self.whole_row = false;
        self.range_mode = true;
        self.selected_row = self.selection.end_row.clone();
        self.selected_column = self.selection.end_column.clone();
        true
    }
    pub fn selected_range(&self) -> &GridRange {
        &self.selection
    }
    pub fn revision(&self) -> u64 {
        self.revision.get()
    }
    pub(super) fn next_request(&self) {
        self.revision.set(self.revision.get().saturating_add(1));
    }
    pub fn apply_source(&mut self, revision: u64, source: Box<dyn GridSource>) -> bool {
        if revision != self.revision.get() || revision <= self.applied_revision {
            return false;
        }
        self.set_source(source);
        self.applied_revision = revision;
        true
    }
    pub fn request_page(&self) -> GridEvent {
        if !self.status.has_more || self.status.loading {
            return GridEvent::default();
        }
        self.next_request();
        GridEvent {
            kind: "load_more".into(),
            ..Default::default()
        }
    }
    pub(super) fn copy_range(&self) -> GridEvent {
        let Some((r1, r2, c1, c2)) = self.range_bounds() else {
            return GridEvent::default();
        };
        let mut e = GridEvent {
            kind: "copy".into(),
            row_id: self.row_id.clone(),
            column_id: self.column_id.clone(),
            ..Default::default()
        };
        let limit = if self.options.max_copy_cells == 0 {
            10000
        } else {
            self.options.max_copy_cells
        };
        if r2 - r1 + 1 > limit / (c2 - c1 + 1) {
            e.kind = "copy_request".into();
            return e;
        }
        e.text = (r1..=r2)
            .map(|r| {
                let row = self.source.row(r);
                (c1..=c2)
                    .map(|c| {
                        let s = row
                            .cells
                            .get(&self.columns[c].id)
                            .cloned()
                            .unwrap_or_default();
                        if s.contains(['\t', '\r', '\n', '"']) {
                            format!("\"{}\"", s.replace('"', "\"\""))
                        } else {
                            s
                        }
                    })
                    .collect::<Vec<_>>()
                    .join("\t")
            })
            .collect::<Vec<_>>()
            .join("\n");
        e
    }
    pub(super) fn extra_action(&mut self, action: &str, height: usize) -> Option<GridEvent> {
        let mut e = GridEvent {
            row_id: self.row_id.clone(),
            column_id: self.column_id.clone(),
            ..Default::default()
        };
        if let Some(nav) = action.strip_prefix("extend_") {
            let mut r = if self.range_mode && self.range_bounds().is_some() {
                self.selection.clone()
            } else {
                GridRange {
                    anchor_row: self.row_id.clone(),
                    anchor_column: self.column_id.clone(),
                    ..Default::default()
                }
            };
            let mut event = self.handle(nav, height);
            if !event.kind.is_empty() {
                r.end_row = self.row_id.clone();
                r.end_column = self.column_id.clone();
                self.select_range(r);
                event.kind = "select".into()
            }
            return Some(event);
        }
        match action {
            "range_start" | "range_mode" => {
                if action == "range_mode" && self.range_mode {
                    self.range_mode = false
                } else {
                    self.select_range(GridRange {
                        anchor_row: self.row_id.clone(),
                        anchor_column: self.column_id.clone(),
                        end_row: self.row_id.clone(),
                        end_column: self.column_id.clone(),
                    });
                }
                self.whole_row = false;
                e.kind = if action == "range_mode" {
                    "mode"
                } else {
                    "select"
                }
                .into()
            }
            "cancel" => {
                self.selection = GridRange::default();
                self.range_mode = false;
                self.selected_row.clear();
                self.selected_column.clear();
                e.kind = "cancel".into()
            }
            "copy_range" => {
                return Some(if self.options.disable_copy {
                    GridEvent::default()
                } else {
                    self.copy_range()
                });
            }
            "copy" if self.options.disable_copy => return Some(GridEvent::default()),
            "copy" if self.range_mode && !self.whole_row => return Some(self.copy_range()),
            "copy_cell" | "copy_row" | "details" => {
                if self.row_id.is_empty() || (action != "details" && self.options.disable_copy) {
                    return Some(GridEvent::default());
                }
                let r = self.source.row(self.row);
                e.kind = if action == "details" {
                    "details"
                } else {
                    "copy"
                }
                .into();
                e.text = if action == "copy_row" {
                    self.columns
                        .iter()
                        .map(|c| r.cells.get(&c.id).cloned().unwrap_or_default())
                        .collect::<Vec<_>>()
                        .join("\t")
                } else {
                    r.cells.get(&self.column_id).cloned().unwrap_or_default()
                }
            }
            "load_more" => return Some(self.request_page()),
            "cell_pan_left" | "cell_pan_right" => {
                let offset = self.cell_pan.entry(self.column_id.clone()).or_default();
                *offset = if action == "cell_pan_left" {
                    offset.saturating_sub(1)
                } else {
                    (*offset + 1).min(1_000_000)
                };
                e.kind = "pan".into()
            }
            "autofit" => {
                let id = self.column_id.clone();
                if !self.options.disable_resize && self.auto_fit_column(&id, height) {
                    e.kind = "resize".into()
                }
            }
            "widen" | "narrow" if self.options.disable_resize => return Some(GridEvent::default()),
            _ => return None,
        }
        Some(e)
    }
    pub fn auto_fit_column(&mut self, id: &str, height: usize) -> bool {
        let Some(c) = self.column_index(id) else {
            return false;
        };
        let col = &self.columns[c];
        let mut w = super::presentation::text_width(&col.label) + 2;
        let geo = self.geometry(self.last_width.get().max(1), height);
        for n in geo.top
            ..self
                .source
                .len()
                .min(geo.top.saturating_add(geo.body_rows.max(1)))
        {
            let r = self.source.row(n);
            let i = self.info(&r, col);
            let s = if i.has_display {
                i.display
            } else if i.null {
                self.label("null", "NULL")
            } else {
                r.cells.get(id).cloned().unwrap_or_default()
            };
            w = w.max(super::presentation::text_width(&s));
        }
        let (lo, hi) = bounds(&self.column_options(id));
        self.resize_column(id, w.clamp(lo, hi))
    }
}
pub(super) fn revision_cell() -> Cell<u64> {
    Cell::new(0)
}
