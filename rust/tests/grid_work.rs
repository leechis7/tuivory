use tuivory::{grid::*, input::InputEvent, interaction::ControlState};
fn rows() -> MemoryRows {
    MemoryRows::new(vec![
        GridRecord {
            id: "a".into(),
            cells: [
                ("name".into(), "한글😀e\u{301} long".into()),
                ("value".into(), "1\t2".into()),
            ]
            .into(),
            ..Default::default()
        },
        GridRecord {
            id: "b".into(),
            cells: [
                ("name".into(), "B\n\"C".into()),
                ("value".into(), "".into()),
            ]
            .into(),
            ..Default::default()
        },
        GridRecord {
            id: "c".into(),
            cells: [("name".into(), "C".into()), ("value".into(), "003".into())].into(),
            ..Default::default()
        },
    ])
    .unwrap()
}
fn grid() -> Grid {
    let mut g = Grid::new(
        vec![
            GridColumn {
                id: "name".into(),
                label: "Name".into(),
                width: 18,
                editable: true,
            },
            GridColumn {
                id: "value".into(),
                label: "Value".into(),
                width: 8,
                editable: true,
            },
        ],
        Box::new(rows()),
    )
    .unwrap();
    g.set_edit_options(GridEditOptions {
        enabled: true,
        start_typing: true,
        allow_null: true,
        ..Default::default()
    });
    g
}
fn key(k: &str, mods: &[&str]) -> InputEvent {
    InputEvent {
        kind: "key".into(),
        key: k.into(),
        modifiers: mods.iter().map(|m| m.to_string()).collect(),
        ..Default::default()
    }
}
#[test]
fn approval_retry_cancel_and_stale() {
    let mut g = grid();
    let raw = g.handle("copy", 8).text;
    assert_eq!(g.input(&key("enter", &[]), 60, 8).kind, "edit_begin");
    g.edit_input("select_all", "");
    g.edit_input("insert", "새값👩‍💻e\u{301}");
    g.edit_input("left", "");
    g.edit_input("backspace", "");
    assert_eq!(g.edit_session().unwrap().value.text, "새값e\u{301}");
    assert_eq!(g.input(&key("tab", &[]), 60, 8).kind, "edit_submit");
    let id = g.edit_session().unwrap().id;
    g.edit_input("insert", "blocked");
    assert_eq!(g.column_id, "name");
    assert!(!g.resolve_edit(id + 1, "", None));
    assert!(g.resolve_edit(id, "거절", None));
    let e = g.edit_session().unwrap();
    assert!(!e.pending);
    assert_eq!(e.error, "거절");
    g.edit_input("null", "");
    assert!(g.edit_session().unwrap().value.null);
    g.edit_input("next", "");
    let id = g.edit_session().unwrap().id;
    assert!(g.resolve_edit(id, "", None));
    assert_eq!(g.edit_session().unwrap().column_id, "value");
    g.input(&key("escape", &[]), 60, 8);
    g.focus("a", "name");
    assert_eq!(g.handle("copy", 8).text, raw);
    g.begin_edit("");
    g.edit_input("submit", "");
    let id = g.edit_session().unwrap().id;
    g.request_filter("new");
    assert!(g.edit_session().is_none());
    assert!(!g.resolve_edit(id, "", None));
    g.input(&key("escape", &[]), 60, 8);
    g.begin_edit("x");
    g.edit_input("submit", "");
    let id = g.edit_session().unwrap().id;
    g.set_source(Box::new(MemoryRows::new(vec![]).unwrap()));
    assert!(!g.resolve_edit(id, "", None));
}
#[test]
fn prepare_and_atomic_source_acceptance() {
    let mut g = grid();
    g.set_edit_options(GridEditOptions {
        enabled: true,
        prepare: Some(Box::new(|_, c| {
            if c.id == "value" {
                Some(GridValue {
                    text: "typed".into(),
                    null: true,
                })
            } else {
                None
            }
        })),
        ..Default::default()
    });
    assert!(!g.begin_edit(""));
    g.focus("a", "value");
    assert!(g.begin_edit(""));
    g.edit_input("null", "");
    assert!(g.edit_session().unwrap().value.null);
    g.edit_input("submit", "");
    let id = g.edit_session().unwrap().id;
    let source = MemoryRows::new(vec![GridRecord {
        id: "a".into(),
        cells: [("value".into(), "accepted".into())].into(),
        ..Default::default()
    }])
    .unwrap();
    assert!(g.resolve_edit(id, "", Some(Box::new(source))));
    assert_eq!(g.handle("copy", 8).text, "accepted")
}
#[test]
fn columns_view_state_and_narrow_geometry() {
    let mut g = grid();
    assert!(g.pin_column("name", "left"));
    let saved = g.save_view_state();
    assert!(g.move_column("value", 0));
    assert!(g.hide_column("name", true));
    g.restore_view_state(saved.clone()).unwrap();
    assert_eq!(saved.columns, g.column_layout());
    assert_eq!(saved.row_id, g.row_id);
    let mut bad = saved.clone();
    bad.columns[1].id = "missing".into();
    assert!(g.restore_view_state(bad).is_err());
    assert_eq!(saved.columns, g.column_layout());
    for w in 0..70 {
        let geo = g.geometry(w, 5);
        for s in geo.columns {
            assert!(s.start + s.width <= w)
        }
    }
    assert!(!g.hide_column("value", true) || !g.hide_column("name", true));
}
#[test]
fn quoted_paste_and_atomic_permissions() {
    let mut g = grid();
    let raw = g.handle("copy", 6).text;
    let p = g
        .request_paste(
            "\"한글\t셀\"\t\"줄1\n줄2\"\n\"\"\tNULL",
            GridPasteOptions {
                parse_null: true,
                null_text: "NULL".into(),
                ..Default::default()
            },
        )
        .unwrap();
    assert_eq!(p.changes.len(), 4);
    assert_eq!(p.changes[0].value.text, "한글\t셀");
    assert_eq!(p.changes[1].value.text, "줄1\n줄2");
    assert!(p.changes[3].value.null);
    assert!(!g.resolve_paste(p.id + 1, None));
    assert!(g.resolve_paste(p.id, None));
    assert_eq!(g.handle("copy", 6).text, raw);
    for t in ["\"unterminated", "a\tb\tc", "a\tb\nc", "a\nb\nc\nd"] {
        assert!(
            g.request_paste(t, GridPasteOptions::default()).is_err(),
            "{t}"
        )
    }
    g.set_cell_info(|_, c| GridCellInfo {
        state: ControlState {
            read_only: c.id == "value",
            ..Default::default()
        },
        ..Default::default()
    });
    assert!(
        g.request_paste("a\tb", GridPasteOptions::default())
            .is_err()
    );
    let p = g.request_paste("a", GridPasteOptions::default()).unwrap();
    g.request_filter("new");
    assert!(!g.resolve_paste(p.id, None));
}
#[test]
fn find_details_and_independent_gutter() {
    let mut g = grid();
    g.set_find("한글", GridFindOptions::default());
    assert_eq!(
        g.find_next(false).unwrap(),
        GridCellRef {
            row_id: "a".into(),
            column_id: "name".into()
        }
    );
    assert_eq!(g.request_search("outside").kind, "search_request");
    assert!(g.open_details());
    for w in 0..65 {
        for h in 0..12 {
            let lines = g.layout(w, h);
            assert!(lines.len() <= h, "{w}x{h}");
            for l in lines {
                for s in l.spans {
                    assert!(s.start + s.width <= w);
                    assert!(
                        tuivory::components::cells(&s.text) <= s.width,
                        "{w}x{h}: {s:?}"
                    )
                }
            }
        }
    }
    g.close_details();
    g.set_options(grid_preset("data").unwrap()).unwrap();
    g.set_row_edited(|r| r.id == "a");
    g.set_cell_info(|_, c| GridCellInfo {
        state: ControlState {
            edited: c.id == "name",
            ..Default::default()
        },
        ..Default::default()
    });
    for l in g.layout(60, 8) {
        if l.id == "a" {
            for s in l.spans {
                if s.start == 0 {
                    assert!(s.text.contains('*'))
                }
                if s.start == g.geometry(60, 8).columns[1].start {
                    assert_ne!(s.role, "grid.edited")
                }
            }
        }
    }
}
#[cfg(feature = "ratatui")]
#[test]
fn physical_output_all_palettes() {
    use ratatui::{Terminal, backend::TestBackend, layout::Rect};
    use tuivory::{
        ColorProfile, Theme,
        ratatui::{GridWidget, Styles},
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
                let mut o = grid_preset("data").unwrap();
                o.ascii = ascii;
                g.set_options(o).unwrap();
                g.set_cell_info(|_, c| GridCellInfo {
                    state: ControlState {
                        edited: c.id == "name",
                        ..Default::default()
                    },
                    ..Default::default()
                });
                let mut t = Terminal::new(TestBackend::new(60, 10)).unwrap();
                let draw = |t: &mut Terminal<TestBackend>, g: &Grid| {
                    t.draw(|f| {
                        f.render_widget(
                            GridWidget {
                                model: g,
                                styles: &styles,
                                focused: true,
                            },
                            f.area(),
                        )
                    })
                    .unwrap();
                };
                draw(&mut t, &g);
                let text = |t: &Terminal<TestBackend>| {
                    let b = t.backend().buffer();
                    let mut out = String::new();
                    for y in 0..b.area.height {
                        let mut x = 0;
                        while x < b.area.width {
                            let symbol = b[(x, y)].symbol();
                            out.push_str(symbol);
                            x += tuivory::components::cells(symbol).max(1) as u16
                        }
                    }
                    out
                };
                assert!(text(&t).contains("한글"));
                g.begin_edit("");
                g.edit_input("select_all", "");
                g.edit_input("insert", "수정한글");
                draw(&mut t, &g);
                assert!(text(&t).contains("수정한글"));
                g.edit_input("submit", "");
                let id = g.edit_session().unwrap().id;
                g.resolve_edit(id, "검증 실패", None);
                draw(&mut t, &g);
                assert!(text(&t).contains("검증 실패"));
                g.cancel_edit();
                for w in [40, 20, 8, 3, 1, 60] {
                    t.backend_mut().resize(w, 10);
                    t.resize(Rect::new(0, 0, w, 10)).unwrap();
                    draw(&mut t, &g)
                }
            }
        }
    }
}

