//! Virtual row access, stable cell IDs and host-owned sort/filter/edit/copy I/O.
use crate::{
    Error,
    forms::{ComponentLine, ComponentSpan},
    interaction::ControlState,
};
use std::collections::BTreeMap;
#[derive(Clone, Debug, Default)]
pub struct GridColumn {
    pub id: String,
    pub label: String,
    pub width: usize,
    pub editable: bool,
}
#[derive(Clone, Debug, Default)]
pub struct GridRecord {
    pub id: String,
    pub cells: BTreeMap<String, String>,
    pub state: ControlState,
}
pub trait GridSource {
    fn len(&self) -> usize;
    fn is_empty(&self) -> bool {
        self.len() == 0
    }
    fn row(&self, index: usize) -> GridRecord;
    fn index_of(&self, id: &str) -> Option<usize>;
}
#[derive(Clone, Debug)]
pub struct MemoryRows {
    rows: Vec<GridRecord>,
    index: BTreeMap<String, usize>,
}
impl MemoryRows {
    pub fn new(rows: Vec<GridRecord>) -> Result<Self, Error> {
        let mut index = BTreeMap::new();
        for (i, row) in rows.iter().enumerate() {
            if row.id.is_empty() || index.insert(row.id.clone(), i).is_some() {
                return Err(Error::Invalid("empty or duplicate row ID".into()));
            }
        }
        Ok(Self { rows, index })
    }
}
impl GridSource for MemoryRows {
    fn len(&self) -> usize {
        self.rows.len()
    }
    fn row(&self, index: usize) -> GridRecord {
        self.rows.get(index).cloned().unwrap_or_default()
    }
    fn index_of(&self, id: &str) -> Option<usize> {
        self.index.get(id).copied()
    }
}
#[derive(Clone, Debug, Default)]
pub struct GridEvent {
    pub kind: String,
    pub row_id: String,
    pub column_id: String,
    pub text: String,
    pub direction: String,
}
pub struct Grid {
    columns: Vec<GridColumn>,
    source: Box<dyn GridSource>,
    pub row_id: String,
    pub column_id: String,
    pub selected_row: String,
    pub selected_column: String,
    pub sort_column: String,
    pub sort_direction: String,
    row: usize,
    column: usize,
    top: usize,
    left: usize,
    pub whole_row: bool,
    pub empty: String,
}
#[derive(Clone, Debug)]
pub struct GridSpan {
    pub id: String,
    pub start: usize,
    pub width: usize,
}
impl Grid {
    pub fn new(mut columns: Vec<GridColumn>, source: Box<dyn GridSource>) -> Result<Self, Error> {
        let mut seen = std::collections::BTreeSet::new();
        for col in &mut columns {
            if col.id.is_empty() || !seen.insert(col.id.clone()) {
                return Err(Error::Invalid("invalid column ID".into()));
            }
            if col.width == 0 {
                col.width = 12
            }
            col.width = col.width.min(4096)
        }
        let mut g = Self {
            columns,
            source,
            row_id: String::new(),
            column_id: String::new(),
            selected_row: String::new(),
            selected_column: String::new(),
            sort_column: String::new(),
            sort_direction: String::new(),
            row: 0,
            column: 0,
            top: 0,
            left: 0,
            whole_row: false,
            empty: "(empty)".into(),
        };
        g.reconcile();
        Ok(g)
    }
    pub fn columns(&self) -> &[GridColumn] {
        &self.columns
    }
    pub fn set_source(&mut self, source: Box<dyn GridSource>) {
        if let Some(at) = source
            .index_of(&self.row_id)
            .filter(|at| *at < source.len())
        {
            self.row = at
        }
        if source.index_of(&self.selected_row).is_none() {
            self.selected_row.clear();
            self.selected_column.clear()
        }
        self.source = source;
        self.reconcile()
    }
    fn reconcile(&mut self) {
        if self.columns.is_empty() {
            self.column_id.clear();
            self.row_id.clear();
            return;
        }
        self.column = self.column.min(self.columns.len() - 1);
        self.column_id = self.columns[self.column].id.clone();
        if self.source.is_empty() {
            self.row = 0;
            self.row_id.clear();
            return;
        }
        self.row = self.row.min(self.source.len() - 1);
        if self.source.row(self.row).state.disabled {
            let found = (self.row..self.source.len())
                .find(|i| !self.source.row(*i).state.disabled)
                .or_else(|| {
                    (0..self.row)
                        .rev()
                        .find(|i| !self.source.row(*i).state.disabled)
                });
            if let Some(index) = found {
                self.row = index
            } else {
                self.row_id.clear();
                return;
            }
        }
        self.row_id = self.source.row(self.row).id;
        self.top = self.top.min(self.row);
        self.left = self.left.min(self.column)
    }
    pub fn focus(&mut self, row_id: &str, column_id: &str) -> bool {
        let Some(row) = self
            .source
            .index_of(row_id)
            .filter(|at| *at < self.source.len())
        else {
            return false;
        };
        let record = self.source.row(row);
        if record.id != row_id || record.state.disabled {
            return false;
        }
        let Some(col) = self.columns.iter().position(|c| c.id == column_id) else {
            return false;
        };
        self.row = row;
        self.column = col;
        self.reconcile();
        true
    }
    pub fn resize_column(&mut self, id: &str, width: usize) -> bool {
        if !(1..=4096).contains(&width) {
            return false;
        }
        let Some(col) = self.columns.iter_mut().find(|c| c.id == id) else {
            return false;
        };
        col.width = width;
        true
    }
    pub fn request_filter(&self, query: &str) -> GridEvent {
        GridEvent {
            kind: "filter".into(),
            text: query.into(),
            ..Default::default()
        }
    }
    pub fn handle(&mut self, action: &str, height: usize) -> GridEvent {
        self.reconcile();
        if self.columns.is_empty() {
            return GridEvent::default();
        }
        let mut event = GridEvent {
            row_id: self.row_id.clone(),
            column_id: self.column_id.clone(),
            ..Default::default()
        };
        if action == "sort" {
            let same = self.sort_column == self.column_id;
            self.sort_column = self.column_id.clone();
            self.sort_direction = if same && self.sort_direction == "asc" {
                "desc"
            } else {
                "asc"
            }
            .into();
            event.kind = "sort".into();
            event.direction = self.sort_direction.clone();
            return event;
        }
        if self.row_id.is_empty() {
            return GridEvent::default();
        }
        let row = self.source.row(self.row);
        let old = self.row;
        match action {
            "copy" => {
                event.kind = "copy".into();
                event.text = if self.whole_row {
                    self.columns
                        .iter()
                        .map(|c| row.cells.get(&c.id).cloned().unwrap_or_default())
                        .collect::<Vec<_>>()
                        .join("\t")
                } else {
                    row.cells.get(&self.column_id).cloned().unwrap_or_default()
                };
                return event;
            }
            "activate" => {
                if self.columns[self.column].editable && row.state.visual().editable {
                    event.kind = "edit".into();
                    event.text = row.cells.get(&self.column_id).cloned().unwrap_or_default()
                }
                return event;
            }
            "select" => {
                self.selected_row = self.row_id.clone();
                self.selected_column = self.column_id.clone();
                event.kind = "select".into();
                return event;
            }
            "row_mode" => {
                self.whole_row = !self.whole_row;
                return GridEvent {
                    kind: "mode".into(),
                    ..Default::default()
                };
            }
            "left" => self.column = self.column.saturating_sub(1),
            "right" => self.column = (self.column + 1).min(self.columns.len() - 1),
            "up" => self.row = self.row.saturating_sub(1),
            "down" => self.row = (self.row + 1).min(self.source.len() - 1),
            "first" => self.row = 0,
            "last" => self.row = self.source.len() - 1,
            "page_up" => self.row = self.row.saturating_sub(height.saturating_sub(2).max(1)),
            "page_down" => {
                self.row = (self.row + height.saturating_sub(2).max(1)).min(self.source.len() - 1)
            }
            "widen" => {
                let id = self.column_id.clone();
                self.resize_column(&id, (self.columns[self.column].width + 1).min(4096));
            }
            "narrow" => {
                let id = self.column_id.clone();
                self.resize_column(
                    &id,
                    self.columns[self.column].width.saturating_sub(1).max(1),
                );
            }
            _ => return GridEvent::default(),
        }
        if self.row != old {
            let backwards = self.row < old;
            while self.source.row(self.row).state.disabled {
                if backwards {
                    if self.row == 0 {
                        self.row = old;
                        break;
                    }
                    self.row -= 1
                } else {
                    if self.row + 1 >= self.source.len() {
                        self.row = old;
                        break;
                    }
                    self.row += 1
                }
            }
        }
        self.reconcile();
        event.kind = "focus".into();
        event.row_id = self.row_id.clone();
        event.column_id = self.column_id.clone();
        event
    }
    fn spans(&self, width: usize) -> Vec<GridSpan> {
        let mut left = self.left.min(self.column);
        let capacity = width.saturating_sub(3);
        while left < self.column {
            let used: usize = self.columns[left..=self.column]
                .iter()
                .map(|c| c.width + 1)
                .sum();
            if used <= capacity {
                break;
            }
            left += 1
        }
        let mut out = vec![];
        let mut x = 3;
        for col in self.columns.iter().skip(left) {
            if x >= width {
                break;
            }
            let w = col.width.min(width - x);
            out.push(GridSpan {
                id: col.id.clone(),
                start: x,
                width: w,
            });
            x += w + 1
        }
        out
    }
    pub fn layout(&self, width: usize, height: usize) -> Vec<ComponentLine> {
        if width == 0 || height == 0 || self.columns.is_empty() {
            return vec![];
        }
        let spans = self.spans(width);
        let mut header = ComponentLine {
            role: "header".into(),
            value: "@header".into(),
            ..Default::default()
        };
        for span in &spans {
            let mut label = self
                .columns
                .iter()
                .find(|c| c.id == span.id)
                .map(|c| c.label.clone())
                .unwrap_or_default();
            if span.id == self.sort_column {
                label.push_str(&format!(" {}", self.sort_direction))
            }
            header.spans.push(ComponentSpan {
                start: span.start,
                width: span.width,
                text: if span.id == self.column_id {
                    format!("> {label}")
                } else {
                    label
                },
                role: "header".into(),
                focused: span.id == self.column_id,
            });
        }
        let mut out = vec![header];
        if self.source.is_empty() {
            if height > 1 {
                out.push(ComponentLine {
                    text: crate::components::cell_text(&self.empty, width),
                    role: "hint".into(),
                    ..Default::default()
                })
            }
            return out;
        }
        let mut top = self.top.min(self.row);
        if self.row >= top + height.saturating_sub(1).max(1) {
            top = self.row - height.saturating_sub(1).max(1) + 1
        }
        top = top.min(
            self.source
                .len()
                .saturating_sub(height.saturating_sub(1).max(1)),
        );
        for index in top..self.source.len() {
            if out.len() >= height {
                break;
            }
            let record = self.source.row(index);
            let visual = record.state.visual();
            let mut line = ComponentLine {
                id: record.id.clone(),
                text: format!(
                    "{}{}",
                    if record.id == self.row_id { "> " } else { "  " },
                    visual.markers
                ),
                role: visual.role.into(),
                focused: record.id == self.row_id,
                ..Default::default()
            };
            for span in &spans {
                let mut state = record.state;
                if record.id == self.selected_row
                    && (self.whole_row || span.id == self.selected_column)
                {
                    state.selected = true
                }
                line.spans.push(ComponentSpan {
                    start: span.start,
                    width: span.width,
                    text: format!(
                        "{}{}",
                        if state.selected { "> " } else { "" },
                        record.cells.get(&span.id).cloned().unwrap_or_default()
                    ),
                    role: state.visual().role.into(),
                    focused: record.id == self.row_id && span.id == self.column_id,
                })
            }
            out.push(line)
        }
        out
    }
    pub fn click(
        &mut self,
        row_id: &str,
        kind: &str,
        x: usize,
        width: usize,
        height: usize,
    ) -> GridEvent {
        for span in self.spans(width) {
            if x >= span.start && x < span.start + span.width {
                if kind == "@header" {
                    if let Some(col) = self.columns.iter().position(|c| c.id == span.id) {
                        self.column = col
                    }
                    return self.handle("sort", height);
                }
                if self.focus(row_id, &span.id) {
                    return self.handle("select", height);
                }
            }
        }
        GridEvent::default()
    }
}
