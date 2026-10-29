use super::Styles;
use crate::{Color, Error, interaction::ControlState};
use ratatui::style::{Modifier, Style};

fn plain_text_role(role: &str) -> bool {
    matches!(
        role,
        "body" | "hint" | "disabled" | "info" | "success" | "warning" | "error"
    )
}
fn luminance(color: Color) -> f64 {
    let (r, g, b) = match color {
        Color::Rgb(r, g, b) => (r, g, b),
        Color::Indexed(n) => {
            const ANSI: [(u8, u8, u8); 16] = [
                (0, 0, 0),
                (128, 0, 0),
                (0, 128, 0),
                (128, 128, 0),
                (0, 0, 128),
                (128, 0, 128),
                (0, 128, 128),
                (192, 192, 192),
                (128, 128, 128),
                (255, 0, 0),
                (0, 255, 0),
                (255, 255, 0),
                (0, 0, 255),
                (255, 0, 255),
                (0, 255, 255),
                (255, 255, 255),
            ];
            if n < 16 {
                ANSI[usize::from(n)]
            } else if n >= 232 {
                let v = 8 + (n - 232) * 10;
                (v, v, v)
            } else {
                let n = n - 16;
                let cube = [0, 95, 135, 175, 215, 255];
                (
                    cube[usize::from(n / 36)],
                    cube[usize::from((n / 6) % 6)],
                    cube[usize::from(n % 6)],
                )
            }
        }
    };
    let channel = |v: u8| {
        let v = f64::from(v) / 255.0;
        if v <= 0.04045 {
            v / 12.92
        } else {
            ((v + 0.055) / 1.055).powf(2.4)
        }
    };
    0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
}
fn contrast(a: Color, b: Color) -> f64 {
    let a = luminance(a);
    let b = luminance(b);
    (a.max(b) + 0.05) / (a.min(b) + 0.05)
}
impl Styles {
    pub(super) fn disabled_cue(&self, role: &str, style: Style) -> Style {
        if role == "disabled"
            && self
                .palette
                .style("body")
                .is_ok_and(|body| Some(body.foreground.into()) == style.fg)
        {
            style
                .remove_modifier(Modifier::BOLD)
                .add_modifier(Modifier::DIM)
        } else {
            style
        }
    }
    /// Bind text to an actual surface without mutating the palette. Use the
    /// surface foreground below the role target (disabled 2:1, others 4.5:1), if better.
    /// Keep `role` for explicit field/selection/edit/custom backgrounds.
    pub fn text_on_surface(&self, role: &str, surface: &str) -> Result<Style, Error> {
        let mut text = self.palette.style(role)?;
        let base = self.palette.style(surface)?;
        text.background = base.background;
        let current = contrast(text.foreground, base.background);
        let target = if role == "disabled" { 2.0 } else { 4.5 };
        if current < target && contrast(base.foreground, base.background) > current {
            text.foreground = base.foreground;
        }
        let style = self.disabled_cue(role, text.into());
        Ok(
            if role == "disabled" && text.foreground == base.foreground {
                style
                    .remove_modifier(Modifier::BOLD)
                    .add_modifier(Modifier::DIM)
            } else {
                style
            },
        )
    }
    pub(super) fn component_role(&self, role: &str) -> Result<Style, Error> {
        if plain_text_role(role) {
            self.text_on_surface(role, "surface")
        } else {
            self.role(role)
        }
    }
    /// Bind ordinary control text to a host-selected surface; preserve explicit
    /// selected/edited backgrounds. The original `control` method stays raw.
    pub fn control_on_surface(
        &self,
        state: ControlState,
        focused: bool,
        surface: &str,
    ) -> Result<Style, Error> {
        let visual = state.visual();
        let style = if plain_text_role(visual.role) {
            self.text_on_surface(visual.role, surface)?
        } else {
            self.role(visual.role)?
        };
        Ok(if focused && visual.focusable {
            style.add_modifier(Modifier::UNDERLINED)
        } else {
            style
        })
    }
}
