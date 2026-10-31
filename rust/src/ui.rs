//! SDK-owned application/rendering compatibility. Component models remain
//! backend-neutral; these pinned adapters retain backend type/trait identity.
//! Applications import this module instead of direct renderer dependencies.
/// Tuivory component renderers and semantic styles.
pub use crate::ratatui as components;
pub use ::ratatui::{
    CompletedFrame, Frame, Terminal, TerminalOptions, Viewport, backend, buffer, layout, prelude,
    style, symbols, text, widgets,
};

/// Terminal event/command adapters, available with the `terminal` feature
/// (also enabled by the compatible `playground` feature).
#[cfg(feature = "terminal")]
pub mod terminal {
    pub use ::crossterm::{
        Command, ExecutableCommand, QueueableCommand, cursor, event, execute, queue, style,
        terminal,
    };
}

/// Explicit terminal-session configuration; global keys remain host-owned.
#[cfg(feature = "terminal")]
#[derive(Clone, Copy, Debug)]
pub struct SessionOptions {
    pub mouse: bool,
    pub bracketed_paste: bool,
}
#[cfg(feature = "terminal")]
impl Default for SessionOptions {
    fn default() -> Self {
        Self {
            mouse: true,
            bracketed_paste: true,
        }
    }
}

/// Opt-in stdout alternate-screen/raw-mode guard. Drop restores the terminal;
/// `finish` additionally reports cleanup errors. No process/global key policy.
#[cfg(feature = "terminal")]
pub struct Session {
    active: bool,
    raw: bool,
    alternate: bool,
}
#[cfg(feature = "terminal")]
static SESSION_ACTIVE: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);
#[cfg(feature = "terminal")]
impl Session {
    pub fn enter(options: SessionOptions) -> std::io::Result<Self> {
        use ::crossterm::{
            event::{EnableBracketedPaste, EnableMouseCapture},
            execute,
            terminal::{EnterAlternateScreen, enable_raw_mode},
        };
        use std::sync::atomic::Ordering;
        if SESSION_ACTIVE
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .is_err()
        {
            return Err(std::io::Error::new(
                std::io::ErrorKind::AlreadyExists,
                "a Tuivory terminal session is already active",
            ));
        }
        let mut session = Self {
            active: true,
            raw: false,
            alternate: false,
        };
        if ::crossterm::terminal::is_raw_mode_enabled()? {
            return Err(std::io::Error::new(
                std::io::ErrorKind::AlreadyExists,
                "raw mode is already owned by another terminal controller",
            ));
        }
        enable_raw_mode()?;
        session.raw = true;
        // The guard rolls back raw mode and any successful commands on failure.
        session.alternate = true;
        execute!(std::io::stdout(), EnterAlternateScreen)?;
        if options.mouse {
            execute!(std::io::stdout(), EnableMouseCapture)?;
        }
        if options.bracketed_paste {
            execute!(std::io::stdout(), EnableBracketedPaste)?;
        }
        Ok(session)
    }
    pub fn finish(mut self) -> std::io::Result<()> {
        self.restore()
    }
    fn restore(&mut self) -> std::io::Result<()> {
        if !self.active {
            return Ok(());
        }
        self.active = false;
        use ::crossterm::{
            cursor::Show,
            event::{DisableBracketedPaste, DisableMouseCapture},
            execute,
            terminal::{LeaveAlternateScreen, disable_raw_mode},
        };
        let raw = if self.raw { disable_raw_mode() } else { Ok(()) };
        let screen = if self.alternate {
            execute!(
                std::io::stdout(),
                DisableMouseCapture,
                DisableBracketedPaste,
                LeaveAlternateScreen,
                Show
            )
        } else {
            Ok(())
        };
        SESSION_ACTIVE.store(false, std::sync::atomic::Ordering::Release);
        raw.and(screen)
    }
}
#[cfg(feature = "terminal")]
impl Drop for Session {
    fn drop(&mut self) {
        let _ = self.restore();
    }
}
