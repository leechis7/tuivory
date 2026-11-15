//! Front-layer input policy for host event loops.
use std::collections::BTreeMap;

/// Empty target consumes the event. The action can be downgraded to `click`.
#[derive(Debug, PartialEq, Eq)]
pub struct LayerRoute {
    pub target: String,
    pub action: String,
}

#[derive(Default)]
struct Press {
    target: String,
    down: bool,
}

/// Routes input using host-supplied layer IDs and hit tests.
#[derive(Default)]
pub struct LayerInput {
    front: String,
    presses: BTreeMap<u8, Press>,
    last_click: BTreeMap<u8, String>,
}

impl LayerInput {
    /// Switch front layer; cancel child captures for the returned layer IDs.
    pub fn set_front(&mut self, id: &str) -> Vec<String> {
        if self.front == id {
            return Vec::new();
        }
        self.front = id.into();
        self.invalidate()
    }

    /// Cancel gestures when the host replaces a layer without changing its ID.
    pub fn invalidate(&mut self) -> Vec<String> {
        let mut cancelled = Vec::new();
        for press in self.presses.values_mut() {
            if press.down && !press.target.is_empty() && !cancelled.contains(&press.target) {
                cancelled.push(press.target.clone());
            }
            press.target.clear();
        }
        self.last_click.clear();
        cancelled
    }

    /// Share the guard between keyboard and paste. An empty result consumes the event.
    pub fn keyboard_target<'a>(&self, focused: &'a str) -> &'a str {
        if self.front.is_empty() || self.front == focused {
            focused
        } else {
            ""
        }
    }

    /// Route down, move, up, click, double or wheel. Use 0 for buttonless motion.
    pub fn pointer(&mut self, action: &str, button: u8, hit: &str, through: bool) -> LayerRoute {
        let hit = if !through && !self.front.is_empty() && self.front != hit {
            ""
        } else {
            hit
        };
        let mut route = LayerRoute {
            target: String::new(),
            action: action.into(),
        };
        let press = self.presses.get(&button);
        match action {
            "down" => {
                self.presses.insert(
                    button,
                    Press {
                        target: hit.into(),
                        down: true,
                    },
                );
                route.target = hit.into();
            }
            "move" => {
                let active = if press.is_none() && button == 0 {
                    let mut active = self.presses.values().filter(|p| p.down);
                    let first = active.next();
                    if active.next().is_some() {
                        return route;
                    }
                    first
                } else {
                    press.filter(|p| p.down)
                };
                route.target = active.map_or(hit, |p| p.target.as_str()).into();
            }
            "up" => {
                if let Some(press) = self.presses.get_mut(&button) {
                    press.down = false;
                    route.target.clone_from(&press.target);
                }
            }
            "click" | "double" => {
                if let Some(press) = self.presses.remove(&button) {
                    if !press.down && press.target == hit {
                        route.target = press.target;
                    }
                }
                if route.target.is_empty() {
                    self.last_click.remove(&button);
                } else {
                    if action == "double" && self.last_click.get(&button) != Some(&route.target) {
                        route.action = "click".into();
                    }
                    self.last_click.insert(button, route.target.clone());
                }
            }
            "wheel" => route.target = hit.into(),
            _ => {}
        }
        route
    }
}
