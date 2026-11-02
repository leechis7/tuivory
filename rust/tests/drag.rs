use tuivory::{
    components::{TabItem, TabState, Tabs},
    drag::*,
    tree::{Tree, TreeNode, TreeState},
};
#[cfg(feature = "ratatui")]
#[path = "../examples/playground/snapshot.rs"]
mod snapshot;

#[test]
fn temporary_edge_scroll() {
    let tabs = Tabs::new(
        (0..30)
            .map(|i| TabItem {
                id: i.to_string(),
                title: i.to_string(),
                ..TabItem::default()
            })
            .collect(),
    )
    .unwrap();
    let mut s = TabState {
        active: "0".into(),
        focused: "0".into(),
        first: 0,
    };
    tabs.layout(&mut s, 20);
    let before = s.clone();
    let mut d = DragState::default();
    let o = DragOptions {
        auto_scroll: true,
        ..DragOptions::default()
    };
    tabs.drag(
        &mut s,
        &mut d,
        DragPointer {
            action: DragAction::Down,
            x: 2,
            y: 0,
            width: 20,
            height: 1,
        },
        &o,
        None,
    );
    for _ in 0..6 {
        tabs.drag(
            &mut s,
            &mut d,
            DragPointer {
                action: DragAction::Move,
                x: 19,
                y: 0,
                width: 20,
                height: 1,
            },
            &o,
            None,
        );
    }
    assert_ne!(tabs.drag_layout(&mut s, &mut d, 20).cells[0].id, "0");
    assert_eq!(s, before);
    d.cancel();
    assert_eq!(s, before);
    let mut nodes = vec![TreeNode {
        id: "r".into(),
        ..TreeNode::default()
    }];
    nodes.extend((0..30).map(|i| TreeNode {
        id: i.to_string(),
        parent: "r".into(),
        ..TreeNode::default()
    }));
    let tree = Tree::new(nodes).unwrap();
    let mut state = TreeState {
        selected: "0".into(),
        expanded: ["r".into()].into(),
        ..TreeState::default()
    };
    tree.reconcile(&mut state, 4);
    let original = state.clone();
    tree.drag(
        &mut state,
        &mut d,
        DragPointer {
            action: DragAction::Down,
            x: 4,
            y: 1,
            width: 20,
            height: 4,
        },
        &o,
        None,
    );
    for _ in 0..6 {
        tree.drag(
            &mut state,
            &mut d,
            DragPointer {
                action: DragAction::Move,
                x: 15,
                y: 3,
                width: 20,
                height: 4,
            },
            &o,
            None,
        );
    }
    assert!(tree.drag_rows(&mut state, &mut d, 4).1 > 0);
    assert_eq!(state, original);
    d.cancel();
    assert_eq!(state, original);
}

