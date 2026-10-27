use serde::Deserialize;
use tuivory::tree::{Tree, TreeAction, TreeEvent, TreeNode, TreeState};
#[derive(Deserialize)]
struct Node {
    id: String,
    #[serde(default)]
    parent: String,
    name: String,
    #[serde(default)]
    secondary: String,
    #[serde(default)]
    icon: String,
    #[serde(default)]
    ascii_icon: String,
    count: Option<u64>,
    #[serde(default)]
    branch: bool,
}
#[derive(Deserialize)]
struct Step {
    action: String,
    selected: String,
    expanded: Vec<String>,
    scroll: usize,
    horizontal: usize,
    event: String,
    id: String,
    visible: Vec<String>,
    #[serde(default)]
    column: usize,
    #[serde(default)]
    row: usize,
}
#[derive(Deserialize)]
struct Fixture {
    height: usize,
    nodes: Vec<Node>,
    steps: Vec<Step>,
}
#[test]
fn shared_navigation_contract() {
    let fixture: Fixture = serde_json::from_str(include_str!("data/tree-navigation.json")).unwrap();
    let tree = Tree::new(
        fixture
            .nodes
            .into_iter()
            .map(|n| TreeNode {
                id: n.id,
                parent: n.parent,
                name: n.name,
                secondary: n.secondary,
                icon: n.icon,
                ascii_icon: n.ascii_icon,
                count: n.count,
                branch: n.branch,
            })
            .collect(),
    )
    .unwrap();
    let mut state = TreeState::default();
    for step in fixture.steps {
        let event = if step.action == "click" {
            tree.click(&mut state, step.column, step.row, fixture.height)
        } else {
            tree.handle(
                &mut state,
                match step.action.as_str() {
                    "right" => TreeAction::Right,
                    "left" => TreeAction::Left,
                    "down" => TreeAction::Down,
                    "home" => TreeAction::Home,
                    "end" => TreeAction::End,
                    "pan_right" => TreeAction::PanRight,
                    "activate" => TreeAction::Activate,
                    "toggle" => TreeAction::Toggle,
                    _ => panic!("unknown action"),
                },
                fixture.height,
            )
        };
        let (kind, id) = match event {
            Some(TreeEvent::Select(id)) => ("select", id),
            Some(TreeEvent::Expand(id)) => ("expand", id),
            Some(TreeEvent::Collapse(id)) => ("collapse", id),
            Some(TreeEvent::Activate(id)) => ("activate", id),
            None => ("", String::new()),
        };
        assert_eq!(
            (kind, id),
            (step.event.as_str(), step.id),
            "{}",
            step.action
        );
        assert_eq!(state.selected, step.selected);
        assert_eq!(state.scroll, step.scroll);
        assert_eq!(state.horizontal, step.horizontal);
        assert_eq!(
            state.expanded.iter().cloned().collect::<Vec<_>>(),
            step.expanded
        );
        assert_eq!(
            tree.visible(&state)
                .iter()
                .map(|r| r.node.id.clone())
                .collect::<Vec<_>>(),
            step.visible
        );
    }
}
#[test]
fn invalid_data_and_stable_id_reconciliation() {
    let n = |id: &str, parent: &str| TreeNode {
        id: id.into(),
        parent: parent.into(),
        ..Default::default()
    };
    for nodes in [
        vec![n("", "")],
        vec![n("a", ""), n("a", "")],
        vec![n("a", "missing")],
        vec![n("a", "a")],
    ] {
        assert!(Tree::new(nodes).is_err());
    }
    let tree = Tree::new(vec![n("r", ""), n("a", "r"), n("b", "a")]).unwrap();
    let mut state = TreeState {
        selected: "b".into(),
        expanded: ["r".into(), "removed".into()].into(),
        scroll: 99,
        ..Default::default()
    };
    tree.reconcile(&mut state, 2);
    assert_eq!(state.selected, "a");
    assert_eq!(state.scroll, 0);
    let mut deep = Vec::new();
    for i in 0..=129 {
        deep.push(n(
            &i.to_string(),
            &if i == 0 {
                String::new()
            } else {
                (i - 1).to_string()
            },
        ));
        assert_eq!(Tree::new(deep.clone()).is_ok(), i <= 128, "depth {i}");
    }
    assert!(!state.expanded.contains("removed"));
    Tree::new(vec![n("r", "")])
        .unwrap()
        .reconcile(&mut state, 1);
    assert_eq!(state.selected, "r");
    assert!(state.expanded.contains("r"));
    Tree::new(vec![]).unwrap().reconcile(&mut state, 0);
    assert!(state.selected.is_empty());
    assert_eq!(state.scroll, 0);
}

