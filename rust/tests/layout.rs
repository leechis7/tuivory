use tuivory::layout::{
    Badge, CellRect, Chip, Density, Help, Shortcut, SpacingTokens, StackItem, drawer_layout,
    stack_layout, stack_rects,
};
#[test]
fn shared_tokens_and_stack_bounds() {
    let data: serde_json::Value =
        serde_json::from_str(include_str!("data/layout-tokens.json")).unwrap();
    let compact = SpacingTokens::for_width(Density::Auto, 79);
    let comfortable = SpacingTokens::for_width(Density::Auto, 80);
    for (name, tokens) in [("compact", compact), ("comfortable", comfortable)] {
        assert_eq!(tokens.gap as u64, data[name]["gap"].as_u64().unwrap());
        assert_eq!(
            tokens.padding as u64,
            data[name]["padding"].as_u64().unwrap()
        );
        assert_eq!(
            tokens.control_gap as u64,
            data[name]["control_gap"].as_u64().unwrap()
        );
        assert_eq!(
            tokens.compact_below as u64,
            data["compact_below"].as_u64().unwrap()
        );
    }
    let items = vec![
        StackItem {
            id: "main".into(),
            min: 12,
            preferred: 40,
            weight: 1,
        },
        StackItem {
            id: "aside".into(),
            min: 10,
            preferred: 24,
            weight: 0,
        },
    ];
    for width in 0..241 {
        let r = stack_layout(&items, width, 2).unwrap();
        let mut end = 0;
        for slot in r.slots {
            assert!(slot.start >= end && slot.start + slot.size <= width);
            if slot.size > 0 {
                end = slot.start + slot.size
            }
        }
        let (rects, _) = stack_rects(
            CellRect {
                x: 2,
                y: 3,
                width,
                height: 20,
            },
            &items,
            comfortable,
            false,
        )
        .unwrap();
        assert!(rects.iter().all(|r| r.rect.x >= 2
            && r.rect.x + r.rect.width <= 2 + width
            && r.rect.y >= 3
            && r.rect.y + r.rect.height <= 23));
    }
    assert_eq!(items[0].preferred, 40);
    let narrow = stack_layout(&items, 8, 2).unwrap();
    assert_eq!(narrow.slots[0].size, 8);
    assert_eq!(narrow.hidden.len(), 1);
    assert!(
        drawer_layout(
            CellRect {
                x: 0,
                y: 0,
                width: 30,
                height: 10
            },
            24,
            40
        )
        .overlay
    );
    assert!(
        !drawer_layout(
            CellRect {
                x: 0,
                y: 0,
                width: 100,
                height: 10
            },
            24,
            40
        )
        .overlay
    );
    assert!(
        stack_layout(
            &[
                StackItem {
                    id: "a".into(),
                    min: 1,
                    preferred: 1,
                    weight: 0
                },
                StackItem {
                    id: "a".into(),
                    min: 1,
                    preferred: 1,
                    weight: 0
                }
            ],
            20,
            1
        )
        .is_err()
    );
}
#[test]
fn badges_chips_help() {
    assert_eq!(
        Badge {
            label: "Count".into(),
            count: Some(0),
            ..Default::default()
        }
        .line(30)
        .text,
        "Count [0]"
    );
    assert_eq!(
        Badge {
            label: "Count".into(),
            count: Some(123),
            ..Default::default()
        }
        .line(30)
        .text,
        "Count [99+]"
    );
    let mut chip = Chip {
        id: "filter".into(),
        label: "한글 필터".into(),
        removable: true,
        ..Default::default()
    };
    assert_eq!(chip.request_remove().kind, "remove");
    assert!(chip.removable);
    chip.state.read_only = true;
    assert!(chip.request_remove().kind.is_empty());
    assert!(tuivory::components::cells(&chip.line(6).text) <= 6);
    let h = Help::new(vec![
        Shortcut {
            key: "x".into(),
            text: "Remove".into(),
            priority: 1,
            disabled: false,
        },
        Shortcut {
            key: "F1".into(),
            text: "Help".into(),
            priority: 10,
            disabled: false,
        },
    ])
    .unwrap();
    assert!(h.layout(20, 1)[0].text.contains("F1"));
    assert!(
        Help::new(vec![
            Shortcut {
                key: "F1".into(),
                ..Default::default()
            },
            Shortcut {
                key: "f1".into(),
                ..Default::default()
            }
        ])
        .is_err()
    );
}
