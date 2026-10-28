use tuivory::collections::{ListItem, ListModel, SearchPicker};
fn items() -> Vec<ListItem> {
    vec![
        ListItem {
            id: "g".into(),
            separator: true,
            ..Default::default()
        },
        ListItem {
            id: "go".into(),
            label: "Go".into(),
            secondary: "module".into(),
            ..Default::default()
        },
        ListItem {
            id: "x".into(),
            label: "disabled".into(),
            disabled: true,
            ..Default::default()
        },
        ListItem {
            id: "rust".into(),
            label: "Rust".into(),
            secondary: "crate".into(),
            ..Default::default()
        },
    ]
}
#[test]
fn list_and_pending_picker() {
    let mut m = ListModel::new(items()).unwrap();
    assert_eq!(m.focused, "go");
    m.handle("next", 3);
    assert_eq!(m.focused, "rust");
    assert!(m.selected.is_empty());
    m.handle("select", 3);
    m.set_query("GO");
    assert_eq!(m.focused, "go");
    assert_eq!(m.selected, "rust");
    let bad = vec![
        ListItem {
            id: "a".into(),
            ..Default::default()
        };
        2
    ];
    assert!(m.set_items(bad).is_err());
    assert_eq!(m.focused, "go");
    let mut p = SearchPicker::new(items()).unwrap();
    p.handle("open", "", 4);
    p.handle("insert", "Rust", 4);
    assert!(p.value.is_empty());
    assert_eq!(p.list.focused, "rust");
    assert_eq!(p.handle("activate", "", 4).kind, "change");
    assert_eq!(p.value, "rust");
    assert!(!p.open);
    p.handle("open", "", 4);
    p.handle("insert", "Go", 4);
    p.handle("cancel", "", 4);
    assert_eq!(p.value, "rust");
    p.handle("open", "", 4);
    p.handle("insert", &"한".repeat(40), 4);
    let rows = p.layout(12, 4, true);
    assert!(rows[0].text.contains('|'));
    assert!(
        rows.iter()
            .all(|r| tuivory::components::cells(&r.text) <= 12)
    );
    assert!(p.click("x").kind.is_empty());
}
