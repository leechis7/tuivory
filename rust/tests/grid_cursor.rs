use tuivory::grid::*;
#[cfg(feature = "ratatui")]
use tuivory::interaction::ControlState;
fn grid() -> Grid {
    let rows = MemoryRows::new(
        (0..3)
            .map(|i| GridRecord {
                id: format!("r{i}"),
                cells: [
                    ("name".into(), "한글👩‍💻e\u{301}".into()),
                    ("value".into(), "123".into()),
                ]
                .into(),
                ..Default::default()
            })
            .collect(),
    )
    .unwrap();
    let mut g = Grid::new(
        vec![
            GridColumn {
                id: "name".into(),
                width: 12,
                editable: true,
                ..Default::default()
            },
            GridColumn {
                id: "value".into(),
                width: 8,
                editable: true,
                ..Default::default()
            },
        ],
        Box::new(rows),
    )
    .unwrap();
    g.set_edit_options(GridEditOptions {
        enabled: true,
        allow_null: true,
        ..Default::default()
    });
    g
}
#[test]
fn cursor_and_mouse_share_grapheme_viewport() {
    let mut g = grid();
    g.begin_edit("A한글👩‍💻e\u{301}Z");
    g.edit_input("home", "");
    g.edit_input("right", "");
    let c = g.edit_cursor(40, 8).unwrap();
    assert_eq!(
        g.pointer("click", c.x as isize, c.y as isize, 40, 8, false)
            .kind,
        "edit_select"
    );
    g.edit_input("insert", "X");
    assert_eq!(g.edit_session().unwrap().value.text, "AX한글👩‍💻e\u{301}Z");
    for w in 0..50 {
        for h in 0..8 {
            if let Some(c) = g.edit_cursor(w, h) {
                assert!(c.x + c.width <= w && c.y < h);
                assert!(c.width > 0)
            }
        }
    }
}
#[cfg(feature = "ratatui")]
#[test]
fn real_backend_cursor_lifecycle_all_palettes() {
    use tuivory::{
        ColorProfile, Theme,
        ui::{
            Terminal,
            backend::TestBackend,
            components::{GridWidget, Styles},
            layout::Rect,
        },
    };
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            for ascii in [false, true] {
                let styles = Styles::new(theme, profile).unwrap();
                let mut g = grid();
                let mut opts = grid_preset("data").unwrap();
                opts.ascii = ascii;
                g.set_options(opts).unwrap();
                g.set_cell_info(|_, c| GridCellInfo {
                    state: ControlState {
                        edited: c.id == "name",
                        ..Default::default()
                    },
                    ..Default::default()
                });
                g.set_column_options(
                    "name",
                    GridColumnOptions {
                        align: "right".into(),
                        overflow: "scroll".into(),
                        ..Default::default()
                    },
                )
                .unwrap();
                g.handle("cell_pan_right", 9);
                let mut term = Terminal::new(TestBackend::new(80, 14)).unwrap();
                let draw = |g: &Grid,
                            t: &mut Terminal<TestBackend>,
                            w: u16,
                            h: u16,
                            focused: bool,
                            want: bool| {
                    t.draw(|f| {
                        GridWidget {
                            model: g,
                            styles: &styles,
                            focused,
                        }
                        .render_frame(f, Rect::new(3, 2, w, h))
                    })
                    .unwrap();
                    assert_eq!(
                        t.backend().cursor_visible(),
                        want,
                        "{theme:?}/{profile:?}/{ascii}: {w}x{h}"
                    );
                    if want {
                        let c = g.edit_cursor(w.into(), h.into()).unwrap();
                        let p = t.backend().cursor_position();
                        assert_eq!((p.x, p.y), (3 + c.x as u16, 2 + c.y as u16));
                    }
                    for l in g.layout(w.into(), h.into()) {
                        if l.id == "r0" {
                            for s in l.spans {
                                if s.role != "grid.divider" {
                                    assert!(!s.text.contains('|'), "fake caret: {}", s.text)
                                }
                            }
                        }
                    }
                };
                draw(&g, &mut term, 60, 9, true, false);
                g.begin_edit("");
                draw(&g, &mut term, 60, 9, true, true);
                g.edit_input("home", "");
                draw(&g, &mut term, 60, 9, true, true);
                let c = g.edit_cursor(60, 9).unwrap();
                assert_eq!(c.width, 2);
                assert_eq!(
                    term.backend().buffer()[(3 + c.x as u16, 2 + c.y as u16)].symbol(),
                    "한"
                );
                g.edit_input("end", "");
                for w in [40, 20, 8, 3, 1, 0, 60] {
                    let visible = g.edit_cursor(w, 9).is_some();
                    draw(&g, &mut term, w as u16, 9, true, visible)
                }
                draw(&g, &mut term, 60, 9, false, false);
                term.draw(|f| {
                    f.set_cursor_position((1, 1));
                    GridWidget {
                        model: &g,
                        styles: &styles,
                        focused: false,
                    }
                    .render_frame(f, Rect::new(3, 2, 60, 9));
                })
                .unwrap();
                assert_eq!(term.backend().cursor_position().x, 1);
                assert!(term.backend().cursor_visible());
                g.edit_input("null", "");
                draw(&g, &mut term, 60, 9, true, false);
                g.edit_input("null", "");
                draw(&g, &mut term, 60, 9, true, true);
                g.edit_input("submit", "");
                let id = g.edit_session().unwrap().id;
                draw(&g, &mut term, 60, 9, true, false);
                assert!(g.resolve_edit(id, "retry", None));
                draw(&g, &mut term, 60, 9, true, true);
                g.focus("r2", "name");
                draw(&g, &mut term, 60, 2, true, false);
                g.focus("r0", "name");
                draw(&g, &mut term, 60, 9, true, true);
                g.invalidate_requests();
                draw(&g, &mut term, 60, 9, true, false);
                g.begin_edit("x");
                g.cancel_edit();
                draw(&g, &mut term, 60, 9, true, false);
                g.begin_edit("x");
                g.edit_input("submit", "");
                let id = g.edit_session().unwrap().id;
                assert!(g.resolve_edit(id, "", None));
                draw(&g, &mut term, 60, 9, true, false);
                g.begin_edit("x");
                g.edit_input("home", "");
                term.backend_mut().resize(4, 14);
                term.resize(Rect::new(0, 0, 4, 14)).unwrap();
                draw(&g, &mut term, 60, 9, true, false);
                term.backend_mut().resize(80, 14);
                term.resize(Rect::new(0, 0, 80, 14)).unwrap();
                draw(&g, &mut term, 60, 9, true, true);
                g.set_source(Box::new(MemoryRows::new(vec![]).unwrap()));
                draw(&g, &mut term, 60, 9, true, false);
            }
        }
    }
}
#[test]
fn shared_cursor_cases() {
    let d: serde_json::Value =
        serde_json::from_str(include_str!("data/grid-cursor-cases.json")).unwrap();
    for c in d["cases"].as_array().unwrap() {
        let width = c["width"].as_u64().unwrap() as usize;
        let rows = MemoryRows::new(vec![GridRecord {
            id: "r".into(),
            cells: [("c".into(), c["text"].as_str().unwrap().into())].into(),
            ..Default::default()
        }])
        .unwrap();
        let mut g = Grid::new(
            vec![GridColumn {
                id: "c".into(),
                width,
                editable: true,
                ..Default::default()
            }],
            Box::new(rows),
        )
        .unwrap();
        g.set_options(GridOptions {
            hide_markers: true,
            hide_header: true,
            ..Default::default()
        })
        .unwrap();
        g.set_edit_options(GridEditOptions {
            enabled: true,
            ..Default::default()
        });
        g.begin_edit("");
        g.edit_input("select_all", "");
        g.edit_input("left", "");
        for _ in 0..c["cursor"].as_u64().unwrap() {
            g.edit_input("right", "");
        }
        let pos = g.edit_cursor(width, 2).unwrap();
        assert_eq!(pos.x, c["x"].as_u64().unwrap() as usize, "{}", c["id"]);
        assert_eq!(pos.y, 0);
        assert_eq!(
            g.layout(width, 2)[0].spans[0].text.trim_end_matches(' '),
            c["visible_text"].as_str().unwrap(),
            "{}",
            c["id"]
        );
    }
}
