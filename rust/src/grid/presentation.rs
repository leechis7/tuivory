use super::*;
use crate::components::{StatusItem, cell_text, cells, clean, status_line};
use unicode_segmentation::UnicodeSegmentation;
pub(super) fn text_width(s: &str) -> usize {
    cells(&clean(s))
}
fn fit(s: &str, w: usize, offset: usize, overflow: &str) -> String {
    let s = clean(s);
    let mut text = String::new();
    let mut used = 0;
    if overflow == "scroll" && offset > 0 {
        for g in s.graphemes(true) {
            let n = cells(g);
            if used >= offset {
                text.push_str(g)
            } else if used + n > offset {
                text.push_str(&" ".repeat(used + n - offset))
            }
            used += n;
        }
    } else {
        text = s
    }
    if overflow != "clip" {
        return cell_text(&text, w);
    }
    let mut out = String::new();
    let mut used = 0;
    for g in text.graphemes(true) {
        let n = cells(g);
        if used + n > w {
            break;
        }
        out.push_str(g);
        used += n;
    }
    out
}
fn align(s: &str, w: usize, a: &str) -> String {
    let pad = w.saturating_sub(text_width(s));
    let left = match a {
        "right" => pad,
        "center" => pad / 2,
        _ => 0,
    };
    format!("{}{}{}", " ".repeat(left), s, " ".repeat(pad - left))
}
struct Window {
    geo: GridGeometry,
    rows: Vec<GridRecord>,
}
impl Grid {
    fn window(&self, width: usize, height: usize) -> Window {
        let width = width.min(65535);
        let height = height.min(4096);
        let o = &self.options;
        let mut geo = GridGeometry {
            stride: 1 + o.row_spacing + usize::from(o.horizontal_lines),
            ..Default::default()
        };
        if width == 0 || height == 0 || self.columns.is_empty() {
            return Window { geo, rows: vec![] };
        }
        geo.gutter = if o.hide_markers { 0 } else { 3 };
        if o.row_numbers {
            geo.gutter =
                self.source.len().max(1).to_string().len() + 3 - usize::from(o.hide_markers)
        }
        geo.gutter = geo.gutter.max(o.gutter_width).min(width);
        geo.header_rows = usize::from(!o.hide_header);
        geo.footer_rows = usize::from(o.status_bar && height >= 3);
        let mut rows = height
            .saturating_sub(geo.header_rows + geo.footer_rows)
            .div_ceil(geo.stride);
        geo.top = self.top.min(self.row);
        if rows > 0 && self.row >= geo.top + rows {
            geo.top = self.row - rows + 1
        }
        geo.top = geo.top.min(self.source.len().saturating_sub(rows));
        if o.scroll_header && geo.top > 0 {
            geo.header_rows = 0;
            rows = height.saturating_sub(geo.footer_rows).div_ceil(geo.stride)
        }
        geo.body_rows = rows;
        let records = (geo.top..self.source.len().min(geo.top.saturating_add(rows)))
            .map(|n| self.source.row(n))
            .collect::<Vec<_>>();
        let mut widths = vec![];
        for col in &self.columns {
            let co = self.column_options(&col.id);
            let (lo, hi) = options::bounds(&co);
            let mut w = col.width;
            if co.auto_fit {
                w = text_width(&col.label) + 2;
                for r in &records {
                    let i = self.info(r, col);
                    let s = if i.has_display {
                        i.display
                    } else if i.null {
                        self.label("null", "NULL")
                    } else {
                        r.cells.get(&col.id).cloned().unwrap_or_default()
                    };
                    w = w.max(text_width(&s) + if o.show_cell_markers { 2 } else { 0 });
                }
            }
            widths.push(w.clamp(lo, hi));
        }
        let capacity = width.saturating_sub(geo.gutter);
        geo.left = self.left.min(self.column);
        while geo.left < self.column {
            let used: usize = (geo.left..=self.column)
                .map(|c| widths[c] + 2 * o.padding + 1)
                .sum();
            if used <= capacity {
                break;
            }
            geo.left += 1;
        }
        let mut used = 0;
        let mut end = geo.left;
        while end < self.columns.len() && used < capacity {
            used += widths[end] + 2 * o.padding + 1;
            end += 1;
        }
        let extra = capacity.saturating_sub(used);
        let weight: usize = self.columns[geo.left..end]
            .iter()
            .map(|c| self.column_options(&c.id).expand)
            .sum();
        if weight > 0 {
            for (c, width) in widths.iter_mut().enumerate().take(end).skip(geo.left) {
                let co = self.column_options(&self.columns[c].id);
                let (_, hi) = options::bounds(&co);
                *width = (*width + extra * co.expand / weight).min(hi);
            }
        }
        let mut x = geo.gutter;
        for (c, col) in self.columns.iter().enumerate().skip(geo.left) {
            if x >= width {
                break;
            }
            let w = (widths[c] + 2 * o.padding).min(width - x);
            geo.columns.push(GridSpan {
                id: col.id.clone(),
                start: x,
                width: w,
            });
            x += w + 1;
        }
        Window { geo, rows: records }
    }
    pub fn geometry(&self, width: usize, height: usize) -> GridGeometry {
        self.window(width, height).geo
    }
    fn row_role(&self, r: &GridRecord, index: usize) -> String {
        let mut role = r.state.visual().role;
        if role == "body" {
            if self.options.use_surface {
                role = "grid.base"
            }
            if self.options.striped && index % 2 == 1 {
                role = "grid.stripe"
            }
            if self.options.highlight_row && r.id == self.row_id {
                role = "grid.current-row"
            }
        }
        role.into()
    }
    fn cell_role(&self, r: &GridRecord, c: &GridColumn, index: usize, selected: bool) -> String {
        let i = self.info(r, c);
        let s = options::combine(r.state, i.state);
        let role = if s.disabled {
            "disabled"
        } else if s.invalid {
            "error"
        } else if s.edited && self.options.preserve_edited {
            "grid.edited"
        } else if self.options.highlight_cell && r.id == self.row_id && c.id == self.column_id {
            "grid.active"
        } else if selected && self.range_mode && !self.whole_row {
            "grid.range"
        } else if selected {
            "selection"
        } else if s.edited {
            "edited"
        } else if s.busy && (self.options.use_surface || self.cell_info.is_some()) {
            "grid.loading"
        } else if s.read_only && (self.options.use_surface || self.cell_info.is_some()) {
            "grid.readonly"
        } else if i.null {
            "grid.null"
        } else {
            return self.row_role(r, index);
        };
        role.into()
    }
    fn cell_text(&self, r: &GridRecord, c: &GridColumn, w: usize, selected: bool) -> String {
        let o = &self.options;
        let co = self.column_options(&c.id);
        let i = self.info(r, c);
        let mut s = options::combine(r.state, i.state);
        if self.range_mode && selected && o.show_cell_markers {
            s.selected = true;
        }
        let raw = if i.has_display {
            i.display
        } else if i.null {
            self.label("null", "NULL")
        } else {
            r.cells.get(&c.id).cloned().unwrap_or_default()
        };
        let mut prefix = if selected && !o.hide_selection_marker {
            "> ".to_string()
        } else {
            String::new()
        };
        if o.show_cell_markers {
            prefix.push_str(&s.visual().markers);
            if !prefix.is_empty() {
                prefix.push(' ')
            }
        }
        let content = w.saturating_sub(2 * o.padding);
        let text = fit(
            &format!("{prefix}{raw}"),
            content,
            *self.cell_pan.get(&c.id).unwrap_or(&0),
            &co.overflow,
        );
        let a = if co.align == "numeric" {
            if i.numeric { "right" } else { "left" }
        } else {
            &co.align
        };
        fit(
            &format!(
                "{}{}{}",
                " ".repeat(o.padding.min(w)),
                align(&text, content, a),
                " ".repeat(o.padding.min(w))
            ),
            w,
            0,
            "clip",
        )
    }
    fn selected(&self, row: usize, col: usize, r: &GridRecord, c: &GridColumn) -> bool {
        if self.range_mode && !self.whole_row {
            if let Some((r1, r2, c1, c2)) = self.range_bounds() {
                return row >= r1 && row <= r2 && col >= c1 && col <= c2;
            }
            return false;
        }
        r.id == self.selected_row && (self.whole_row || c.id == self.selected_column)
    }
    fn decorations(
        &self,
        l: &mut ComponentLine,
        geo: &GridGeometry,
        width: usize,
        header: bool,
        r: &GridRecord,
        index: usize,
    ) {
        let o = &self.options;
        let vertical = if o.ascii { "|" } else { "│" };
        if o.row_numbers && geo.gutter > 0 {
            let mut label = if header {
                "#".into()
            } else {
                (index + 1).to_string()
            };
            if !header && !o.hide_markers {
                if r.state.edited {
                    label = format!("*{label}")
                }
                if r.id == self.row_id {
                    label = format!(">{label}")
                }
            }
            let w = geo.gutter.saturating_sub(usize::from(o.vertical_lines));
            l.spans.push(ComponentSpan {
                start: 0,
                width: w,
                text: align(&fit(&label, w, 0, "clip"), w, "right"),
                role: if header { "header" } else { "grid.gutter" }.into(),
                focused: false,
            });
        }
        if o.vertical_lines {
            let mut at = vec![];
            if geo.gutter > 0 {
                at.push(geo.gutter - 1)
            }
            for s in &geo.columns {
                if s.start + s.width < width {
                    at.push(s.start + s.width)
                }
            }
            for x in at {
                l.spans.push(ComponentSpan {
                    start: x,
                    width: 1,
                    text: vertical.into(),
                    role: "grid.divider".into(),
                    focused: false,
                });
            }
        }
    }
    pub fn layout(&self, width: usize, height: usize) -> Vec<ComponentLine> {
        self.last_width.set(width.min(65535));
        let width = width.min(65535);
        let height = height.min(4096);
        if width == 0 || height == 0 || self.columns.is_empty() {
            return vec![];
        }
        let win = self.window(width, height);
        let geo = &win.geo;
        let o = &self.options;
        let mut out = vec![];
        if geo.header_rows > 0 {
            let mut h = ComponentLine {
                role: "header".into(),
                value: "@header".into(),
                ..Default::default()
            };
            for s in &geo.columns {
                let c = &self.columns[self.column_index(&s.id).unwrap()];
                let mut label = c.label.clone();
                if s.id == self.sort_column {
                    label.push_str(&format!(" {}", self.sort_direction))
                }
                if s.id == self.column_id && !o.hide_selection_marker {
                    label = format!("> {label}")
                }
                let content = s.width.saturating_sub(2 * o.padding);
                h.spans.push(ComponentSpan {
                    start: s.start,
                    width: s.width,
                    text: format!(
                        "{}{}",
                        " ".repeat(o.padding.min(s.width)),
                        align(
                            &cell_text(&label, content),
                            content,
                            &self.column_options(&s.id).align
                        )
                    ),
                    role: if s.id == self.column_id && o.highlight_cell {
                        "grid.header-active"
                    } else {
                        "header"
                    }
                    .into(),
                    focused: s.id == self.column_id,
                });
            }
            self.decorations(&mut h, geo, width, true, &GridRecord::default(), 0);
            out.push(h);
        }
        let body_limit = height - geo.footer_rows;
        if self.source.is_empty() && out.len() < body_limit {
            let mut message = self.empty.clone();
            let mut role = "hint";
            if self.status.loading {
                message = self.label("loading", "loading")
            }
            if !self.status.error.is_empty() {
                message = self.status.error.clone();
                role = "error"
            }
            out.push(ComponentLine {
                text: cell_text(&message, width),
                role: role.into(),
                ..Default::default()
            });
        }
        for (n, r) in win.rows.iter().enumerate() {
            if out.len() >= body_limit {
                break;
            }
            let index = geo.top + n;
            let marker = if o.hide_markers {
                ""
            } else if r.id == self.row_id {
                "> "
            } else {
                "  "
            };
            let mut l = ComponentLine {
                id: r.id.clone(),
                text: format!("{}{}", marker, r.state.visual().markers),
                role: self.row_role(r, index),
                focused: r.id == self.row_id,
                ..Default::default()
            };
            for s in &geo.columns {
                let ci = self.column_index(&s.id).unwrap();
                let c = &self.columns[ci];
                let selected = self.selected(index, ci, r, c);
                l.spans.push(ComponentSpan {
                    start: s.start,
                    width: s.width,
                    text: self.cell_text(r, c, s.width, selected),
                    role: self.cell_role(r, c, index, selected),
                    focused: r.id == self.row_id && s.id == self.column_id,
                });
            }
            self.decorations(&mut l, geo, width, false, r, index);
            out.push(l.clone());
            for _ in 0..o.row_spacing {
                if out.len() >= body_limit {
                    break;
                }
                let mut blank = l.clone();
                blank.text.clear();
                blank.value = "@padding".into();
                blank.focused = false;
                for s in &mut blank.spans {
                    s.text.clear();
                    s.focused = false
                }
                self.decorations(&mut blank, geo, width, false, r, index);
                out.push(blank);
            }
            if o.horizontal_lines && n + 1 < win.rows.len() && out.len() < body_limit {
                let mut sep = ComponentLine {
                    text: if o.ascii { "-" } else { "─" }.repeat(width),
                    role: "grid.divider".into(),
                    value: "@separator".into(),
                    ..Default::default()
                };
                if o.vertical_lines {
                    let mut at = vec![];
                    if geo.gutter > 0 {
                        at.push(geo.gutter - 1)
                    }
                    for s in &geo.columns {
                        if s.start + s.width < width {
                            at.push(s.start + s.width)
                        }
                    }
                    for x in at {
                        sep.spans.push(ComponentSpan {
                            start: x,
                            width: 1,
                            text: if o.ascii { "+" } else { "┼" }.into(),
                            role: "grid.divider".into(),
                            focused: false,
                        });
                    }
                }
                out.push(sep);
            }
        }
        if geo.footer_rows > 0 {
            while out.len() < height - 1 {
                out.push(ComponentLine {
                    role: "grid.base".into(),
                    ..Default::default()
                })
            }
            let bar = status_line(&self.status_items(), width);
            out.push(ComponentLine {
                text: bar.runs.iter().map(|r| r.text.as_str()).collect(),
                role: if self.status.error.is_empty() {
                    "grid.status"
                } else {
                    "error"
                }
                .into(),
                value: "@status".into(),
                ..Default::default()
            });
        }
        out
    }
    /// Can also be composed with the public status_line/LineWidget API.
    pub fn status_items(&self) -> Vec<StatusItem> {
        let mut all = BTreeMap::new();
        let mut add = |id: &str, text: String, priority: i32, role: &str| {
            all.insert(
                id.to_string(),
                StatusItem {
                    id: id.into(),
                    text,
                    priority,
                    role: role.into(),
                },
            );
        };
        let row = if self.row_id.is_empty() {
            0
        } else {
            self.row + 1
        };
        let col = if self.column_id.is_empty() {
            0
        } else {
            self.column + 1
        };
        add(
            "position",
            format!(
                "{} {}/{} {} {}/{}",
                self.label("row", "R"),
                row,
                self.source.len().max(self.status.total_rows),
                self.label("column", "C"),
                col,
                self.columns.len()
            ),
            30,
            "body",
        );
        if col > 0 {
            add(
                "column",
                self.columns[self.column].label.clone(),
                20,
                "hint",
            )
        }
        if self.range_mode {
            if let Some((r1, r2, c1, c2)) = self.range_bounds() {
                add(
                    "selection",
                    format!(
                        "{} {}x{}",
                        self.label("selected", "selected"),
                        r2 - r1 + 1,
                        c2 - c1 + 1
                    ),
                    40,
                    "info",
                )
            }
        }
        if !self.sort_column.is_empty() {
            add(
                "sort",
                format!(
                    "{} {} {}",
                    self.label("sort", "sort"),
                    self.sort_column,
                    self.sort_direction
                ),
                10,
                "hint",
            )
        }
        if !self.status.filter.is_empty() {
            add(
                "filter",
                format!("{} {}", self.label("filter", "filter"), self.status.filter),
                10,
                "hint",
            )
        }
        if self.status.loading {
            add("loading", self.label("loading", "loading"), 80, "info")
        }
        if self.status.has_more {
            add("more", self.label("more", "more"), 50, "info")
        }
        let mut meta = self.status.metadata.clone();
        if self.cell_info.is_some() && row > 0 && col > 0 {
            let m = self
                .info(&self.source.row(self.row), &self.columns[self.column])
                .metadata;
            if !m.is_empty() {
                if !meta.is_empty() {
                    meta.push_str(" / ")
                }
                meta.push_str(&m)
            }
        }
        if !meta.is_empty() {
            add("meta", meta, 15, "hint")
        }
        if !self.status.error.is_empty() {
            add("error", self.status.error.clone(), 100, "error")
        }
        let defaults = [
            "error",
            "position",
            "column",
            "selection",
            "loading",
            "more",
            "sort",
            "filter",
            "meta",
        ]
        .map(String::from)
        .to_vec();
        self.options
            .status_fields
            .as_ref()
            .unwrap_or(&defaults)
            .iter()
            .filter_map(|k| all.remove(k))
            .collect()
    }
}
