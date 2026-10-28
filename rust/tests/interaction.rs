use serde::Deserialize;
use tuivory::interaction::{ControlState, FocusStack, FocusTarget};

#[derive(Deserialize)]
struct StateCase {
    state: ControlState,
    role: String,
    markers: String,
    focusable: bool,
    activatable: bool,
    editable: bool,
}
#[derive(Deserialize, Default)]
#[serde(default)]
struct Step {
    op: String,
    id: String,
    initial: String,
    target: String,
    request: String,
    expect_scope: String,
    expect_focus: String,
    expect_depth: usize,
    targets: Vec<FocusTarget>,
    dismissible: bool,
    backwards: bool,
    blocked: bool,
    accepted: bool,
    error: bool,
}
#[derive(Deserialize)]
struct Contract {
    states: Vec<StateCase>,
    root: Vec<FocusTarget>,
    steps: Vec<Step>,
}

#[test]
fn common_interaction_contract() {
    let data: Contract = serde_json::from_str(include_str!("data/interaction-cases.json")).unwrap();
    for c in data.states {
        let v = c.state.visual();
        assert_eq!(
            (
                v.role,
                v.markers.as_str(),
                v.focusable,
                v.activatable,
                v.editable
            ),
            (
                c.role.as_str(),
                c.markers.as_str(),
                c.focusable,
                c.activatable,
                c.editable
            )
        );
        #[cfg(feature = "ratatui")]
        for theme in [
            tuivory::Theme::Dark,
            tuivory::Theme::Light,
            tuivory::Theme::Blackwhite,
        ] {
            for profile in [
                tuivory::ColorProfile::Ansi8,
                tuivory::ColorProfile::Ansi16,
                tuivory::ColorProfile::Indexed256,
                tuivory::ColorProfile::Truecolor,
            ] {
                let styles = tuivory::ratatui::Styles::new(theme, profile).unwrap();
                let style = styles.control(c.state, true).unwrap();
                let base = styles.role(&c.role).unwrap();
                assert_eq!((style.fg, style.bg), (base.fg, base.bg));
                assert_eq!(
                    style
                        .add_modifier
                        .contains(ratatui::style::Modifier::UNDERLINED),
                    c.focusable
                );
            }
        }
    }
    let mut stack = FocusStack::new("root", data.root).unwrap();
    for (index, c) in data.steps.into_iter().enumerate() {
        let result = match c.op.as_str() {
            "move" => {
                stack.move_focus(c.backwards);
                Ok(())
            }
            "focus" => {
                assert_eq!(stack.focus(&c.id), c.accepted);
                Ok(())
            }
            "open" => stack.open(&c.id, c.targets, &c.initial, c.dismissible),
            "close" => stack.close(&c.id),
            "update" => stack.update(&c.id, c.targets),
            "route" => {
                let route = stack.route(&c.target);
                assert_eq!(route.scope_id, c.expect_scope);
                assert_eq!(route.blocked, c.blocked);
                Ok(())
            }
            "request" => {
                let request = stack.request_close();
                if let Some(r) = &request {
                    assert_eq!(r.reason, "escape");
                }
                assert_eq!(request.map(|r| r.id).unwrap_or_default(), c.request);
                Ok(())
            }
            op => panic!("unknown action {op}"),
        };
        assert_eq!(result.is_err(), c.error, "step {index}: {result:?}");
        assert_eq!(
            (stack.scope_id(), stack.focused(), stack.depth()),
            (
                c.expect_scope.as_str(),
                c.expect_focus.as_str(),
                c.expect_depth
            ),
            "step {index}"
        );
    }
}

#[test]
fn stable_ids_and_bounded_depth() {
    let target = |id: &str| FocusTarget {
        id: id.into(),
        ..Default::default()
    };
    let mut stack = FocusStack::new("root", vec![target("a"), target("b")]).unwrap();
    stack
        .update("root", vec![target("b"), target("a")])
        .unwrap();
    assert_eq!(stack.focused(), "a");
    assert_eq!(stack.move_focus(false), "b");
    assert_eq!(stack.move_focus(true), "a");
    for index in 0..64 {
        stack.open(index.to_string(), vec![], "", true).unwrap();
    }
    assert!(stack.open("overflow", vec![], "", true).is_err());
    assert_eq!(stack.depth(), 64);
    assert!(FocusStack::new("root", vec![target("")]).is_err());
}
