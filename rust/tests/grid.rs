use std::{cell::Cell, rc::Rc};
use tuivory::{
    grid::{Grid, GridColumn, GridRecord, GridSource, MemoryRows},
    interaction::ControlState,
};
struct Virtual {
    calls: Rc<Cell<usize>>,
}
impl GridSource for Virtual {
    fn len(&self) -> usize {
        100000
    }
    fn index_of(&self, id: &str) -> Option<usize> {
        id.strip_prefix("row-")?
            .parse::<usize>()
            .ok()
            .filter(|n| *n < self.len())
    }
    fn row(&self, n: usize) -> GridRecord {
        assert!(n < self.len());
        self.calls.set(self.calls.get() + 1);
        GridRecord {
            id: format!("row-{n}"),
            cells: [
                ("name".into(), format!("한글{n}")),
                ("value".into(), n.to_string()),
            ]
            .into(),
            state: ControlState {
                disabled: n == 1,
                ..Default::default()
            },
        }
    }
}
#[test]
fn virtual_grid_and_requests() {
    let calls = Rc::new(Cell::new(0));
    let mut g = Grid::new(
        vec![
            GridColumn {
                id: "name".into(),
                label: "Name".into(),
                width: 8,
                editable: true,
            },
            GridColumn {
                id: "value".into(),
                label: "Value".into(),
                width: 8,
                editable: false,
            },
        ],
        Box::new(Virtual {
            calls: calls.clone(),
        }),
    )
    .unwrap();
    calls.set(0);
    let lines = g.layout(18, 7);
    assert_eq!(lines.len(), 7);
    assert!(calls.get() <= 10);
    g.handle("down", 7);
    assert_eq!(g.row_id, "row-2");
    g.handle("select", 7);
    assert_eq!(g.handle("copy", 7).text, "한글2");
    assert_eq!(g.handle("activate", 7).kind, "edit");
    g.handle("right", 7);
    assert!(g.handle("activate", 7).kind.is_empty());
    g.handle("last", 7);
    assert_eq!(g.row_id, "row-99999");
    assert!(
        g.layout(8, 4)
            .iter()
            .flat_map(|r| &r.spans)
            .all(|s| s.start + s.width <= 8)
    );
    assert_eq!(g.request_filter("query").text, "query");
    assert_eq!(g.handle("sort", 4).direction, "asc");
    assert!(!g.resize_column("name", 0));
    assert!(g.resize_column("name", 20));
}
#[test]
fn stable_ids_and_empty() {
    let cols = vec![GridColumn {
        id: "n".into(),
        width: 8,
        editable: true,
        ..Default::default()
    }];
    let a = GridRecord {
        id: "a".into(),
        cells: [("n".into(), "A".into())].into(),
        ..Default::default()
    };
    let b = GridRecord {
        id: "b".into(),
        cells: [("n".into(), "B".into())].into(),
        state: ControlState {
            read_only: true,
            ..Default::default()
        },
    };
    let mut g = Grid::new(
        cols,
        Box::new(MemoryRows::new(vec![a.clone(), b.clone()]).unwrap()),
    )
    .unwrap();
    g.focus("b", "n");
    assert!(g.handle("activate", 3).kind.is_empty());
    g.set_source(Box::new(MemoryRows::new(vec![b, a]).unwrap()));
    assert_eq!(g.row_id, "b");
    g.set_source(Box::new(MemoryRows::new(vec![]).unwrap()));
    assert_eq!(g.layout(20, 3).len(), 2);
    assert_eq!(g.handle("sort", 3).kind, "sort");
    assert!(
        MemoryRows::new(vec![
            GridRecord {
                id: "a".into(),
                ..Default::default()
            };
            2
        ])
        .is_err()
    );
}

