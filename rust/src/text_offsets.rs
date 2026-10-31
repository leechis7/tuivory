//! Exact UTF-8 byte to grapheme conversion for host lexer integrations.
use crate::{
    Error,
    text::{SyntaxSpan, TextDocument},
};
use unicode_segmentation::UnicodeSegmentation;
pub fn grapheme_index(text: &str, byte_offset: usize) -> Result<usize, Error> {
    for (index, (offset, _)) in text.grapheme_indices(true).enumerate() {
        if offset == byte_offset {
            return Ok(index);
        }
    }
    if byte_offset == text.len() {
        return Ok(text.graphemes(true).count());
    }
    Err(Error::Invalid(
        "byte offset outside text or splitting a grapheme".into(),
    ))
}
/// Half-open host lexer range in original UTF-8 bytes.
#[derive(Clone, Debug)]
pub struct ByteSyntaxSpan {
    pub start: usize,
    pub end: usize,
    pub role: String,
}
impl TextDocument {
    /// Convert byte ranges atomically; host lexing/business semantics remain outside the SDK.
    pub fn set_byte_syntax(&mut self, spans: &[ByteSyntaxSpan]) -> Result<(), Error> {
        let mut boundaries = std::collections::BTreeMap::new();
        for (index, (offset, _)) in self.buffer.text().grapheme_indices(true).enumerate() {
            boundaries.insert(offset, index);
        }
        boundaries.insert(
            self.buffer.text().len(),
            self.buffer.text().graphemes(true).count(),
        );
        let get = |offset| {
            boundaries
                .get(&offset)
                .copied()
                .ok_or_else(|| Error::Invalid("invalid grapheme byte boundary".into()))
        };
        let converted = spans
            .iter()
            .map(|s| {
                Ok(SyntaxSpan {
                    start: get(s.start)?,
                    end: get(s.end)?,
                    role: s.role.clone(),
                })
            })
            .collect::<Result<Vec<_>, Error>>()?;
        self.set_syntax(converted)
    }
}