#[cfg(feature = "ratatui")]
#[test]
fn localized_drag_snapshots() {
    let Some(directory) = std::env::var_os("TUIVORY_DRAG_SNAPSHOT_DIR") else {
        return;
    };
    use tuivory::{
        ColorProfile, Theme,
        ui::{
            Terminal,
            backend::TestBackend,
            components::{Styles, TabsWidget, TreeWidget},
            layout::Rect,
            widgets::Paragraph,
        },
    };
    let directory = std::path::Path::new(&directory);
    std::fs::create_dir_all(directory).unwrap();
    for en in [false, true] {
        for (view, theme, ascii) in [
            ("dark", Theme::Dark, false),
            ("light", Theme::Light, false),
            ("blackwhite", Theme::Blackwhite, false),
            ("ascii", Theme::Dark, true),
        ] {
            let (base_tabs, base_tree) = models();
            let mut items = base_tabs.items().to_vec();
            let mut nodes = base_tree.nodes();
            if en {
                items[0].title = "Document A".into();
                for n in &mut nodes {
                    n.name = match n.id.as_str() {
                        "root" => "Project",
                        "a" => "Folder A",
                        "a1" => "Document A1",
                        "b" => "Document B",
                        "c" => "Folder C",
                        _ => "Document C1",
                    }
                    .into();
                }
            }
            let tabs = Tabs::new(items).unwrap();
            let tree = Tree::new(nodes).unwrap();
            let styles = Styles::new(theme, ColorProfile::Ansi8).unwrap();
            let mut s = TabState {
                active: "b".into(),
                focused: "a".into(),
                first: 0,
            };
            let layout = tabs.layout(&mut s, 80);
            let target = &layout.cells[2];
            let x = (target.start + target.width - 1) as i32;
            let o = DragOptions::default();
            let mut d = DragState::default();
            tabs.drag(
                &mut s,
                &mut d,
                DragPointer {
                    action: DragAction::Down,
                    x: 2,
                    y: 0,
                    width: 80,
                    height: 1,
                },
                &o,
                None,
            );
            tabs.drag(
                &mut s,
                &mut d,
                DragPointer {
                    action: DragAction::Move,
                    x,
                    y: 0,
                    width: 80,
                    height: 1,
                },
                &o,
                None,
            );
            let mut state = TreeState {
                selected: "a1".into(),
                expanded: ["root".into(), "a".into()].into(),
                ..TreeState::default()
            };
            let mut rejected_state = state.clone();
            let mut td = DragState::default();
            let mut rejected = DragState::default();
            tree.drag(
                &mut state,
                &mut td,
                DragPointer {
                    action: DragAction::Down,
                    x: 4,
                    y: 3,
                    width: 40,
                    height: 10,
                },
                &o,
                None,
            );
            tree.drag(
                &mut state,
                &mut td,
                DragPointer {
                    action: DragAction::Move,
                    x: 10,
                    y: 4,
                    width: 40,
                    height: 10,
                },
                &o,
                None,
            );
            tree.drag(
                &mut rejected_state,
                &mut rejected,
                DragPointer {
                    action: DragAction::Down,
                    x: 4,
                    y: 1,
                    width: 40,
                    height: 10,
                },
                &o,
                None,
            );
            tree.drag(
                &mut rejected_state,
                &mut rejected,
                DragPointer {
                    action: DragAction::Move,
                    x: 10,
                    y: 2,
                    width: 40,
                    height: 10,
                },
                &o,
                None,
            );
            let mut terminal = Terminal::new(TestBackend::new(80, 14)).unwrap();
            terminal
                .draw(|f| {
                    f.render_widget(
                        Paragraph::new("").style(styles.role("surface").unwrap()),
                        f.area(),
                    );
                    f.render_stateful_widget(
                        TabsWidget::new(&tabs, &styles)
                            .unwrap()
                            .with_drag(&mut d, ascii),
                        Rect::new(0, 0, 80, 1),
                        &mut s,
                    );
                    f.render_widget(
                        Paragraph::new(if en {
                            "Allowed: last-child request"
                        } else {
                            "허용: 마지막 자식 이동 요청"
                        })
                        .style(styles.role("body").unwrap()),
                        Rect::new(0, 2, 40, 1),
                    );
                    f.render_widget(
                        Paragraph::new(if en {
                            "Rejected: descendant cycle"
                        } else {
                            "거부: 자기 자손으로 이동"
                        })
                        .style(styles.role("body").unwrap()),
                        Rect::new(40, 2, 40, 1),
                    );
                    let mut widget = TreeWidget::new(&tree, &styles).unwrap();
                    widget.ascii = ascii;
                    f.render_stateful_widget(
                        widget.with_drag(&mut td),
                        Rect::new(0, 3, 40, 10),
                        &mut state,
                    );
                    let mut widget = TreeWidget::new(&tree, &styles).unwrap();
                    widget.ascii = ascii;
                    f.render_stateful_widget(
                        widget.with_drag(&mut rejected),
                        Rect::new(40, 3, 40, 10),
                        &mut rejected_state,
                    );
                    f.render_widget(
                        Paragraph::new(if en {
                            "Preview only: host data, selection and focus unchanged"
                        } else {
                            "미리 보기: 원본 데이터·선택·포커스 유지"
                        })
                        .style(styles.role("hint").unwrap()),
                        Rect::new(0, 13, 80, 1),
                    );
                })
                .unwrap();
            snapshot::write(
                &directory.join(format!("drag-{view}{}.svg", if en { "-en" } else { "" })),
                terminal.backend().buffer(),
            )
            .unwrap();
        }
    }
}
fn fixture() -> serde_json::Value {
    serde_json::from_str(include_str!("data/drag-cases.json")).unwrap()
}
fn models() -> (Tabs, Tree) {
    let f = fixture();
    let tabs = Tabs::new(
        f["tabs"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| TabItem {
                id: v["id"].as_str().unwrap().into(),
                title: v["title"].as_str().unwrap().into(),
                edited: v["edited"].as_bool().unwrap_or(false),
                closable: v["closable"].as_bool().unwrap_or(false),
                disabled: v["disabled"].as_bool().unwrap_or(false),
            })
            .collect(),
    )
    .unwrap();
    let tree = Tree::new(
        f["tree"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| TreeNode {
                id: v["id"].as_str().unwrap().into(),
                parent: v["parent"].as_str().unwrap_or("").into(),
                name: v["name"].as_str().unwrap().into(),
                ..TreeNode::default()
            })
            .collect(),
    )
    .unwrap();
    (tabs, tree)
}
fn position(v: &str) -> DropPosition {
    match v {
        "before" => DropPosition::Before,
        "after" => DropPosition::After,
        _ => DropPosition::Inside,
    }
}
#[test]
fn shared_drop_requests() {
    let (tabs, tree) = models();
    let f = fixture();
    for c in f["cases"].as_array().unwrap() {
        let source = c["source"].as_str().unwrap();
        let target = c["target"].as_str().unwrap();
        let pos = position(c["position"].as_str().unwrap());
        let o = DragOptions {
            locked: c["locked"]
                .as_array()
                .map(|a| a.iter().map(|v| v.as_str().unwrap().into()).collect())
                .unwrap_or_default(),
            ..DragOptions::default()
        };
        let policy = |_: &DropRequest| !c["deny"].as_bool().unwrap_or(false);
        let result = if c["kind"] == "tabs" {
            tabs.request_drop(source, target, pos, &o, Some(&policy))
        } else {
            tree.request_drop(source, target, pos, &o, Some(&policy))
        };
        if let Some(error) = c["error"].as_str() {
            assert_eq!(result.unwrap_err(), error, "{c}");
            continue;
        }
        let request = result.unwrap();
        assert_eq!(
            request.revision,
            f[if c["kind"] == "tabs" {
                "tab_revision"
            } else {
                "tree_revision"
            }]
            .as_u64()
            .unwrap()
        );
        let order: Vec<String> = if c["kind"] == "tabs" {
            let before = tabs
                .items()
                .iter()
                .map(|i| i.id.clone())
                .collect::<Vec<_>>();
            let moved = tabs.apply_drop(&request).unwrap();
            assert_eq!(
                before,
                tabs.items()
                    .iter()
                    .map(|i| i.id.clone())
                    .collect::<Vec<_>>()
            );
            moved.items().iter().map(|i| i.id.clone()).collect()
        } else {
            let before = tree
                .nodes()
                .iter()
                .map(|n| (n.id.clone(), n.parent.clone()))
                .collect::<Vec<_>>();
            let moved = tree.apply_drop(&request).unwrap();
            assert_eq!(
                before,
                tree.nodes()
                    .iter()
                    .map(|n| (n.id.clone(), n.parent.clone()))
                    .collect::<Vec<_>>()
            );
            assert_eq!(
                moved
                    .nodes()
                    .iter()
                    .find(|n| n.id == source)
                    .unwrap()
                    .parent,
                c["parent"].as_str().unwrap()
            );
            moved.nodes().into_iter().map(|n| n.id).collect()
        };
        assert_eq!(
            order,
            c["order"]
                .as_array()
                .unwrap()
                .iter()
                .map(|v| v.as_str().unwrap().to_string())
                .collect::<Vec<_>>(),
            "{c}"
        );
    }
}
#[test]
fn capture_cancel_stale_and_keyboard() {
    let tabs = Tabs::new(
        ["a", "b", "c"]
            .map(|id| TabItem {
                id: id.into(),
                title: id.to_uppercase(),
                ..TabItem::default()
            })
            .to_vec(),
    )
    .unwrap();
    let mut s = TabState {
        active: "b".into(),
        focused: "a".into(),
        first: 0,
    };
    tabs.layout(&mut s, 40);
    let original = s.clone();
    let mut d = DragState::default();
    let o = DragOptions {
        auto_scroll: true,
        ..DragOptions::default()
    };
    let p = |action, x, y, width| DragPointer {
        action,
        x,
        y,
        width,
        height: 1,
    };
    tabs.drag(&mut s, &mut d, p(DragAction::Down, 2, 0, 40), &o, None);
    assert!(d.captured());
    tabs.drag(&mut s, &mut d, p(DragAction::Move, 3, 0, 40), &o, None);
    assert_eq!(d.phase, "armed");
    tabs.drag(&mut s, &mut d, p(DragAction::Move, 17, 0, 40), &o, None);
    assert!(d.allowed);
    let request = tabs
        .drag(&mut s, &mut d, p(DragAction::Up, 17, 0, 40), &o, None)
        .unwrap();
    assert_eq!(s, original);
    assert!(!d.captured());
    assert_eq!(d.result, "drop");
    assert_eq!(
        tabs.apply_drop(&request)
            .unwrap()
            .items()
            .iter()
            .map(|i| i.id.as_str())
            .collect::<Vec<_>>(),
        ["b", "c", "a"]
    );
    tabs.drag(&mut s, &mut d, p(DragAction::Down, 2, 0, 40), &o, None);
    tabs.drag(&mut s, &mut d, p(DragAction::Move, 17, 0, 40), &o, None);
    assert!(
        tabs.drag(&mut s, &mut d, p(DragAction::Up, -5, 5, 40), &o, None)
            .is_none()
    );
    assert_eq!(d.result, "reject");
    assert_eq!(s, original);
    tabs.drag(&mut s, &mut d, p(DragAction::Down, 2, 0, 40), &o, None);
    tabs.drag(&mut s, &mut d, p(DragAction::Move, 17, 0, 39), &o, None);
    assert_eq!(d.result, "stale");
    assert!(!d.captured());
    tabs.drag(&mut s, &mut d, p(DragAction::Down, 2, 0, 40), &o, None);
    let mut updated = tabs.items().to_vec();
    updated[2].title = "updated".into();
    let replacement = Tabs::new(updated).unwrap();
    replacement.drag(&mut s, &mut d, p(DragAction::Up, 17, 0, 40), &o, None);
    assert_eq!(d.result, "stale");
    assert!(replacement.apply_drop(&request).is_err());
    let key = tabs
        .keyboard_drop(
            &TabState {
                focused: "b".into(),
                ..TabState::default()
            },
            DragMove::Next,
            &o,
            None,
        )
        .unwrap();
    assert_eq!(key.source_id, "b");
    assert_eq!(key.target_id, "c");
    tabs.drag(&mut s, &mut d, p(DragAction::Down, 2, 0, 40), &o, None);
    tabs.drag(&mut s, &mut d, p(DragAction::Move, 17, 0, 40), &o, None);
    let revoked = DragOptions {
        locked: vec!["c".into()],
        ..o.clone()
    };
    assert!(
        tabs.drag(&mut s, &mut d, p(DragAction::Up, 17, 0, 40), &revoked, None)
            .is_none()
    );
    assert_eq!(d.result, "reject");
    tabs.drag(&mut s, &mut d, p(DragAction::Down, 2, 0, 40), &o, None);
    d.cancel();
    assert_eq!(s, original);
    assert!(!d.captured());
    tabs.drag(&mut s, &mut d, p(DragAction::Down, 2, 0, 40), &o, None);
    s.focused = "b".into();
    assert!(
        tabs.drag(&mut s, &mut d, p(DragAction::Up, 17, 0, 40), &o, None)
            .is_none()
    );
    assert_eq!(d.result, "stale");
    assert_eq!(s.focused, "b");
}
#[test]
fn tree_preview_and_keyboard() {
    let (_, tree) = models();
    let mut s = TreeState {
        selected: "a1".into(),
        expanded: ["root".into(), "a".into()].into(),
        ..TreeState::default()
    };
    tree.reconcile(&mut s, 8);
    let original = s.clone();
    let mut d = DragState::default();
    let o = DragOptions {
        hover_expand: true,
        auto_scroll: true,
        ..DragOptions::default()
    };
    let p = |action, x, y| DragPointer {
        action,
        x,
        y,
        width: 30,
        height: 8,
    };
    tree.drag(&mut s, &mut d, p(DragAction::Down, 4, 3), &o, None);
    tree.drag(&mut s, &mut d, p(DragAction::Move, 10, 4), &o, None);
    assert!(d.allowed);
    assert_eq!(d.position, Some(DropPosition::Inside));
    let (rows, _) = tree.drag_rows(&mut s, &mut d, 8);
    assert_eq!(rows.len(), 6);
    assert_eq!(s, original);
    let r = tree
        .drag(&mut s, &mut d, p(DragAction::Up, 10, 4), &o, None)
        .unwrap();
    assert_eq!(s, original);
    assert_eq!(
        tree.apply_drop(&r)
            .unwrap()
            .nodes()
            .iter()
            .find(|n| n.id == "b")
            .unwrap()
            .parent,
        "c"
    );
    let key = tree
        .keyboard_drop(
            &TreeState {
                selected: "b".into(),
                ..TreeState::default()
            },
            DragMove::Inside,
            &o,
            None,
        )
        .unwrap();
    assert_eq!(key.target_id, "a");
    let key = tree
        .keyboard_drop(
            &TreeState {
                selected: "a1".into(),
                ..TreeState::default()
            },
            DragMove::Outside,
            &o,
            None,
        )
        .unwrap();
    assert_eq!(key.target_id, "a");
    assert_eq!(key.position, DropPosition::After);
    tree.drag(&mut s, &mut d, p(DragAction::Down, 4, 1), &o, None);
    tree.drag(&mut s, &mut d, p(DragAction::Move, 10, 2), &o, None);
    assert!(!d.allowed);
    assert_eq!(d.reason, "cycle");
    d.cancel();
    assert_eq!(s, original);
    tree.drag(&mut s, &mut d, p(DragAction::Down, 4, 3), &o, None);
    s.expanded.insert("c".into());
    assert!(
        tree.drag(&mut s, &mut d, p(DragAction::Up, 10, 5), &o, None)
            .is_none()
    );
    assert_eq!(d.result, "stale");
    assert!(s.expanded.contains("c"));
}
#[cfg(feature = "ratatui")]
#[test]
fn physical_drag_feedback_and_restyle() {
    use tuivory::{
        ColorProfile, Theme,
        ui::{
            Terminal,
            backend::TestBackend,
            components::{Styles, TabsWidget, TreeWidget},
            layout::Rect,
            style::Modifier,
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
                let (tabs, tree) = models();
                let styles = Styles::new(theme, profile).unwrap();
                let mut terminal = Terminal::new(TestBackend::new(60, 10)).unwrap();
                let mut s = TabState {
                    active: "b".into(),
                    focused: "a".into(),
                    first: 0,
                };
                let mut d = DragState::default();
                terminal
                    .draw(|f| {
                        f.render_stateful_widget(
                            TabsWidget::new(&tabs, &styles)
                                .unwrap()
                                .with_drag(&mut d, ascii),
                            Rect::new(0, 0, 60, 1),
                            &mut s,
                        )
                    })
                    .unwrap();
                let layout = tabs.layout(&mut s, 60);
                let target = &layout.cells[2];
                let x = (target.start + target.width - 1) as i32;
                tabs.drag(
                    &mut s,
                    &mut d,
                    DragPointer {
                        action: DragAction::Down,
                        x: 2,
                        y: 0,
                        width: 60,
                        height: 1,
                    },
                    &DragOptions::default(),
                    None,
                );
                tabs.drag(
                    &mut s,
                    &mut d,
                    DragPointer {
                        action: DragAction::Move,
                        x,
                        y: 0,
                        width: 60,
                        height: 1,
                    },
                    &DragOptions::default(),
                    None,
                );
                terminal
                    .draw(|f| {
                        f.render_stateful_widget(
                            TabsWidget::new(&tabs, &styles)
                                .unwrap()
                                .with_drag(&mut d, ascii),
                            Rect::new(0, 0, 60, 1),
                            &mut s,
                        )
                    })
                    .unwrap();
                assert_eq!(
                    terminal.backend().buffer()[(x as u16, 0)].symbol(),
                    if ascii { "|" } else { "│" }
                );
                assert!(
                    terminal.backend().buffer()[(x as u16, 0)]
                        .modifier
                        .contains(Modifier::UNDERLINED)
                );
                terminal
                    .draw(|f| {
                        f.render_stateful_widget(
                            TabsWidget::new(&tabs, &styles)
                                .unwrap()
                                .with_drag(&mut d, ascii),
                            Rect::new(1, 0, 59, 1),
                            &mut s,
                        )
                    })
                    .unwrap();
                assert!(!d.captured());
                assert_eq!(d.result, "stale");
                let mut state = TreeState {
                    selected: "a1".into(),
                    expanded: ["root".into(), "a".into()].into(),
                    ..TreeState::default()
                };
                let mut td = DragState::default();
                terminal
                    .draw(|f| {
                        let mut widget = TreeWidget::new(&tree, &styles).unwrap();
                        widget.ascii = ascii;
                        f.render_stateful_widget(
                            widget.with_drag(&mut td),
                            Rect::new(0, 1, 30, 8),
                            &mut state,
                        )
                    })
                    .unwrap();
                tree.drag(
                    &mut state,
                    &mut td,
                    DragPointer {
                        action: DragAction::Down,
                        x: 4,
                        y: 3,
                        width: 30,
                        height: 8,
                    },
                    &DragOptions::default(),
                    None,
                );
                tree.drag(
                    &mut state,
                    &mut td,
                    DragPointer {
                        action: DragAction::Move,
                        x: 10,
                        y: 4,
                        width: 30,
                        height: 8,
                    },
                    &DragOptions::default(),
                    None,
                );
                terminal
                    .draw(|f| {
                        let mut widget = TreeWidget::new(&tree, &styles).unwrap();
                        widget.ascii = ascii;
                        f.render_stateful_widget(
                            widget.with_drag(&mut td),
                            Rect::new(0, 1, 30, 8),
                            &mut state,
                        )
                    })
                    .unwrap();
                assert_eq!(
                    terminal.backend().buffer()[(0, 5)].symbol(),
                    if ascii { "+" } else { "↳" }
                );
                assert_eq!(state.selected, "a1");
            }
        }
    }
}
