//! Standalone controls reuse Form semantics; activation never executes host work.
use crate::{
    Error,
    components::cell_text,
    forms::{ComponentLine, Form, FormField, FormOption},
};
#[derive(Clone, Debug)]
pub struct Control {
    pub model: Form,
    pub id: String,
}
impl Control {
    pub fn new(field: FormField) -> Result<Self, Error> {
        let id = field.id.clone();
        Ok(Self {
            model: Form::new(vec![field])?,
            id,
        })
    }
    pub fn input(id: &str, label: &str, value: &str, secret: bool) -> Result<Self, Error> {
        Self::new(FormField {
            id: id.into(),
            label: label.into(),
            value: value.into(),
            kind: if secret { "password" } else { "text" }.into(),
            ..Default::default()
        })
    }
    pub fn button(id: &str, label: &str) -> Result<Self, Error> {
        Self::new(FormField {
            id: id.into(),
            label: label.into(),
            kind: "button".into(),
            ..Default::default()
        })
    }
    pub fn check(id: &str, label: &str, checked: bool) -> Result<Self, Error> {
        Self::new(FormField {
            id: id.into(),
            label: label.into(),
            kind: "checkbox".into(),
            checked,
            ..Default::default()
        })
    }
    pub fn select(
        id: &str,
        label: &str,
        options: Vec<FormOption>,
        choice: &str,
    ) -> Result<Self, Error> {
        Self::new(FormField {
            id: id.into(),
            label: label.into(),
            kind: "select".into(),
            options,
            choice: choice.into(),
            ..Default::default()
        })
    }
    pub fn layout(&self, width: usize, height: usize) -> Vec<ComponentLine> {
        let f = &self.model.fields()[0];
        if f.kind == "button" {
            if width == 0 || height == 0 {
                return vec![];
            }
            return vec![ComponentLine {
                id: f.id.clone(),
                text: cell_text(
                    &format!("[ {}{} ]", f.label, if f.state.busy { " ~" } else { "" }),
                    width,
                ),
                role: if f.state.disabled {
                    "disabled"
                } else if f.state.busy {
                    "hint"
                } else {
                    "button"
                }
                .into(),
                focused: true,
                ..Default::default()
            }];
        }
        self.model.layout(width, height)
    }
}
