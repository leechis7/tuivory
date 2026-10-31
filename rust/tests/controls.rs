use tuivory::{
    containers::{ContainerOptions, ContainerState, LayoutItem, compute_container},
    forms::{Form, FormField},
    layout::CellRect,
    text::{TextBuffer, TextDocument},
};
#[test]
fn long_document_scroll_and_edit() {
    let raw = "line 界 é [literal]\n".repeat(10000);
    let mut d = TextDocument::viewer(&raw);
    d.scroll_y = 9995;
    let rows = d.layout(40, 5);
    assert_eq!(rows.len(), 5);
    assert!(rows[0].text.contains("literal"));
    d.buffer.handle("select_all", "");
    assert_eq!(d.handle("copy", "").text, raw);
    d.buffer.state.read_only = false;
    d.handle("paste", "replacement");
    d.handle("undo", "");
    assert_eq!(d.buffer.text(), raw);
}
#[test]
fn explicit_markup_is_atomic_and_grapheme_safe() {
    let mut d = TextDocument::viewer("[info]literal[/]");
    assert_eq!(d.buffer.text(), "[info]literal[/]");
    d.set_markup("[info]界é[/][[raw]").unwrap();
    assert_eq!(d.buffer.text(), "界é[raw]");
    assert_eq!(d.syntax[0].end, 2);
    let before = d.buffer.text().to_string();
    for bad in ["[unknown]x[/]", "[info]x", "[/]"] {
        assert!(d.set_markup(bad).is_err());
        assert_eq!(d.buffer.text(), before)
    }
    d.set_markup("e[info]́[/]").unwrap();
    assert_eq!(d.buffer.text(), "é");
    assert!(d.syntax.is_empty());
}
#[test]
fn nested_modal_restores_the_calling_child() {
    let mut items = vec![
        LayoutItem {
            id: "one".into(),
            ..Default::default()
        },
        LayoutItem {
            id: "two".into(),
            ..Default::default()
        },
        LayoutItem {
            id: "a".into(),
            modal: true,
            hidden: true,
            ..Default::default()
        },
        LayoutItem {
            id: "b".into(),
            modal: true,
            hidden: true,
            ..Default::default()
        },
    ];
    let mut s = ContainerState::default();
    s.focused = "two".into();
    s.reconcile(&items);
    items[2].hidden = false;
    s.reconcile(&items);
    assert_eq!(s.focused, "a");
    items[3].hidden = false;
    s.reconcile(&items);
    items[3].hidden = true;
    s.reconcile(&items);
    assert_eq!(s.focused, "a");
    items[2].hidden = true;
    s.reconcile(&items);
    assert_eq!(s.focused, "two");
}
#[test]
fn shared_text_and_layout_cases() {
    let data: serde_json::Value =
        serde_json::from_str(include_str!("data/controls-cases.json")).unwrap();
    for c in data["text"].as_array().unwrap() {
        let mut b = TextBuffer::new(c["text"].as_str().unwrap());
        b.secret = c["secret"].as_bool().unwrap_or(false);
        b.single_line = c["single_line"].as_bool().unwrap_or(false);
        b.state.read_only = c["read_only"].as_bool().unwrap_or(false);
        for op in c["ops"].as_array().unwrap() {
            let e = b.handle(
                op["action"].as_str().unwrap(),
                op["text"].as_str().unwrap_or(""),
            );
            assert_eq!(e.kind, op["kind"].as_str().unwrap(), "{}", c["name"]);
            assert_eq!(e.text, op["event_text"].as_str().unwrap_or(""));
        }
        assert_eq!(b.text(), c["expected"].as_str().unwrap());
        assert_eq!(b.cursor, c["cursor"].as_u64().unwrap() as usize);
        if b.secret {
            assert!(!format!("{b:?}").contains(b.text()))
        }
    }
    for c in data["layout"].as_array().unwrap() {
        let bounds: CellRect = serde_json::from_value(c["bounds"].clone()).unwrap();
        let options: ContainerOptions = serde_json::from_value(c["options"].clone()).unwrap();
        let items: Vec<LayoutItem> = serde_json::from_value(c["items"].clone()).unwrap();
        let rects = compute_container(bounds, &items, &options).unwrap();
        let expected = c["expected"].as_array().unwrap();
        assert_eq!(rects.len(), expected.len());
        for (r, e) in rects.iter().zip(expected) {
            assert_eq!(r.id, e[0].as_str().unwrap());
            assert_eq!(
                [r.rect.x, r.rect.y, r.rect.width, r.rect.height],
                std::array::from_fn(|i| e[i + 1].as_u64().unwrap() as usize),
                "{}",
                c["name"]
            )
        }
        if c["name"] == "modal-layer" {
            let mut s = ContainerState::default();
            s.focused = "background".into();
            s.reconcile(&items);
            assert_eq!(s.focused, "popup");
            assert_eq!(s.hit(&items, &rects, 0, 0), None);
            assert_eq!(
                s.pointer(&items, &rects, 3, 3, true, false),
                Some("popup".into())
            );
            assert_eq!(
                s.pointer(&items, &rects, 50, 50, false, false),
                Some("popup".into())
            );
            s.pointer(&items, &rects, 50, 50, false, true);
            assert!(s.captured.is_empty());
        }
    }
}
#[test]
fn secret_form_values_and_required_validation() {
    let secret = "秘密é😀";
    let mut f = Form::new(vec![FormField {
        id: "pw".into(),
        kind: "password".into(),
        value: secret.into(),
        required: true,
        ..Default::default()
    }])
    .unwrap();
    assert_eq!(f.value("pw"), Some(secret));
    assert!(!format!("{f:?}").contains(secret));
    assert!(!serde_json::to_string(f.fields()).unwrap().contains(secret));
    assert!(
        !serde_json::to_string(&f.layout(50, 8))
            .unwrap()
            .contains(secret)
    );
    f.handle("select_all", "");
    assert!(f.handle("copy", "").text.is_empty());
    f.handle("paste", "new");
    assert_eq!(f.value("pw"), Some("new"));
    f.handle("select_all", "");
    f.handle("delete", "");
    assert_eq!(f.handle("submit", "").kind, "invalid");
    f.handle("paste", "   ");
    assert_eq!(f.handle("submit", "").kind, "invalid");
}
#[test]
fn document_resize_and_readonly_original_copy() {
    let mut d = TextDocument::viewer("[red]界é😀\r\nnext");
    let original = d.buffer.text().to_string();
    d.handle("select_all", "");
    d.handle("paste", "bad");
    for (w, h) in [(20, 4), (1, 1), (0, 0), (30, 8)] {
        d.layout(w, h);
    }
    assert_eq!(d.handle("copy", "").text, original);
    let mut editor = TextDocument::editor(&("a\n".to_string() + &"界".repeat(100)));
    editor.handle("insert", "x");
    assert_eq!(editor.layout(12, 1).len(), 1);
    assert!(editor.scroll_x > 0 && editor.scroll_y > 0);
    editor.point(2, 0, 12, 1, false);
    editor.point(8, 0, 12, 1, true);
    let (lo, hi) = editor.buffer.selection();
    assert!(hi > lo);
}
#[cfg(feature = "ratatui")]
#[test]
fn render_surfaces_controls_text_and_clipped_layers() {
    use ratatui::{
        buffer::Buffer,
        layout::Rect,
        widgets::{Paragraph, Widget},
    };
    use tuivory::{
        ColorProfile, Theme,
        controls::Control,
        ratatui::{ContainerWidget, ControlWidget, Styles, SurfaceWidget, TextWidget},
    };
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let styles = Styles::new(theme, profile).unwrap();
            let mut b = Buffer::empty(Rect::new(0, 0, 40, 14));
            let control = Control::input("pw", "암호 Password", "秘密", true).unwrap();
            SurfaceWidget::new(
                ControlWidget {
                    model: &control,
                    styles: &styles,
                    focused: true,
                },
                &styles,
            )
            .render(Rect::new(1, 1, 16, 5), &mut b);
            let mut d = TextDocument::viewer("[red]界😀\nnext");
            TextWidget {
                model: &mut d,
                styles: &styles,
                focused: true,
            }
            .render(Rect::new(18, 1, 20, 5), &mut b);
            assert_eq!(b[(18, 1)].symbol(), "[");
            assert!(!format!("{b:?}").contains("秘密"));
            let items = vec![
                LayoutItem {
                    id: "one".into(),
                    ..Default::default()
                },
                LayoutItem {
                    id: "two".into(),
                    ..Default::default()
                },
            ];
            let options = ContainerOptions {
                kind: "row".into(),
                gap: 1,
                ..Default::default()
            };
            ContainerWidget {
                items: &items,
                options: &options,
                styles: &styles,
                scroll_x: 0,
                scroll_y: 0,
                render_child: |id: &str, area: Rect, buf: &mut Buffer| {
                    Paragraph::new(id).render(area, buf)
                },
            }
            .render(Rect::new(1, 8, 30, 3), &mut b);
            assert_eq!(b[(1, 8)].symbol(), "o");
            assert_eq!(b[(17, 8)].symbol(), "t");
        }
    }
}
#[cfg(feature = "ratatui")]
#[test]
fn virtual_canvas_scroll_preserves_original_cell_positions() {
    use ratatui::{
        buffer::Buffer,
        layout::Rect,
        widgets::{Paragraph, Widget},
    };
    use tuivory::{
        ColorProfile, Theme,
        ratatui::{ContainerWidget, Styles},
    };
    let styles = Styles::new(Theme::Dark, ColorProfile::Indexed256).unwrap();
    let items = vec![LayoutItem {
        id: "text".into(),
        ..Default::default()
    }];
    let options = ContainerOptions {
        kind: "row".into(),
        virtual_width: 8,
        ..Default::default()
    };
    let mut b = Buffer::empty(Rect::new(0, 0, 4, 2));
    ContainerWidget {
        items: &items,
        options: &options,
        styles: &styles,
        scroll_x: 3,
        scroll_y: 0,
        render_child: |_: &str, r: Rect, b: &mut Buffer| Paragraph::new("ABCDEFGH").render(r, b),
    }
    .render(b.area, &mut b);
    assert_eq!(b[(0, 0)].symbol(), "D");
    assert_eq!(b[(3, 0)].symbol(), "G");
}
