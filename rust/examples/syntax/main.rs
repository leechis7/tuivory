//! Optional Oracle SQL tokenizer and shared editor; no database connection.
#[path = "../playground/snapshot.rs"]
mod snapshot;
use std::{error::Error, io, path::Path, sync::Arc};
use tuivory::{
    ColorProfile, Theme,
    input::InputEvent,
    syntax::SyntaxRequest,
    syntax_sql::SQLAnalyzer,
    text::TextDocument,
    ui::{
        Terminal,
        backend::{CrosstermBackend, TestBackend},
        buffer::Buffer,
        components::{Styles, TextWidget},
        layout::Rect,
        terminal::event::{
            self, Event, KeyCode, KeyEventKind, KeyModifiers, MouseButton, MouseEventKind,
        },
        widgets::{Paragraph, Widget},
    },
};
struct App {
    en: bool,
    ascii: bool,
    theme: Theme,
    profile: ColorProfile,
    styles: Styles,
    doc: TextDocument,
    status: String,
}
impl App {
    fn draw(&mut self, area: Rect, buf: &mut Buffer) {
        let panel = Rect::new(area.x, area.y, area.width, area.height.saturating_sub(2));
        let title = if self.en {
            "SQL syntax highlighting"
        } else {
            "SQL 문법 강조"
        };
        let block = self.styles.panel(title, true, 0, self.ascii).unwrap();
        let inner = block.inner(panel);
        block.render(panel, buf);
        TextWidget {
            model: &mut self.doc,
            styles: &self.styles,
            focused: true,
        }
        .render(inner, buf);
        let footer = Rect::new(area.x, panel.bottom(), area.width, area.height.min(2));
        let help = if self.en {
            "F2 theme / F3 colors / select/paste/undo / Ctrl+Q quit"
        } else {
            "F2 테마 · F3 색상 · 선택/붙여넣기/Undo · Ctrl+Q 종료"
        };
        Paragraph::new(format!("{}\n{help}", self.status))
            .style(self.styles.text_on_surface("hint", "surface").unwrap())
            .render(footer, buf);
    }
}
pub fn run(arguments: Vec<String>) -> Result<(), Box<dyn Error>> {
    let mut en = false;
    let mut ascii = false;
    let mut theme = Theme::Dark;
    let mut profile = ColorProfile::Indexed256;
    let mut output = None;
    let mut args = arguments.into_iter();
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--lang" => {
                let lang = args.next().ok_or("lang")?;
                if lang != "ko" && lang != "en" {
                    return Err("invalid language".into());
                }
                en = lang == "en"
            }
            "--theme" => theme = args.next().ok_or("theme")?.parse()?,
            "--colors" => profile = args.next().ok_or("colors")?.parse()?,
            "--ascii" => ascii = true,
            "--snapshot" => output = Some(args.next().ok_or("snapshot")?),
            _ => return Err(format!("unknown argument {arg}").into()),
        }
    }
    let source = if en {
        "-- Oracle SQL / PL/SQL highlighting\nSELECT NVL(:name, q'[Unicode]') AS \"result\",\n       COUNT(*), 1.25e2 FROM example\nWHERE id = :id;\n\nBEGIN\n  NULL; -- The host decides whether to execute SQL.\nEND;"
    } else {
        "-- Oracle SQL / PL/SQL 강조 예제\nSELECT NVL(:이름, q'[한글 😀 é]') AS \"결과\",\n       COUNT(*), 1.25e2 FROM 예제\nWHERE id = :id;\n\nBEGIN\n  NULL; -- SQL 실행은 앱이 결정합니다.\nEND;"
    };
    let mut doc = TextDocument::editor(source);
    doc.buffer.select(0, 0);
    doc.set_syntax_analyzer(
        Some(Arc::new(SQLAnalyzer::new())),
        SyntaxRequest {
            language: "sql".into(),
            dialect: "oracle".into(),
        },
    )?;
    let mut app = App {
        en,
        ascii,
        theme,
        profile,
        styles: Styles::new(theme, profile)?,
        doc,
        status: if en {
            "Highlighting only; no database connection."
        } else {
            "강조만 수행하며 DB에 연결하지 않습니다."
        }
        .into(),
    };
    if let Some(output) = output {
        let mut terminal = Terminal::new(TestBackend::new(96, 22))?;
        terminal.draw(|f| app.draw(f.area(), f.buffer_mut()))?;
        snapshot::write(Path::new(&output), terminal.backend().buffer())?;
        return Ok(());
    }
    let session = tuivory::ui::Session::enter(Default::default())?;
    let mut terminal = Terminal::new(CrosstermBackend::new(io::stdout()))?;
    let mut dragging = false;
    loop {
        terminal.draw(|f| app.draw(f.area(), f.buffer_mut()))?;
        match event::read()? {
            Event::Key(key) if key.kind != KeyEventKind::Release => {
                if key.code == KeyCode::Char('q') && key.modifiers.contains(KeyModifiers::CONTROL) {
                    break;
                }
                if key.code == KeyCode::F(2) {
                    app.theme = match app.theme {
                        Theme::Dark => Theme::Light,
                        Theme::Light => Theme::Blackwhite,
                        Theme::Blackwhite => Theme::Dark,
                    };
                    app.styles = Styles::new(app.theme, app.profile)?
                } else if key.code == KeyCode::F(3) {
                    app.profile = match app.profile {
                        ColorProfile::Ansi8 => ColorProfile::Ansi16,
                        ColorProfile::Ansi16 => ColorProfile::Indexed256,
                        ColorProfile::Indexed256 => ColorProfile::Truecolor,
                        ColorProfile::Truecolor => ColorProfile::Ansi8,
                    };
                    app.styles = Styles::new(app.theme, app.profile)?
                } else {
                    let (action, text) = InputEvent::from_key(key).editing_action();
                    let event = app.doc.handle(&action, &text);
                    if !event.kind.is_empty() {
                        app.status = event.kind
                    }
                }
            }
            Event::Paste(text) => {
                app.doc.handle("paste", &text);
            }
            Event::Mouse(mouse) => {
                let size = terminal.size()?;
                match mouse.kind {
                    MouseEventKind::Down(MouseButton::Left) => {
                        dragging = true;
                        app.doc.point(
                            mouse.column as isize - 1,
                            mouse.row as isize - 1,
                            usize::from(size.width.saturating_sub(2)),
                            usize::from(size.height.saturating_sub(4)),
                            false,
                        )
                    }
                    MouseEventKind::Drag(MouseButton::Left)
                    | MouseEventKind::Up(MouseButton::Left)
                        if dragging =>
                    {
                        app.doc.point(
                            mouse.column as isize - 1,
                            mouse.row as isize - 1,
                            usize::from(size.width.saturating_sub(2)),
                            usize::from(size.height.saturating_sub(4)),
                            true,
                        );
                        if matches!(mouse.kind, MouseEventKind::Up(_)) {
                            dragging = false
                        }
                    }
                    MouseEventKind::ScrollUp => {
                        app.doc.handle("scroll_up", "");
                    }
                    MouseEventKind::ScrollDown => {
                        app.doc.handle("scroll_down", "");
                    }
                    _ => {}
                }
            }
            _ => {}
        }
    }
    session.finish()?;
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    run(std::env::args().skip(1).collect())
}
