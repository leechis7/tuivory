//! Optional Oracle SQL/PLSQL highlighting tokenizer, not an execution/safety parser.
use crate::{
    Error,
    syntax::{SyntaxAnalysis, SyntaxAnalyzer, SyntaxRequest, SyntaxToken},
};
use std::{
    collections::{BTreeMap, HashSet},
    sync::OnceLock,
};
use unicode_segmentation::UnicodeSegmentation;

type WordSets = BTreeMap<String, HashSet<String>>;
fn words() -> &'static WordSets {
    static WORDS: OnceLock<WordSets> = OnceLock::new();
    WORDS.get_or_init(|| {
        serde_json::from_str(include_str!("data/sql-syntax-words.json"))
            .expect("embedded SQL vocabulary")
    })
}
#[derive(Clone, Debug, Default)]
pub struct SQLAnalyzer;
impl SQLAnalyzer {
    pub fn new() -> Self {
        Self
    }
}
fn ident_start(c: char) -> bool {
    c.is_alphabetic() || c == '_'
}
fn ident_part(c: char) -> bool {
    ident_start(c) || c.is_numeric() || matches!(c, '$' | '#') || unicode_mark(c)
}
// Unicode combining marks are accepted by scanning a complete grapheme after
// each identifier character; this helper handles common standalone marks too.
fn unicode_mark(c: char) -> bool {
    matches!(c as u32,0x0300..=0x036f|0x1ab0..=0x1aff|0x1dc0..=0x1dff|0x20d0..=0x20ff|0xfe20..=0xfe2f)
}
fn at(text: &str, i: usize) -> char {
    text[i..].chars().next().expect("within source")
}
fn quoted(text: &str, mut i: usize, quote: u8) -> usize {
    i += 1;
    let bytes = text.as_bytes();
    while i < bytes.len() {
        if bytes[i] == quote {
            i += 1;
            if i < bytes.len() && bytes[i] == quote {
                i += 1;
                continue;
            }
            return i;
        }
        i += 1
    }
    i
}
fn q_prefix(text: &str) -> usize {
    let b = text.as_bytes();
    if b.len() >= 3 && matches!(b[0], b'q' | b'Q') && b[1] == b'\'' {
        2
    } else if b.len() >= 4
        && matches!(b[0], b'n' | b'N')
        && matches!(b[1], b'q' | b'Q')
        && b[2] == b'\''
    {
        3
    } else {
        0
    }
}
impl SyntaxAnalyzer for SQLAnalyzer {
    fn analyze_syntax(&self, text: &str, request: &SyntaxRequest) -> Result<SyntaxAnalysis, Error> {
        let language = if request.language.is_empty() {
            "sql".into()
        } else {
            request.language.to_ascii_lowercase()
        };
        let dialect = if request.dialect.is_empty() {
            "oracle".into()
        } else {
            request.dialect.to_ascii_lowercase()
        };
        if !matches!(language.as_str(), "sql" | "plsql") || dialect != "oracle" {
            return Err(Error::Invalid(format!(
                "unsupported syntax language/dialect: {language}/{dialect}"
            )));
        }
        let mut tokens = Vec::<SyntaxToken>::new();
        let mut i = 0;
        let bytes = text.as_bytes();
        let vocabulary = words();
        while i < text.len() {
            let start = i;
            let c = at(text, i);
            if c.is_whitespace() {
                i += c.len_utf8();
                continue;
            }
            let mut role = "punctuation";
            if text[i..].starts_with("--") {
                role = "comment";
                i += 2;
                while i < text.len() && !matches!(bytes[i], b'\n' | b'\r') {
                    i += 1
                }
            } else if text[i..].starts_with("/*") {
                role = "comment";
                i = match text[i + 2..].find("*/") {
                    Some(end) => i + end + 4,
                    None => text.len(),
                };
            } else if q_prefix(&text[i..]) > 0 {
                role = "string";
                i += q_prefix(&text[i..]);
                if i < text.len() {
                    let open = at(text, i);
                    if !open.is_whitespace() {
                        let close = match open {
                            '[' => ']',
                            '{' => '}',
                            '(' => ')',
                            '<' => '>',
                            _ => open,
                        };
                        i += open.len_utf8();
                        let ending = format!("{close}'");
                        i = match text[i..].find(&ending) {
                            Some(end) => i + end + ending.len(),
                            None => text.len(),
                        };
                    } else {
                        i = start + c.len_utf8();
                        role = "identifier"
                    }
                }
            } else if c == '\''
                || matches!(c, 'n' | 'N') && i + 1 < bytes.len() && bytes[i + 1] == b'\''
            {
                role = "string";
                if c != '\'' {
                    i += 1
                }
                i = quoted(text, i, b'\'');
            } else if c == '"' {
                role = "identifier";
                i = quoted(text, i, b'"');
            } else if c == ':'
                && i + 1 < bytes.len()
                && (ident_start(at(text, i + 1))
                    || bytes[i + 1].is_ascii_digit()
                    || bytes[i + 1] == b'"')
            {
                role = "parameter";
                i += 1;
                if bytes[i] == b'"' {
                    i = quoted(text, i, b'"')
                } else {
                    while i < bytes.len() && ident_part(at(text, i)) {
                        i += at(text, i).len_utf8()
                    }
                }
            } else if text[i..].starts_with("..") {
                role = "operator";
                i += 2;
            } else if bytes[i].is_ascii_digit()
                || c == '.' && i + 1 < bytes.len() && bytes[i + 1].is_ascii_digit()
            {
                role = "number";
                while i < bytes.len() && bytes[i].is_ascii_digit() {
                    i += 1
                }
                if i < bytes.len()
                    && bytes[i] == b'.'
                    && !(i + 1 < bytes.len() && bytes[i + 1] == b'.')
                {
                    i += 1;
                    while i < bytes.len() && bytes[i].is_ascii_digit() {
                        i += 1
                    }
                }
                if i < bytes.len() && matches!(bytes[i], b'e' | b'E') {
                    let mut end = i + 1;
                    if end < bytes.len() && matches!(bytes[end], b'+' | b'-') {
                        end += 1
                    }
                    let first = end;
                    while end < bytes.len() && bytes[end].is_ascii_digit() {
                        end += 1
                    }
                    if end > first {
                        i = end
                    }
                }
                if i < bytes.len() && matches!(bytes[i], b'f' | b'F' | b'd' | b'D') {
                    i += 1
                }
            } else if ident_start(c) {
                i += c.len_utf8();
                while i < bytes.len() && ident_part(at(text, i)) {
                    i += at(text, i).len_utf8()
                }
                let word = text[start..i].to_ascii_uppercase();
                role = "identifier";
                for (group, kind) in [
                    ("types", "type"),
                    ("functions", "function"),
                    ("keywords", "keyword"),
                ] {
                    if vocabulary[group].contains(&word) {
                        role = kind;
                        break;
                    }
                }
            } else {
                i += c.len_utf8();
                if "+-*/%=<>!|:^~".contains(c) {
                    role = "operator";
                    if i < bytes.len()
                        && bytes[i].is_ascii()
                        && matches!(
                            &text[start..i + 1],
                            ":=" | "=>" | "<=" | ">=" | "!=" | "<>" | "||" | "**"
                        )
                    {
                        i += 1
                    }
                }
            }
            tokens.push(SyntaxToken {
                start,
                end: i,
                role: role.into(),
            });
        }
        let mut aligned = Vec::<SyntaxToken>::new();
        let mut index = 0;
        let mut previous = None;
        for (start, cluster) in text.grapheme_indices(true) {
            let end = start + cluster.len();
            while index < tokens.len() && tokens[index].end <= start {
                index += 1
            }
            if index < tokens.len() && tokens[index].start < end {
                if previous == Some(index) && aligned.last().is_some_and(|t| t.end == start) {
                    aligned.last_mut().unwrap().end = end
                } else {
                    aligned.push(SyntaxToken {
                        start,
                        end,
                        role: tokens[index].role.clone(),
                    })
                }
                previous = Some(index);
            } else {
                previous = None
            }
        }
        Ok(SyntaxAnalysis {
            source: text.into(),
            language,
            dialect,
            tokens: aligned,
        })
    }
}