#[test]
fn options_preserve_raw_ids_range_and_lazy_requests() {
    use tuivory::grid::{GridCellInfo, GridColumnOptions, GridRange, grid_preset};
    let calls = Rc::new(Cell::new(0));
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
                ..Default::default()
            },
        ],
        Box::new(Virtual {
            calls: calls.clone(),
        }),
    )
    .unwrap();
    g.set_cell_info(|_, _| GridCellInfo {
        display: "formatted".into(),
        has_display: true,
        metadata: "TEXT".into(),
        state: ControlState {
            edited: true,
            ..Default::default()
        },
        ..Default::default()
    });
    let range = GridRange {
        anchor_row: "row-0".into(),
        anchor_column: "name".into(),
        end_row: "row-2".into(),
        end_column: "value".into(),
    };
    assert!(g.select_range(range.clone()));
    g.focus("row-2", "value");
    let before = g.handle("copy_range", 8).text;
    assert_eq!(before, "한글0\t0\n한글1\t1\n한글2\t2");
    for preset in ["data", "simple", "data"] {
        g.set_options(grid_preset(preset).unwrap()).unwrap();
        g.layout(60, 9);
        assert_eq!(g.selected_range(), &range);
        assert_eq!(g.row_id, "row-2");
        assert_eq!(g.column_id, "value");
        assert_eq!(g.handle("copy_range", 8).text, before);
        assert_eq!(g.columns()[0].width, 12);
    }
    let mut o = g.options().clone();
    o.padding = 99;
    assert!(g.set_options(o).is_err());
    assert_eq!(g.options().padding, 1);
    g.set_column_options(
        "name",
        GridColumnOptions {
            auto_fit: true,
            min_width: 4,
            max_width: 20,
            ..Default::default()
        },
    )
    .unwrap();
    calls.set(0);
    g.layout(80, 12);
    assert!(calls.get() <= 13, "viewport reads: {}", calls.get());
    assert!(g.select_range(GridRange {
        end_row: "row-99999".into(),
        ..range
    }));
    calls.set(0);
    assert_eq!(g.handle("copy_range", 12).kind, "copy_request");
    assert!(calls.get() <= 3);
    g.request_filter("old");
    let old = g.revision();
    g.request_filter("new");
    assert!(!g.apply_source(old, Box::new(MemoryRows::new(vec![]).unwrap())));
    assert!(g.apply_source(g.revision(), Box::new(MemoryRows::new(vec![]).unwrap())));
    assert!(!g.apply_source(g.revision(), Box::new(MemoryRows::new(vec![]).unwrap())));
}
#[test]
fn configured_unicode_layouts_and_pointer() {
    use tuivory::grid::{GridCellInfo, GridColumnOptions, grid_preset};
    let mut g = Grid::new(
        vec![
            GridColumn {
                id: "name".into(),
                label: "Name".into(),
                width: 12,
                editable: true,
            },
            GridColumn {
                id: "value".into(),
                label: "Value".into(),
                width: 8,
                editable: true,
            },
        ],
        Box::new(
            MemoryRows::new(
                (0..3)
                    .map(|n| GridRecord {
                        id: format!("r{n}"),
                        cells: [
                            ("name".into(), "한글😀e\u{301} long".into()),
                            ("value".into(), "003".into()),
                        ]
                        .into(),
                        ..Default::default()
                    })
                    .collect(),
            )
            .unwrap(),
        ),
    )
    .unwrap();
    g.set_cell_info(|r, c| GridCellInfo {
        state: ControlState {
            edited: r.id == "r0",
            read_only: c.id == "value",
            ..Default::default()
        },
        numeric: c.id == "value",
        metadata: "TEXT".into(),
        ..Default::default()
    });
    for ascii in [false, true] {
        for density in ["compact", "normal", "comfortable"] {
            let mut o = grid_preset("data").unwrap().with_density(density).unwrap();
            o.ascii = ascii;
            o.horizontal_lines = true;
            o.striped = true;
            g.set_options(o).unwrap();
            for overflow in ["ellipsis", "clip", "scroll"] {
                g.set_column_options(
                    "name",
                    GridColumnOptions {
                        align: "center".into(),
                        overflow: overflow.into(),
                        ..Default::default()
                    },
                )
                .unwrap();
                for w in 0..80 {
                    for h in 0..12 {
                        let lines = g.layout(w, h);
                        assert!(lines.len() <= h);
                        for s in lines.iter().flat_map(|r| &r.spans) {
                            assert!(s.start + s.width <= w);
                            assert!(
                                tuivory::components::cells(&s.text) <= s.width,
                                "{w} {h} {s:?}"
                            );
                        }
                    }
                }
            }
        }
    }
    g.set_options(grid_preset("data").unwrap()).unwrap();
    let geo = g.geometry(60, 8);
    let x = geo.columns[0].start as isize;
    g.pointer("move", x, 2, 60, 8, false);
    assert_eq!(g.row_id, "r0");
    g.pointer("down", x, 1, 60, 8, false);
    g.pointer("move", geo.columns[1].start as isize, 3, 60, 8, false);
    g.pointer("up", 0, 0, 60, 8, false);
    assert_eq!(g.selected_range().end_row, "r2");
    g.pointer("down", x, 1, 60, 8, false);
    g.pointer("up", x, 1, 60, 8, false);
    assert_eq!(g.selection_mode(), "cell");
    g.focus("r0", "value");
    assert!(g.handle("activate", 8).kind.is_empty());
    g.focus("r0", "name");
    assert_eq!(g.handle("activate", 8).kind, "edit");
    assert!(
        g.status_items()
            .iter()
            .any(|s| s.id == "meta" && s.text == "TEXT")
    );
}