#[test]
fn shared_paste_cases() {
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("data/grid-work-cases.json")).unwrap();
    for c in fixture["cases"].as_array().unwrap() {
        let mut g = grid();
        let p = g.request_paste(c["text"].as_str().unwrap(), GridPasteOptions::default());
        assert_eq!(
            p.is_ok(),
            c["accepted"].as_bool().unwrap(),
            "{}: {p:?}",
            c["id"]
        );
        let values: Vec<_> = p
            .map(|p| p.changes.into_iter().map(|c| c.value.text).collect())
            .unwrap_or_default();
        assert_eq!(serde_json::json!(values), c["values"], "{}", c["id"]);
    }
}
#[test]
fn column_mouse_copy_and_view_json() {
    let mut g = grid();
    let geo = g.geometry(60, 8);
    g.pointer("down", geo.columns[0].start as isize, 0, 60, 8, false);
    assert_eq!(
        g.pointer("move", geo.columns[1].start as isize, 0, 60, 8, false)
            .kind,
        "columns"
    );
    g.pointer("up", 0, 0, 60, 8, false);
    assert_eq!(g.columns()[0].id, "value");
    g.hide_column("value", true);
    g.focus("a", "name");
    assert_eq!(g.handle("copy_row", 8).text, "한글😀e\u{301} long");
    let json = serde_json::to_string(&g.save_view_state()).unwrap();
    g.restore_view_state(serde_json::from_str(&json).unwrap())
        .unwrap();
    g.begin_edit("");
    let geo = g.geometry(60, 8);
    assert_eq!(
        g.pointer("click", geo.columns[0].start as isize, 1, 60, 8, false)
            .kind,
        "edit_select"
    );
    g.edit_input("submit", "");
    let id = g.edit_session().unwrap().id;
    let mut o = g.options().clone();
    o.disable_editing = true;
    g.set_options(o).unwrap();
    assert!(!g.resolve_edit(id, "", None));
}
#[cfg(feature = "ratatui")]
#[test]
fn edited_combinations_physical() {
    use ratatui::{Terminal, backend::TestBackend};
    use tuivory::{
        ColorProfile, Theme,
        ratatui::{GridWidget, Styles},
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
                for mask in 0..64 {
                    let mut g = grid();
                    let mut o = grid_preset("data").unwrap();
                    o.ascii = ascii;
                    o.preserve_edited = mask & 32 != 0;
                    g.set_options(o).unwrap();
                    g.set_cell_info(move |_, c| GridCellInfo {
                        null: mask & 16 != 0,
                        state: ControlState {
                            edited: c.id == "name",
                            disabled: mask & 1 != 0,
                            invalid: mask & 2 != 0,
                            read_only: mask & 4 != 0,
                            busy: mask & 8 != 0,
                            ..Default::default()
                        },
                        ..Default::default()
                    });
                    g.handle("select", 8);
                    let mut t = Terminal::new(TestBackend::new(60, 8)).unwrap();
                    t.draw(|f| {
                        f.render_widget(
                            GridWidget {
                                model: &g,
                                styles: &styles,
                                focused: true,
                            },
                            f.area(),
                        )
                    })
                    .unwrap();
                    let b = t.backend().buffer();
                    assert!(
                        b.content.iter().any(|c| c.symbol() == "*"),
                        "{theme:?}/{profile:?}/{ascii}/{mask}"
                    );
                    let span = &g.geometry(60, 8).columns[0];
                    let cell = &b[(span.start as u16 + 2, 1)];
                    assert_ne!(cell.fg, cell.bg, "{theme:?}/{profile:?}/{ascii}/{mask}")
                }
            }
        }
    }
}

