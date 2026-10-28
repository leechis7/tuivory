use tuivory::{
    forms::{Form, FormField, FormOption},
    interaction::ControlState,
};
fn field(id: &str, kind: &str) -> FormField {
    FormField {
        id: id.into(),
        kind: kind.into(),
        ..Default::default()
    }
}
#[test]
fn editing_requests_and_states() {
    let mut name = field("text", "text");
    name.required = true;
    let mut read = field("read", "text");
    read.value = "keep".into();
    read.state.read_only = true;
    let mut check = field("check", "checkbox");
    check.required = true;
    let mut submit = field("submit", "button");
    submit.action = "submit".into();
    let mut f = Form::new(vec![name, read, check, submit]).unwrap();
    assert_eq!(f.handle("submit", "").kind, "invalid");
    f.handle("insert", "가👩‍💻é");
    f.handle("backspace", "");
    assert_eq!(f.fields()[0].value, "가👩‍💻");
    f.handle("left", "");
    f.handle("delete", "");
    assert_eq!(f.fields()[0].value, "가");
    f.handle("next", "");
    f.handle("insert", "bad");
    assert_eq!(f.fields()[1].value, "keep");
    f.focus("check");
    f.handle("toggle", "");
    f.focus("submit");
    assert_eq!(f.handle("activate", "").kind, "submit");
    f.set_feedback("text", "", "host error");
    assert_eq!(f.handle("submit", "").kind, "invalid");
    f.set_state(
        "text",
        ControlState {
            disabled: true,
            ..Default::default()
        },
    );
    assert_eq!(f.handle("submit", "").kind, "submit");
}
#[test]
fn pending_select_and_caret() {
    let mut select = field("select", "select");
    select.choice = "a".into();
    select.options = vec![
        FormOption {
            id: "a".into(),
            label: "A".into(),
            disabled: false,
        },
        FormOption {
            id: "x".into(),
            disabled: true,
            ..Default::default()
        },
        FormOption {
            id: "b".into(),
            label: "B".into(),
            disabled: false,
        },
    ];
    let mut long = field("long", "text");
    long.value = "한".repeat(30);
    let mut f = Form::new(vec![select, long]).unwrap();
    f.handle("activate", "");
    f.handle("down", "");
    assert_eq!(f.fields()[0].choice, "a");
    assert_eq!(f.fields()[0].pending, "b");
    f.handle("cancel", "");
    assert_eq!(f.fields()[0].choice, "a");
    f.handle("activate", "");
    f.handle("down", "");
    f.handle("activate", "");
    assert_eq!(f.fields()[0].choice, "b");
    f.set_state(
        "select",
        ControlState {
            read_only: true,
            ..Default::default()
        },
    );
    f.click("select", "a");
    assert_eq!(f.fields()[0].choice, "b");
    f.focus("long");
    let rows = f.layout(12, 4);
    assert!(
        rows.iter()
            .all(|r| tuivory::components::cells(&r.text) <= 12)
    );
    assert!(rows.iter().any(|r| r.text.contains('|')));
    assert!(Form::new(vec![field("a", "unknown")]).is_err());
}
