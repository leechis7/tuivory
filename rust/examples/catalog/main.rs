mod grid_demo;
#[path = "../playground/snapshot.rs"]
mod snapshot;
use std::{
    error::Error,
    io::{self, IsTerminal},
    time::Duration,
};
use tuivory::collections::{ListItem, SearchPicker};
use tuivory::dialog::{Dialog, DialogButton, DialogEvent, DialogLayout};
use tuivory::feedback::{DataState, Notice, NoticeAction, NoticeEvent, NoticeQueue, Progress};
use tuivory::grid::{Grid, GridColumn, GridRecord, GridSource};
use tuivory::ratatui::DialogWidget;
use tuivory::ui::terminal::{
    cursor::Show,
    event::{
        self, DisableBracketedPaste, DisableMouseCapture, EnableBracketedPaste, EnableMouseCapture,
        Event, KeyCode, KeyEventKind, KeyModifiers, MouseButton, MouseEventKind,
    },
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use tuivory::ui::{
    Terminal,
    backend::{CrosstermBackend, TestBackend},
    layout::Rect,
    widgets::Paragraph,
};
use tuivory::{
    ColorProfile, Theme,
    forms::{Form, FormEvent, FormField, FormOption},
    interaction::ControlState,
    ui::components::{FormWidget, RowsWidget, Styles},
};
fn text(en: bool, ko: &str, english: &str) -> String {
    if en { english } else { ko }.into()
}
fn demo(en: bool) -> Form {
    let option = |id: &str, ko: &str, english: &str, disabled: bool| FormOption {
        id: id.into(),
        label: text(en, ko, english),
        disabled,
    };
    let options = vec![
        option("fast", "빠르게", "Fast", false),
        option("old", "사용 불가", "Unavailable", true),
        option("safe", "안전하게", "Safe", false),
    ];
    let field = |id: &str, kind: &str, ko: &str, english: &str| FormField {
        id: id.into(),
        kind: kind.into(),
        label: text(en, ko, english),
        ..Default::default()
    };
    let mut name = field("name", "text", "이름", "Name");
    name.required = true;
    name.help = text(en, "필수 입력", "Required");
    let mut notes = field("notes", "textarea", "메모", "Notes");
    notes.value = text(en, "합성 데이터", "Synthetic data");
    let mut read = field("read", "text", "읽기 전용", "Read-only");
    read.value = "Tuivory".into();
    read.state = ControlState {
        read_only: true,
        ..Default::default()
    };
    let mut locked = field("locked", "text", "비활성 입력", "Disabled input");
    locked.value = "Tuivory".into();
    locked.state.disabled = true;
    let mut save = field("save", "button", "저장 불가", "Save unavailable");
    save.state.disabled = true;
    let mut agree = field("agree", "checkbox", "동의", "Agree");
    agree.required = true;
    let mut radio = field("radio", "radio", "방식", "Method");
    radio.options = options.clone();
    radio.choice = "fast".into();
    let mut select = field("select", "select", "선택", "Choice");
    select.options = options;
    select.choice = "fast".into();
    let mut submit = field("submit", "button", "제출", "Submit");
    submit.action = "submit".into();
    let mut cancel = field("cancel", "button", "취소", "Cancel");
    cancel.action = "cancel".into();
    Form::new(vec![
        name, notes, read, locked, save, agree, radio, select, submit, cancel,
    ])
    .unwrap()
}
fn key(form: &mut Form, code: KeyCode) -> FormEvent {
    let (action, value) = match code {
        KeyCode::Tab => ("next", String::new()),
        KeyCode::BackTab => ("previous", String::new()),
        KeyCode::Enter => ("activate", String::new()),
        KeyCode::Esc => ("cancel", String::new()),
        KeyCode::Left => ("left", String::new()),
        KeyCode::Right => ("right", String::new()),
        KeyCode::Up => ("up", String::new()),
        KeyCode::Down => ("down", String::new()),
        KeyCode::Home => ("home", String::new()),
        KeyCode::End => ("end", String::new()),
        KeyCode::Backspace => ("backspace", String::new()),
        KeyCode::Delete => ("delete", String::new()),
        KeyCode::Char(c) => {
            let kind = form
                .fields()
                .iter()
                .find(|f| f.id == form.focused())
                .map(|f| f.kind.as_str())
                .unwrap_or("");
            (
                if c == ' ' && kind != "text" && kind != "textarea" {
                    "toggle"
                } else {
                    "insert"
                },
                c.to_string(),
            )
        }
        _ => ("", String::new()),
    };
    form.handle(action, &value)
}
fn feedback_rows(
    queue: &NoticeQueue,
    progress: &Progress,
    w: usize,
    h: usize,
    now: u64,
    en: bool,
) -> Vec<tuivory::forms::ComponentLine> {
    if h == 0 {
        return vec![];
    }
    let mut rows = queue.layout(w, h.saturating_sub(4).max(1), now);
    if rows.is_empty() {
        rows = DataState {
            kind: "empty".into(),
            text: text(en, "알림 없음", "No pending notices"),
            ..Default::default()
        }
        .layout(w)
    }
    rows.push(tuivory::forms::ComponentLine {
        role: "hint".into(),
        ..Default::default()
    });
    rows.extend(progress.layout(w, now));
    rows
}
struct DemoRows {
    count: usize,
    en: bool,
}
impl GridSource for DemoRows {
    fn len(&self) -> usize {
        self.count
    }
    fn index_of(&self, id: &str) -> Option<usize> {
        let n = id.strip_prefix("row-")?.parse::<usize>().ok()?;
        (n < self.count).then_some(n)
    }
    fn row(&self, n: usize) -> GridRecord {
        if n >= self.count {
            return GridRecord::default();
        }
        GridRecord {
            id: format!("row-{n}"),
            cells: [
                (
                    "name".into(),
                    format!("{} {n}", text(self.en, "합성 항목", "Synthetic")),
                ),
                ("value".into(), (n * 10).to_string()),
                ("state".into(), "ready".into()),
            ]
            .into(),
            state: ControlState {
                disabled: n == 1,
                edited: n == 3,
                ..Default::default()
            },
        }
    }
}
struct Session;
impl Drop for Session {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let _ = execute!(
            io::stdout(),
            DisableMouseCapture,
            DisableBracketedPaste,
            LeaveAlternateScreen,
            Show
        );
    }
}
pub fn run(arguments: Vec<String>) -> Result<(), Box<dyn Error>> {
    let mut en = false;
    let mut ascii = false;
    let mut theme = Theme::Dark;
    let mut colors = ColorProfile::Indexed256;
    let mut output = None;
    let mut mode = "forms".to_owned();
    let mut grid_preset = "simple".to_string();
    let mut grid_sample = false;
    let mut edit_preview = false;
    let mut density = tuivory::layout::Density::Auto;
    let mut args = arguments.into_iter();
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--lang" => {
                en = match args.next().as_deref() {
                    Some("en") => true,
                    Some("ko") => false,
                    _ => return Err("invalid language".into()),
                }
            }
            "--ascii" => ascii = true,
            "--theme" => theme = args.next().ok_or("missing theme")?.parse()?,
            "--colors" => colors = args.next().ok_or("missing colors")?.parse()?,
            "--snapshot" => output = Some(args.next().ok_or("missing output")?),
            "--grid-preset" => grid_preset = args.next().ok_or("missing grid preset")?,
            "--grid-sample" => grid_sample = true,
            "--grid-edit-preview" => edit_preview = true,
            "--density" => density = args.next().ok_or("missing density")?.parse()?,
            "--mode" => {
                mode = args.next().ok_or("missing mode")?;
                if ![
                    "forms",
                    "collections",
                    "grid",
                    "feedback",
                    "layout",
                    "dialog",
                ]
                .contains(&mode.as_str())
                {
                    return Err("unknown mode".into());
                }
            }
            _ => return Err(format!("unknown option {arg}").into()),
        }
    }
    let mut styles = Styles::new(theme, colors)?;
    let mut layout_demo = LayoutDemo {
        density,
        removed: false,
        help_open: false,
    };
    let changes = grid_demo::Changes::default();
    let mut saved_view = None;
    let mut last_grid_click = None;
    let mut grid = Grid::new(
        vec![
            GridColumn {
                id: "name".into(),
                label: text(en, "이름", "Name"),
                width: 28,
                editable: true,
            },
            GridColumn {
                id: "value".into(),
                label: text(en, "값", "Value"),
                width: 16,
                editable: true,
            },
            GridColumn {
                id: "state".into(),
                label: text(en, "상태", "State"),
                width: 16,
                editable: false,
            },
        ],
        Box::new(grid_demo::EditableRows {
            base: Box::new(DemoRows { count: 100000, en }),
            changes: changes.clone(),
        }),
    )?;
    if grid_sample {
        grid = grid_demo::sample(en, changes.clone());
    }
    let mut grid_options = tuivory::grid::grid_preset(&grid_preset)?;
    grid_options.ascii = ascii;
    grid_options = match density {
        tuivory::layout::Density::Compact => grid_options.with_density("compact")?,
        tuivory::layout::Density::Comfortable => grid_options.with_density("comfortable")?,
        _ => grid_options,
    };
    grid.set_options(grid_options)?;
    grid_demo::configure(&mut grid, en, changes.clone());
    if edit_preview {
        grid.begin_edit("");
        grid.edit_input("select_all", "");
        grid.edit_input("insert", if en { "Updated value" } else { "수정한 값" });
    }
    grid.empty = text(en, "결과 없음", "No results");
    let mut queue = NoticeQueue::new(8)?;
    queue.push(Notice {
        id: "saved".into(),
        text: text(en, "임시 알림", "Transient notice"),
        severity: "success".into(),
        expires_at: 5,
        ..Default::default()
    })?;
    queue.push(Notice {
        id: "error".into(),
        text: text(en, "연결 실패", "Connection failed"),
        detail: text(en, "재시도가 필요합니다", "Retry is available"),
        severity: "error".into(),
        expires_at: 1,
        actions: vec![NoticeAction {
            id: "retry".into(),
            label: text(en, "재시도", "Retry"),
            disabled: false,
        }],
        ..Default::default()
    })?;
    let mut progress = Progress {
        id: "load".into(),
        label: text(en, "합성 작업", "Synthetic operation"),
        status: "loading".into(),
        current: 50,
        total: 100,
        cancellable: true,
        cancel_label: text(en, "c 취소 요청", "c request cancellation"),
        ..Default::default()
    };
    let mut now = 0;
    let mut form = demo(en);
    let mut picker = SearchPicker::new(vec![
        ListItem {
            id: "group".into(),
            label: text(en, "언어", "Languages"),
            separator: true,
            ..Default::default()
        },
        ListItem {
            id: "go".into(),
            label: "Go".into(),
            secondary: text(en, "공통 공개 모듈", "Shared public module"),
            icon: "◆".into(),
            ascii_icon: "*".into(),
            shortcut: "G".into(),
            ..Default::default()
        },
        ListItem {
            id: "old".into(),
            label: text(en, "비활성 항목", "Disabled item"),
            disabled: true,
            ..Default::default()
        },
        ListItem {
            id: "rust".into(),
            label: "Rust".into(),
            secondary: text(en, "공통 공개 crate", "Shared public crate"),
            icon: "◆".into(),
            ascii_icon: "*".into(),
            shortcut: "R".into(),
            ..Default::default()
        },
    ])?;
    picker.list.empty = text(en, "결과 없음", "No results");
    picker.handle("open", "", 1);
    let mut status = text(
        en,
        "Tab 이동 / Enter 확정 / Esc 취소 / Ctrl+Q 종료",
        "Tab move / Enter confirm / Esc cancel / Ctrl+Q quit",
    );
    let mut body = Rect::default();
    let mut dialog = Dialog::new(
        text(en, "다시 연결", "Reconnect"),
        text(
            en,
            "변경 사항을 처리하세요.",
            "Choose what to do with your changes.",
        ),
        [
            ("commit", "커밋 후 접속", "Commit and connect"),
            ("rollback", "롤백 후 접속", "Roll back and connect"),
            ("cancel", "취소", "Cancel"),
        ]
        .into_iter()
        .map(|(id, ko, english)| DialogButton {
            id: id.into(),
            label: text(en, ko, english),
            disabled: false,
        })
        .collect(),
        "cancel",
    )?;
    let mut dialog_layout = DialogLayout::default();
    let dialog_event = |event: Option<DialogEvent>| match event {
        Some(DialogEvent::Activate(id)) => FormEvent {
            kind: "activate".into(),
            id,
            ..Default::default()
        },
        Some(DialogEvent::Cancel(id)) => FormEvent {
            kind: "cancel".into(),
            id,
            ..Default::default()
        },
        Some(DialogEvent::Focus(id)) => FormEvent {
            kind: "focus".into(),
            id,
            ..Default::default()
        },
        None => FormEvent::default(),
    };
    let draw = |f: &mut tuivory::ui::Frame<'_>,
                form: &Form,
                picker: &SearchPicker,
                grid: &Grid,
                layout_demo: &LayoutDemo,
                styles: &Styles,
                queue: &NoticeQueue,
                progress: &Progress,
                now: u64,
                status: &str,
                body: &mut Rect,
                dialog: &Dialog,
                dialog_layout: &mut DialogLayout| {
        let r = f.area();
        f.render_widget(Paragraph::new("").style(styles.role("surface").unwrap()), r);
        f.render_widget(
            Paragraph::new(format!(
                "TUIVORY Catalog / {}",
                text(en, "이름 · 공통 컴포넌트", "Name / shared components")
            )),
            Rect::new(r.x, r.y, r.width, u16::from(r.height > 0)),
        );
        let title = mode.clone();
        let panel = styles.panel(&title, true, 1, ascii).unwrap();
        let area = Rect::new(r.x, r.y + 1, r.width, r.height.saturating_sub(2));
        *body = panel.inner(area);
        if mode != "dialog" {
            f.render_widget(panel, area);
        }
        if mode == "dialog" {
            let width = area.width.min(56);
            let height = area.height.min(12);
            let card = Rect::new(
                area.x + (area.width - width) / 2,
                area.y + (area.height - height) / 2,
                width,
                height,
            );
            *dialog_layout = DialogWidget {
                dialog,
                styles,
                focused: true,
                ascii,
            }
            .draw(card, f.buffer_mut());
        } else if mode == "layout" {
            let rows = layout_demo.rows(body.width.into(), body.height.into(), en);
            f.render_widget(
                RowsWidget {
                    rows: &rows,
                    styles,
                    focused: true,
                },
                *body,
            );
        } else if mode == "feedback" {
            let rows = feedback_rows(
                queue,
                progress,
                body.width.into(),
                body.height.into(),
                now,
                en,
            );
            f.render_widget(
                RowsWidget {
                    rows: &rows,
                    styles,
                    focused: true,
                },
                *body,
            );
        } else if mode == "grid" {
            tuivory::ui::components::GridWidget {
                model: grid,
                styles,
                focused: true,
            }
            .render_frame(f, *body);
        } else if mode == "collections" {
            let rows = picker.layout(body.width.into(), body.height.into(), ascii);
            f.render_widget(
                RowsWidget {
                    rows: &rows,
                    styles,
                    focused: true,
                },
                *body,
            );
        } else {
            f.render_widget(
                FormWidget {
                    form,
                    styles,
                    focused: true,
                },
                *body,
            );
        }
        if r.height > 0 {
            f.render_widget(
                Paragraph::new(status),
                Rect::new(r.x, r.bottom() - 1, r.width, 1),
            );
        }
    };
    if let Some(path) = output {
        let mut terminal = Terminal::new(TestBackend::new(120, 36))?;
        terminal.draw(|f| {
            draw(
                f,
                &form,
                &picker,
                &grid,
                &layout_demo,
                &styles,
                &queue,
                &progress,
                now,
                &status,
                &mut body,
                &dialog,
                &mut dialog_layout,
            )
        })?;
        snapshot::write(std::path::Path::new(&path), terminal.backend().buffer())?;
        return Ok(());
    }
    if !io::stdin().is_terminal() {
        return Err("terminal required".into());
    }
    enable_raw_mode()?;
    let _session = Session;
    execute!(
        io::stdout(),
        EnterAlternateScreen,
        EnableMouseCapture,
        EnableBracketedPaste
    )?;
    let mut terminal = Terminal::new(CrosstermBackend::new(io::stdout()))?;
    loop {
        terminal.draw(|f| {
            draw(
                f,
                &form,
                &picker,
                &grid,
                &layout_demo,
                &styles,
                &queue,
                &progress,
                now,
                &status,
                &mut body,
                &dialog,
                &mut dialog_layout,
            )
        })?;
        if !event::poll(Duration::from_millis(100))? {
            continue;
        }
        let event = match event::read()? {
            Event::Key(k) if matches!(k.kind, KeyEventKind::Press | KeyEventKind::Repeat) => {
                if k.code == KeyCode::Char('q') && k.modifiers.contains(KeyModifiers::CONTROL) {
                    break;
                }
                if k.code == KeyCode::F(2) || k.code == KeyCode::F(3) {
                    if k.code == KeyCode::F(2) {
                        theme = match theme {
                            Theme::Dark => Theme::Light,
                            Theme::Light => Theme::Blackwhite,
                            Theme::Blackwhite => Theme::Dark,
                        };
                    } else {
                        colors = match colors {
                            ColorProfile::Ansi8 => ColorProfile::Ansi16,
                            ColorProfile::Ansi16 => ColorProfile::Indexed256,
                            ColorProfile::Indexed256 => ColorProfile::Truecolor,
                            ColorProfile::Truecolor => ColorProfile::Ansi8,
                        };
                    }
                    styles = Styles::new(theme, colors)?;
                    continue;
                }
                if mode == "dialog" {
                    let action = match k.code {
                        KeyCode::Tab if k.modifiers.contains(KeyModifiers::SHIFT) => "previous",
                        KeyCode::BackTab | KeyCode::Left | KeyCode::Up => "previous",
                        KeyCode::Tab | KeyCode::Right | KeyCode::Down => "next",
                        KeyCode::Enter => "activate",
                        KeyCode::Esc => "cancel",
                        _ => "",
                    };
                    dialog_event(dialog.handle(action))
                } else if mode == "layout" {
                    layout_demo.key(k.code)
                } else if mode == "feedback" {
                    let event = if k.code == KeyCode::Char('c') {
                        progress.request_cancel()
                    } else if k.code == KeyCode::Char('t') {
                        now = 100;
                        queue.expire(now);
                        NoticeEvent {
                            kind: "expired".into(),
                            ..Default::default()
                        }
                    } else {
                        let action = match k.code {
                            KeyCode::Up => "previous",
                            KeyCode::Down => "next",
                            KeyCode::Enter => "activate",
                            KeyCode::Delete => "dismiss",
                            _ => "",
                        };
                        queue.handle(
                            action,
                            now,
                            usize::from(body.height).saturating_sub(4).max(1),
                        )
                    };
                    if event.kind == "dismiss" {
                        queue.dismiss(&event.id);
                    }
                    if event.kind == "cancel" {
                        progress.status = "cancelled".into();
                        progress.message = text(
                            en,
                            "앱이 취소를 처리했습니다",
                            "The host handled cancellation",
                        );
                    }
                    FormEvent {
                        kind: event.kind,
                        id: format!("{} / {}", event.id, event.action),
                        ..Default::default()
                    }
                } else if mode == "grid" {
                    let e = grid.input(
                        &tuivory::input::InputEvent::from_key(k),
                        body.width.into(),
                        body.height.into(),
                    );
                    grid_demo::respond(&mut grid, &changes, &e, en);
                    if e.kind == "view_save" {
                        saved_view = Some(grid.save_view_state())
                    }
                    if e.kind == "view_restore" {
                        if let Some(s) = saved_view.clone() {
                            grid.restore_view_state(s)?;
                        }
                    }
                    FormEvent {
                        kind: e.kind,
                        id: format!("{} / {}", e.row_id, e.column_id),
                        ..Default::default()
                    }
                } else if mode == "collections" {
                    let action = match k.code {
                        KeyCode::Up => "previous",
                        KeyCode::Down => "next",
                        KeyCode::Home => "first",
                        KeyCode::End => "last",
                        KeyCode::PageUp => "page_up",
                        KeyCode::PageDown => "page_down",
                        KeyCode::Enter => "activate",
                        KeyCode::Esc => "cancel",
                        KeyCode::Backspace => "backspace",
                        KeyCode::Char(_) => "insert",
                        _ => "",
                    };
                    let value = if let KeyCode::Char(c) = k.code {
                        c.to_string()
                    } else {
                        String::new()
                    };
                    let e = picker.handle(action, &value, body.height.into());
                    FormEvent {
                        kind: e.kind,
                        id: e.id,
                        ..Default::default()
                    }
                } else {
                    key(&mut form, k.code)
                }
            }
            Event::Paste(value) if mode == "grid" => {
                let e = grid.input(
                    &tuivory::input::InputEvent::paste(&value),
                    body.width.into(),
                    body.height.into(),
                );
                grid_demo::respond(&mut grid, &changes, &e, en);
                FormEvent {
                    kind: e.kind,
                    id: format!("{} / {}", e.row_id, e.column_id),
                    ..Default::default()
                }
            }
            Event::Mouse(m)
                if mode == "dialog" && m.kind == MouseEventKind::Down(MouseButton::Left) =>
            {
                dialog_event(dialog.click(&dialog_layout, m.column.into(), m.row.into()))
            }
            Event::Mouse(m)
                if mode == "grid"
                    && (body.contains((m.column, m.row).into()) || grid.pointer_captured()) =>
            {
                let action = match m.kind {
                    MouseEventKind::Down(MouseButton::Left) => "down",
                    MouseEventKind::Drag(MouseButton::Left) => "move",
                    MouseEventKind::Up(MouseButton::Left) => "up",
                    MouseEventKind::ScrollUp => "wheel_up",
                    MouseEventKind::ScrollDown => "wheel_down",
                    MouseEventKind::ScrollLeft => "wheel_left",
                    MouseEventKind::ScrollRight => "wheel_right",
                    _ => "",
                };
                let local_x = isize::try_from(m.column).unwrap() - isize::try_from(body.x).unwrap();
                let local_y = isize::try_from(m.row).unwrap() - isize::try_from(body.y).unwrap();
                let mut action = action;
                if action == "down" {
                    let now = std::time::Instant::now();
                    if let Some((when, x, y)) = last_grid_click {
                        if now.duration_since(when) < Duration::from_millis(400)
                            && x == local_x
                            && y == local_y
                        {
                            action = "double";
                            last_grid_click = None;
                        }
                    }
                    if action != "double" {
                        last_grid_click = Some((now, local_x, local_y));
                    }
                }
                // Header click on release allows column dragging before sorting.
                let header = local_y >= 0
                    && (local_y as usize)
                        < grid
                            .geometry(body.width.into(), body.height.into())
                            .header_rows;
                let mut e = grid.pointer(
                    action,
                    local_x,
                    local_y,
                    body.width.into(),
                    body.height.into(),
                    m.modifiers.contains(KeyModifiers::SHIFT),
                );
                if action == "up" && header {
                    e = grid.pointer(
                        "click",
                        local_x,
                        local_y,
                        body.width.into(),
                        body.height.into(),
                        false,
                    );
                }
                grid_demo::respond(&mut grid, &changes, &e, en);
                FormEvent {
                    kind: e.kind,
                    id: format!("{} / {}", e.row_id, e.column_id),
                    ..Default::default()
                }
            }
            Event::Mouse(m)
                if m.kind == MouseEventKind::Down(MouseButton::Left)
                    && body.contains((m.column, m.row).into()) =>
            {
                let rows = if mode == "layout" {
                    layout_demo.rows(body.width.into(), body.height.into(), en)
                } else if mode == "feedback" {
                    feedback_rows(
                        &queue,
                        &progress,
                        body.width.into(),
                        body.height.into(),
                        now,
                        en,
                    )
                } else if mode == "grid" {
                    grid.layout(body.width.into(), body.height.into())
                } else if mode == "collections" {
                    picker.layout(body.width.into(), body.height.into(), ascii)
                } else {
                    form.layout(body.width.into(), body.height.into())
                };
                if let Some(row) = rows.get(usize::from(m.row - body.y)) {
                    if mode == "layout" {
                        FormEvent::default()
                    } else if mode == "feedback" {
                        if queue.visible(now).iter().any(|n| n.id == row.id) {
                            queue.focused = row.id.clone();
                        }
                        FormEvent::default()
                    } else if mode == "grid" {
                        let e = grid.pointer(
                            "click",
                            isize::try_from(m.column - body.x).unwrap(),
                            isize::try_from(m.row - body.y).unwrap(),
                            body.width.into(),
                            body.height.into(),
                            false,
                        );
                        FormEvent {
                            kind: e.kind,
                            id: format!("{} / {}", e.row_id, e.column_id),
                            ..Default::default()
                        }
                    } else if mode == "collections" {
                        let e = if !picker.open {
                            picker.handle("open", "", body.height.into())
                        } else {
                            picker.click(&row.id)
                        };
                        FormEvent {
                            kind: e.kind,
                            id: e.id,
                            ..Default::default()
                        }
                    } else {
                        form.click(&row.id, &row.value)
                    }
                } else {
                    FormEvent::default()
                }
            }
            _ => FormEvent::default(),
        };
        if !event.kind.is_empty() {
            status = if mode == "dialog" {
                let action = match event.kind.as_str() {
                    "activate" => text(en, "선택 요청", "Selection requested"),
                    "cancel" => text(en, "취소 요청", "Cancel requested"),
                    _ => text(en, "버튼 이동", "Button focused"),
                };
                let label = match event.id.as_str() {
                    "commit" => text(en, "커밋 후 접속", "Commit and connect"),
                    "rollback" => text(en, "롤백 후 접속", "Roll back and connect"),
                    _ => text(en, "취소", "Cancel"),
                };
                format!("{action} · {label}")
            } else {
                format!("{}: {}", event.kind, event.id)
            };
            if event.kind == "invalid" {
                for id in event.missing {
                    form.set_feedback(
                        &id,
                        "",
                        &text(en, "입력 내용을 확인하세요", "Check this value"),
                    );
                }
            } else if event.kind == "change" {
                form.set_feedback(&event.id, "", "");
            }
        }
    }
    Ok(())
}

