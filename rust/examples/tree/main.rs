//! Database-free host using Tuivory's public tree model and Ratatui widget.
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
    layout::{Constraint, Layout, Rect},
    widgets::Paragraph,
};
use std::{
    error::Error,
    io::{self, IsTerminal},
    time::Duration,
};
use tuivory::{
    ColorProfile, Theme,
    ratatui::{Styles, TreeWidget},
    tree::{Tree, TreeAction, TreeNode, TreeState},
};

struct App {
    tree: Tree,
    state: TreeState,
    theme: Theme,
    profile: ColorProfile,
    styles: Styles,
    en: bool,
    ascii: bool,
    focused: bool,
    status: String,
    inner: Rect,
}
impl App {
    fn text<'a>(&self, ko: &'a str, en: &'a str) -> &'a str {
        if self.en { en } else { ko }
    }
    fn draw(&mut self, frame: &mut Frame<'_>) {
        let area = frame.area();
        frame.render_widget(
            Paragraph::new("").style(self.styles.role("surface").unwrap()),
            area,
        );
        let layout = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(0),
            Constraint::Length(1),
            Constraint::Length(2),
        ])
        .split(area);
        let title = format!(
            "TUIVORY Tree · {} / {}\n{}",
            self.theme.as_str(),
            self.profile.as_str(),
            self.status
        );
        frame.render_widget(
            Paragraph::new(title).style(self.styles.text_on_surface("body", "surface").unwrap()),
            layout[0],
        );
        let block = self
            .styles
            .block(self.text(" 트리 ", " Tree "), self.focused)
            .unwrap();
        self.inner = block.inner(layout[1]);
        frame.render_widget(block, layout[1]);
        let mut widget = TreeWidget::new(&self.tree, &self.styles).unwrap();
        widget.focused = self.focused;
        widget.ascii = self.ascii;
        frame.render_stateful_widget(widget, self.inner, &mut self.state);
        let button = self.text("포커스 비교: Enter", "Focus comparison: Enter");
        frame.render_widget(
            Paragraph::new(button).style(if self.focused {
                self.styles.text_on_surface("body", "surface").unwrap()
            } else {
                self.styles.role("selection").unwrap()
            }),
            layout[2],
        );
        let help=self.text("방향키 탐색 · Space 펼침 · Enter 실행 · Alt+←/→ 가로 이동\nTab 포커스 · F2 테마 · F3 색상 · F4 ASCII · Ctrl+Q 종료","Arrows navigate · Space expand · Enter activate · Alt+Left/Right pan\nTab focus · F2 theme · F3 colors · F4 ASCII · Ctrl+Q quit");
        frame.render_widget(
            Paragraph::new(help).style(self.styles.role("hint").unwrap()),
            layout[3],
        );
    }
    fn action(&mut self, action: TreeAction) {
        if let Some(event) =
            self.tree
                .handle(&mut self.state, action, usize::from(self.inner.height))
        {
            self.status = format!("{event:?}");
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
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--lang" => {
                en = match args.next().as_deref() {
                    Some("en") => true,
                    Some("ko") => false,
                    _ => return Err("--lang requires ko or en".into()),
                }
            }
            "--theme" => theme = args.next().ok_or("missing theme")?.parse()?,
            "--colors" => profile = args.next().ok_or("missing colors")?.parse()?,
            "--ascii" => ascii = true,
            "--snapshot" => snapshot = Some(args.next().ok_or("missing file")?),
            "--help" => {
                println!(
                    "TUIVORY Tree: --lang ko|en --theme dark|light|blackwhite --colors 8|16|256|truecolor --ascii --snapshot FILE.svg"
                );
                return Ok(());
            }
            _ => return Err(format!("unknown option: {arg}").into()),
        }
    }
    let text = |ko: &str, english: &str| {
        if en {
            english.to_string()
        } else {
            ko.to_string()
        }
    };
    let node =
        |id: &str, parent: &str, name: String, secondary: String, icon: &str, ascii_icon: &str| {
            TreeNode {
                id: id.into(),
                parent: parent.into(),
                name,
                secondary,
                icon: icon.into(),
                ascii_icon: ascii_icon.into(),
                ..Default::default()
            }
        };
    let mut examples = node(
        "examples",
        "workspace",
        text("예제", "Examples"),
        String::new(),
        "□",
        "D",
    );
    examples.count = Some(3);
    let mut lazy = node(
        "lazy",
        "workspace",
        text("아직 불러오지 않은 항목", "Unloaded items"),
        text("펼침 이벤트만 반환", "Returns an expansion event"),
        "",
        "",
    );
    lazy.branch = true;
    let tree = Tree::new(vec![
        node(
            "workspace",
            "",
            text("작업 공간", "Workspace"),
            text("DB 없는 견본", "Database-free sample"),
            "◇",
            "R",
        ),
        examples,
        node(
            "go",
            "examples",
            "Go".into(),
            text("공개 패키지", "Public package"),
            "·",
            "F",
        ),
        node(
            "rust",
            "examples",
            "Rust".into(),
            text("공개 crate", "Public crate"),
            "·",
            "F",
        ),
        node(
            "long",
            "examples",
            text(
                "매우 긴 한글 이름과 English 표시 셀 스크롤 예시",
                "A very long name demonstrating terminal cell scrolling",
            ),
            String::new(),
            "·",
            "F",
        ),
        lazy,
        node(
            "notes",
            "",
            text("참고", "Notes"),
            "[red] literal text".into(),
            "□",
            "F",
        ),
    ])?;
    let mut app = App {
        tree,
        state: TreeState {
            expanded: ["workspace".into(), "examples".into()].into(),
            ..Default::default()
        },
        theme,
        profile,
        styles: Styles::new(theme, profile)?,
        en,
        ascii,
        focused: true,
        status: text("이름 · 보조 설명 · 개수", "Name · Secondary · Count"),
        inner: Rect::default(),
    };
    if let Some(path) = snapshot {
        let mut terminal = Terminal::new(TestBackend::new(120, 28))?;
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
    terminal.clear()?;
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
                    KeyCode::Tab | KeyCode::BackTab => app.focused = !app.focused,
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
                    KeyCode::Enter if !app.focused => {
                        app.status = app
                            .text(
                                "선택은 유지되고 입력 포커스만 이동합니다.",
                                "Selection persists independently of input focus.",
                            )
                            .into()
                    }
                    _ if app.focused => {
                        let action = match key.code {
                            KeyCode::Left if key.modifiers.contains(KeyModifiers::ALT) => {
                                Some(TreeAction::PanLeft)
                            }
                            KeyCode::Right if key.modifiers.contains(KeyModifiers::ALT) => {
                                Some(TreeAction::PanRight)
                            }
                            KeyCode::Up => Some(TreeAction::Up),
                            KeyCode::Down => Some(TreeAction::Down),
                            KeyCode::Left => Some(TreeAction::Left),
                            KeyCode::Right => Some(TreeAction::Right),
                            KeyCode::Char(' ') => Some(TreeAction::Toggle),
                            KeyCode::Enter => Some(TreeAction::Activate),
                            KeyCode::Home => Some(TreeAction::Home),
                            KeyCode::End => Some(TreeAction::End),
                            KeyCode::PageUp => Some(TreeAction::PageUp),
                            KeyCode::PageDown => Some(TreeAction::PageDown),
                            _ => None,
                        };
                        if let Some(action) = action {
                            app.action(action)
                        }
                    }
                    _ => (),
                }
            }
            Event::Mouse(mouse) if app.inner.contains((mouse.column, mouse.row).into()) => {
                match mouse.kind {
                    MouseEventKind::ScrollUp => app.action(TreeAction::Up),
                    MouseEventKind::ScrollDown => app.action(TreeAction::Down),
                    MouseEventKind::Down(MouseButton::Left) => {
                        app.focused = true;
                        if let Some(event) = app.tree.click(
                            &mut app.state,
                            usize::from(mouse.column - app.inner.x),
                            usize::from(mouse.row - app.inner.y),
                            usize::from(app.inner.height),
                        ) {
                            app.status = format!("{event:?}");
                        }
                    }
                    _ => (),
                }
            }
            _ => (),
        }
    }
    Ok(())
}
