use super::{SplitLayout, SplitSpec, SplitState};

/// Panel affected by a divider action.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum SplitSide {
    #[default]
    Neither,
    First,
    Second,
}

/// Optional collapse, proportional restoration and pointer capture for a split.
/// Keep a separate control and state for each independently sized axis.
#[derive(Clone, Debug, Default)]
pub struct SplitControl {
    collapsed: SplitSide,
    ratio: f64,
    press: Option<(isize, usize)>,
    moved: bool,
}
impl SplitControl {
    pub fn collapsed(&self) -> SplitSide {
        self.collapsed
    }
    pub fn captured(&self) -> bool {
        self.press.is_some()
    }
    pub fn dragging(&self) -> bool {
        self.captured() && self.moved
    }
    pub fn cancel_pointer(&mut self) {
        self.press = None;
        self.moved = false;
    }
    /// Returns the visible panel to which the host should route focus.
    pub fn visible_focus(&self, active_second: bool) -> bool {
        match self.collapsed {
            SplitSide::First => true,
            SplitSide::Second => false,
            SplitSide::Neither => active_second,
        }
    }
    pub fn layout(&self, spec: SplitSpec, state: &SplitState, total: usize) -> SplitLayout {
        if self.collapsed != SplitSide::Neither && total > 0 {
            let first = if self.collapsed == SplitSide::First {
                0
            } else {
                total - 1
            };
            return SplitLayout {
                first,
                divider: 1,
                second: total - 1 - first,
                compact: false,
            };
        }
        let layout = spec.layout(state, total);
        if self.ratio > 0.0 && !layout.compact {
            return spec.layout(
                &SplitState {
                    preferred: ((self.ratio * (total - 1) as f64 + 0.5) as usize).max(1),
                },
                total,
            );
        }
        layout
    }
    /// Shared action for keyboard bindings, menus and divider clicks.
    pub fn toggle(
        &mut self,
        spec: SplitSpec,
        state: &SplitState,
        total: usize,
        side: SplitSide,
    ) -> bool {
        self.cancel_pointer();
        if self.collapsed != SplitSide::Neither {
            self.collapsed = SplitSide::Neither;
            return true;
        }
        if side == SplitSide::Neither {
            return false;
        }
        let layout = self.layout(spec, state, total);
        if self.ratio == 0.0 && !layout.compact {
            self.ratio = layout.first as f64 / (total - 1) as f64;
        }
        self.collapsed = side;
        true
    }
    pub fn resize(
        &mut self,
        spec: SplitSpec,
        state: &mut SplitState,
        total: usize,
        position: usize,
    ) -> bool {
        let old = self.layout(spec, state, total);
        if self.collapsed != SplitSide::Neither || old.compact {
            return false;
        }
        spec.resize(state, total, position);
        self.ratio = 0.0;
        state.preferred != old.first
    }
    /// Handle down, move, up or cancel; the coordinate is relative to the split axis.
    /// `inside` includes the perpendicular bounds of the split.
    #[allow(clippy::too_many_arguments)]
    pub fn pointer(
        &mut self,
        spec: SplitSpec,
        state: &mut SplitState,
        total: usize,
        position: isize,
        inside: bool,
        action: &str,
        side: SplitSide,
    ) -> bool {
        if action == "cancel" {
            let captured = self.captured();
            self.cancel_pointer();
            return captured;
        }
        if action == "down" {
            self.cancel_pointer();
            let layout = self.layout(spec, state, total);
            if !inside || layout.divider != 1 || usize::try_from(position) != Ok(layout.first) {
                return false;
            }
            self.press = Some((position, total));
            return true;
        }
        let Some((start, press_total)) = self.press else {
            return false;
        };
        if !matches!(action, "move" | "up") {
            return false;
        }
        if total != press_total {
            self.cancel_pointer();
            return true;
        }
        self.moved |= action == "move" || position != start || !inside;
        if self.moved {
            self.resize(spec, state, total, position.max(0) as usize);
        }
        if action == "up" {
            let click = !self.moved;
            self.cancel_pointer();
            if click {
                self.toggle(spec, state, total, side);
            }
        }
        true
    }
}

/// Divider glyph, or an arrow pointing in the direction of the action.
pub fn split_glyph(
    rows: bool,
    ascii: bool,
    grip: bool,
    side: SplitSide,
    collapsed: SplitSide,
) -> char {
    let side = if collapsed == SplitSide::Neither {
        side
    } else {
        collapsed
    };
    if grip && side != SplitSide::Neither {
        let toward_first = (side == SplitSide::First) != (collapsed != SplitSide::Neither);
        return match (rows, ascii, toward_first) {
            (true, true, true) => '^',
            (true, true, false) => 'v',
            (true, false, true) => '↑',
            (true, false, false) => '↓',
            (false, true, true) => '<',
            (false, true, false) => '>',
            (false, false, true) => '‹',
            (false, false, false) => '›',
        };
    }
    match (rows, ascii) {
        (true, true) => '-',
        (true, false) => '─',
        (false, true) => '|',
        (false, false) => '│',
    }
}
