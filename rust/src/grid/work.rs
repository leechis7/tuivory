//! Host-approved editing, stable column/view state, batch paste and local find.
use super::*;
use crate::text::{TextBuffer, TextDocument};
#[derive(Clone, Debug, Default, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct GridColumnLayout {
    pub id: String,
    pub pin: String,
    pub hidden: bool,
}
#[derive(Clone, Debug, Default, serde::Serialize, serde::Deserialize)]
pub struct GridViewState {
    pub columns: Vec<GridColumnLayout>,
    pub widths: BTreeMap<String, usize>,
    pub column_options: BTreeMap<String, GridColumnOptions>,
    pub row_id: String,
    pub column_id: String,
    pub top_row_id: String,
    pub left_column_id: String,
    pub sort_column: String,
    pub sort_direction: String,
    pub selected: GridRange,
    pub selected_row: String,
    pub selected_column: String,
    pub selection: String,
    pub filter: String,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct GridValue {
    pub text: String,
    pub null: bool,
}
pub type GridEditPrepare = Box<dyn Fn(&GridRecord, &GridColumn) -> Option<GridValue>>;
#[derive(Default)]
pub struct GridEditOptions {
    pub enabled: bool,
    pub start_typing: bool,
    pub allow_null: bool,
    pub prepare: Option<GridEditPrepare>,
}
#[derive(Clone, Debug, Default)]
pub struct GridEditSession {
    pub id: u64,
    pub row_id: String,
    pub column_id: String,
    pub original: GridValue,
    pub value: GridValue,
    pub pending: bool,
    pub error: String,
}
#[derive(Clone, Debug, Default)]
pub struct GridChange {
    pub row_id: String,
    pub column_id: String,
    pub value: GridValue,
}
#[derive(Clone, Debug, Default)]
pub struct GridPasteRequest {
    pub id: u64,
    pub changes: Vec<GridChange>,
}
#[derive(Clone, Debug, Default)]
pub struct GridPasteOptions {
    pub max_cells: usize,
    pub null_text: String,
    pub parse_null: bool,
}
#[derive(Clone, Debug, Default)]
pub struct GridFindOptions {
    pub case_sensitive: bool,
    pub use_display: bool,
    pub max_cells: usize,
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct GridCellRef {
    pub row_id: String,
    pub column_id: String,
}
type RowEdited = Box<dyn Fn(&GridRecord) -> bool>;
#[derive(Default)]
pub(super) struct GridWork {
    pub details_enabled: bool,
    pub edit_dragging: bool,
    pub row_edited: Option<RowEdited>,
    pub find_buffer: Option<TextBuffer>,
    pub drag_move_column: String,
    pub drag_moved: bool,
    pub hidden: BTreeMap<String, bool>,
    pub pins: BTreeMap<String, String>,
    epoch: u64,
    serial: u64,
    pub edit_options: GridEditOptions,
    pub edit: Option<GridEditSession>,
    pub buffer: Option<TextBuffer>,
    edit_epoch: u64,
    move_after: String,
    paste: Option<GridPasteRequest>,
    paste_epoch: u64,
    pub edit_revision: u64,
    paste_revision: u64,
    pub query: String,
    pub find_options: GridFindOptions,
    pub detail: Option<std::cell::RefCell<TextDocument>>,
    detail_title: String,
}
impl Grid {
    /// Call when a host workspace/tab/context changes without replacing its source.
    pub fn invalidate_requests(&mut self) {
        self.next_request();
        self.invalidate_work()
    }
    fn clear_stale_work(&mut self) {
        if self.work.edit_revision != self.revision() {
            self.cancel_edit()
        }
        if self.work.paste_revision != self.revision() {
            self.work.paste = None
        }
    }
    pub(super) fn invalidate_work(&mut self) {
        self.work.epoch += 1;
        self.cancel_edit();
        self.work.paste = None;
        self.work.detail = None;
        self.work.find_buffer = None;
    }
    fn work_id(&mut self) -> u64 {
        self.work.serial += 1;
        self.work.serial
    }
    pub(super) fn reconcile_visible(&mut self) {
        if self.work.hidden.get(&self.column_id) == Some(&true) {
            if let Some(i) = self
                .columns
                .iter()
                .position(|c| self.work.hidden.get(&c.id) != Some(&true))
            {
                self.column = i;
                self.column_id = self.columns[i].id.clone()
            } else {
                self.column_id.clear()
            }
        }
    }
    pub fn column_layout(&self) -> Vec<GridColumnLayout> {
        self.columns
            .iter()
            .map(|c| GridColumnLayout {
                id: c.id.clone(),
                pin: self.work.pins.get(&c.id).cloned().unwrap_or_default(),
                hidden: self.work.hidden.get(&c.id) == Some(&true),
            })
            .collect()
    }
    pub fn set_column_layout(&mut self, l: Vec<GridColumnLayout>) -> Result<(), Error> {
        if l.len() != self.columns.len() {
            return Err(Error::Invalid("column layout must include all IDs".into()));
        }
        let mut seen = std::collections::BTreeSet::new();
        let mut cols = vec![];
        let mut hidden = BTreeMap::new();
        let mut pins = BTreeMap::new();
        let mut visible = 0;
        for v in l {
            let Some(c) = self.columns.iter().find(|c| c.id == v.id) else {
                return Err(Error::Invalid("unknown column".into()));
            };
            if !seen.insert(v.id.clone()) || !["", "left", "right"].contains(&v.pin.as_str()) {
                return Err(Error::Invalid("invalid column layout".into()));
            };
            cols.push(c.clone());
            if !v.hidden {
                visible += 1
            }
            hidden.insert(v.id.clone(), v.hidden);
            pins.insert(v.id, v.pin);
        }
        if visible == 0 && !cols.is_empty() {
            return Err(Error::Invalid(
                "at least one visible column required".into(),
            ));
        }
        let current = self.column_id.clone();
        self.invalidate_work();
        self.columns = cols;
        self.work.hidden = hidden;
        self.work.pins = pins;
        self.column = self.column_index(&current).unwrap_or(0);
        self.reconcile();
        Ok(())
    }
    pub fn move_column(&mut self, id: &str, at: usize) -> bool {
        let Some(i) = self.column_index(id) else {
            return false;
        };
        let mut l = self.column_layout();
        if at >= l.len() {
            return false;
        }
        let v = l.remove(i);
        l.insert(at, v);
        self.set_column_layout(l).is_ok()
    }
    pub fn hide_column(&mut self, id: &str, hidden: bool) -> bool {
        let Some(i) = self.column_index(id) else {
            return false;
        };
        let mut l = self.column_layout();
        l[i].hidden = hidden;
        self.set_column_layout(l).is_ok()
    }
    pub fn pin_column(&mut self, id: &str, side: &str) -> bool {
        let Some(i) = self.column_index(id) else {
            return false;
        };
        let mut l = self.column_layout();
        l[i].pin = side.into();
        self.set_column_layout(l).is_ok()
    }
    pub(super) fn visible_indices(&self) -> Vec<usize> {
        let mut out = vec![];
        for pin in ["left", "", "right"] {
            for (i, c) in self.columns.iter().enumerate() {
                if self.work.hidden.get(&c.id) != Some(&true)
                    && self.work.pins.get(&c.id).map_or("", String::as_str) == pin
                {
                    out.push(i)
                }
            }
        }
        out
    }
    pub fn save_view_state(&self) -> GridViewState {
        GridViewState {
            columns: self.column_layout(),
            widths: self
                .columns
                .iter()
                .map(|c| (c.id.clone(), c.width))
                .collect(),
            column_options: self.column_options.clone(),
            row_id: self.row_id.clone(),
            column_id: self.column_id.clone(),
            top_row_id: if self.top < self.source.len() {
                self.source.row(self.top).id
            } else {
                String::new()
            },
            left_column_id: self
                .columns
                .get(self.left)
                .map(|c| c.id.clone())
                .unwrap_or_default(),
            sort_column: self.sort_column.clone(),
            sort_direction: self.sort_direction.clone(),
            selected: self.selection.clone(),
            selected_row: self.selected_row.clone(),
            selected_column: self.selected_column.clone(),
            selection: self.selection_mode().into(),
            filter: self.status.filter.clone(),
        }
    }
    pub fn restore_view_state(&mut self, s: GridViewState) -> Result<(), Error> {
        if !["cell", "row", "range"].contains(&s.selection.as_str())
            || !["", "asc", "desc"].contains(&s.sort_direction.as_str())
        {
            return Err(Error::Invalid("invalid view state".into()));
        }
        let mut tmp = Grid::new(self.columns.clone(), Box::new(MemoryRows::new(vec![])?))?;
        for (id, o) in &s.column_options {
            tmp.set_column_options(id, o.clone())?;
        }
        tmp.set_column_layout(s.columns.clone())?;
        for (id, w) in &s.widths {
            let (lo, hi) = options::bounds(&tmp.column_options(id));
            if tmp.column_index(id).is_none() || *w < lo || *w > hi {
                return Err(Error::Invalid("invalid view width".into()));
            }
        }
        if !s.sort_column.is_empty() && tmp.column_index(&s.sort_column).is_none() {
            return Err(Error::Invalid("invalid sort column".into()));
        }
        self.invalidate_work();
        self.columns = tmp.columns;
        self.work.hidden = tmp.work.hidden;
        self.work.pins = tmp.work.pins;
        self.column_options = tmp.column_options;
        for c in &mut self.columns {
            if let Some(w) = s.widths.get(&c.id) {
                c.width = *w
            }
        }
        self.sort_column = s.sort_column;
        self.sort_direction = s.sort_direction;
        self.status.filter = s.filter;
        self.selected_row = s.selected_row;
        self.selected_column = s.selected_column;
        self.selection = s.selected;
        self.set_selection_mode(&s.selection)?;
        self.focus(&s.row_id, &s.column_id);
        self.top = self.source.index_of(&s.top_row_id).unwrap_or(0);
        self.left = self.column_index(&s.left_column_id).unwrap_or(0);
        self.reconcile();
        if self.range_bounds().is_none() {
            self.selection = GridRange::default()
        }
        if self.source.index_of(&self.selected_row).is_none() {
            self.selected_row.clear();
            self.selected_column.clear()
        }
        Ok(())
    }
    pub fn set_edit_options(&mut self, o: GridEditOptions) {
        self.cancel_edit();
        self.work.edit_options = o
    }
    pub(super) fn prepared(&self, r: &GridRecord, c: &GridColumn) -> bool {
        self.work
            .edit_options
            .prepare
            .as_ref()
            .is_none_or(|p| p(r, c).is_some())
    }
    pub(super) fn editable(&self, r: &GridRecord, c: &GridColumn) -> bool {
        !self.options.disable_editing
            && self.work.hidden.get(&c.id) != Some(&true)
            && c.editable
            && options::combine(r.state, self.info(r, c).state)
                .visual()
                .editable
    }
    pub fn begin_edit(&mut self, first: &str) -> bool {
        self.clear_stale_work();
        if !self.work.edit_options.enabled
            || self.work.edit.is_some()
            || self.work.paste.is_some()
            || self.row_id.is_empty()
            || self.column_id.is_empty()
        {
            return false;
        }
        let r = self.source.row(self.row);
        let c = &self.columns[self.column];
        if !self.editable(&r, c) {
            return false;
        }
        let info = self.info(&r, c);
        let mut v = GridValue {
            text: r.cells.get(&c.id).cloned().unwrap_or_default(),
            null: info.null,
        };
        if let Some(prepare) = &self.work.edit_options.prepare {
            let Some(value) = prepare(&r, c) else {
                return false;
            };
            v = value
        }
        let row_id = r.id;
        let column_id = c.id.clone();
        let id = self.work_id();
        let mut buffer = TextBuffer::new(&v.text);
        buffer.single_line = true;
        let mut value = v.clone();
        if !first.is_empty() {
            buffer.select(0, v.text.graphemes(true).count());
            buffer.handle("insert", first);
            value = GridValue {
                text: buffer.text().into(),
                null: false,
            };
        }
        self.drag_column.clear();
        self.drag_anchor = GridRange::default();
        self.work.drag_move_column.clear();
        self.work.edit = Some(GridEditSession {
            id,
            row_id,
            column_id,
            original: v,
            value,
            ..Default::default()
        });
        self.work.edit_epoch = self.work.epoch;
        self.work.edit_revision = self.revision();
        self.work.buffer = Some(buffer);
        true
    }
    pub fn edit_session(&self) -> Option<&GridEditSession> {
        self.work
            .edit
            .as_ref()
            .filter(|_| self.work.edit_revision == self.revision())
    }
    pub fn cancel_edit(&mut self) {
        self.work.edit = None;
        self.work.buffer = None;
        self.work.move_after.clear();
        self.work.edit_dragging = false
    }
    pub fn edit_input(&mut self, action: &str, text: &str) -> GridEvent {
        if self.work.edit_revision != self.revision() {
            self.cancel_edit()
        }
        if self.work.edit.is_none() {
            return GridEvent::default();
        }
        if action == "cancel" {
            let e = self.work.edit.take().unwrap();
            self.cancel_edit();
            return GridEvent {
                kind: "edit_cancel".into(),
                row_id: e.row_id,
                column_id: e.column_id,
                ..Default::default()
            };
        }
        let e = self.work.edit.as_ref().unwrap();
        let valid = self
            .source
            .index_of(&e.row_id)
            .filter(|i| *i < self.source.len())
            .zip(self.column_index(&e.column_id))
            .is_some_and(|(i, c)| {
                self.source.row(i).id == e.row_id
                    && self.editable(&self.source.row(i), &self.columns[c])
                    && self.prepared(&self.source.row(i), &self.columns[c])
            });
        if !valid {
            self.cancel_edit();
            return GridEvent {
                kind: "edit_cancel".into(),
                ..Default::default()
            };
        }
        if self.work.edit.as_ref().unwrap().pending {
            return GridEvent::default();
        }
        let id = if ["submit", "next", "previous"].contains(&action) {
            self.work_id()
        } else {
            0
        };
        let e = self.work.edit.as_mut().unwrap();
        let mut out = GridEvent {
            row_id: e.row_id.clone(),
            column_id: e.column_id.clone(),
            ..Default::default()
        };
        if id > 0 {
            e.id = id;
            e.pending = true;
            e.error.clear();
            self.work.move_after = action.into();
            out.kind = "edit_submit".into();
            out.text = e.value.text.clone();
            return out;
        }
        if action == "null" {
            if self.work.edit_options.allow_null {
                e.value.null = !e.value.null
            }
        } else {
            let b = self.work.buffer.as_mut().unwrap();
            let v = b.handle(action, text);
            if v.kind == "copy" || v.kind == "cut" {
                return GridEvent {
                    kind: v.kind,
                    text: v.text,
                    row_id: e.row_id.clone(),
                    column_id: e.column_id.clone(),
                    ..Default::default()
                };
            }
            e.value.text = b.text().into();
            if ["insert", "paste", "backspace", "delete"].contains(&action) {
                e.value.null = false;
                e.error.clear()
            }
        }
        out.kind = "edit_change".into();
        out
    }
    pub fn resolve_edit(
        &mut self,
        id: u64,
        message: &str,
        source: Option<Box<dyn GridSource>>,
    ) -> bool {
        let Some(e) = self.work.edit.as_ref() else {
            return false;
        };
        if !e.pending
            || e.id != id
            || self.work.edit_epoch != self.work.epoch
            || self.work.edit_revision != self.revision()
        {
            return false;
        }
        let valid = self
            .source
            .index_of(&e.row_id)
            .filter(|i| *i < self.source.len())
            .zip(self.column_index(&e.column_id))
            .is_some_and(|(i, c)| {
                self.source.row(i).id == e.row_id
                    && self.editable(&self.source.row(i), &self.columns[c])
                    && self.prepared(&self.source.row(i), &self.columns[c])
            });
        if !valid {
            self.cancel_edit();
            return false;
        }
        if !message.is_empty() {
            let e = self.work.edit.as_mut().unwrap();
            e.pending = false;
            e.error = message.into();
            return true;
        }
        let row = e.row_id.clone();
        let col = e.column_id.clone();
        let movement = self.work.move_after.clone();
        self.cancel_edit();
        if let Some(s) = source {
            self.set_source(s)
        }
        if !self.focus(&row, &col) {
            return true;
        }
        if (movement == "next" || movement == "previous")
            && self.move_editable(movement == "previous")
        {
            self.begin_edit("");
        }
        true
    }
    pub fn move_editable(&mut self, previous: bool) -> bool {
        let cols = self.visible_indices();
        let Some(ci) = cols.iter().position(|c| *c == self.column) else {
            return false;
        };
        let start = self.row * cols.len() + ci;
        let n = self.source.len().saturating_mul(cols.len());
        let step = if previous { -1 } else { 1 };
        let mut at = start as isize + step;
        while at >= 0 && (at as usize) < n {
            let r = self.source.row(at as usize / cols.len());
            let c = &self.columns[cols[at as usize % cols.len()]];
            if self.editable(&r, c)
                && self
                    .work
                    .edit_options
                    .prepare
                    .as_ref()
                    .is_none_or(|p| p(&r, c).is_some())
            {
                let id = c.id.clone();
                return self.focus(&r.id, &id);
            }
            at += step
        }
        false
    }
    pub fn request_paste(
        &mut self,
        text: &str,
        o: GridPasteOptions,
    ) -> Result<GridPasteRequest, Error> {
        self.clear_stale_work();
        let fail = || Error::Invalid("paste rejected: bounds, limits or non-editable cell".into());
        let limit = if o.max_cells == 0 { 10000 } else { o.max_cells };
        if limit > 1_000_000
            || text.len() > 16 * 1024 * 1024
            || self.work.edit.is_some()
            || self.work.paste.is_some()
            || self.row_id.is_empty()
        {
            return Err(fail());
        }
        let records = parse_tsv(text, limit)?;
        let cols = self.visible_indices();
        let Some(start) = cols.iter().position(|c| *c == self.column) else {
            return Err(fail());
        };
        let mut req = GridPasteRequest::default();
        let width = records.first().map_or(0, Vec::len);
        for (ri, values) in records.into_iter().enumerate() {
            if values.len() != width
                || self.row + ri >= self.source.len()
                || start + width > cols.len()
                || req.changes.len() + width > limit
            {
                return Err(fail());
            }
            let row = self.source.row(self.row + ri);
            if row.id.is_empty() || self.source.index_of(&row.id) != Some(self.row + ri) {
                return Err(fail());
            }
            for (j, value) in values.into_iter().enumerate() {
                let c = &self.columns[cols[start + j]];
                if !self.editable(&row, c) || !self.prepared(&row, c) {
                    return Err(fail());
                }
                req.changes.push(GridChange {
                    row_id: row.id.clone(),
                    column_id: c.id.clone(),
                    value: GridValue {
                        null: o.parse_null && value == o.null_text,
                        text: value,
                    },
                })
            }
        }
        if req.changes.is_empty() {
            return Err(fail());
        }
        req.id = self.work_id();
        self.work.paste_epoch = self.work.epoch;
        self.work.paste_revision = self.revision();
        self.work.paste = Some(req.clone());
        Ok(req)
    }
    pub fn pending_paste(&self) -> Option<&GridPasteRequest> {
        self.work
            .paste
            .as_ref()
            .filter(|_| self.work.paste_revision == self.revision())
    }
    pub fn resolve_paste(&mut self, id: u64, source: Option<Box<dyn GridSource>>) -> bool {
        let Some(p) = &self.work.paste else {
            return false;
        };
        if p.id != id
            || self.work.paste_epoch != self.work.epoch
            || self.work.paste_revision != self.revision()
        {
            return false;
        }
        for v in &p.changes {
            if !self
                .source
                .index_of(&v.row_id)
                .filter(|i| *i < self.source.len())
                .zip(self.column_index(&v.column_id))
                .is_some_and(|(i, c)| {
                    self.source.row(i).id == v.row_id
                        && self.editable(&self.source.row(i), &self.columns[c])
                        && self.prepared(&self.source.row(i), &self.columns[c])
                })
            {
                self.work.paste = None;
                return false;
            }
        }
        self.work.paste = None;
        if let Some(s) = source {
            self.set_source(s)
        }
        true
    }
    pub fn cancel_paste(&mut self) {
        self.work.paste = None
    }
    pub fn set_find(&mut self, query: &str, o: GridFindOptions) {
        self.work.query = query.into();
        self.work.find_options = o
    }
    pub(super) fn matches(&self, r: &GridRecord, c: &GridColumn) -> bool {
        if self.work.query.is_empty() {
            return false;
        }
        let mut v = r.cells.get(&c.id).cloned().unwrap_or_default();
        let mut q = self.work.query.clone();
        if self.work.find_options.use_display {
            let i = self.info(r, c);
            if i.has_display {
                v = i.display
            } else if i.null {
                v = self.label("null", "NULL")
            }
        }
        if !self.work.find_options.case_sensitive {
            v = v.to_lowercase();
            q = q.to_lowercase()
        }
        v.contains(&q)
    }
    pub fn find_next(&mut self, previous: bool) -> Option<GridCellRef> {
        let cols = self.visible_indices();
        if cols.is_empty() || self.work.query.is_empty() {
            return None;
        }
        let limit = if self.work.find_options.max_cells == 0 {
            100000
        } else {
            self.work.find_options.max_cells
        };
        let ci = cols.iter().position(|c| *c == self.column).unwrap_or(0);
        let n = self.source.len().saturating_mul(cols.len());
        if n == 0 {
            return None;
        }
        let start = self.row * cols.len() + ci;
        for i in 1..=n.min(limit) {
            let at = if previous {
                (start + n - i) % n
            } else {
                (start + i) % n
            };
            let r = self.source.row(at / cols.len());
            let c = &self.columns[cols[at % cols.len()]];
            if !r.state.disabled && self.matches(&r, c) {
                let id = c.id.clone();
                self.focus(&r.id, &id);
                return Some(GridCellRef {
                    row_id: r.id,
                    column_id: id,
                });
            }
        }
        None
    }
    pub fn request_search(&self, query: &str) -> GridEvent {
        self.next_request();
        GridEvent {
            kind: "search_request".into(),
            text: query.into(),
            ..Default::default()
        }
    }
    pub fn set_details_enabled(&mut self, enabled: bool) {
        self.work.details_enabled = enabled;
        if !enabled {
            self.close_details()
        }
    }
    pub fn open_details(&mut self) -> bool {
        if self.row_id.is_empty() || self.column_id.is_empty() {
            return false;
        }
        let r = self.source.row(self.row);
        self.work.detail = Some(std::cell::RefCell::new(TextDocument::viewer(
            r.cells.get(&self.column_id).map_or("", String::as_str),
        )));
        self.work.detail_title = self.columns[self.column].label.clone();
        true
    }
    pub fn close_details(&mut self) {
        self.work.detail = None
    }
    pub(super) fn work_action(&mut self, action: &str, _height: usize) -> Option<GridEvent> {
        self.clear_stale_work();
        if self.work.detail.is_some() {
            if action == "cancel" {
                self.close_details()
            } else {
                self.work
                    .detail
                    .as_ref()
                    .unwrap()
                    .borrow_mut()
                    .handle(action, "");
            }
            return Some(GridEvent::default());
        }
        if self.work.edit.is_some() {
            return Some(self.edit_input(
                if action == "activate" {
                    "submit"
                } else {
                    action
                },
                "",
            ));
        }
        if action == "activate" && self.work.edit_options.enabled {
            let started = self.begin_edit("");
            return Some(GridEvent {
                kind: if started { "edit_begin" } else { "" }.into(),
                row_id: self.row_id.clone(),
                column_id: self.column_id.clone(),
                ..Default::default()
            });
        }
        let mut out = GridEvent::default();
        match action {
            "details" => {
                if self.row_id.is_empty() {
                    return Some(GridEvent::default());
                }
                if self.work.details_enabled {
                    self.open_details();
                }
                out.text = self
                    .source
                    .row(self.row)
                    .cells
                    .get(&self.column_id)
                    .cloned()
                    .unwrap_or_default();
                out.kind = "details".into();
                out.row_id = self.row_id.clone();
                out.column_id = self.column_id.clone()
            }
            "find_next" | "find_previous" => {
                if let Some(r) = self.find_next(action == "find_previous") {
                    out.kind = "find".into();
                    out.row_id = r.row_id;
                    out.column_id = r.column_id
                }
            }
            "next" | "previous" => {
                self.move_editable(action == "previous");
                out.kind = "focus".into()
            }
            "hide_column" => {
                self.hide_column(&self.column_id.clone(), true);
                out.kind = "columns".into()
            }
            "pin_column" => {
                let side = if self
                    .work
                    .pins
                    .get(&self.column_id)
                    .is_some_and(|s| !s.is_empty())
                {
                    ""
                } else {
                    "left"
                };
                self.pin_column(&self.column_id.clone(), side);
                out.kind = "columns".into()
            }
            "column_previous" | "column_next" => {
                let at = if action == "column_previous" {
                    self.column.saturating_sub(1)
                } else {
                    self.column + 1
                };
                self.move_column(&self.column_id.clone(), at);
                out.kind = "columns".into()
            }
            "left" | "right" => {
                let cols = self.visible_indices();
                if let Some(i) = cols.iter().position(|c| *c == self.column) {
                    let j = if action == "left" {
                        i.saturating_sub(1)
                    } else {
                        (i + 1).min(cols.len() - 1)
                    };
                    self.column = cols[j];
                    self.column_id = self.columns[self.column].id.clone()
                }
                out.kind = "focus".into();
                out.row_id = self.row_id.clone();
                out.column_id = self.column_id.clone()
            }
            _ => return None,
        }
        Some(out)
    }
}
use unicode_segmentation::UnicodeSegmentation;
// RFC-style TSV quoting, including embedded newlines and escaped double quotes.
fn parse_tsv(text: &str, limit: usize) -> Result<Vec<Vec<String>>, Error> {
    let fail = || Error::Invalid("invalid quoted TSV".into());
    let mut rows = vec![];
    let mut row = vec![];
    let mut field = String::new();
    let mut quoted = false;
    let mut closed = false;
    let mut chars = text.chars().peekable();
    let mut total = 0;
    while let Some(c) = chars.next() {
        if quoted {
            if c == '"' {
                if chars.peek() == Some(&'"') {
                    chars.next();
                    field.push('"')
                } else {
                    quoted = false;
                    closed = true
                }
            } else if c == '\r' && chars.peek() == Some(&'\n') {
                chars.next();
                field.push('\n')
            } else {
                field.push(c)
            }
            continue;
        }
        if c == '"' && field.is_empty() && !closed {
            quoted = true;
            continue;
        }
        if c == '"' || closed && !['\t', '\r', '\n'].contains(&c) {
            return Err(fail());
        }
        if c == '\r' && chars.peek() != Some(&'\n') {
            if closed {
                return Err(fail());
            }
            field.push(c);
            continue;
        }
        if (c == '\n' || c == '\r') && field.is_empty() && row.is_empty() && !closed {
            if c == '\r' && chars.peek() == Some(&'\n') {
                chars.next();
            }
            continue;
        }
        if c == '\t' || c == '\n' || c == '\r' {
            row.push(std::mem::take(&mut field));
            total += 1;
            if total > limit {
                return Err(fail());
            }
            closed = false;
            if c != '\t' {
                if c == '\r' && chars.peek() == Some(&'\n') {
                    chars.next();
                }
                rows.push(std::mem::take(&mut row));
            }
        } else {
            field.push(c)
        }
    }
    if quoted {
        return Err(fail());
    }
    if !field.is_empty() || closed || !row.is_empty() {
        row.push(field);
        rows.push(row)
    }
    if rows.is_empty() {
        return Err(fail());
    }
    Ok(rows)
}
impl Grid {
    pub fn set_row_edited(&mut self, callback: impl Fn(&GridRecord) -> bool + 'static) {
        self.work.row_edited = Some(Box::new(callback))
    }
    pub(super) fn row_edited(&self, r: &GridRecord) -> bool {
        self.work
            .row_edited
            .as_ref()
            .map_or(r.state.edited, |f| f(r))
    }
    pub(super) fn cell_state(&self, r: &GridRecord, i: &GridCellInfo) -> ControlState {
        let mut s = r.state;
        s.edited = false;
        options::combine(s, i.state)
    }
    pub(super) fn column_spans(
        &self,
        width: usize,
        gutter: usize,
        widths: &mut [usize],
    ) -> (usize, Vec<GridSpan>) {
        let visible = self.visible_indices();
        let mut left = vec![];
        let mut right = vec![];
        let mut normal = vec![];
        for c in visible {
            match self
                .work
                .pins
                .get(&self.columns[c].id)
                .map_or("", String::as_str)
            {
                "left" => left.push(c),
                "right" => right.push(c),
                _ => normal.push(c),
            }
        }
        let physical = |c: usize| widths[c] + 2 * self.options.padding + 1;
        let capacity = width.saturating_sub(gutter);
        let pinned: usize = left.iter().chain(&right).map(|c| physical(*c)).sum();
        let mut budget = capacity.min(pinned);
        if !normal.is_empty() {
            budget = budget.min(capacity.saturating_sub(8.min(capacity)))
        }
        let mut start = 0;
        for (i, c) in normal.iter().enumerate() {
            if *c <= self.left {
                start = i
            }
        }
        if let Some(target) = normal.iter().position(|c| *c == self.column) {
            start = start.min(target);
            while start < target {
                let used: usize = normal[start..=target].iter().map(|c| physical(*c)).sum();
                if used <= capacity - budget {
                    break;
                }
                start += 1
            }
        }
        if let Some(i) = left.iter().position(|c| *c == self.column) {
            left = left[i..].to_vec()
        }
        if let Some(i) = right.iter().position(|c| *c == self.column) {
            right = right[i..].to_vec()
        }
        let mut spans = vec![];
        let mut x = gutter;
        let left_budget = if !right.is_empty() && !left.is_empty() {
            budget.div_ceil(2)
        } else {
            budget
        };
        let left_end = width.min(gutter + left_budget);
        let add =
            |c: usize, x: &mut usize, limit: usize, spans: &mut Vec<GridSpan>, widths: &[usize]| {
                if *x >= limit {
                    return;
                }
                let w = (limit - *x).min(widths[c] + 2 * self.options.padding);
                if w == 0 {
                    return;
                }
                spans.push(GridSpan {
                    id: self.columns[c].id.clone(),
                    start: *x,
                    width: w,
                });
                *x += w + 1;
            };
        for c in left {
            add(c, &mut x, left_end, &mut spans, widths)
        }
        let remaining = budget.saturating_sub(x.saturating_sub(gutter));
        let right_width: usize = right.iter().map(|c| physical(*c)).sum();
        let right_start = x.max(width.saturating_sub(remaining.min(right_width)));
        let mut end = start;
        let mut used = 0;
        while end < normal.len() && used < right_start.saturating_sub(x) {
            used += physical(normal[end]);
            end += 1
        }
        let extra = right_start.saturating_sub(x + used);
        let weight: usize = normal[start..end]
            .iter()
            .map(|c| self.column_options(&self.columns[*c].id).expand)
            .sum();
        if weight > 0 {
            for c in &normal[start..end] {
                let o = self.column_options(&self.columns[*c].id);
                let (_, hi) = options::bounds(&o);
                widths[*c] = (widths[*c] + extra * o.expand / weight).min(hi)
            }
        }
        for c in normal.iter().skip(start) {
            add(*c, &mut x, right_start, &mut spans, widths)
        }
        x = right_start;
        for c in right {
            add(c, &mut x, width, &mut spans, widths)
        }
        (normal.get(start).copied().unwrap_or(self.left), spans)
    }
    pub(super) fn detail_layout(&self, width: usize, height: usize) -> Vec<ComponentLine> {
        let mut doc = self.work.detail.as_ref().unwrap().borrow_mut();
        if width < 4 || height < 4 {
            return doc.layout(width, height);
        }
        let w = width - 2;
        let h = height - 2;
        let body = doc.layout(w.saturating_sub(2).max(1), h.saturating_sub(2).max(1));
        let mut rows = vec![ComponentLine {
            role: "grid.base".into(),
            ..Default::default()
        }];
        let (tl, tr, bl, br, edge, side) = if self.options.ascii {
            ("+", "+", "+", "+", "-", "|")
        } else {
            ("╔", "╗", "╚", "╝", "═", "║")
        };
        let title = crate::components::cell_text(
            &format!(" {} ", self.work.detail_title),
            w.saturating_sub(2),
        );
        let top = format!(
            "{}{}{}{}",
            tl,
            title,
            edge.repeat(w.saturating_sub(2 + crate::components::cells(&title))),
            tr
        );
        rows.push(ComponentLine {
            role: "grid.base".into(),
            spans: vec![ComponentSpan {
                start: 1,
                width: w,
                text: top,
                role: "header".into(),
                focused: false,
            }],
            ..Default::default()
        });
        for i in 0..h.saturating_sub(2) {
            let mut l = body.get(i).cloned().unwrap_or_else(|| ComponentLine {
                role: "grid.base".into(),
                ..Default::default()
            });
            for s in &mut l.spans {
                s.start += 2
            }
            l.spans.insert(
                0,
                ComponentSpan {
                    start: 2,
                    width: w.saturating_sub(2),
                    text: std::mem::take(&mut l.text),
                    role: l.role.clone(),
                    focused: false,
                },
            );
            for x in [1, width - 2] {
                l.spans.push(ComponentSpan {
                    start: x,
                    width: 1,
                    text: side.into(),
                    role: "header".into(),
                    focused: false,
                })
            }
            rows.push(l)
        }
        rows.push(ComponentLine {
            role: "grid.base".into(),
            spans: vec![ComponentSpan {
                start: 1,
                width: w,
                text: format!("{}{}{}", bl, edge.repeat(w.saturating_sub(2)), br),
                role: "header".into(),
                focused: false,
            }],
            ..Default::default()
        });
        rows
    }
}
impl Grid {
    pub(super) fn edit_point(
        &mut self,
        action: &str,
        x: isize,
        y: isize,
        width: usize,
        height: usize,
        extend: bool,
    ) -> GridEvent {
        if action == "up" {
            self.work.edit_dragging = false;
            return GridEvent::default();
        }
        let Some(e) = &self.work.edit else {
            return GridEvent::default();
        };
        if e.pending || e.value.null {
            return GridEvent::default();
        }
        let geo = self.geometry(width, height);
        let row = self.source.index_of(&e.row_id).unwrap_or(self.row);
        let at = geo.header_rows as isize + (row as isize - geo.top as isize) * geo.stride as isize;
        for s in geo.columns {
            if s.id != e.column_id
                || y != at
                || x < s.start as isize
                || x >= (s.start + s.width) as isize
            {
                continue;
            }
            if !(["down", "click", "double"].contains(&action)
                || action == "move" && self.work.edit_dragging)
            {
                return GridEvent::default();
            }
            let dirty = self
                .info(
                    &self.source.row(row),
                    &self.columns[self.column_index(&s.id).unwrap()],
                )
                .state
                .edited;
            let b = self.work.buffer.as_mut().unwrap();
            let gs = b.text().graphemes(true).collect::<Vec<_>>();
            let (_, _, start) = super::cursor::editor_window(
                b.text(),
                b.cursor,
                s.width
                    .saturating_sub(2 * self.options.padding + if dirty { 2 } else { 0 }),
            );
            let offset = x
                .saturating_sub(
                    s.start as isize + self.options.padding as isize + if dirty { 2 } else { 0 },
                )
                .max(0) as usize;
            let mut pos = start;
            let mut used = 0;
            for g in gs.iter().skip(start) {
                let w = crate::components::cells(g);
                if used + w > offset {
                    break;
                }
                used += w;
                pos += 1
            }
            let anchor = if extend || action == "move" {
                b.anchor
            } else {
                pos
            };
            b.select(anchor, pos);
            self.work.edit_dragging = action != "click" && action != "double";
            return GridEvent {
                kind: "edit_select".into(),
                row_id: e.row_id.clone(),
                column_id: e.column_id.clone(),
                ..Default::default()
            };
        }
        GridEvent {
            kind: if ["down", "click", "double"].contains(&action) {
                "edit_blocked"
            } else {
                ""
            }
            .into(),
            ..Default::default()
        }
    }
}