#[cfg(feature = "ratatui")]
#[test]
fn twelve_palette_rendering_focus_ascii_and_wide_clipping() {
    use ratatui::{
        Terminal,
        backend::TestBackend,
        layout::Rect,
        style::{Color, Modifier},
    };
    use tuivory::{
        ColorProfile, Theme, TokenDocument,
        ratatui::{Styles, TreeWidget},
    };
    let tree = Tree::new(vec![TreeNode {
        id: "r".into(),
        name: "[red]한글 ABC".into(),
        icon: "◇".into(),
        ascii_icon: "R".into(),
        secondary: "secondary".into(),
        ..Default::default()
    }])
    .unwrap();
    let mut state = TreeState {
        selected: "r".into(),
        ..Default::default()
    };
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let styles = Styles::new(theme, profile).unwrap();
            let mut terminal = Terminal::new(TestBackend::new(38, 7)).unwrap();
            let before = state.clone();
            for focused in [false, true] {
                terminal
                    .draw(|f| {
                        let mut w = TreeWidget::new(&tree, &styles).unwrap();
                        w.focused = focused;
                        w.ascii = true;
                        f.render_stateful_widget(w, f.area(), &mut state);
                    })
                    .unwrap();
                let cell = &terminal.backend().buffer()[(3, 0)];
                let selected = styles.role("selection").unwrap();
                assert_eq!(cell.fg, selected.fg.unwrap());
                assert_eq!(cell.bg, selected.bg.unwrap());
                assert_eq!(cell.modifier.contains(Modifier::UNDERLINED), focused);
                let text = terminal
                    .backend()
                    .buffer()
                    .content
                    .iter()
                    .map(|c| c.symbol())
                    .collect::<String>();
                assert!(text.contains("[red]"));
                assert!(!text.contains('◇'));
            }
            assert_eq!(state, before);
            terminal
                .draw(|f| {
                    f.render_stateful_widget(
                        TreeWidget::new(&tree, &styles).unwrap(),
                        Rect::new(0, 0, 0, 0),
                        &mut state,
                    )
                })
                .unwrap();
            for offset in 0..30 {
                state.horizontal = offset;
                terminal
                    .draw(|f| {
                        f.render_stateful_widget(
                            TreeWidget::new(&tree, &styles).unwrap(),
                            Rect::new(0, 0, 5, 1),
                            &mut state,
                        )
                    })
                    .unwrap();
            }
            state.horizontal = 0;
            if profile == ColorProfile::Ansi8 {
                assert!(matches!(
                    terminal.backend().buffer()[(0, 0)].fg,
                    Color::Indexed(_)
                ));
            }
        }
    }
    let doc=TokenDocument::from_json(r##"{"format":"tuivory.tokens.draft","roles":["body"],"palettes":{"dark-8":{"body":{"foreground":"7","background":"0","referenceForeground":"#ffffff","referenceBackground":"#000000","fontWeight":"none"}}}}"##).unwrap();
    let incomplete = Styles::from_palette(doc.palette(Theme::Dark, ColorProfile::Ansi8).unwrap());
    assert!(TreeWidget::new(&tree, &incomplete).is_err());
}
