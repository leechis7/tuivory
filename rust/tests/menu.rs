use serde::Deserialize;
use tuivory::{
    layout::CellRect,
    menu::{Menu, MenuItem, menu_placement},
};
#[derive(Deserialize)]
struct Fixture {
    items: Vec<MenuItem>,
    scenarios: Vec<Scenario>,
}
#[derive(Deserialize)]
struct Scenario {
    root: String,
    caller: String,
    steps: Vec<Step>,
}
#[derive(Deserialize)]
struct Step {
    action: String,
    #[serde(default)]
    value: String,
    event: String,
    id: String,
    #[serde(default)]
    focus: String,
    #[serde(default)]
    path: Vec<String>,
    #[serde(default)]
    closed: bool,
}
fn fixture() -> Fixture {
    serde_json::from_str(include_str!("data/menu-cases.json")).unwrap()
}
#[test]
fn shared_navigation() {
    let f = fixture();
    for s in f.scenarios {
        let mut m = Menu::new(f.items.clone()).unwrap();
        assert_eq!(m.open(&s.root, &s.caller).unwrap().kind, "open");
        for step in s.steps {
            let e = m.handle(&step.action, &step.value, 5).unwrap();
            assert_eq!(
                (e.kind.as_str(), e.id.as_str(), e.return_id.as_str()),
                (step.event.as_str(), step.id.as_str(), s.caller.as_str())
            );
            assert_ne!(m.opened(), step.closed);
            if !step.closed {
                assert_eq!(m.focused_id(), step.focus);
                assert_eq!(m.path(), &step.path);
            }
        }
    }
}
#[test]
fn validation_and_updates() {
    let items = fixture().items;
    let mut m = Menu::new(items.clone()).unwrap();
    m.open("file", "origin");
    m.handle("next", "", 4);
    m.handle("activate", "", 4);
    m.handle("next", "", 4);
    let before = m.path().to_vec();
    let mut bad = items.clone();
    bad.push(items[0].clone());
    assert!(m.set_items(bad).is_err());
    assert_eq!(m.path(), &before);
    m.set_items(items.clone()).unwrap();
    assert_eq!(m.focused_id(), "deep");
    let mut changed = items;
    changed[4].disabled = true;
    let e = m.set_items(changed).unwrap().unwrap();
    assert_eq!(e.kind, "close");
    assert_eq!(e.return_id, "origin");
    assert!(!m.opened());
    for items in [
        vec![MenuItem {
            id: "@back".into(),
            ..Default::default()
        }],
        vec![
            MenuItem {
                id: "a".into(),
                parent: "b".into(),
                ..Default::default()
            },
            MenuItem {
                id: "b".into(),
                parent: "a".into(),
                ..Default::default()
            },
        ],
        vec![MenuItem {
            id: "a".into(),
            parent: "missing".into(),
            ..Default::default()
        }],
        vec![
            MenuItem {
                id: "a".into(),
                mnemonic: "f".into(),
                ..Default::default()
            },
            MenuItem {
                id: "b".into(),
                mnemonic: "F".into(),
                ..Default::default()
            },
        ],
        vec![
            MenuItem {
                id: "a".into(),
                separator: true,
                ..Default::default()
            },
            MenuItem {
                id: "b".into(),
                parent: "a".into(),
                ..Default::default()
            },
        ],
    ] {
        assert!(Menu::new(items).is_err())
    }
    let mut m = Menu::new(vec![
        MenuItem {
            id: "g".into(),
            ..Default::default()
        },
        MenuItem {
            id: "a".into(),
            parent: "g".into(),
            disabled: true,
            ..Default::default()
        },
    ])
    .unwrap();
    m.open("g", "origin");
    assert!(m.handle("activate", "", 5).is_none());
    assert!(m.handle("right", "", 5).is_none());
}
#[test]
fn literal_layout_and_geometry() {
    let mut items = fixture().items;
    items[1].secondary = "[red] literal 界".into();
    items[1].icon = "◆".into();
    items[1].ascii_icon = "*".into();
    let mut m = Menu::new(items).unwrap();
    m.open("file", "origin");
    for ascii in [false, true] {
        for w in 0..90 {
            for h in 0..12 {
                let out = m.layout(w, h, ascii);
                assert!(out.len() <= h);
                for l in out {
                    assert!(tuivory::components::cells(&l.text) <= w);
                    for s in l.spans {
                        assert!(s.start + s.width <= w);
                        assert!(tuivory::components::cells(&s.text) <= s.width);
                    }
                }
                for c in m.bar_layout(w).cells {
                    assert!(c.start + c.width <= w);
                    assert!(tuivory::components::cells(&c.text) <= c.width);
                }
            }
        }
    }
    for w in 0..80 {
        for h in 0..20 {
            let r = menu_placement(
                CellRect {
                    x: 70,
                    y: 18,
                    width: 1,
                    height: 1,
                },
                CellRect {
                    x: 0,
                    y: 0,
                    width: w,
                    height: h,
                },
                40,
                20,
            );
            assert!(r.x + r.width <= w);
            assert!(r.y + r.height <= h);
        }
    }
    m.open("recent", "origin");
    m.focus("deep");
    assert!(m.click("off").is_none());
    assert!(m.click("line").is_none());
    assert_eq!(m.click("@back").unwrap().kind, "back");
    assert_eq!(m.focused_id(), "recent");
}
#[cfg(feature = "ratatui")]
#[test]
fn twelve_palettes_and_overlay_output() {
    use ratatui::{Terminal, backend::TestBackend, layout::Rect, widgets::Paragraph};
    use tuivory::{
        ColorProfile, Theme,
        ratatui::{MenuPopupWidget, Styles},
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
                let mut m = Menu::new(fixture().items).unwrap();
                m.open("file", "origin");
                let mut terminal = Terminal::new(TestBackend::new(40, 12)).unwrap();
                terminal
                    .draw(|f| {
                        f.render_widget(Paragraph::new("界".repeat(20)), Rect::new(0, 2, 40, 1));
                        f.render_widget(
                            MenuPopupWidget {
                                model: &mut m,
                                styles: &styles,
                                title: "Menu",
                                padding: 1,
                                ascii,
                                focused: true,
                            },
                            Rect::new(3, 1, 32, 8),
                        );
                    })
                    .unwrap();
                assert_eq!(terminal.backend().buffer()[(0, 2)].symbol(), "界");
                assert_eq!(terminal.backend().buffer()[(2, 2)].symbol(), " ");
                assert_eq!(terminal.backend().buffer()[(35, 2)].symbol(), " ");
                assert_eq!(terminal.backend().buffer()[(38, 2)].symbol(), "界");
                let active = &terminal.backend().buffer()[(5, 3)];
                assert_eq!(active.symbol(), ">");
                let selection = styles.role("selection").unwrap();
                assert_eq!(Some(active.fg), selection.fg);
                assert_eq!(Some(active.bg), selection.bg);
                assert!(
                    !active
                        .modifier
                        .contains(ratatui::style::Modifier::UNDERLINED)
                );
                assert_eq!(
                    terminal.backend().buffer()[(3, 1)].symbol(),
                    if ascii { "+" } else { "┌" }
                );
                let title = (3..35)
                    .map(|x| terminal.backend().buffer()[(x, 1)].symbol())
                    .collect::<String>();
                assert_eq!(title.matches("Menu").count(), 1, "{title}");
                assert!(
                    !title.contains('>'),
                    "menu title must not show focus: {title}"
                );
                let focused_buffer = terminal.backend().buffer().clone();
                terminal
                    .draw(|f| {
                        f.render_widget(Paragraph::new("界".repeat(20)), Rect::new(0, 2, 40, 1));
                        f.render_widget(
                            MenuPopupWidget {
                                model: &mut m,
                                styles: &styles,
                                title: "Menu",
                                padding: 1,
                                ascii,
                                focused: false,
                            },
                            Rect::new(3, 1, 32, 8),
                        );
                    })
                    .unwrap();
                assert_eq!(
                    terminal.backend().buffer(),
                    &focused_buffer,
                    "menu visuals must not depend on input focus"
                );
                assert_eq!(m.return_id(), "origin");
                assert_eq!(m.focused_id(), "new");
            }
        }
    }
}
#[test]
fn empty_depth_and_count_limits() {
    let mut m = Menu::new(vec![]).unwrap();
    m.open("", "editor");
    let (_, h) = m.content_size();
    assert_eq!(h, 1);
    assert_eq!(m.layout(20, h, false).len(), 1);
    assert!(m.handle("activate", "", h).is_none());
    let mut items = vec![];
    let mut parent = String::new();
    for n in 0..32 {
        let id = n.to_string();
        items.push(MenuItem {
            id: id.clone(),
            parent,
            ..Default::default()
        });
        parent = id;
    }
    assert!(Menu::new(items.clone()).is_ok());
    items.push(MenuItem {
        id: "too-deep".into(),
        parent,
        ..Default::default()
    });
    assert!(Menu::new(items).is_err());
    let mut many = (0..10000)
        .map(|n| MenuItem {
            id: format!("item-{n}"),
            ..Default::default()
        })
        .collect::<Vec<_>>();
    assert!(Menu::new(many.clone()).is_ok());
    many.push(MenuItem {
        id: "item-10000".into(),
        ..Default::default()
    });
    assert!(Menu::new(many).is_err());
}
