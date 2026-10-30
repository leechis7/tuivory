//! Framework-independent card/shadow footprint geometry. Hosts supply anchors.
use crate::layout::CellRect;
use serde::{Deserialize, Serialize};
#[derive(Clone, Copy, Debug, Default, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ShadowMode {
    #[default]
    Off,
    Auto,
    Solid,
    Dim,
}
/// Cell offsets; enabled modes with both offsets zero use right-two/down-one.
#[derive(Clone, Copy, Debug, Default, Deserialize, Serialize, PartialEq, Eq)]
#[serde(default, rename_all = "camelCase")]
pub struct ShadowOptions {
    pub mode: ShadowMode,
    pub offset_x: usize,
    pub offset_y: usize,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PopupLayout {
    pub bounds: CellRect,
    pub card: CellRect,
    pub shadow: CellRect,
}
impl ShadowOptions {
    fn offsets(self) -> (usize, usize) {
        if self.mode == ShadowMode::Off {
            (0, 0)
        } else if self.offset_x == 0 && self.offset_y == 0 {
            (2, 1)
        } else {
            (self.offset_x, self.offset_y)
        }
    }
    /// Reserve the shadow inside an allocation; preserve a nonempty card if possible.
    pub fn layout(self, bounds: CellRect) -> PopupLayout {
        let mut l = PopupLayout {
            bounds,
            card: bounds,
            shadow: CellRect::default(),
        };
        if bounds.width == 0 || bounds.height == 0 {
            return l;
        }
        let (dx, dy) = self.offsets();
        let dx = dx.min(bounds.width - 1);
        let dy = dy.min(bounds.height - 1);
        l.card.width -= dx;
        l.card.height -= dy;
        if dx != 0 || dy != 0 {
            l.shadow = CellRect {
                x: bounds.x.saturating_add(dx),
                y: bounds.y.saturating_add(dy),
                width: l.card.width,
                height: l.card.height,
            };
        }
        l
    }
}
/// Place a requested card plus optional shadow, clamping/flipping the full footprint.
pub fn popup_placement(
    anchor: CellRect,
    viewport: CellRect,
    width: usize,
    height: usize,
    shadow: ShadowOptions,
) -> PopupLayout {
    let (dx, dy) = shadow.offsets();
    let (w, h) = if width == 0 || height == 0 {
        (0, 0)
    } else {
        (
            width.saturating_add(dx).min(viewport.width),
            height.saturating_add(dy).min(viewport.height),
        )
    };
    let max_x = viewport.x.saturating_add(viewport.width - w);
    let max_y = viewport.y.saturating_add(viewport.height - h);
    let x = anchor.x.clamp(viewport.x, max_x);
    let mut y = anchor.y.saturating_add(anchor.height);
    if y > max_y {
        y = anchor.y.saturating_sub(h)
    }
    shadow.layout(CellRect {
        x,
        y: y.clamp(viewport.y, max_y),
        width: w,
        height: h,
    })
}

impl PopupLayout {
    /// Disjoint right/bottom shadow strips, never the card itself.
    pub fn shadow_regions(self) -> [CellRect; 2] {
        let s = self.shadow;
        let c = self.card;
        let sr = s.x.saturating_add(s.width);
        let sb = s.y.saturating_add(s.height);
        let cr = c.x.saturating_add(c.width);
        let cb = c.y.saturating_add(c.height);
        let x = s.x.max(cr);
        let y = s.y.max(cb);
        [
            CellRect {
                x,
                y: s.y,
                width: sr.saturating_sub(x),
                height: sb.min(cb).saturating_sub(s.y),
            },
            CellRect {
                x: s.x,
                y,
                width: s.width,
                height: sb.saturating_sub(y),
            },
        ]
    }
}

impl std::str::FromStr for ShadowMode {
    type Err = crate::Error;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "off" => Ok(Self::Off),
            "auto" => Ok(Self::Auto),
            "solid" => Ok(Self::Solid),
            "dim" => Ok(Self::Dim),
            _ => Err(crate::Error::Invalid(format!("unknown shadow mode: {s}"))),
        }
    }
}

impl ShadowMode {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Off => "off",
            Self::Auto => "auto",
            Self::Solid => "solid",
            Self::Dim => "dim",
        }
    }
}
