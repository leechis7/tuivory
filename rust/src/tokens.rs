use crate::{Color, ColorProfile, Error, Palette, Style, Theme};
use serde::{
    Deserialize, Deserializer, Serialize,
    de::{self, MapAccess, Visitor},
};
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
};

pub const TOKEN_FORMAT: &str = "tuivory.tokens.draft";
pub const CANDIDATE_JSON: &str = include_str!("data/candidate.json");

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct TokenPair {
    pub foreground: String,
    pub background: String,
    pub reference_foreground: String,
    pub reference_background: String,
    pub font_weight: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(transparent)]
pub struct TokenPalette(#[serde(deserialize_with = "unique_map")] BTreeMap<String, TokenPair>);

impl TokenPalette {
    pub fn pairs(&self) -> &BTreeMap<String, TokenPair> {
        &self.0
    }

    /// Resolve checked colors without substituting reference RGB values.
    pub fn resolve(&self) -> Result<Palette, Error> {
        self.0
            .iter()
            .map(|(role, p)| {
                if p.font_weight != "none" && p.font_weight != "bold" {
                    return Err(Error::Invalid(format!("font weight for {role}")));
                }
                Ok((
                    role.clone(),
                    Style {
                        foreground: p.foreground.parse()?,
                        background: p.background.parse()?,
                        bold: p.font_weight == "bold",
                    },
                ))
            })
            .collect::<Result<BTreeMap<_, _>, _>>()
            .map(Palette)
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct DocumentData {
    format: String,
    roles: Vec<String>,
    #[serde(deserialize_with = "unique_map")]
    palettes: BTreeMap<String, TokenPalette>,
}

/// A validated document. Mutation cannot bypass profile/role validation.
pub struct TokenDocument(DocumentData);

impl TokenDocument {
    pub fn from_json(data: &str) -> Result<Self, Error> {
        let d: DocumentData = serde_json::from_str(data)?;
        if d.format != TOKEN_FORMAT || d.roles.is_empty() || d.palettes.is_empty() {
            return Err(Error::Invalid("format or empty document".into()));
        }
        let roles: BTreeSet<_> = d.roles.iter().collect();
        if roles.len() != d.roles.len() || roles.iter().any(|r| r.is_empty()) {
            return Err(Error::Invalid("empty or duplicate role".into()));
        }
        for (name, palette) in &d.palettes {
            let (theme, profile) = name
                .split_once('-')
                .ok_or_else(|| Error::Invalid(format!("palette {name}")))?;
            let _: Theme = theme.parse()?;
            let profile: ColorProfile = profile.parse()?;
            if palette.0.keys().collect::<BTreeSet<_>>() != roles {
                return Err(Error::Invalid(format!(
                    "incomplete or unknown roles in {name}"
                )));
            }
            for (role, pair) in &palette.0 {
                for value in [&pair.foreground, &pair.background] {
                    match value.parse::<Color>()? {
                        Color::Indexed(n) if u16::from(n) < profile.limit() => (),
                        Color::Rgb(..) if profile == ColorProfile::Truecolor => (),
                        _ => {
                            return Err(Error::Invalid(format!(
                                "color outside {name}/{role}: {value}"
                            )));
                        }
                    }
                }
                for value in [&pair.reference_foreground, &pair.reference_background] {
                    if !matches!(value.parse::<Color>()?, Color::Rgb(..)) {
                        return Err(Error::Invalid(format!("reference RGB in {name}/{role}")));
                    }
                }
                if pair.font_weight != "none" && pair.font_weight != "bold" {
                    return Err(Error::Invalid(format!("font weight in {name}/{role}")));
                }
            }
        }
        Ok(Self(d))
    }

    pub fn candidate() -> Result<Self, Error> {
        Self::from_json(CANDIDATE_JSON)
    }
    pub fn roles(&self) -> &[String] {
        &self.0.roles
    }
    pub fn palette_names(&self) -> impl Iterator<Item = &str> {
        self.0.palettes.keys().map(String::as_str)
    }

    /// Return an independent raw palette suitable for cross-language checks.
    pub fn tokens(&self, theme: Theme, profile: ColorProfile) -> Result<TokenPalette, Error> {
        let name = format!("{}-{}", theme.as_str(), profile.as_str());
        self.0
            .palettes
            .get(&name)
            .cloned()
            .ok_or(Error::UnknownPalette(name))
    }

    pub fn palette(&self, theme: Theme, profile: ColorProfile) -> Result<Palette, Error> {
        self.tokens(theme, profile)?.resolve()
    }
}

// JSON maps must not silently accept duplicate palette or role keys.
fn unique_map<'de, D, V>(deserializer: D) -> Result<BTreeMap<String, V>, D::Error>
where
    D: Deserializer<'de>,
    V: Deserialize<'de>,
{
    struct Unique<V>(std::marker::PhantomData<V>);
    impl<'de, V: Deserialize<'de>> Visitor<'de> for Unique<V> {
        type Value = BTreeMap<String, V>;
        fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            f.write_str("an object with unique keys")
        }
        fn visit_map<M: MapAccess<'de>>(self, mut access: M) -> Result<Self::Value, M::Error> {
            let mut result = BTreeMap::new();
            while let Some((key, value)) = access.next_entry::<String, V>()? {
                if result.insert(key.clone(), value).is_some() {
                    return Err(de::Error::custom(format!("duplicate key {key}")));
                }
            }
            Ok(result)
        }
    }
    deserializer.deserialize_map(Unique(std::marker::PhantomData))
}
