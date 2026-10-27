//! Framework-independent Tuivory tokens and styles. No terminal, application,
//! filesystem, or database I/O is performed by this library.
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

pub mod components;
mod tokens;
pub mod tree;
mod types;

#[cfg(feature = "ratatui")]
pub mod ratatui;

pub use tokens::{CANDIDATE_JSON, TOKEN_FORMAT, TokenDocument, TokenPair, TokenPalette};
pub use types::{Color, ColorProfile, Error, Palette, Style, Theme, profile_for_colors};
