mod app;
mod snapshot;

use app::{App, Language};
use std::{
    error::Error,
    io::{self, IsTerminal},
    path::PathBuf,
    time::Duration,
};
use tuivory::ui::terminal::{
    cursor::Show,
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyEventKind},
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use tuivory::ui::{
    Terminal,
    backend::{CrosstermBackend, TestBackend},
};
use tuivory::{ColorProfile, Theme, profile_for_colors};

struct Options {
    language: Language,
    theme: Theme,
    profile: Option<ColorProfile>,
    mouse: bool,
    snapshot: Option<PathBuf>,
    popup: bool,
}
fn options() -> Result<Option<Options>, Box<dyn Error>> {
    let mut result = Options {
        language: Language::Ko,
        theme: Theme::Dark,
        profile: None,
        mouse: true,
        snapshot: None,
        popup: false,
    };
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--help" | "-h" => {
                println!(
                    "TUIVORY Rust playground\n--lang ko|en (default ko)\n--theme dark|light|blackwhite\n--colors auto|8|16|256|truecolor\n--mouse=false\nDocumentation: --snapshot FILE.svg [--popup]"
                );
                return Ok(None);
            }
            "--lang" => {
                result.language = match args.next().as_deref() {
                    Some("ko") => Language::Ko,
                    Some("en") => Language::En,
                    _ => return Err("--lang requires ko or en".into()),
                }
            }
            "--theme" => result.theme = args.next().ok_or("--theme requires a value")?.parse()?,
            "--colors" => {
                let value = args.next().ok_or("--colors requires a value")?;
                result.profile = if value == "auto" {
                    None
                } else {
                    Some(value.parse()?)
                };
            }
            "--mouse=false" => result.mouse = false,
            "--mouse=true" => result.mouse = true,
            "--snapshot" => {
                result.snapshot = Some(args.next().ok_or("--snapshot requires a file")?.into())
            }
            "--popup" => result.popup = true,
            _ => return Err(format!("unknown option: {arg}").into()),
        }
    }
    if result.popup && result.snapshot.is_none() {
        return Err("--popup is a documentation snapshot option".into());
    }
    Ok(Some(result))
}

// Cleanup also runs on early errors and unwinding. Terminal ownership stays in
// this example host, never in the Tuivory core or Ratatui adapter.
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

fn run() -> Result<(), Box<dyn Error>> {
    let Some(options) = options()? else {
        return Ok(());
    };
    let profile = options.profile.unwrap_or_else(|| {
        if options.snapshot.is_some() {
            ColorProfile::Truecolor
        } else {
            profile_for_colors(
                i32::from(tuivory::ui::terminal::style::available_color_count()),
                false,
            )
        }
    });
    let mut app = App::new(options.language, options.theme, profile)?;
    if let Some(path) = options.snapshot {
        if options.popup {
            app.preview();
        }
        let mut terminal = Terminal::new(TestBackend::new(120, 36))?;
        terminal.draw(|f| app.draw(f))?;
        snapshot::write(&path, terminal.backend().buffer())?;
        return Ok(());
    }
    if !io::stdin().is_terminal() || !io::stdout().is_terminal() {
        return Err("interactive playground requires a terminal".into());
    }
    enable_raw_mode()?;
    let _session = Session;
    execute!(io::stdout(), EnterAlternateScreen)?;
    if options.mouse {
        execute!(io::stdout(), EnableMouseCapture)?;
    }
    let mut terminal = Terminal::new(CrosstermBackend::new(io::stdout()))?;
    terminal.clear()?;
    loop {
        terminal.draw(|f| app.draw(f))?;
        if !event::poll(Duration::from_millis(200))? {
            continue;
        }
        match event::read()? {
            Event::Key(key) if matches!(key.kind, KeyEventKind::Press | KeyEventKind::Repeat) => {
                if app.key(key)? {
                    break;
                }
            }
            Event::Mouse(mouse) if options.mouse => app.mouse(mouse)?,
            Event::Resize(..) => (),
            _ => (),
        }
    }
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("TUIVORY: {error}");
        std::process::exit(1);
    }
}
