use ratatui::{
    buffer::Buffer,
    style::{Color, Modifier},
    text::Span,
};
use std::{fmt::Write, path::Path};

fn color(c: Color) -> String {
    let (r, g, b) = match c {
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
        Color::Black => (0, 0, 0),
        Color::White => (255, 255, 255),
        Color::Gray => (192, 192, 192),
        _ => (0, 0, 0),
    };
    format!("#{r:02x}{g:02x}{b:02x}")
}
fn escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

/// Generate a reference from actual Ratatui cells, not a remote terminal capture.
pub fn write(path: &Path, buffer: &Buffer) -> std::io::Result<()> {
    let width = buffer.area.width;
    let height = buffer.area.height;
    let mut svg = format!(
        r#"<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}"><title>Tuivory Rust live widget preview</title><desc>Ratatui TestBackend reference rendering; not a remote terminal screenshot.</desc>"#,
        width * 10,
        height * 22,
        width * 10,
        height * 22
    );
    for y in 0..height {
        // Ratatui resets continuation cells after a wide glyph. A terminal
        // paints both columns with the leading cell's background instead.
        let mut backgrounds = Vec::with_capacity(usize::from(width));
        let mut x = 0;
        while x < width {
            let cell = &buffer[(x, y)];
            let columns = (Span::raw(cell.symbol()).width() as u16)
                .max(1)
                .min(width - x);
            for _ in 0..columns {
                backgrounds.push(color(cell.bg));
            }
            x += columns;
        }
        let mut start = 0;
        let mut previous = backgrounds[0].clone();
        for x in 1..=width {
            let next = if x < width {
                backgrounds[usize::from(x)].clone()
            } else {
                String::new()
            };
            if next != previous {
                write!(
                    svg,
                    r#"<rect x="{}" y="{}" width="{}" height="22" fill="{}"/>"#,
                    start * 10,
                    y * 22,
                    (x - start) * 10,
                    previous
                )
                .unwrap();
                start = x;
                previous = next;
            }
        }
    }
    svg.push_str(r#"<g font-family="D2Coding,monospace" font-size="20">"#);
    for y in 0..height {
        for x in 0..width {
            let cell = &buffer[(x, y)];
            if cell.symbol().trim().is_empty() {
                continue;
            }
            let bold = if cell.modifier.contains(Modifier::BOLD) {
                "bold"
            } else {
                "normal"
            };
            write!(
                svg,
                r#"<text x="{}" y="{}" fill="{}" font-weight="{}" opacity="{}">{}</text>"#,
                x * 10,
                y * 22 + 18,
                color(cell.fg),
                bold,
                if cell.modifier.contains(Modifier::DIM) {
                    "0.45"
                } else {
                    "1"
                },
                escape(cell.symbol())
            )
            .unwrap();
            if cell.modifier.contains(Modifier::UNDERLINED) {
                write!(
                    svg,
                    r#"<path d="M{} {}h{}" stroke="{}"/>"#,
                    x * 10,
                    y * 22 + 20,
                    Span::raw(cell.symbol()).width() * 10,
                    color(cell.fg)
                )
                .unwrap();
            }
        }
    }
    svg.push_str("</g></svg>");
    std::fs::write(path, svg)
}
