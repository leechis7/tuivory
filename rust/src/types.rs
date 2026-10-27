use std::{collections::BTreeMap, error, fmt, str::FromStr};

#[derive(Debug)]
pub enum Error {
    Json(serde_json::Error),
    Invalid(String),
    UnknownPalette(String),
    UnknownRole(String),
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Json(e) => write!(f, "invalid token JSON: {e}"),
            Self::Invalid(s) => write!(f, "invalid token data: {s}"),
            Self::UnknownPalette(s) => write!(f, "unknown palette: {s}"),
            Self::UnknownRole(s) => write!(f, "unknown role: {s}"),
        }
    }
}

impl error::Error for Error {
    fn source(&self) -> Option<&(dyn error::Error + 'static)> {
        match self {
            Self::Json(e) => Some(e),
            _ => None,
        }
    }
}

impl From<serde_json::Error> for Error {
    fn from(value: serde_json::Error) -> Self {
        Self::Json(value)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Theme {
    Dark,
    Light,
    Blackwhite,
}

impl Theme {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Dark => "dark",
            Self::Light => "light",
            Self::Blackwhite => "blackwhite",
        }
    }
}

impl FromStr for Theme {
    type Err = Error;
    fn from_str(s: &str) -> Result<Self, Error> {
        match s {
            "dark" => Ok(Self::Dark),
            "light" => Ok(Self::Light),
            "blackwhite" => Ok(Self::Blackwhite),
            _ => Err(Error::Invalid(format!("theme {s:?}"))),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ColorProfile {
    Ansi8,
    Ansi16,
    Indexed256,
    Truecolor,
}

impl ColorProfile {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Ansi8 => "8",
            Self::Ansi16 => "16",
            Self::Indexed256 => "256",
            Self::Truecolor => "truecolor",
        }
    }

    pub(crate) fn limit(self) -> u16 {
        match self {
            Self::Ansi8 => 8,
            Self::Ansi16 => 16,
            _ => 256,
        }
    }
}

impl FromStr for ColorProfile {
    type Err = Error;
    fn from_str(s: &str) -> Result<Self, Error> {
        match s {
            "8" => Ok(Self::Ansi8),
            "16" => Ok(Self::Ansi16),
            "256" => Ok(Self::Indexed256),
            "truecolor" => Ok(Self::Truecolor),
            _ => Err(Error::Invalid(format!("profile {s:?}"))),
        }
    }
}

/// Resolve an explicit host-reported color count using the Go API's rules.
/// Zero/negative counts select Truecolor, or Ansi16 when limited is true.
pub fn profile_for_colors(count: i32, limited: bool) -> ColorProfile {
    if count > 0 && count <= 8 {
        return ColorProfile::Ansi8;
    }
    if limited || (count > 0 && count <= 16) {
        return ColorProfile::Ansi16;
    }
    if count > 0 && count <= 256 {
        ColorProfile::Indexed256
    } else {
        ColorProfile::Truecolor
    }
}

/// ANSI indices stay distinct from reference RGB values and user palettes.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Color {
    Indexed(u8),
    Rgb(u8, u8, u8),
}

impl FromStr for Color {
    type Err = Error;
    fn from_str(s: &str) -> Result<Self, Error> {
        if s.len() == 7 && s.starts_with('#') && s.as_bytes()[1..].iter().all(u8::is_ascii_hexdigit)
        {
            let n = u32::from_str_radix(&s[1..], 16)
                .map_err(|_| Error::Invalid(format!("color {s:?}")))?;
            return Ok(Self::Rgb((n >> 16) as u8, (n >> 8) as u8, n as u8));
        }
        if !s.is_empty()
            && s.bytes().all(|b| b.is_ascii_digit())
            && (s == "0" || !s.starts_with('0'))
        {
            if let Ok(n) = s.parse::<u8>() {
                return Ok(Self::Indexed(n));
            }
        }
        Err(Error::Invalid(format!("color {s:?}")))
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Style {
    pub foreground: Color,
    pub background: Color,
    pub bold: bool,
}

/// An owned palette; styles carry no widget state or callbacks.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Palette(pub(crate) BTreeMap<String, Style>);

impl Palette {
    pub fn style(&self, role: &str) -> Result<Style, Error> {
        self.0
            .get(role)
            .copied()
            .ok_or_else(|| Error::UnknownRole(role.into()))
    }

    pub fn styles(&self) -> &BTreeMap<String, Style> {
        &self.0
    }
}
