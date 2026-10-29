//! Host connecting public modal scopes and shared control-state styles.
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
    Frame, Terminal,
    backend::{CrosstermBackend, TestBackend},
    layout::Rect,
    widgets::{Clear, Paragraph},
};
use std::{
    error::Error,
    io::{self, IsTerminal},
    time::Duration,
};
use tuivory::{
    ColorProfile, Theme,
    interaction::{ControlState, FocusStack, FocusTarget},
    ratatui::Styles,
};
fn targets(level: usize) -> Vec<FocusTarget> {
    let item = |id: &str, state: ControlState| FocusTarget {
        id: id.into(),
        state,
        hidden: false,
    };
    match level {
        0 => vec![
            item("open", ControlState::default()),
            item(
                "read",
                ControlState {
                    read_only: true,
                    ..Default::default()
                },
            ),
            item(
                "busy",
                ControlState {
                    busy: true,
                    ..Default::default()
                },
            ),
            item(
                "disabled",
                ControlState {
                    disabled: true,
                    ..Default::default()
                },
            ),
            item("tail", ControlState::default()),
        ],
        1 => vec![
            item("child", ControlState::default()),
            item(
                "invalid",
                ControlState {
                    invalid: true,
                    selected: true,
                    edited: true,
                    ..Default::default()
                },
            ),
            item(
                "disabled",
                ControlState {
                    disabled: true,
                    ..Default::default()
                },
            ),
            item("close", ControlState::default()),
        ],
        _ => vec![
            item("close", ControlState::default()),
            item(
                "read",
                ControlState {
                    read_only: true,
                    ..Default::default()
                },
            ),
        ],
    }
}
fn text<'a>(en: bool, ko: &'a str, english: &'a str) -> &'a str {
    if en { english } else { ko }
}
fn label(id: &str, en: bool) -> &str {
    let (ko, english) = match id {
        "open" => ("팝업 열기", "Open popup"),
        "read" => ("읽기 전용 내용", "Read-only content"),
        "busy" => ("처리 중인 항목", "Busy control"),
        "disabled" => ("사용 불가", "Disabled"),
        "tail" => ("마지막 항목", "Last control"),
        "child" => ("중첩 팝업 열기", "Open nested popup"),
        "invalid" => ("오류 · 선택 · 변경됨", "Invalid · Selected · Edited"),
        _ => ("닫기", "Close"),
    };
    text(en, ko, english)
}
fn area(level: usize, screen: Rect) -> Rect {
    let (w, h) = (screen.width, screen.height);
    if level == 0 {
        return Rect::new(
            screen.x + 2.min(w.saturating_sub(1)),
            screen.y + 3,
            w.saturating_sub(4),
            10.min(h.saturating_sub(6)),
        );
    }
    let (width, height) = if level == 1 {
        (64.min(w.saturating_sub(4)), 10.min(h.saturating_sub(4)))
    } else {
        (48.min(w.saturating_sub(2)), 8.min(h.saturating_sub(4)))
    };
    Rect::new(
        screen.x + (w - width) / 2,
        screen.y + 2.max((h - height) / 2),
        width,
        height,
    )
}
struct App {
    en: bool,
    ascii: bool,
    theme: Theme,
    profile: ColorProfile,
    styles: Styles,
    stack: FocusStack,
    screen: Rect,
}
impl App {
    fn draw(&mut self, f: &mut Frame<'_>) {
        let screen = f.area();
        self.screen = screen;
        f.render_widget(
            Paragraph::new("").style(self.styles.role("surface").unwrap()),
            screen,
        );
        let line = |row: u16| {
            Rect::new(
                screen.x,
                screen.y + row,
                screen.width,
                u16::from(row < screen.height),
            )
        };
        f.render_widget(
            Paragraph::new(format!(
                "TUIVORY Focus · {}",
                text(
                    self.en,
                    "한글 상태·팝업 견본 / 이름",
                    "Control and popup example / Name"
                )
            ))
            .style(self.styles.text_on_surface("body", "surface").unwrap()),
            line(0),
        );
        f.render_widget(
            Paragraph::new(format!(
                "Scope={} Focus={} Depth={}",
                self.stack.scope_id(),
                self.stack.focused(),
                self.stack.depth()
            ))
            .style(self.styles.role("info").unwrap()),
            line(1),
        );
        for level in 0..=self.stack.depth() {
            let r = area(level, screen);
            if r.width < 3 || r.height < 3 {
                continue;
            }
            let active = level == self.stack.depth();
            let titles = [
                ("기본 컨트롤", "Root controls"),
                ("바깥 팝업", "Outer popup"),
                ("안쪽 팝업", "Inner popup"),
            ];
            let title = text(self.en, titles[level].0, titles[level].1);
            let panel = self.styles.panel(title, active, 1, self.ascii).unwrap();
            let inner = panel.inner(r);
            f.render_widget(Clear, r);
            f.render_widget(panel, r);
            for (index, item) in targets(level).iter().enumerate() {
                if index >= usize::from(inner.height) {
                    break;
                }
                let focused = active && self.stack.focused() == item.id;
                let visual = item.state.visual();
                let cursor = if focused { "> " } else { "  " };
                let s = format!(
                    "{cursor}{:<6}{}",
                    visual.markers.trim_start_matches('-'),
                    label(&item.id, self.en)
                );
                f.render_widget(
                    Paragraph::new(s).style(
                        self.styles
                            .control_on_surface(item.state, focused, "surface")
                            .unwrap(),
                    ),
                    Rect::new(inner.x, inner.y + index as u16, inner.width, 1),
                );
            }
        }
        if screen.height > 0 {
            f.render_widget(Paragraph::new(text(self.en,"Tab/Shift+Tab 이동 · Enter 열기/닫기 · Esc 복귀 · F2 테마 · F3 색상 · F4 ASCII · Ctrl+Q 종료","Tab/Shift+Tab move · Enter open/close · Esc return · F2 theme · F3 colors · F4 ASCII · Ctrl+Q quit")).style(self.styles.role("hint").unwrap()),line(screen.height-1));
        }
    }
    fn activate(&mut self) -> Result<(), tuivory::Error> {
        if !self
            .stack
            .targets()
            .iter()
            .any(|t| t.id == self.stack.focused() && t.state.visual().activatable)
        {
            return Ok(());
        }
        match self.stack.focused() {
            "open" => self.stack.open("outer", targets(1), "child", true),
            "child" => self.stack.open("inner", targets(2), "close", true),
            "close" => {
                let id = self.stack.scope_id().to_owned();
                self.stack.close(&id)
            }
            _ => Ok(()),
        }
    }
    fn click(&mut self, x: u16, y: u16) {
        for level in (0..=self.stack.depth()).rev() {
            let r = area(level, self.screen);
            if !r.contains((x, y).into()) {
                continue;
            }
            let id = ["root", "outer", "inner"][level];
            if self.stack.route(id).blocked {
                return;
            }
            let Some(row) = y.checked_sub(r.y + 2) else {
                return;
            };
            if x >= r.x + 2 && x < r.right().saturating_sub(2) {
                if let Some(target) = targets(level).get(usize::from(row)) {
                    self.stack.focus(&target.id);
                }
            }
            return;
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
    let mut profile = ColorProfile::Indexed256;
    let mut snapshot = None;
    let mut nested = false;
    let mut popup = false;
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--lang" => {
                en = match args.next().as_deref() {
                    Some("en") => true,
                    Some("ko") => false,
                    _ => return Err("--lang must be ko or en".into()),
                }
            }
            "--theme" => theme = args.next().ok_or("missing theme")?.parse()?,
            "--colors" => profile = args.next().ok_or("missing colors")?.parse()?,
            "--ascii" => ascii = true,
            "--nested" => nested = true,
            "--popup" => popup = true,
            "--snapshot" => snapshot = Some(args.next().ok_or("missing snapshot path")?),
            _ => return Err(format!("unknown option {arg}").into()),
        }
    }
    let mut app = App {
        en,
        ascii,
        theme,
        profile,
        styles: Styles::new(theme, profile)?,
        stack: FocusStack::new("root", targets(0))?,
        screen: Rect::default(),
    };
    if nested || popup {
        app.activate()?;
    }
    if nested {
        app.activate()?;
    }
    if let Some(path) = snapshot {
        let mut terminal = Terminal::new(TestBackend::new(120, 32))?;
        terminal.draw(|f| app.draw(f))?;
        snapshot::write(std::path::Path::new(&path), terminal.backend().buffer())?;
        return Ok(());
    }
    if !io::stdin().is_terminal() || !io::stdout().is_terminal() {
        return Err("interactive example requires a terminal".into());
    }
    enable_raw_mode()?;
    let _session = Session;
    execute!(io::stdout(), EnterAlternateScreen, EnableMouseCapture)?;
    let mut terminal = Terminal::new(CrosstermBackend::new(io::stdout()))?;
    loop {
        terminal.draw(|f| app.draw(f))?;
        if !event::poll(Duration::from_millis(200))? {
            continue;
        }
        match event::read()? {
            Event::Key(key) if matches!(key.kind, KeyEventKind::Press | KeyEventKind::Repeat) => {
                if key.code == KeyCode::Char('q') && key.modifiers.contains(KeyModifiers::CONTROL) {
                    break;
                }
                match key.code {
                    KeyCode::Tab | KeyCode::BackTab => {
                        app.stack.move_focus(key.code == KeyCode::BackTab);
                    }
                    KeyCode::Enter => app.activate()?,
                    KeyCode::Esc => {
                        if let Some(request) = app.stack.request_close() {
                            app.stack.close(&request.id)?;
                        }
                    }
                    KeyCode::F(2) => {
                        app.theme = match app.theme {
                            Theme::Dark => Theme::Light,
                            Theme::Light => Theme::Blackwhite,
                            Theme::Blackwhite => Theme::Dark,
                        };
                        app.styles = Styles::new(app.theme, app.profile)?
                    }
                    KeyCode::F(3) => {
                        app.profile = match app.profile {
                            ColorProfile::Ansi8 => ColorProfile::Ansi16,
                            ColorProfile::Ansi16 => ColorProfile::Indexed256,
                            ColorProfile::Indexed256 => ColorProfile::Truecolor,
                            ColorProfile::Truecolor => ColorProfile::Ansi8,
                        };
                        app.styles = Styles::new(app.theme, app.profile)?
                    }
                    KeyCode::F(4) => app.ascii = !app.ascii,
                    _ => (),
                }
            }
            Event::Mouse(mouse) if mouse.kind == MouseEventKind::Down(MouseButton::Left) => {
                app.click(mouse.column, mouse.row)
            }
            _ => (),
        }
    }
    Ok(())
}