#[cfg(feature = "ratatui")]
#[test]
fn rich_grid_backend_output_and_overlay_restoration() {
    use ratatui::{Terminal, backend::TestBackend, layout::Rect, widgets::Paragraph};
    use tuivory::{
        ColorProfile, Theme,
        grid::grid_preset,
        ratatui::{GridWidget, Styles},
    };
    let mut g = Grid::new(
        vec![GridColumn {
            id: "name".into(),
            label: "Name".into(),
            width: 12,
            editable: true,
        }],
        Box::new(
            MemoryRows::new(vec![GridRecord {
                id: "a".into(),
                cells: [("name".into(), "한글😀e\u{301}".into())].into(),
                ..Default::default()
            }])
            .unwrap(),
        ),
    )
    .unwrap();
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            for ascii in [false, true] {
                let styles = Styles::new(theme, profile).unwrap();
                let mut o = grid_preset("data").unwrap();
                o.ascii = ascii;
                g.set_options(o).unwrap();
                let area = Rect::new(3, 2, 24, 7);
                let mut terminal = Terminal::new(TestBackend::new(32, 12)).unwrap();
                let draw = |f: &mut ratatui::Frame<'_>, overlay: bool| {
                    for y in 0..12 {
                        f.render_widget(Paragraph::new("界".repeat(16)), Rect::new(0, y, 32, 1));
                    }
                    f.render_widget(
                        GridWidget {
                            model: &g,
                            styles: &styles,
                            focused: true,
                        },
                        area,
                    );
                    if overlay {
                        f.render_widget(Paragraph::new("overlay"), Rect::new(4, 3, 10, 2));
                    }
                };
                terminal.draw(|f| draw(f, false)).unwrap();
                let before = terminal.backend().buffer().clone();
                let x = area.x + g.geometry(24, 7).gutter as u16 - 1;
                assert_eq!(before[(x, 2)].symbol(), if ascii { "|" } else { "│" });
                assert_eq!(before[(2, 2)].symbol(), " ");
                terminal.draw(|f| draw(f, true)).unwrap();
                terminal.draw(|f| draw(f, false)).unwrap();
                // TestBackend may retain hidden continuation cells after wide glyphs.
                // Compare terminal-visible leaders/styles, including repaired outside edges.
                let after = terminal.backend().buffer();
                for y in 0..12 {
                    let mut x = 0;
                    while x < 32 {
                        assert_eq!(
                            after[(x, y)],
                            before[(x, y)],
                            "{theme:?}/{profile:?} ({x},{y})"
                        );
                        x += (tuivory::components::cells(before[(x, y)].symbol()) as u16).max(1);
                    }
                }
            }
        }
    }
}
#[test]
fn viewport_does_not_jump_when_moving_up() {
    let mut g = Grid::new(
        vec![GridColumn {
            id: "name".into(),
            width: 12,
            ..Default::default()
        }],
        Box::new(Virtual {
            calls: Rc::new(Cell::new(0)),
        }),
    )
    .unwrap();
    g.set_options(
        tuivory::grid::grid_preset("data")
            .unwrap()
            .with_density("comfortable")
            .unwrap(),
    )
    .unwrap();
    g.layout(40, 12);
    g.handle("page_down", 12);
    assert_eq!(g.row_id, "row-5");
    g.handle("last", 12);
    let before = g.geometry(40, 12).top;
    g.handle("up", 12);
    assert_eq!(g.geometry(40, 12).top, before);
}