fn layout_help(en: bool) -> tuivory::layout::Help {
    use tuivory::layout::{Help, Shortcut};
    Help::new(vec![
        Shortcut {
            key: "Ctrl+Q".into(),
            text: text(en, "종료", "Quit"),
            priority: 100,
            disabled: false,
        },
        Shortcut {
            key: "F1/Esc".into(),
            text: text(en, "도움말 열기/복귀", "Open help / return"),
            priority: 90,
            disabled: false,
        },
        Shortcut {
            key: "x".into(),
            text: text(en, "필터 제거 요청", "Request filter removal"),
            priority: 80,
            disabled: false,
        },
        Shortcut {
            key: "d".into(),
            text: text(en, "밀도 전환", "Change density"),
            priority: 70,
            disabled: false,
        },
    ])
    .unwrap()
}
struct LayoutDemo {
    density: tuivory::layout::Density,
    removed: bool,
    help_open: bool,
}
impl LayoutDemo {
    fn rows(&self, w: usize, h: usize, en: bool) -> Vec<tuivory::forms::ComponentLine> {
        use tuivory::forms::{ComponentLine, ComponentSpan};
        use tuivory::layout::{Badge, CellRect, Chip, SpacingTokens, StackItem};
        if self.help_open {
            return layout_help(en).layout(w, h);
        }
        if w == 0 || h == 0 {
            return vec![];
        }
        let tokens = SpacingTokens::for_width(self.density, w);
        let (rects, hidden) = tuivory::layout::stack_rects(
            CellRect {
                x: 0,
                y: 0,
                width: w,
                height: h.saturating_sub(2),
            },
            &[
                StackItem {
                    id: "main".into(),
                    min: 12,
                    preferred: 40,
                    weight: 1,
                },
                StackItem {
                    id: "aside".into(),
                    min: 10,
                    preferred: 24,
                    weight: 0,
                },
            ],
            tokens,
            false,
        )
        .unwrap();
        let mut rows = vec![
            ComponentLine {
                role: "surface".into(),
                ..Default::default()
            };
            h
        ];
        let mut add = |y: usize, x: usize, width: usize, value: String, role: String| {
            if y < h && width > 0 {
                rows[y].spans.push(ComponentSpan {
                    start: x,
                    width,
                    text: value,
                    role,
                    focused: false,
                })
            }
        };
        for slot in rects {
            let r = slot.rect;
            if r.width == 0 || r.height == 0 {
                continue;
            }
            add(
                r.y,
                r.x,
                r.width,
                format!("[ {} ]", slot.id),
                "header".into(),
            );
            if slot.id == "main" {
                if r.height > 1 {
                    let line = Badge {
                        id: "count".into(),
                        label: text(en, "작업", "Tasks"),
                        count: Some(145),
                        ..Default::default()
                    }
                    .line(r.width);
                    add(r.y + 1, r.x, r.width, line.text, line.role)
                }
                if !self.removed && r.height > 2 {
                    let line = Chip {
                        id: "filter".into(),
                        label: text(en, "검토 필터", "Review filter"),
                        state: ControlState {
                            selected: true,
                            ..Default::default()
                        },
                        removable: true,
                    }
                    .line(r.width);
                    add(r.y + 2, r.x, r.width, line.text, line.role)
                }
            } else {
                for (i, line) in layout_help(en)
                    .layout(r.width, r.height.saturating_sub(1))
                    .into_iter()
                    .enumerate()
                {
                    add(r.y + 1 + i, r.x, r.width, line.text, line.role)
                }
            }
        }
        let placement = tuivory::layout::drawer_layout(
            CellRect {
                x: 0,
                y: 0,
                width: w,
                height: h,
            },
            24,
            40,
        );
        rows[h - 1] = ComponentLine {
            text: tuivory::components::cell_text(
                &format!(
                    "density={:?} gap={} padding={} hidden={} overlay={}",
                    self.density,
                    tokens.gap,
                    tokens.padding,
                    hidden.len(),
                    placement.overlay
                ),
                w,
            ),
            role: "hint".into(),
            ..Default::default()
        };
        rows
    }
    fn key(&mut self, code: KeyCode) -> FormEvent {
        use tuivory::layout::{Chip, Density};
        if code == KeyCode::F(1) {
            self.help_open = !self.help_open;
            return FormEvent::default();
        }
        if self.help_open {
            if code == KeyCode::Esc {
                self.help_open = false
            }
            return FormEvent::default();
        }
        if code == KeyCode::Char('x') {
            let event = Chip {
                id: "filter".into(),
                removable: true,
                ..Default::default()
            }
            .request_remove();
            if !event.kind.is_empty() {
                self.removed = true
            }
            return FormEvent {
                kind: event.kind,
                id: event.id,
                ..Default::default()
            };
        }
        if code == KeyCode::Char('d') {
            self.density = if self.density == Density::Compact {
                Density::Comfortable
            } else {
                Density::Compact
            };
            return FormEvent {
                kind: "density".into(),
                id: format!("{:?}", self.density),
                ..Default::default()
            };
        }
        FormEvent::default()
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    run(std::env::args().skip(1).collect())
}
