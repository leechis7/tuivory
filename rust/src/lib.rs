//! Reusable TUI component models, tokens and styles, with optional renderers.
//! Hosts own screen composition, cross-component focus order, global keymaps,
//! data/actions and terminal lifecycle policy. Core models perform no terminal,
//! filesystem or database I/O. The optional ui::Session performs terminal I/O
//! only when explicitly entered by the host.
//!
//! The candidate palette is shared reference data, not the LazyOra-derived
//! palette exposed by the Go widget styler.
//!
//! ```
//! use tuivory::{ColorProfile, Theme, TokenDocument};
//! let document = TokenDocument::candidate()?;
//! let palette = document.palette(Theme::Dark, ColorProfile::Indexed256)?;
//! let selected = palette.style("selection")?;
//! # Ok::<(), tuivory::Error>(())
//! ```

pub mod collections;
pub mod components;
pub mod containers;
pub mod controls;
pub mod feedback;
pub mod forms;
pub mod grid;
pub mod input;
pub mod interaction;
pub mod layout;
pub mod menu;
pub mod popup;
pub mod text;
pub mod text_markup;
pub mod text_offsets;
mod tokens;
pub mod tree;
mod types;

#[cfg(feature = "ratatui")]
pub mod ratatui;

#[cfg(feature = "ratatui")]
pub mod ui;

pub use tokens::{CANDIDATE_JSON, TOKEN_FORMAT, TokenDocument, TokenPair, TokenPalette};
pub use types::{Color, ColorProfile, Error, Palette, Style, Theme, profile_for_colors};
