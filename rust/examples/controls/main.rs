//! Database-free host using public containers, surface, form and text widgets.
#[path = "../playground/snapshot.rs"]
mod snapshot;
use crossterm::{
    cursor::Show,
    event::{
        self, DisableBracketedPaste, DisableMouseCapture, EnableBracketedPaste, EnableMouseCapture,
        Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers, MouseButton, MouseEventKind,
    },
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use ratatui::{
    Terminal,
    backend::{CrosstermBackend, TestBackend},
    buffer::Buffer,
    layout::Rect,
    widgets::{Paragraph, Widget},
};
use std::{
    error::Error,
    io::{self, IsTerminal},
    path::Path,
};
use tuivory::{
    ColorProfile, Theme,
    containers::{ContainerOptions, ContainerState, LayoutItem, Track, compute_container},
    forms::{Form, FormField},
    layout::{CellRect, NamedRect},
    popup::{ShadowMode, ShadowOptions},
    ratatui::{ContainerWidget, FormWidget, ShadowWidget, Styles, SurfaceWidget, TextWidget},
    text::{SyntaxSpan, TextDocument},
};
fn tr(en: bool, ko: &str, english: &str) -> String {
    if en { english } else { ko }.into()
}
fn cell(r: Rect) -> CellRect {
    CellRect {
        x: r.x.into(),
        y: r.y.into(),
        width: r.width.into(),
        height: r.height.into(),
    }
}
fn rect(r: CellRect) -> Rect {
    Rect::new(r.x as u16, r.y as u16, r.width as u16, r.height as u16)
}
fn item(id: &str) -> LayoutItem {
    LayoutItem {
        id: id.into(),
        ..Default::default()
    }
}
struct App {
    en: bool,
    ascii: bool,
    opened: bool,
    theme: Theme,
    profile: ColorProfile,
    styles: Styles,
    form: Form,
    popup: Form,
    editor: TextDocument,
    viewer: TextDocument,
    focus: ContainerState,
    rects: Vec<NamedRect>,
    popup_rect: Rect,
    status: String,
}
impl App {
    fn grid_items(&self) -> Vec<LayoutItem> {
        vec![
            LayoutItem {
                row_span: 2,
                ..item("form")
            },
            LayoutItem {
                column: 1,
                ..item("editor")
            },
            LayoutItem {
                row: 1,
                column: 1,
                ..item("viewer")
            },
        ]
    }
    fn draw_main(&mut self, area: Rect, buf: &mut Buffer, styles: &Styles) {
        let options = ContainerOptions {
            kind: "column".into(),
            ..Default::default()
        };
        let items = vec![
            LayoutItem {
                track: Track {
                    fixed: 1,
                    ..Default::default()
                },
                disabled: true,
                ..item("header")
            },
            LayoutItem {
                track: Track {
                    weight: 1,
                    ..Default::default()
                },
                ..item("content")
            },
            LayoutItem {
                track: Track {
                    fixed: 2,
                    ..Default::default()
                },
                disabled: true,
                ..item("footer")
            },
        ];
        ContainerWidget {
            items: &items,
            options: &options,
            styles,
            scroll_x: 0,
            scroll_y: 0,
            render_child: |id: &str, area: Rect, buf: &mut Buffer| match id {
                "header" => Paragraph::new(tr(
                    self.en,
                    "TUIVORY 공통 컨트롤·배치",
                    "TUIVORY Controls and layout",
                ))
                .style(styles.role("header").unwrap())
                .render(area, buf),
                "footer" => Paragraph::new(format!(
                    "{}\n{}",
                    self.status,
                    tr(
                        self.en,
                        "Tab 이동 · F2 테마 · F3 색상 · F4 팝업 · Ctrl+Q 종료",
                        "Tab focus / F2 theme / F3 colors / F4 popup / Ctrl+Q quit"
                    )
                ))
                .style(styles.role("hint").unwrap())
                .render(area, buf),
                _ => {
                    let options = ContainerOptions {
                        kind: "grid".into(),
                        gap: 1,
                        rows: vec![
                            Track {
                                weight: 2,
                                ..Default::default()
                            },
                            Track {
                                weight: 1,
                                ..Default::default()
                            },
                        ],
                        columns: vec![
                            Track {
                                weight: 1,
                                ..Default::default()
                            },
                            Track {
                                weight: 2,
                                ..Default::default()
                            },
                        ],
                        ..Default::default()
                    };
                    let items = self.grid_items();
                    self.focus.reconcile(&items);
                    self.rects = compute_container(cell(area), &items, &options).unwrap();
                    ContainerWidget {
                        items: &items,
                        options: &options,
                        styles,
                        scroll_x: 0,
                        scroll_y: 0,
                        render_child: |id: &str, area: Rect, buf: &mut Buffer| {
                            let focused = !self.opened && self.focus.focused == id;
                            let title = match id {
                                "form" => tr(self.en, "독립 컨트롤·폼", "Controls and form"),
                                "editor" => tr(self.en, "편집기", "Editor"),
                                _ => tr(self.en, "읽기 전용 텍스트", "Read-only text"),
                            };
                            let block = styles.panel(&title, focused, 1, self.ascii).unwrap();
                            let inner = block.inner(area);
                            block.render(area, buf);
                            match id {
                                "form" => FormWidget {
                                    form: &self.form,
                                    styles,
                                    focused,
                                }
                                .render(inner, buf),
                                "editor" => TextWidget {
                                    model: &mut self.editor,
                                    styles,
                                    focused,
                                }
                                .render(inner, buf),
                                _ => TextWidget {
                                    model: &mut self.viewer,
                                    styles,
                                    focused,
                                }
                                .render(inner, buf),
                            }
                        },
                    }
                    .render(area, buf)
                }
            },
        }
        .render(area, buf)
    }
    fn draw(&mut self, area: Rect, buf: &mut Buffer) {
        let styles = self.styles.clone();
        let options = ContainerOptions {
            kind: "layers".into(),
            ..Default::default()
        };
        let items = vec![
            item("main"),
            LayoutItem {
                modal: true,
                hidden: !self.opened,
                centered: true,
                area: CellRect {
                    x: 0,
                    y: 0,
                    width: 48,
                    height: 10,
                },
                ..item("popup")
            },
        ];
        ContainerWidget {
            items: &items,
            options: &options,
            styles: &styles,
            scroll_x: 0,
            scroll_y: 0,
            render_child: |id: &str, area: Rect, buf: &mut Buffer| {
                if id == "main" {
                    self.draw_main(area, buf, &styles)
                } else {
                    self.popup_rect = area;
                    ShadowWidget::new(
                        SurfaceWidget::new(
                            FormWidget {
                                form: &self.popup,
                                styles: &styles,
                                focused: true,
                            },
                            &styles,
                        )
                        .padding(1),
                        &styles,
                        ShadowOptions {
                            mode: ShadowMode::Auto,
                            ..Default::default()
                        },
                    )
                    .ascii(self.ascii)
                    .render(area, buf)
                }
            },
        }
        .render(area, buf)
    }
    fn action(&mut self, action: &str, text: &str) {
        self.status = if self.opened {
            self.popup.handle(action, text).kind
        } else {
            match self.focus.focused.as_str() {
                "form" => self.form.handle(action, text).kind,
                "editor" => {
                    self.editor
                        .handle(
                            if action == "activate" {
                                "newline"
                            } else {
                                action
                            },
                            text,
                        )
                        .kind
                }
                _ => self.viewer.handle(action, text).kind,
            }
        };
    }
    fn key(&mut self, key: KeyEvent) -> bool {
        if key.code == KeyCode::Char('q') && key.modifiers.contains(KeyModifiers::CONTROL) {
            return false;
        }
        match key.code {
            KeyCode::F(2) => {
                self.theme = match self.theme {
                    Theme::Dark => Theme::Light,
                    Theme::Light => Theme::Blackwhite,
                    Theme::Blackwhite => Theme::Dark,
                };
                self.styles = Styles::new(self.theme, self.profile).unwrap();
                return true;
            }
            KeyCode::F(3) => {
                self.profile = match self.profile {
                    ColorProfile::Ansi8 => ColorProfile::Ansi16,
                    ColorProfile::Ansi16 => ColorProfile::Indexed256,
                    ColorProfile::Indexed256 => ColorProfile::Truecolor,
                    ColorProfile::Truecolor => ColorProfile::Ansi8,
                };
                self.styles = Styles::new(self.theme, self.profile).unwrap();
                return true;
            }
            KeyCode::F(4) => {
                self.opened = !self.opened;
                return true;
            }
            KeyCode::Esc if self.opened => {
                self.opened = false;
                return true;
            }
            KeyCode::Tab | KeyCode::BackTab => {
                let previous = key.code == KeyCode::BackTab;
                if !self.opened
                    && (self.focus.focused != "form" || self.form.at_tab_boundary(previous))
                {
                    self.focus.move_focus(&self.grid_items(), previous);
                } else {
                    self.action(if previous { "previous" } else { "next" }, "")
                }
                return true;
            }
            _ => (),
        }
        let mut text = String::new();
        let action = if key.modifiers.contains(KeyModifiers::CONTROL) {
            match key.code {
                KeyCode::Char('a') => "select_all",
                KeyCode::Char('c') => "copy",
                KeyCode::Char('x') => "cut",
                KeyCode::Char('z') => "undo",
                KeyCode::Char('y') => "redo",
                _ => "",
            }
        } else {
            match key.code {
                KeyCode::Left => "left",
                KeyCode::Right => "right",
                KeyCode::Up => "up",
                KeyCode::Down => "down",
                KeyCode::Home => "home",
                KeyCode::End => "end",
                KeyCode::Backspace => "backspace",
                KeyCode::Delete => "delete",
                KeyCode::Enter => "activate",
                KeyCode::PageUp => "page_up",
                KeyCode::PageDown => "page_down",
                KeyCode::Char(c) => {
                    text = c.to_string();
                    "insert"
                }
                _ => "",
            }
        };
        let mut action = action.to_string();
        if key.modifiers.contains(KeyModifiers::SHIFT)
            && ["left", "right", "up", "down", "home", "end"].contains(&action.as_str())
        {
            action = "select_".to_string() + &action
        }
        if key.modifiers.contains(KeyModifiers::ALT) {
            if action == "left" {
                action = "scroll_left".into()
            }
            if action == "right" {
                action = "scroll_right".into()
            }
        }
        self.action(&action, &text);
        true
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
fn main() -> Result<(), Box<dyn Error>> {
    let (mut en, mut ascii, mut opened) = (false, false, false);
    let mut theme = Theme::Dark;
    let mut profile = ColorProfile::Indexed256;
    let mut output = None;
    let mut args = std::env::args().skip(1);
    while let Some(a) = args.next() {
        match a.as_str() {
            "--lang" => {
                en = match args.next().as_deref() {
                    Some("en") => true,
                    Some("ko") => false,
                    _ => return Err("invalid language".into()),
                }
            }
            "--ascii" => ascii = true,
            "--open" => opened = true,
            "--theme" => theme = args.next().ok_or("theme")?.parse()?,
            "--colors" => profile = args.next().ok_or("colors")?.parse()?,
            "--snapshot" => output = Some(args.next().ok_or("snapshot")?),
            _ => return Err("unknown flag".into()),
        }
    }
    let mut editor = TextDocument::editor("fn example() {\n    print(\"Unicode 界 😀 é\");\n}\n");
    editor.buffer.select(0, 0);
    editor.syntax = vec![SyntaxSpan {
        start: 0,
        end: 2,
        role: "info".into(),
    }];
    let mut app = App {
        en,
        ascii,
        opened,
        theme,
        profile,
        styles: Styles::new(theme, profile)?,
        form: Form::new(vec![
            FormField {
                id: "name".into(),
                kind: "text".into(),
                label: tr(en, "이름", "Name"),
                value: tr(en, "예제 사용자", "Example user"),
                ..Default::default()
            },
            FormField {
                id: "password".into(),
                kind: "password".into(),
                label: tr(en, "암호", "Password"),
                value: "example-secret".into(),
                ..Default::default()
            },
            FormField {
                id: "check".into(),
                kind: "checkbox".into(),
                label: tr(en, "선택 상태 보존", "Preserve selection"),
                checked: true,
                ..Default::default()
            },
            FormField {
                id: "save".into(),
                kind: "button".into(),
                label: tr(en, "저장 요청", "Request save"),
                ..Default::default()
            },
        ])?,
        popup: Form::new(vec![
            FormField {
                id: "secret".into(),
                kind: "password".into(),
                label: tr(en, "암호 마스킹", "Secret masking"),
                value: "never-render-this".into(),
                ..Default::default()
            },
            FormField {
                id: "ok".into(),
                kind: "button".into(),
                label: tr(en, "확인 요청", "Confirm request"),
                ..Default::default()
            },
        ])?,
        editor,
        viewer: TextDocument::viewer(&tr(
            en,
            "[리터럴] 도움말과 긴 원문\n세로·가로 스크롤 / Shift+방향키 선택\n원문 복사는 앱에 요청합니다.",
            "[literal] Help and original text\nScroll vertically/horizontally; Shift+arrows select\nCopying requests a host action.",
        )),
        focus: ContainerState::default(),
        rects: vec![],
        popup_rect: Rect::default(),
        status: tr(
            en,
            "명령은 요청만 전달합니다.",
            "Actions emit requests only.",
        ),
    };
    if let Some(output) = output {
        let mut t = Terminal::new(TestBackend::new(120, 32))?;
        t.draw(|f| {
            let area = f.area();
            app.draw(area, f.buffer_mut())
        })?;
        snapshot::write(Path::new(&output), t.backend().buffer())?;
        return Ok(());
    }
    if !io::stdin().is_terminal() {
        return Err("interactive terminal required".into());
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
            let area = f.area();
            app.draw(area, f.buffer_mut())
        })?;
        match event::read()? {
            Event::Key(k) if matches!(k.kind, KeyEventKind::Press | KeyEventKind::Repeat) => {
                if !app.key(k) {
                    break;
                }
            }
            Event::Paste(text) => app.action("paste", &text),
            Event::Mouse(m) => {
                let (x, y) = (m.column as usize, m.row as usize);
                if app.opened {
                    if m.kind == MouseEventKind::Down(MouseButton::Left)
                        && !app.popup_rect.contains((m.column, m.row).into())
                    {
                        app.opened = false
                    }
                    continue;
                }
                let press = m.kind == MouseEventKind::Down(MouseButton::Left);
                let release = m.kind == MouseEventKind::Up(MouseButton::Left);
                let previous = app.focus.captured.clone();
                let items = app.grid_items();
                let id = app.focus.pointer(&items, &app.rects, x, y, press, release);
                if let Some(id) = id {
                    if let Some(r) = app.rects.iter().find(|r| r.id == id) {
                        let inner = rect(r.rect).inner(ratatui::layout::Margin::new(2, 2));
                        match m.kind {
                            MouseEventKind::ScrollUp => app.action("scroll_up", ""),
                            MouseEventKind::ScrollDown => app.action("scroll_down", ""),
                            _ if press || release || !previous.is_empty() => {
                                if id == "form" {
                                    let rows =
                                        app.form.layout(inner.width.into(), inner.height.into());
                                    if let Some(row) = rows.get(y.saturating_sub(inner.y as usize))
                                    {
                                        if press {
                                            app.form.click(&row.id, &row.value);
                                        }
                                    }
                                } else {
                                    let d = if id == "editor" {
                                        &mut app.editor
                                    } else {
                                        &mut app.viewer
                                    };
                                    d.point(
                                        x as isize - inner.x as isize,
                                        y as isize - inner.y as isize,
                                        inner.width.into(),
                                        inner.height.into(),
                                        !press,
                                    )
                                }
                            }
                            _ => (),
                        }
                    }
                }
            }
            _ => (),
        }
    }
    Ok(())
}
