//! Optional Ratatui 0.30 adapter. This module owns no terminal or widget state.
//! Enable the `ratatui` feature with Rust 1.88 or later.
//!
//! ```
//! # #[cfg(feature = "ratatui")]
//! # fn example() -> Result<(), tuivory::Error> {
//! use tuivory::{ColorProfile, Theme};
//! use tuivory::ratatui::Styles;
//! let styles = Styles::new(Theme::Dark, ColorProfile::Ansi16)?;
//! let focused_panel = styles.block("Panel", true)?;
//! let selection = styles.role("selection")?;
//! # Ok(())
//! # }
//! ```

use crate::{ColorProfile, Error, Palette, Theme, TokenDocument};
mod components;
mod rows;
pub use rows::{FormWidget, ListWidget, RowsWidget, SearchPickerWidget};
mod tree;
use ::ratatui::{
    style::{Color, Modifier, Style},
    widgets::{Block, BorderType, Borders},
};
pub use components::{LineWidget, SplitRects, TabsWidget, split_rects};
pub use tree::TreeWidget;

impl From<crate::Color> for Color {
    fn from(value: crate::Color) -> Self {
        match value {
            crate::Color::Indexed(n) => Self::Indexed(n),
            crate::Color::Rgb(r, g, b) => Self::Rgb(r, g, b),
        }
    }
}

impl From<crate::Style> for Style {
    fn from(value: crate::Style) -> Self {
        let style = Self::default()
            .fg(value.foreground.into())
            .bg(value.background.into());
        if value.bold {
            style.add_modifier(Modifier::BOLD)
        } else {
            style
        }
    }
}

/// An owned style palette for existing Ratatui widgets. The host retains
/// list/table/input state and chooses when to replace this value on theme change.
#[derive(Clone, Debug)]
pub struct Styles {
    palette: Palette,
}

impl Styles {
    /// Resolve common control states; the host draws visual().markers separately.
    pub fn control(
        &self,
        state: crate::interaction::ControlState,
        focused: bool,
    ) -> Result<Style, Error> {
        let visual = state.visual();
        let style = self.role(visual.role)?;
        Ok(if focused && visual.focusable {
            style.add_modifier(Modifier::UNDERLINED)
        } else {
            style
        })
    }
    /// A padded panel using the same focus and ordinary-font fallback contract.
    pub fn panel<'a>(
        &self,
        title: &'a str,
        focused: bool,
        padding: u16,
        ascii: bool,
    ) -> Result<Block<'a>, Error> {
        let mut block = self
            .block(title, focused)?
            .padding(::ratatui::widgets::Padding::uniform(padding));
        if focused {
            block = block.title(format!("> {title}"));
        }
        if ascii {
            block = block.border_set(::ratatui::symbols::border::Set {
                top_left: "+",
                top_right: "+",
                bottom_left: "+",
                bottom_right: "+",
                vertical_left: "|",
                vertical_right: "|",
                horizontal_top: "-",
                horizontal_bottom: "-",
            });
        }
        Ok(block)
    }
    /// Load the shared candidate palette, distinct from Go's extracted styles.
    pub fn new(theme: Theme, profile: ColorProfile) -> Result<Self, Error> {
        Ok(Self::from_palette(
            TokenDocument::candidate()?.palette(theme, profile)?,
        ))
    }

    pub fn from_palette(palette: Palette) -> Self {
        Self { palette }
    }

    /// Resolve a semantic role without replacing ANSI indices with RGB values.
    pub fn role(&self, name: &str) -> Result<Style, Error> {
        self.palette.style(name).map(Style::from)
    }

    /// Create a panel border without modifying the host's focus callbacks.
    /// Double borders preserve the focus cue even without color.
    pub fn block<'a>(&self, title: &'a str, focused: bool) -> Result<Block<'a>, Error> {
        Ok(Block::default()
            .title(title)
            .borders(Borders::ALL)
            .border_type(if focused {
                BorderType::Double
            } else {
                BorderType::Plain
            })
            .style(self.role("surface")?)
            .border_style(self.role(if focused { "focus.border" } else { "hint" })?))
    }
}
