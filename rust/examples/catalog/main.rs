#[path = "../playground/snapshot.rs"]
mod snapshot;
use crossterm::{
    cursor::Show,
    event::{
        self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind, KeyModifiers,
        MouseButton, MouseEventKind,
    },
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use ratatui::{
    Terminal,
    backend::{CrosstermBackend, TestBackend},
    layout::Rect,
    widgets::Paragraph,
};
use std::{
    error::Error,
    io::{self, IsTerminal},
    time::Duration,
};
use tuivory::collections::{ListItem, SearchPicker};
use tuivory::feedback::{DataState, Notice, NoticeAction, NoticeEvent, NoticeQueue, Progress};
use tuivory::grid::{Grid, GridColumn, GridRecord, GridSource};
use tuivory::{
    ColorProfile, Theme,
    forms::{Form, FormEvent, FormField, FormOption},
    interaction::ControlState,
    ratatui::{FormWidget, RowsWidget, Styles},
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
        name, notes, read, agree, radio, select, submit, cancel,
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
            LeaveAlternateScreen,
            Show
        );
    }
}
fn main() -> Result<(), Box<dyn Error>> {
    let mut en = false;
    let mut ascii = false;
    let mut theme = Theme::Dark;
    let mut colors = ColorProfile::Indexed256;
    let mut output = None;
    let mut mode = "forms".to_owned();
    let mut args = std::env::args().skip(1);
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
            "--mode" => {
                mode = args.next().ok_or("missing mode")?;
                if !["forms", "collections", "grid", "feedback"].contains(&mode.as_str()) {
                    return Err("unknown mode".into());
                }
            }
            _ => return Err(format!("unknown option {arg}").into()),
        }
    }
    let styles = Styles::new(theme, colors)?;
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
        Box::new(DemoRows { count: 100000, en }),
    )?;
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
    let draw = |f: &mut ratatui::Frame<'_>,
                form: &Form,
                picker: &SearchPicker,
                grid: &Grid,
                queue: &NoticeQueue,
                progress: &Progress,
                now: u64,
                status: &str,
                body: &mut Rect| {
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
        f.render_widget(panel, area);
        if mode == "feedback" {
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
                    styles: &styles,
                    focused: true,
                },
                *body,
            );
        } else if mode == "grid" {
            let rows = grid.layout(body.width.into(), body.height.into());
            f.render_widget(
                RowsWidget {
                    rows: &rows,
                    styles: &styles,
                    focused: true,
                },
                *body,
            );
        } else if mode == "collections" {
            let rows = picker.layout(body.width.into(), body.height.into(), ascii);
            f.render_widget(
                RowsWidget {
                    rows: &rows,
                    styles: &styles,
                    focused: true,
                },
                *body,
            );
        } else {
            f.render_widget(
                FormWidget {
                    form,
                    styles: &styles,
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
                f, &form, &picker, &grid, &queue, &progress, now, &status, &mut body,
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
    execute!(io::stdout(), EnterAlternateScreen, EnableMouseCapture)?;
    let mut terminal = Terminal::new(CrosstermBackend::new(io::stdout()))?;
    loop {
        terminal.draw(|f| {
            draw(
                f, &form, &picker, &grid, &queue, &progress, now, &status, &mut body,
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
                if mode == "feedback" {
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
                    let action = match k.code {
                        KeyCode::Left => "left",
                        KeyCode::Right => "right",
                        KeyCode::Up => "up",
                        KeyCode::Down => "down",
                        KeyCode::Home => "first",
                        KeyCode::End => "last",
                        KeyCode::PageUp => "page_up",
                        KeyCode::PageDown => "page_down",
                        KeyCode::Enter => "activate",
                        KeyCode::F(6) => "row_mode",
                        KeyCode::F(7) => "widen",
                        KeyCode::F(8) => "narrow",
                        KeyCode::F(9) => "sort",
                        KeyCode::Char(' ') => "select",
                        KeyCode::Char('c') if k.modifiers.contains(KeyModifiers::CONTROL) => "copy",
                        _ => "",
                    };
                    let e = if k.code == KeyCode::F(5) {
                        grid.request_filter("sample")
                    } else {
                        grid.handle(action, body.height.into())
                    };
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
            Event::Mouse(m)
                if m.kind == MouseEventKind::Down(MouseButton::Left)
                    && body.contains((m.column, m.row).into()) =>
            {
                let rows = if mode == "feedback" {
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
                    if mode == "feedback" {
                        if queue.visible(now).iter().any(|n| n.id == row.id) {
                            queue.focused = row.id.clone();
                        }
                        FormEvent::default()
                    } else if mode == "grid" {
                        let e = grid.click(
                            &row.id,
                            &row.value,
                            usize::from(m.column - body.x),
                            body.width.into(),
                            body.height.into(),
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
            status = format!("{}: {}", event.kind, event.id);
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
