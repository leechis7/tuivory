//! Host-owned composition/global keys around the public menu components.
#[path = "../playground/snapshot.rs"]
mod snapshot;
use crossterm::{
    cursor::Show,
    event::{
        self, DisableBracketedPaste, DisableMouseCapture, EnableBracketedPaste, EnableMouseCapture,
        Event, KeyCode, KeyEventKind, KeyModifiers, MouseButton, MouseEventKind,
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
};
use tuivory::{
    ColorProfile, Theme,
    forms::{Form, FormField},
    layout::CellRect,
    menu::{Menu, MenuEvent, MenuItem, menu_placement},
    ratatui::{FormWidget, MenuBarWidget, MenuPopupWidget, Styles},
};
fn tr(en: bool, ko: &str, english: &str) -> String {
    if en { english } else { ko }.into()
}
fn items(en: bool) -> Vec<MenuItem> {
    let i = |id: &str, parent: &str, ko: &str, en_text: &str, key: &str, shortcut: &str| MenuItem {
        id: id.into(),
        parent: parent.into(),
        label: tr(en, ko, en_text),
        mnemonic: key.into(),
        shortcut: shortcut.into(),
        ..Default::default()
    };
    let mut out = vec![
        i("file", "", "파일", "File", "f", ""),
        i("new", "file", "새 문서", "New document", "n", "Ctrl+N"),
        i("save", "file", "저장 요청", "Save request", "s", "Ctrl+S"),
        MenuItem {
            id: "sep".into(),
            parent: "file".into(),
            separator: true,
            ..Default::default()
        },
        i("recent", "file", "최근 예제", "Recent examples", "r", ""),
        i(
            "alpha",
            "recent",
            "한글 예제와 긴 이름",
            "A long example name",
            "a",
            "",
        ),
        i("more", "recent", "다른 예제", "More examples", "m", ""),
        i(
            "beta",
            "more",
            "Unicode 界 😀 é",
            "Unicode 界 😀 é",
            "b",
            "",
        ),
        i("edit", "", "편집", "Edit", "e", ""),
        i(
            "clipboard",
            "edit",
            "클립보드 요청",
            "Clipboard requests",
            "c",
            "",
        ),
        i(
            "copy",
            "clipboard",
            "복사 요청",
            "Copy request",
            "c",
            "Ctrl+C",
        ),
        i(
            "paste",
            "clipboard",
            "붙여넣기 요청",
            "Paste request",
            "p",
            "Ctrl+V",
        ),
        i("view", "", "보기", "View", "v", ""),
        i("detail", "view", "상세 요청", "Detail request", "d", ""),
    ];
    out[1].icon = "◇".into();
    out[1].ascii_icon = "*".into();
    out[2].disabled = true;
    out[5].secondary = "[red] literal".into();
    out
}
struct App {
    en: bool,
    ascii: bool,
    theme: Theme,
    profile: ColorProfile,
    styles: Styles,
    menu: Menu,
    form: Form,
    origin: String,
    status: String,
    popup: Rect,
    inner: Rect,
    editor: Rect,
    preview: Rect,
}
impl App {
    fn emit(&mut self, event: Option<MenuEvent>) {
        let Some(mut e) = event else { return };
        if e.kind == "open_request" {
            let origin = if self.menu.opened() {
                self.menu.return_id().to_string()
            } else {
                self.origin.clone()
            };
            let Some(open) = self.menu.open(&e.id, &origin) else {
                return;
            };
            e = open;
        }
        if !self.menu.opened() && !e.return_id.is_empty() {
            self.origin = e.return_id.clone();
        }
        self.status = format!("{}: {} / origin={}", e.kind, e.id, e.return_id);
    }
    fn draw(&mut self, f: &mut ratatui::Frame<'_>) {
        let a = f.area();
        f.render_widget(
            Paragraph::new("").style(self.styles.role("surface").unwrap()),
            a,
        );
        let width = a.width;
        let height = a.height;
        f.render_widget(
            Paragraph::new(format!(
                "TUIVORY Menu / {}",
                tr(
                    self.en,
                    "컴포넌트와 앱의 명령 연결",
                    "Components and host actions"
                )
            ))
            .style(self.styles.text_on_surface("body", "surface").unwrap()),
            Rect::new(0, 0, width, u16::from(height > 0)),
        );
        if height > 1 {
            f.render_widget(
                MenuBarWidget {
                    model: &mut self.menu,
                    styles: &self.styles,
                    focused: false,
                },
                Rect::new(0, 1, width, 1),
            );
        }
        let h = height.saturating_sub(4) / 2;
        self.editor = Rect::new(0, 2, width, h);
        self.preview = Rect::new(0, 2 + h, width, height.saturating_sub(4) - h);
        let editor_title = tr(self.en, "편집 영역", "Editor");
        let block = self
            .styles
            .panel(
                &editor_title,
                self.origin == "editor" && !self.menu.opened(),
                1,
                self.ascii,
            )
            .unwrap();
        let inner = block.inner(self.editor);
        f.render_widget(block, self.editor);
        f.render_widget(
            FormWidget {
                form: &self.form,
                styles: &self.styles,
                focused: self.origin == "editor" && !self.menu.opened(),
            },
            inner,
        );
        let preview_title = tr(self.en, "미리보기", "Preview");
        let block = self
            .styles
            .panel(
                &preview_title,
                self.origin == "preview" && !self.menu.opened(),
                1,
                self.ascii,
            )
            .unwrap();
        let inner = block.inner(self.preview);
        f.render_widget(block, self.preview);
        f.render_widget(Paragraph::new(tr(self.en,"앱이 선택한 내용·명령·화면 배치\n메뉴 항목은 실제 파일·DB·클립보드를 변경하지 않습니다.","Host-owned content, commands and screen layout\nMenu items do not change files, databases or clipboard.")).style(self.styles.text_on_surface("body", "surface").unwrap()),inner);
        if height >= 2 {
            f.render_widget(
                Paragraph::new(self.status.clone())
                    .style(self.styles.text_on_surface("body", "surface").unwrap()),
                Rect::new(0, height - 2, width, 1),
            );
            f.render_widget(Paragraph::new(tr(self.en,"F10 메뉴 · Shift+F10 문맥 · Alt+F/E/V · F2 테마 F3 색상 F4 ASCII F5 사용 가능 상태 · Tab 영역 · Ctrl+Q 종료","F10 menu / Shift+F10 context / Alt+F/E/V / F2 theme F3 colors F4 ASCII F5 eligibility / Tab panel / Ctrl+Q quit")).style(self.styles.role("hint").unwrap()),Rect::new(0,height-1,width,1));
        }
        if self.menu.opened() {
            let mut anchor = CellRect {
                x: 4,
                y: 3,
                width: 1,
                height: 1,
            };
            let root = self.menu.path().first().cloned();
            if let Some(root) = root {
                for c in self.menu.bar_layout(width.into()).cells {
                    if c.id == root {
                        anchor = CellRect {
                            x: c.start,
                            y: 1,
                            width: c.width,
                            height: 1,
                        }
                    }
                }
            }
            let (w, h) = self.menu.content_size();
            let r = menu_placement(
                anchor,
                CellRect {
                    x: 0,
                    y: 0,
                    width: width.into(),
                    height: height.into(),
                },
                (w + 4).clamp(24, 52),
                h + 4,
            );
            self.popup = Rect::new(r.x as u16, r.y as u16, r.width as u16, r.height as u16);
            let mut title = self.menu.title();
            if title.is_empty() {
                title = tr(self.en, "문맥 메뉴", "Context menu")
            };
            self.inner = self
                .styles
                .panel(&title, false, 1, self.ascii)
                .unwrap()
                .inner(self.popup);
            f.render_widget(
                MenuPopupWidget {
                    model: &mut self.menu,
                    styles: &self.styles,
                    title: &title,
                    ascii: self.ascii,
                    focused: true,
                    padding: 1,
                },
                self.popup,
            );
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
fn main() -> Result<(), Box<dyn Error>> {
    let mut en = false;
    let mut ascii = false;
    let mut theme = Theme::Dark;
    let mut profile = ColorProfile::Indexed256;
    let mut output = None;
    let mut opened = false;
    let mut open_id = "file".to_string();
    let mut args = std::env::args().skip(1);
    while let Some(a) = args.next() {
        match a.as_str() {
            "--lang" => {
                en = match args.next().as_deref() {
                    Some("ko") => false,
                    Some("en") => true,
                    _ => return Err("invalid language".into()),
                }
            }
            "--ascii" => ascii = true,
            "--theme" => theme = args.next().ok_or("missing theme")?.parse()?,
            "--colors" => profile = args.next().ok_or("missing colors")?.parse()?,
            "--snapshot" => output = Some(args.next().ok_or("missing snapshot")?),
            "--open" => opened = true,
            "--menu-id" => open_id = args.next().ok_or("missing menu ID")?,
            _ => return Err(format!("unknown option {a}").into()),
        }
    }
    let mut menu = Menu::new(items(en))?;
    menu.back_label = tr(en, "뒤로", "Back");
    menu.empty_label = tr(en, "항목 없음", "No items");
    let mut app = App {
        en,
        ascii,
        theme,
        profile,
        styles: Styles::new(theme, profile)?,
        menu,
        form: Form::new(vec![FormField {
            id: "value".into(),
            kind: "text".into(),
            label: tr(en, "값", "Value"),
            value: tr(en, "합성 문서", "Synthetic draft"),
            ..Default::default()
        }])?,
        origin: "editor".into(),
        status: tr(
            en,
            "명령 요청만 반환하며 실제 동작은 앱이 결정합니다.",
            "Menus emit requests; the host decides actual actions.",
        ),
        popup: Rect::default(),
        inner: Rect::default(),
        editor: Rect::default(),
        preview: Rect::default(),
    };
    if opened {
        let e = app
            .menu
            .open(&open_id, "editor")
            .ok_or("invalid --menu-id")?;
        app.emit(Some(e));
    }
    if let Some(path) = output {
        let mut terminal = Terminal::new(TestBackend::new(120, 32))?;
        terminal.draw(|f| app.draw(f))?;
        snapshot::write(std::path::Path::new(&path), terminal.backend().buffer())?;
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
        terminal.draw(|f| app.draw(f))?;
        match event::read()? {
            Event::Key(k) if matches!(k.kind, KeyEventKind::Press | KeyEventKind::Repeat) => {
                if k.code == KeyCode::Char('q') && k.modifiers.contains(KeyModifiers::CONTROL) {
                    break;
                }
                match k.code {
                    KeyCode::F(2) => {
                        app.theme = match app.theme {
                            Theme::Dark => Theme::Light,
                            Theme::Light => Theme::Blackwhite,
                            Theme::Blackwhite => Theme::Dark,
                        };
                        app.styles = Styles::new(app.theme, app.profile)?;
                        continue;
                    }
                    KeyCode::F(3) => {
                        app.profile = match app.profile {
                            ColorProfile::Ansi8 => ColorProfile::Ansi16,
                            ColorProfile::Ansi16 => ColorProfile::Indexed256,
                            ColorProfile::Indexed256 => ColorProfile::Truecolor,
                            ColorProfile::Truecolor => ColorProfile::Ansi8,
                        };
                        app.styles = Styles::new(app.theme, app.profile)?;
                        continue;
                    }
                    KeyCode::F(4) => {
                        app.ascii = !app.ascii;
                        continue;
                    }
                    KeyCode::F(5) => {
                        let mut items = app.menu.items().to_vec();
                        items[2].disabled = !items[2].disabled;
                        let e = app.menu.set_items(items)?;
                        app.emit(e);
                        continue;
                    }
                    KeyCode::F(10) => {
                        let e = if app.menu.opened() {
                            if k.modifiers.contains(KeyModifiers::SHIFT) {
                                {
                                    let caller = app.menu.return_id().to_owned();
                                    app.menu.open("", &caller)
                                }
                            } else {
                                app.menu.close()
                            }
                        } else {
                            let id = if k.modifiers.contains(KeyModifiers::SHIFT) {
                                String::new()
                            } else {
                                app.menu.bar_focused_id().to_string()
                            };
                            app.menu.open(&id, &app.origin)
                        };
                        app.emit(e);
                        continue;
                    }
                    _ => (),
                }
                if let KeyCode::Char(c) = k.code {
                    if k.modifiers.contains(KeyModifiers::ALT) {
                        let e = app.menu.handle_bar("mnemonic", &c.to_string());
                        app.emit(e);
                        continue;
                    }
                }
                if app.menu.opened() {
                    let (a, v) = match k.code {
                        KeyCode::Up => ("previous", String::new()),
                        KeyCode::Down => ("next", String::new()),
                        KeyCode::Left => ("left", String::new()),
                        KeyCode::Right => ("right", String::new()),
                        KeyCode::Home => ("first", String::new()),
                        KeyCode::End => ("last", String::new()),
                        KeyCode::PageUp => ("page_up", String::new()),
                        KeyCode::PageDown => ("page_down", String::new()),
                        KeyCode::Esc => ("cancel", String::new()),
                        KeyCode::Enter => ("activate", String::new()),
                        KeyCode::Char(c) if !k.modifiers.contains(KeyModifiers::CONTROL) => {
                            ("mnemonic", c.to_string())
                        }
                        _ => ("", String::new()),
                    };
                    let e = app.menu.handle(a, &v, app.inner.height.into());
                    app.emit(e);
                    continue;
                }
                if k.code == KeyCode::Tab {
                    app.origin = if app.origin == "editor" {
                        "preview"
                    } else {
                        "editor"
                    }
                    .into();
                    continue;
                }
                if app.origin == "editor" {
                    let (a, v) = match k.code {
                        KeyCode::Char(c) if !k.modifiers.contains(KeyModifiers::CONTROL) => {
                            ("insert", c.to_string())
                        }
                        KeyCode::Backspace => ("backspace", String::new()),
                        _ => ("", String::new()),
                    };
                    app.form.handle(a, &v);
                }
            }
            Event::Paste(text) => {
                if !app.menu.opened() && app.origin == "editor" {
                    app.form.handle("insert", &text);
                }
            }
            Event::Mouse(m) => {
                let pos = (m.column, m.row).into();
                if app.menu.opened() {
                    if m.row == 1 && m.kind == MouseEventKind::Down(MouseButton::Left) {
                        let mut e = app
                            .menu
                            .bar_click(m.column.into(), terminal.size()?.width.into());
                        if let Some(ev) = &e {
                            if ev.kind == "focus" {
                                {
                                    let caller = app.menu.return_id().to_owned();
                                    e = app.menu.open(&ev.id, &caller);
                                }
                            }
                        }
                        app.emit(e);
                    } else if app.inner.contains(pos) {
                        let rows = app.menu.layout(
                            app.inner.width.into(),
                            app.inner.height.into(),
                            app.ascii,
                        );
                        let id = rows
                            .get(usize::from(m.row - app.inner.y))
                            .map(|r| r.id.clone())
                            .unwrap_or_default();
                        let e = match m.kind {
                            MouseEventKind::Down(MouseButton::Left) => app.menu.click(&id),
                            MouseEventKind::Moved => {
                                app.menu.focus(&id);
                                None
                            }
                            MouseEventKind::ScrollUp => {
                                app.menu.handle("previous", "", app.inner.height.into())
                            }
                            MouseEventKind::ScrollDown => {
                                app.menu.handle("next", "", app.inner.height.into())
                            }
                            _ => None,
                        };
                        app.emit(e);
                    } else if !app.popup.contains(pos)
                        && m.kind == MouseEventKind::Down(MouseButton::Left)
                    {
                        let e = app.menu.close();
                        app.emit(e);
                    }
                } else if m.row == 1 && m.kind == MouseEventKind::Down(MouseButton::Left) {
                    let e = app
                        .menu
                        .bar_click(m.column.into(), terminal.size()?.width.into());
                    app.emit(e);
                } else if m.kind == MouseEventKind::Down(MouseButton::Left) {
                    if app.editor.contains(pos) {
                        app.origin = "editor".into()
                    } else if app.preview.contains(pos) {
                        app.origin = "preview".into()
                    }
                }
            }
            _ => (),
        }
    }
    Ok(())
}
