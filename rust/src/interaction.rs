//! Host-owned control states and modal focus scopes, with no terminal I/O.
use crate::Error;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Clone, Copy, Debug, Default, Deserialize, Serialize, PartialEq, Eq)]
#[serde(default)]
pub struct ControlState {
    pub disabled: bool,
    pub read_only: bool,
    pub busy: bool,
    pub selected: bool,
    pub edited: bool,
    pub invalid: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ControlVisual {
    pub role: &'static str,
    pub markers: String,
    pub focusable: bool,
    pub activatable: bool,
    pub editable: bool,
}

impl ControlState {
    /// Color precedence never removes non-color state markers.
    pub fn visual(self) -> ControlVisual {
        let role = if self.disabled {
            "disabled"
        } else if self.invalid {
            "error"
        } else if self.selected {
            "selection"
        } else if self.edited {
            "edited"
        } else {
            "body"
        };
        let mut markers = String::new();
        for (on, marker) in [
            (self.disabled, '-'),
            (self.invalid, '!'),
            (self.selected, '>'),
            (self.edited, '*'),
            (self.busy, '~'),
            (self.read_only, '='),
        ] {
            if on {
                markers.push(marker);
            }
        }
        ControlVisual {
            role,
            markers,
            focusable: !self.disabled,
            activatable: !self.disabled && !self.busy,
            editable: !self.disabled && !self.busy && !self.read_only,
        }
    }
}

#[derive(Clone, Debug, Default, Deserialize, Serialize, PartialEq, Eq)]
#[serde(default)]
pub struct FocusTarget {
    pub id: String,
    pub state: ControlState,
    pub hidden: bool,
}

#[derive(Clone, Debug)]
struct Scope {
    id: String,
    targets: Vec<FocusTarget>,
    focused: String,
    restore: String,
    dismissible: bool,
}

fn validate(targets: &[FocusTarget]) -> Result<(), Error> {
    let mut seen = BTreeSet::new();
    for target in targets {
        if target.id.is_empty() || !seen.insert(&target.id) {
            return Err(Error::Invalid(format!(
                "empty or duplicate focus target {:?}",
                target.id
            )));
        }
    }
    Ok(())
}

impl Scope {
    fn focus(&mut self, id: &str) -> bool {
        if self
            .targets
            .iter()
            .any(|t| t.id == id && !t.hidden && !t.state.disabled)
        {
            self.focused = id.into();
            true
        } else {
            false
        }
    }
    fn reconcile(&mut self) {
        let focused = self.focused.clone();
        if !self.focus(&focused) {
            self.focused = self
                .targets
                .iter()
                .find(|t| !t.hidden && !t.state.disabled)
                .map(|t| t.id.clone())
                .unwrap_or_default();
        }
    }
}

/// Own this value in the host. It does not own framework widgets or event loops.
#[derive(Clone, Debug)]
pub struct FocusStack {
    scopes: Vec<Scope>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PopupCloseRequest {
    pub id: String,
    pub reason: &'static str,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct InputRoute<'a> {
    pub scope_id: &'a str,
    pub blocked: bool,
}

impl FocusStack {
    pub fn new(root_id: impl Into<String>, targets: Vec<FocusTarget>) -> Result<Self, Error> {
        let id = root_id.into();
        if id.is_empty() {
            return Err(Error::Invalid("empty root scope".into()));
        }
        validate(&targets)?;
        let mut root = Scope {
            id,
            targets,
            focused: String::new(),
            restore: String::new(),
            dismissible: false,
        };
        root.reconcile();
        Ok(Self { scopes: vec![root] })
    }
    fn top(&self) -> &Scope {
        self.scopes.last().expect("root scope")
    }
    fn top_mut(&mut self) -> &mut Scope {
        self.scopes.last_mut().expect("root scope")
    }
    pub fn scope_id(&self) -> &str {
        &self.top().id
    }
    pub fn focused(&self) -> &str {
        &self.top().focused
    }
    pub fn depth(&self) -> usize {
        self.scopes.len() - 1
    }
    pub fn targets(&self) -> &[FocusTarget] {
        &self.top().targets
    }
    pub fn focus(&mut self, id: &str) -> bool {
        self.top_mut().focus(id)
    }

    pub fn move_focus(&mut self, backwards: bool) -> &str {
        let top = self.top_mut();
        let ids: Vec<_> = top
            .targets
            .iter()
            .filter(|t| !t.hidden && !t.state.disabled)
            .map(|t| t.id.clone())
            .collect();
        let current = ids.iter().position(|id| *id == top.focused);
        if ids.is_empty() {
            top.focused.clear();
        } else {
            let next = if backwards {
                (current.unwrap_or(0) + ids.len() - 1) % ids.len()
            } else {
                current.map(|n| (n + 1) % ids.len()).unwrap_or(0)
            };
            top.focused = ids[next].clone();
        }
        &top.focused
    }

    /// Preserve focus by ID; invalid updates leave all scopes unchanged.
    pub fn update(&mut self, scope_id: &str, targets: Vec<FocusTarget>) -> Result<(), Error> {
        validate(&targets)?;
        let scope = self
            .scopes
            .iter_mut()
            .find(|s| s.id == scope_id)
            .ok_or_else(|| Error::Invalid(format!("unknown focus scope {scope_id:?}")))?;
        scope.targets = targets;
        scope.reconcile();
        Ok(())
    }

    /// Empty scopes still consume input. At most 64 popup layers are accepted.
    pub fn open(
        &mut self,
        id: impl Into<String>,
        targets: Vec<FocusTarget>,
        initial: &str,
        dismissible: bool,
    ) -> Result<(), Error> {
        let id = id.into();
        if id.is_empty() || self.scopes.len() >= 65 || self.scopes.iter().any(|s| s.id == id) {
            return Err(Error::Invalid(
                "invalid/duplicate popup scope or depth".into(),
            ));
        }
        validate(&targets)?;
        let mut next = Scope {
            id,
            targets,
            focused: String::new(),
            restore: self.focused().into(),
            dismissible,
        };
        next.reconcile();
        if !initial.is_empty() && !next.focus(initial) {
            return Err(Error::Invalid(format!(
                "initial target {initial:?} is not focusable"
            )));
        }
        self.scopes.push(next);
        Ok(())
    }

    /// Escape only requests dismissal. Outside pointer input never auto-closes.
    pub fn request_close(&self) -> Option<PopupCloseRequest> {
        (self.depth() > 0 && self.top().dismissible).then(|| PopupCloseRequest {
            id: self.scope_id().into(),
            reason: "escape",
        })
    }

    /// Reject stale callbacks; the host may explicitly close locked popups.
    pub fn close(&mut self, id: &str) -> Result<(), Error> {
        if self.depth() == 0 || self.scope_id() != id {
            return Err(Error::Invalid(format!("popup {id:?} is not on top")));
        }
        let restore = self.scopes.pop().expect("popup").restore;
        if !self.top_mut().focus(&restore) {
            self.top_mut().reconcile();
        }
        Ok(())
    }

    /// Empty target means keyboard input. Pointer input supplies its hit scope.
    pub fn route(&self, target_scope: &str) -> InputRoute<'_> {
        InputRoute {
            scope_id: self.scope_id(),
            blocked: !target_scope.is_empty() && target_scope != self.scope_id(),
        }
    }
}
