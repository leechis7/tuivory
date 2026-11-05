use super::*;
use crate::input::InputEvent;
impl Grid {
    /// Grid-local input only; hosts choose global shortcuts and clipboard I/O.
    pub fn input(&mut self, e: &InputEvent, width: usize, height: usize) -> GridEvent {
        if e.phase == "release" {
            return GridEvent::default();
        }
        if e.kind == "resize" {
            self.layout(e.width, e.height);
            return GridEvent::default();
        }
        if (e.kind == "key" || e.kind == "paste") && self.options.disable_keyboard {
            return GridEvent::default();
        }
        if self.work.edit_revision != self.revision() {
            self.cancel_edit()
        }
        let has = |m: &str| e.modifiers.iter().any(|v| v == m);
        if self.work.detail.is_some() {
            if e.key == "escape" {
                self.close_details();
                return GridEvent::default();
            }
            let (a, t) = e.editing_action();
            let v = self
                .work
                .detail
                .as_ref()
                .unwrap()
                .borrow_mut()
                .handle(&a, &t);
            return GridEvent {
                kind: v.kind,
                text: v.text,
                ..Default::default()
            };
        }
        if self.work.find_buffer.is_some() {
            if e.key == "escape" {
                self.work.find_buffer = None;
                return GridEvent::default();
            }
            if e.key == "enter" {
                let q = self.work.find_buffer.take().unwrap().text().to_string();
                self.set_find(&q, self.work.find_options.clone());
                if has("ctrl") {
                    return self.request_search(&q);
                }
                if let Some(r) = self.find_next(false) {
                    return GridEvent {
                        kind: "find".into(),
                        row_id: r.row_id,
                        column_id: r.column_id,
                        ..Default::default()
                    };
                }
                return GridEvent {
                    kind: "find_end".into(),
                    ..Default::default()
                };
            }
            let (a, t) = e.editing_action();
            self.work.find_buffer.as_mut().unwrap().handle(&a, &t);
            return GridEvent::default();
        }
        if self.work.edit.is_some() {
            let (mut a, t) = e.editing_action();
            match e.key.as_str() {
                "enter" => a = "submit".into(),
                "escape" => a = "cancel".into(),
                "tab" => a = if has("shift") { "previous" } else { "next" }.into(),
                "n" if has("ctrl") => a = "null".into(),
                _ => {}
            }
            return self.edit_input(&a, &t);
        }
        if e.kind == "paste" {
            return match self.request_paste(&e.text, GridPasteOptions::default()) {
                Ok(_) => GridEvent {
                    kind: "paste_request".into(),
                    ..Default::default()
                },
                Err(err) => GridEvent {
                    kind: "paste_rejected".into(),
                    text: err.to_string(),
                    ..Default::default()
                },
            };
        }
        if e.kind != "key" {
            return GridEvent::default();
        }
        if has("alt") {
            match e.key.as_str() {
                "p" => return self.handle("pin_column", height),
                "h" => return self.handle("hide_column", height),
                "u" => {
                    let mut l = self.column_layout();
                    for v in &mut l {
                        v.hidden = false
                    }
                    let _ = self.set_column_layout(l);
                    return GridEvent {
                        kind: "columns".into(),
                        ..Default::default()
                    };
                }
                _ => {}
            }
        }
        if has("ctrl") && ["s", "r"].contains(&e.key.as_str()) {
            return GridEvent {
                kind: if e.key == "s" {
                    "view_save"
                } else {
                    "view_restore"
                }
                .into(),
                ..Default::default()
            };
        }
        if has("ctrl") {
            if has("shift") && ["left", "right"].contains(&e.key.as_str()) {
                return self.handle(
                    if e.key == "left" {
                        "column_previous"
                    } else {
                        "column_next"
                    },
                    height,
                );
            }
            match e.key.as_str() {
                "f" => {
                    let mut b = crate::text::TextBuffer::new(&self.work.query);
                    b.single_line = true;
                    self.work.find_buffer = Some(b);
                    return GridEvent::default();
                }
                "p" => return self.handle("pin_column", height),
                "h" => return self.handle("hide_column", height),
                "c" => return self.handle("copy", height),
                _ => {}
            }
        }
        let mut action = match e.key.as_str() {
            "enter" => "activate",
            "escape" => "cancel",
            "left" => "left",
            "right" => "right",
            "up" => "up",
            "down" => "down",
            "home" => "first",
            "end" => "last",
            "page_up" => "page_up",
            "page_down" => "page_down",
            "f6" => "row_mode",
            "f7" => "widen",
            "f8" => "narrow",
            "f9" => "sort",
            "f10" => "range_mode",
            "f11" => "autofit",
            "f12" => "details",
            " " => "select",
            "tab" => "next",
            "f4" => "find_next",
            _ => "",
        }
        .to_string();
        if e.key == "f4" && has("shift") {
            action = "find_previous".into()
        }
        if e.key == "tab" && has("shift") {
            action = "previous".into()
        }
        if has("shift") && ["left", "right", "up", "down"].contains(&action.as_str()) {
            action = format!("extend_{action}")
        }
        if has("alt") && ["left", "right"].contains(&e.key.as_str()) {
            action = format!("cell_pan_{}", e.key)
        }
        if e.key == "f5" {
            return self.request_filter(&self.status.filter);
        }
        if !action.is_empty() {
            return self.handle(&action, height);
        }
        if !e.text.is_empty()
            && !has("ctrl")
            && !has("alt")
            && self.work.edit_options.start_typing
            && self.begin_edit(&e.text)
        {
            return GridEvent {
                kind: "edit_begin".into(),
                row_id: self.row_id.clone(),
                column_id: self.column_id.clone(),
                ..Default::default()
            };
        }
        let _ = width;
        GridEvent::default()
    }
}