#[test]
fn disabled_input_caret_and_removed_approval_row() {
    let mut g = grid();
    let mut o = g.options().clone();
    o.disable_keyboard = true;
    g.set_options(o.clone()).unwrap();
    assert!(g.input(&InputEvent::paste("x"), 60, 8).kind.is_empty());
    o.disable_keyboard = false;
    g.set_options(o).unwrap();
    g.begin_edit("abcdef");
    g.edit_input("home", "");
    for _ in 0..3 {
        g.edit_input("right", "");
    }
    let geo = g.geometry(60, 8);
    g.pointer("click", geo.columns[0].start as isize + 4, 1, 60, 8, false);
    g.edit_input("insert", "X");
    assert_eq!(g.edit_session().unwrap().value.text, "abcXdef");
    g.edit_input("next", "");
    let id = g.edit_session().unwrap().id;
    assert!(g.resolve_edit(id, "", Some(Box::new(MemoryRows::new(vec![]).unwrap()))));
    assert!(g.edit_session().is_none());
    let mut g = grid();
    g.set_edit_options(GridEditOptions {
        prepare: Some(Box::new(|_, _| None)),
        ..Default::default()
    });
    assert!(g.request_paste("x", GridPasteOptions::default()).is_err());
}

#[test]
fn paste_rechecks_host_eligibility() {
    let mut g = grid();
    let allowed = std::rc::Rc::new(std::cell::Cell::new(true));
    let flag = allowed.clone();
    g.set_edit_options(GridEditOptions {
        prepare: Some(Box::new(move |_, _| {
            if flag.get() {
                Some(GridValue::default())
            } else {
                None
            }
        })),
        ..Default::default()
    });
    let p = g.request_paste("x", GridPasteOptions::default()).unwrap();
    allowed.set(false);
    assert!(!g.resolve_paste(p.id, None));
}

#[test]
fn hiding_current_column_with_empty_source() {
    let mut g = grid();
    g.set_source(Box::new(MemoryRows::new(vec![]).unwrap()));
    assert!(g.hide_column("name", true));
    assert_eq!(g.column_id, "value");
}
