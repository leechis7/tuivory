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
