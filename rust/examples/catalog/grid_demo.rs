use tuivory::{grid::*, interaction::ControlState};
fn tr(en: bool, ko: &str, english: &str) -> String {
    if en { english } else { ko }.into()
}
pub fn sample(en: bool) -> Grid {
    let columns = [
        ("id", "ID", "ID", 5, false),
        ("name", "이름", "Name", 18, true),
        ("email", "이메일", "Email", 25, true),
        ("value", "금액", "Amount", 10, true),
        ("state", "상태", "State", 10, false),
    ]
    .into_iter()
    .map(|(id, ko, english, width, editable)| GridColumn {
        id: id.into(),
        label: tr(en, ko, english),
        width,
        editable,
    })
    .collect();
    let rows = [
        ("김하늘", "Haneul Kim"),
        ("이수정", "Sujeong Lee"),
        ("박지수", "Jisu Park"),
        ("최민준", "Minjun Choi"),
        ("정유진", "Yujin Jung"),
    ]
    .into_iter()
    .enumerate()
    .map(|(n, (ko, english))| {
        let id = (n + 1).to_string();
        GridRecord {
            id: format!("row-{id}"),
            cells: [
                ("id".into(), id.clone()),
                ("name".into(), tr(en, ko, english)),
                ("email".into(), format!("user{id}@example.test")),
                (
                    "value".into(),
                    ["12500.00", "24000.00", "", "950.00", "3100.50"][n].into(),
                ),
                ("state".into(), tr(en, "준비", "ready")),
            ]
            .into(),
            ..Default::default()
        }
    })
    .collect();
    let mut g = Grid::new(columns, Box::new(MemoryRows::new(rows).unwrap())).unwrap();
    g.focus("row-2", "name");
    g.handle("select", 12);
    g
}
pub fn configure(g: &mut Grid, en: bool) {
    for (key, ko, english) in [
        ("row", "행", "R"),
        ("column", "열", "C"),
        ("selected", "선택", "selected"),
        ("loading", "로딩", "loading"),
        ("more", "추가", "more"),
        ("sort", "정렬", "sort"),
        ("filter", "필터", "filter"),
    ] {
        g.labels.insert(key.into(), tr(en, ko, english));
    }
    g.set_cell_info(|r, c| GridCellInfo {
        null: c.id == "value" && r.cells.get(&c.id).is_some_and(String::is_empty),
        numeric: c.id == "value",
        metadata: match c.id.as_str() {
            "id" => "INTEGER",
            "value" => "DECIMAL",
            _ => "TEXT",
        }
        .into(),
        state: ControlState {
            edited: r.id == "row-2" && c.id == "name",
            read_only: !c.editable,
            ..Default::default()
        },
        ..Default::default()
    });
    g.set_column_options(
        "value",
        GridColumnOptions {
            align: "numeric".into(),
            min_width: 4,
            max_width: 40,
            ..Default::default()
        },
    )
    .unwrap();
}
