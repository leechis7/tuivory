#![cfg(feature = "ratatui")]
#![deny(deprecated)]
use ratatui::{buffer::Buffer, layout::Rect, widgets::Widget};
use tuivory::{
    ColorProfile, Theme,
    menu::{Menu, MenuItem},
    ratatui::{MenuBarWidget, MenuPopupWidget, MenuWidget, Styles},
};
fn menu() -> Menu {
    let mut m = Menu::new(vec![
        MenuItem {
            id: "root".into(),
            label: "File".into(),
            ..Default::default()
        },
        MenuItem {
            id: "open".into(),
            parent: "root".into(),
            label: "열기界".into(),
            ..Default::default()
        },
    ])
    .unwrap();
    m.open("root", "editor");
    m
}
#[allow(deprecated)] // Exercise old literals only; the replacement tests deny this lint.
fn legacy(kind: u8, m: &mut Menu, s: &Styles, ascii: bool) -> Buffer {
    let area = Rect::new(0, 0, 36, 10);
    let mut b = Buffer::empty(area);
    match kind {
        0 => MenuWidget {
            model: m,
            styles: s,
            ascii,
            focused: true,
        }
        .render(area, &mut b),
        1 => MenuBarWidget {
            model: m,
            styles: s,
            focused: true,
        }
        .render(area, &mut b),
        _ => MenuPopupWidget {
            model: m,
            styles: s,
            title: "Menu",
            ascii,
            focused: true,
            padding: 2,
        }
        .render(area, &mut b),
    };
    b
}
#[test]
fn preferred_constructors_preserve_legacy_output_without_warnings() {
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            for ascii in [false, true] {
                for kind in 0..3 {
                    let styles = Styles::new(theme, profile).unwrap();
                    let mut old = menu();
                    let expected = legacy(kind, &mut old, &styles, ascii);
                    let mut current = menu();
                    let area = Rect::new(0, 0, 36, 10);
                    let mut actual = Buffer::empty(area);
                    match kind {
                        0 => MenuWidget::new(&mut current, &styles)
                            .ascii(ascii)
                            .render(area, &mut actual),
                        1 => MenuBarWidget::new(&mut current, &styles).render(area, &mut actual),
                        _ => MenuPopupWidget::new(&mut current, &styles, "Menu")
                            .ascii(ascii)
                            .padding(2)
                            .render(area, &mut actual),
                    };
                    assert_eq!(actual, expected);
                    assert_eq!(current.return_id(), "editor");
                    assert_eq!(current.focused_id(), old.focused_id());
                }
            }
        }
    }
}
fn grid() -> tuivory::grid::Grid {
    use tuivory::grid::*;
    let rows = MemoryRows::new(vec![
        GridRecord {
            id: "r1".into(),
            cells: [("name".into(), "A".into()), ("value".into(), "1".into())].into(),
            ..Default::default()
        },
        GridRecord {
            id: "r2".into(),
            cells: [("name".into(), "B".into()), ("value".into(), "2".into())].into(),
            ..Default::default()
        },
    ])
    .unwrap();
    Grid::new(
        vec![
            GridColumn {
                id: "name".into(),
                width: 12,
                ..Default::default()
            },
            GridColumn {
                id: "value".into(),
                width: 12,
                ..Default::default()
            },
        ],
        Box::new(rows),
    )
    .unwrap()
}
#[allow(deprecated)]
fn legacy_click(
    g: &mut tuivory::grid::Grid,
    row: &str,
    kind: &str,
    x: usize,
) -> tuivory::grid::GridEvent {
    g.click(row, kind, x, 40, 8)
}
#[test]
fn pointer_migration_preserves_clicks_and_documents_mouse_disable_difference() {
    for header in [false, true] {
        let mut old = grid();
        let mut current = grid();
        let geo = current.geometry(40, 8);
        let x = geo.columns[1].start;
        let y = if header { 0 } else { geo.header_rows };
        let a = legacy_click(&mut old, "r1", if header { "@header" } else { "" }, x);
        let b = current.pointer("click", x as isize, y as isize, 40, 8, false);
        assert_eq!(
            (a.kind, a.row_id, a.column_id, a.text, a.direction),
            (b.kind, b.row_id, b.column_id, b.text, b.direction)
        );
        assert_eq!(old.row_id, current.row_id);
        assert_eq!(old.column_id, current.column_id);
    }
    let mut old = grid();
    let mut current = grid();
    let mut options = old.options().clone();
    options.disable_mouse = true;
    old.set_options(options.clone()).unwrap();
    current.set_options(options).unwrap();
    let geo = current.geometry(40, 8);
    let x = geo.columns[1].start;
    assert!(!legacy_click(&mut old, "r2", "", x).kind.is_empty());
    assert!(
        current
            .pointer("click", x as isize, geo.header_rows as isize, 40, 8, false)
            .kind
            .is_empty()
    );
    assert!(current.focus("r2", "value"));
    assert!(!current.handle("select", 8).kind.is_empty());
}
