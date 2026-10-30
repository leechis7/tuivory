use super::*;
impl Grid {
    /// Host-translated local coordinates. Capture down/move/up while dragging.
    pub fn pointer(
        &mut self,
        action: &str,
        x: isize,
        y: isize,
        width: usize,
        height: usize,
        extend: bool,
    ) -> GridEvent {
        if ![
            "down",
            "move",
            "up",
            "click",
            "double",
            "wheel_up",
            "wheel_down",
            "wheel_left",
            "wheel_right",
        ]
        .contains(&action)
        {
            return GridEvent::default();
        }
        if self.options.disable_mouse {
            return GridEvent::default();
        }
        if action == "up" {
            self.drag_column.clear();
            self.drag_anchor = GridRange::default();
            return GridEvent::default();
        }
        if let Some(nav) = action.strip_prefix("wheel_") {
            return self.handle(
                match nav {
                    "up" => "up",
                    "down" => "down",
                    "left" => "left",
                    "right" => "right",
                    _ => "",
                },
                height,
            );
        }
        if action == "move" && !self.drag_column.is_empty() {
            let id = self.drag_column.clone();
            let (lo, hi) = options::bounds(&self.column_options(&id));
            let w = (self.drag_width as isize + x - self.drag_x).clamp(lo as isize, hi as isize)
                as usize;
            if self.resize_column(&id, w) {
                return GridEvent {
                    kind: "resize".into(),
                    column_id: id,
                    ..Default::default()
                };
            }
            return GridEvent::default();
        }
        if action == "move" && self.drag_anchor.anchor_row.is_empty() {
            return GridEvent::default();
        }
        if x < 0 || y < 0 || x as usize >= width || y as usize >= height {
            return GridEvent::default();
        }
        let x = x as usize;
        let y = y as usize;
        let geo = self.geometry(width, height);
        if y < geo.header_rows {
            if action == "down" && !self.options.disable_resize {
                for s in &geo.columns {
                    if x == s.start + s.width {
                        self.drag_column = s.id.clone();
                        self.drag_x = x as isize;
                        self.drag_width = s.width.saturating_sub(2 * self.options.padding).max(1);
                        return GridEvent {
                            kind: "resize_start".into(),
                            column_id: s.id.clone(),
                            ..Default::default()
                        };
                    }
                }
            }
            if action == "click" || action == "double" {
                return self.click_cell("", "@header", x, width, height);
            }
            return GridEvent::default();
        }
        if y >= height.saturating_sub(geo.footer_rows) || geo.stride == 0 {
            return GridEvent::default();
        }
        let offset = y - geo.header_rows;
        if self.options.horizontal_lines && offset % geo.stride == geo.stride - 1 {
            return GridEvent::default();
        }
        let index = geo.top + offset / geo.stride;
        if index >= self.source.len() {
            return GridEvent::default();
        }
        let row = self.source.row(index);
        let column = if let Some(s) = geo
            .columns
            .iter()
            .find(|s| x >= s.start && x < s.start + s.width)
        {
            s.id.clone()
        } else if x < geo.gutter && self.options.row_numbers && !self.column_id.is_empty() {
            if action == "click" || action == "down" {
                let _ = self.set_selection_mode("row");
            }
            self.column_id.clone()
        } else {
            return GridEvent::default();
        };
        if action == "down" && !extend && !self.whole_row {
            self.selection = GridRange::default();
            self.range_mode = false;
        }
        let before = GridRange {
            anchor_row: self.row_id.clone(),
            anchor_column: self.column_id.clone(),
            ..Default::default()
        };
        if !self.focus(&row.id, &column) {
            return GridEvent::default();
        }
        if action == "down" {
            self.drag_anchor = GridRange {
                anchor_row: row.id.clone(),
                anchor_column: column.clone(),
                end_row: row.id.clone(),
                end_column: column.clone(),
            };
        }
        if action == "move" {
            if row.id == self.drag_anchor.anchor_row && column == self.drag_anchor.anchor_column {
                return GridEvent::default();
            }
            let mut r = self.drag_anchor.clone();
            r.end_row = row.id.clone();
            r.end_column = column.clone();
            if self.select_range(r) {
                return GridEvent {
                    kind: "select".into(),
                    row_id: row.id,
                    column_id: column,
                    ..Default::default()
                };
            }
            return GridEvent::default();
        }
        if action == "double" {
            return self.handle("activate", height);
        }
        if action != "down" && action != "click" {
            return GridEvent::default();
        }
        if extend {
            let mut r = if self.range_bounds().is_some() {
                self.selection.clone()
            } else {
                before
            };
            r.end_row = row.id;
            r.end_column = column;
            self.select_range(r);
        }
        self.handle("select", height)
    }
    pub fn pointer_captured(&self) -> bool {
        !self.drag_column.is_empty() || !self.drag_anchor.anchor_row.is_empty()
    }
}
