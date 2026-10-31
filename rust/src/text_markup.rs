use crate::{
    Error,
    text::{SyntaxSpan, TextDocument},
};
use unicode_segmentation::UnicodeSegmentation;
/// Explicit `[role]text[/]` styling; `[[` escapes `[`. Copies return plain logical
/// text. Literal text APIs never parse tags. Invalid markup leaves data intact.
pub fn parse_markup(markup: &str) -> Result<(String, Vec<SyntaxSpan>), Error> {
    let bad = || Error::Invalid("invalid markup role or unbalanced tags".into());
    let mut changes = vec![(0, "body".to_string())];
    let mut stack = vec!["body".to_string()];
    let mut out = String::new();
    let mut at = 0;
    while at < markup.len() {
        if markup[at..].starts_with("[[") {
            out.push('[');
            at += 2;
            continue;
        }
        if markup[at..].starts_with('[') {
            let end = markup[at..].find(']').ok_or_else(bad)?;
            let tag = &markup[at + 1..at + end];
            if tag == "/" {
                if stack.len() == 1 {
                    return Err(bad());
                }
                stack.pop();
            } else {
                if !crate::text::text_role(tag) {
                    return Err(bad());
                }
                stack.push(tag.into())
            }
            changes.push((out.len(), stack.last().unwrap().clone()));
            at += end + 1;
            continue;
        }
        let end = markup[at..].find('[').unwrap_or(markup.len() - at);
        out.push_str(&markup[at..at + end]);
        at += end;
    }
    if stack.len() != 1 {
        return Err(bad());
    }
    let mut spans: Vec<SyntaxSpan> = vec![];
    let mut which = 0;
    for (index, (byte, _)) in out.grapheme_indices(true).enumerate() {
        while which + 1 < changes.len() && changes[which + 1].0 <= byte {
            which += 1
        }
        let role = &changes[which].1;
        if role != "body" {
            if let Some(last) = spans.last_mut() {
                if last.role == *role && last.end == index {
                    last.end += 1;
                    continue;
                }
            }
            spans.push(SyntaxSpan {
                start: index,
                end: index + 1,
                role: role.clone(),
            })
        }
    }
    Ok((out, spans))
}
impl TextDocument {
    pub fn set_markup(&mut self, markup: &str) -> Result<(), Error> {
        let (plain, spans) = parse_markup(markup)?;
        self.set_text(&plain);
        self.syntax = spans;
        Ok(())
    }
}
