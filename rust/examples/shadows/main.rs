//! Database-free actual popup/shadow references for all twelve palettes.
#[path = "../playground/snapshot.rs"]
mod snapshot;
use ratatui::{Terminal, backend::TestBackend, layout::Rect, widgets::Paragraph};
use std::{error::Error, path::PathBuf};
use tuivory::{
    ColorProfile, Theme,
    layout::CellRect,
    menu::{Menu, MenuItem},
    popup::{ShadowMode, ShadowOptions, popup_placement},
    ratatui::{MenuPopupWidget, Styles},
};
fn main() -> Result<(), Box<dyn Error>> {
    let (mut en, mut edge, mut ascii) = (false, false, false);
    let mut mode = ShadowMode::Off;
    let mut output = None;
    let mut args = std::env::args().skip(1);
    while let Some(a) = args.next() {
        match a.as_str() {
            "--lang" => {
                en = match args.next().as_deref() {
                    Some("ko") => false,
                    Some("en") => true,
                    _ => return Err("invalid language".into()),
                }
            }
            "--shadow" => mode = args.next().ok_or("missing shadow mode")?.parse()?,
            "--edge" => edge = true,
            "--ascii" => ascii = true,
            "--snapshot" => output = Some(PathBuf::from(args.next().ok_or("missing output")?)),
            _ => return Err(format!("unknown option {a}").into()),
        }
    }
    let output = output.ok_or(
        "use --snapshot PATH [--shadow off|auto|solid|dim] [--lang ko|en] [--edge] [--ascii]",
    )?;
    let tr = |ko: &str, english: &str| {
        if en {
            english.to_owned()
        } else {
            ko.to_owned()
        }
    };
    let options = ShadowOptions {
        mode,
        ..Default::default()
    };
    let mut terminal = Terminal::new(TestBackend::new(114, 72))?;
    terminal.draw(|f| {
        for (row, (profile, label)) in [
            (ColorProfile::Ansi8, "8"),
            (ColorProfile::Ansi16, "16"),
            (ColorProfile::Indexed256, "256"),
            (ColorProfile::Truecolor, "True Color"),
        ]
        .into_iter()
        .enumerate()
        {
            for (col, (theme, ko, english)) in [
                (Theme::Dark, "다크", "Dark"),
                (Theme::Light, "라이트", "Light"),
                (Theme::Blackwhite, "흑백", "Monochrome"),
            ]
            .into_iter()
            .enumerate()
            {
                let styles = Styles::new(theme, profile).unwrap();
                let (x, y) = (col * 38, row * 18);
                let title = format!(" {} · {label} ", tr(ko, english));
                f.render_widget(
                    styles.panel(&title, false, 0, ascii).unwrap(),
                    Rect::new(x as u16, y as u16, 38, 18),
                );
                for yy in 2..15 {
                    f.render_widget(
                        Paragraph::new(format!("{yy:02} README.md settings README.md"))
                            .style(styles.text_on_surface("body", "surface").unwrap()),
                        Rect::new(x as u16 + 2, y as u16 + yy, 34, 1),
                    );
                }
                let anchor = if edge {
                    CellRect {
                        x: x + 35,
                        y: y + 15,
                        width: 1,
                        height: 1,
                    }
                } else {
                    CellRect {
                        x: x + 3,
                        y: y + 3,
                        width: 1,
                        height: 1,
                    }
                };
                let viewport = CellRect {
                    x: x + 1,
                    y: y + 1,
                    width: 36,
                    height: 16,
                };
                let layout = popup_placement(anchor, viewport, 28, 8, options);
                assert!(
                    layout.bounds.x + layout.bounds.width <= viewport.x + viewport.width
                        && layout.bounds.y + layout.bounds.height <= viewport.y + viewport.height
                );
                let mut menu = Menu::new(vec![
                    MenuItem {
                        id: "open".into(),
                        label: tr("열기", "Open"),
                        shortcut: "Enter".into(),
                        ..Default::default()
                    },
                    MenuItem {
                        id: "rename".into(),
                        label: tr("이름 바꾸기", "Rename"),
                        shortcut: "F2".into(),
                        ..Default::default()
                    },
                    MenuItem {
                        id: "copy".into(),
                        label: tr("복사", "Copy"),
                        ..Default::default()
                    },
                    MenuItem {
                        id: "delete".into(),
                        label: tr("삭제 불가", "Delete unavailable"),
                        disabled: true,
                        ..Default::default()
                    },
                ])
                .unwrap();
                menu.open("", "source");
                f.render_widget(
                    MenuPopupWidget::new(&mut menu, &styles, &tr("문맥 메뉴", "Context menu"))
                        .ascii(ascii)
                        .shadow(options),
                    Rect::new(
                        layout.bounds.x as u16,
                        layout.bounds.y as u16,
                        layout.bounds.width as u16,
                        layout.bounds.height as u16,
                    ),
                );
                f.render_widget(
                    Paragraph::new("+").style(styles.role("selection").unwrap()),
                    Rect::new(anchor.x as u16, anchor.y as u16, 1, 1),
                );
                f.render_widget(
                    Paragraph::new(format!(
                        "{}: {} · {}",
                        tr("그림자", "Shadow"),
                        mode.as_str(),
                        if edge {
                            tr("모서리", "edge")
                        } else {
                            tr("일반 위치", "normal")
                        }
                    ))
                    .style(styles.text_on_surface("hint", "surface").unwrap()),
                    Rect::new(x as u16 + 2, y as u16 + 16, 34, 1),
                );
            }
        }
    })?;
    snapshot::write(&output, terminal.backend().buffer())?;
    println!("12 palette references: {}", output.display());
    Ok(())
}
