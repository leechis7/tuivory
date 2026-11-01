//! Language-neutral, original UTF-8 byte ranges for optional highlighting.
use crate::{Error, text::TextDocument, text_offsets::ByteSyntaxSpan};
use serde::{Deserialize, Serialize};
use std::{fmt, sync::Arc};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntaxToken {
    pub start: usize,
    pub end: usize,
    pub role: String,
}
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntaxRequest {
    pub language: String,
    pub dialect: String,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntaxAnalysis {
    pub source: String,
    pub language: String,
    pub dialect: String,
    pub tokens: Vec<SyntaxToken>,
}
pub trait SyntaxAnalyzer: Send + Sync {
    fn analyze_syntax(&self, text: &str, request: &SyntaxRequest) -> Result<SyntaxAnalysis, Error>;
}
impl<F> SyntaxAnalyzer for F
where
    F: Fn(&str, &SyntaxRequest) -> Result<SyntaxAnalysis, Error> + Send + Sync,
{
    fn analyze_syntax(&self, text: &str, request: &SyntaxRequest) -> Result<SyntaxAnalysis, Error> {
        self(text, request)
    }
}
/// Unknown roles/identifiers fall back to body; extended roles reuse the seven
/// existing syntax families. No source language creates its own palette.
pub fn role_style(role: &str) -> &str {
    match role {
        "keyword" => "syntax.keyword",
        "function" | "macro" | "attribute" => "syntax.function",
        "type" => "syntax.type",
        "string" | "character" => "syntax.string",
        "number" | "constant" => "syntax.number",
        "comment" | "directive" => "syntax.comment",
        "parameter" | "lifetime" => "syntax.parameter",
        _ => "body",
    }
}
pub fn palette_role(role: &str) -> &str {
    match role.strip_prefix("syntax.").unwrap_or(role) {
        "keyword" => "info",
        "function" => "success",
        "type" => "header",
        "string" => "warning",
        "number" => "edited",
        "comment" => "hint",
        "parameter" => "error",
        _ => "body",
    }
}
impl SyntaxAnalysis {
    pub fn validate(&self, text: &str) -> Result<(), Error> {
        if self.source != text {
            return Err(Error::Invalid("stale syntax source".into()));
        }
        let mut end = 0;
        for token in &self.tokens {
            if token.start < end || token.end <= token.start || token.end > text.len() {
                return Err(Error::Invalid(
                    "unordered, overlapping or invalid syntax byte range".into(),
                ));
            }
            end = token.end;
            if !text.is_char_boundary(token.start) || !text.is_char_boundary(token.end) {
                return Err(Error::Invalid("syntax range splits UTF-8".into()));
            }
        }
        Ok(())
    }
}
#[derive(Clone)]
pub(crate) struct SyntaxBinding {
    pub analyzer: Option<Arc<dyn SyntaxAnalyzer>>,
    pub request: SyntaxRequest,
    pub source: String,
    pub last_error: Option<String>,
    pub dirty: bool,
}
impl fmt::Debug for SyntaxBinding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SyntaxBinding")
            .field("request", &self.request)
            .field("failed", &self.last_error.is_some())
            .finish_non_exhaustive()
    }
}
impl TextDocument {
    /// Apply a source-tagged result atomically, switching from automatic to
    /// supplied analysis. Stale or invalid results preserve existing state.
    pub fn set_syntax_analysis(&mut self, analysis: SyntaxAnalysis) -> Result<(), Error> {
        if self.buffer.secret {
            return Err(Error::Invalid(
                "syntax analysis is unavailable for secret buffers".into(),
            ));
        }
        self.apply_analysis(analysis)?;
        self.syntax_analyzer = Some(SyntaxBinding {
            analyzer: None,
            request: Default::default(),
            source: self.buffer.text().into(),
            last_error: None,
            dirty: false,
        });
        Ok(())
    }
    fn apply_analysis(&mut self, analysis: SyntaxAnalysis) -> Result<(), Error> {
        analysis.validate(self.buffer.text())?;
        let spans = analysis
            .tokens
            .iter()
            .map(|t| ByteSyntaxSpan {
                start: t.start,
                end: t.end,
                role: role_style(&t.role).into(),
            })
            .collect::<Vec<_>>();
        self.set_byte_syntax(&spans)
    }
    /// Attach supplied or custom analysis atomically; None detaches it. Analysis
    /// runs on changed source, never on every scroll/theme-only render.
    pub fn set_syntax_analyzer(
        &mut self,
        analyzer: Option<Arc<dyn SyntaxAnalyzer>>,
        request: SyntaxRequest,
    ) -> Result<(), Error> {
        let Some(analyzer) = analyzer else {
            self.syntax_analyzer = None;
            self.syntax.clear();
            return Ok(());
        };
        if self.buffer.secret {
            return Err(Error::Invalid(
                "syntax analysis is unavailable for secret buffers".into(),
            ));
        }
        let analysis = analyzer.analyze_syntax(self.buffer.text(), &request)?;
        self.apply_analysis(analysis)?;
        self.syntax_analyzer = Some(SyntaxBinding {
            analyzer: Some(analyzer),
            request,
            source: self.buffer.text().into(),
            last_error: None,
            dirty: false,
        });
        Ok(())
    }
    /// Clear stale styles on failure. Existing editor/selection/history survives.
    pub fn refresh_syntax(&mut self) -> Result<(), Error> {
        if self.buffer.secret {
            if let Some(binding) = &mut self.syntax_analyzer {
                binding.source.clear();
                binding.dirty = true;
            }
            self.syntax.clear();
            return Ok(());
        }
        let Some(mut binding) = self.syntax_analyzer.take() else {
            return Ok(());
        };
        if binding.source == self.buffer.text() && !binding.dirty {
            let result = binding
                .last_error
                .as_ref()
                .map_or(Ok(()), |s| Err(Error::Invalid(s.clone())));
            self.syntax_analyzer = Some(binding);
            return result;
        }
        let result = if let Some(analyzer) = &binding.analyzer {
            analyzer
                .analyze_syntax(self.buffer.text(), &binding.request)
                .and_then(|a| self.apply_analysis(a))
        } else {
            self.syntax.clear();
            Ok(())
        };
        binding.source = self.buffer.text().into();
        binding.dirty = false;
        binding.last_error = result.as_ref().err().map(ToString::to_string);
        if result.is_err() {
            self.syntax.clear()
        }
        self.syntax_analyzer = Some(binding);
        result
    }
    pub fn syntax_error(&self) -> Option<&str> {
        self.syntax_analyzer
            .as_ref()
            .and_then(|b| b.last_error.as_deref())
    }
}
