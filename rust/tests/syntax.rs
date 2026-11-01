use std::sync::{
    Arc,
    atomic::{AtomicUsize, Ordering},
};
#[cfg(feature = "syntax-sql")]
use tuivory::syntax::SyntaxAnalyzer;
use tuivory::{
    syntax::{SyntaxAnalysis, SyntaxRequest, SyntaxToken, role_style},
    text::TextDocument,
};

#[cfg(feature = "ratatui")]
#[test]
fn dark_eight_syntax_roles_after_draw() {
    use tuivory::{
        ColorProfile, Theme,
        text::SyntaxSpan,
        ui::{
            Terminal,
            backend::TestBackend,
            components::{Styles, TextWidget},
            style::{Color, Modifier},
        },
    };
    let styles = Styles::new(Theme::Dark, ColorProfile::Ansi8).unwrap();
    let roles = [
        "keyword",
        "function",
        "type",
        "string",
        "number",
        "comment",
        "parameter",
    ];
    let mut doc = TextDocument::editor("xKFTSNCP");
    doc.line_numbers = false;
    doc.buffer.select(0, 0);
    doc.set_syntax(
        roles
            .iter()
            .enumerate()
            .map(|(i, r)| SyntaxSpan {
                start: i + 1,
                end: i + 2,
                role: format!("syntax.{r}"),
            })
            .collect(),
    )
    .unwrap();
    let mut terminal = Terminal::new(TestBackend::new(20, 3)).unwrap();
    terminal
        .draw(|f| {
            f.render_widget(
                TextWidget {
                    model: &mut doc,
                    styles: &styles,
                    focused: false,
                },
                f.area(),
            )
        })
        .unwrap();
    let mut seen = Vec::new();
    for (i, role) in roles.iter().enumerate() {
        let cell = &terminal.backend().buffer()[(i as u16 + 1, 0)];
        let expected = styles.role(&format!("syntax.{role}")).unwrap();
        assert_eq!(Some(cell.fg), expected.fg, "{role}");
        assert_eq!(Some(cell.bg), expected.bg, "{role}");
        assert_eq!(cell.modifier, expected.add_modifier, "{role}");
        assert_eq!(cell.bg, Color::Indexed(0));
        assert!(matches!(cell.fg, Color::Indexed(3 | 7)));
        assert!(!cell.modifier.intersects(Modifier::DIM | Modifier::REVERSED));
        seen.push((cell.fg, cell.modifier));
    }
    seen.sort_by_key(|x| format!("{x:?}"));
    seen.dedup();
    assert_eq!(seen.len(), 7);
    let mono = Styles::new(Theme::Blackwhite, ColorProfile::Ansi8).unwrap();
    assert_eq!(
        mono.role("syntax.keyword").unwrap().fg,
        mono.role("syntax.function").unwrap().fg
    );
}

#[test]
fn role_fallback_and_injection() {
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("data/syntax-cases.json")).unwrap();
    for (role, expected) in fixture["role_fallbacks"].as_object().unwrap() {
        assert_eq!(role_style(role), expected.as_str().unwrap())
    }
    let calls = Arc::new(AtomicUsize::new(0));
    let count = calls.clone();
    let analyzer = Arc::new(move |s: &str, _: &SyntaxRequest| {
        count.fetch_add(1, Ordering::Relaxed);
        if s.contains('!') {
            return Err(tuivory::Error::Invalid("failed".into()));
        }
        Ok(SyntaxAnalysis {
            source: s.into(),
            language: "custom".into(),
            dialect: String::new(),
            tokens: vec![SyntaxToken {
                start: 0,
                end: s.len(),
                role: "future-role".into(),
            }],
        })
    });
    let mut doc = TextDocument::editor("한글 é 😀");
    doc.set_syntax_analyzer(Some(analyzer), SyntaxRequest::default())
        .unwrap();
    for _ in 0..5 {
        doc.layout(20, 4);
    }
    assert_eq!(calls.load(Ordering::Relaxed), 1);
    assert_eq!(doc.syntax[0].role, "body");
    doc.buffer.select(0, 0);
    doc.handle("insert", "!");
    assert!(doc.syntax_error().is_some());
    assert!(doc.syntax.is_empty());
    doc.handle("undo", "");
    assert!(doc.syntax_error().is_none());
    assert_eq!(doc.buffer.text(), "한글 é 😀");
    let bad = Arc::new(|_: &str, _: &SyntaxRequest| {
        Ok(SyntaxAnalysis {
            source: "stale".into(),
            language: String::new(),
            dialect: String::new(),
            tokens: vec![],
        })
    });
    assert!(
        doc.set_syntax_analyzer(Some(bad), SyntaxRequest::default())
            .is_err()
    );
    assert_eq!(doc.syntax[0].role, "body");
    doc.buffer.select_bytes(6, 0).unwrap();
    assert_eq!(doc.buffer.selection_bytes(), (0, 6));
    assert!(doc.buffer.select_bytes(1, 6).is_err());
    doc.buffer.replace_bytes(0, 6, "가\r\n나").unwrap();
    assert!(doc.buffer.text().starts_with("가\r\n나"));
    doc.handle("undo", "");
    assert_eq!(doc.buffer.text(), "한글 é 😀");
    doc.handle("redo", "");
    assert!(doc.buffer.text().starts_with("가\r\n나"));
    doc.buffer.state.read_only = true;
    let original = doc.buffer.text().to_owned();
    doc.buffer.replace_bytes(0, 0, "bad").unwrap();
    assert_eq!(doc.buffer.text(), original);
    doc.buffer.secret = true;
    doc.set_search_matches(vec![tuivory::text::TextRange { start: 0, end: 1 }])
        .unwrap();
    doc.refresh_syntax().unwrap();
    assert!(doc.syntax.is_empty());
    assert!(!format!("{doc:?}").contains("가\r\n나"));
}

#[test]
fn supplied_analysis_and_search_expire() {
    let mut doc = TextDocument::editor("SELECT 1");
    let analysis = SyntaxAnalysis {
        source: "SELECT 1".into(),
        language: "sql".into(),
        dialect: "oracle".into(),
        tokens: vec![SyntaxToken {
            start: 0,
            end: 6,
            role: "keyword".into(),
        }],
    };
    doc.set_syntax_analysis(analysis.clone()).unwrap();
    doc.set_search_matches(vec![tuivory::text::TextRange { start: 0, end: 6 }])
        .unwrap();
    doc.buffer.select(0, 0);
    let rows = doc.layout(40, 3);
    assert!(
        rows[0]
            .spans
            .iter()
            .any(|s| s.start == 2 && s.role == "edited")
    );
    doc.handle("insert", "X");
    assert!(doc.syntax.is_empty());
    let rows = doc.layout(40, 3);
    assert!(!rows[0].spans.iter().any(|s| s.role == "edited"));
    assert!(doc.set_syntax_analysis(analysis).is_err());
    assert!(
        doc.set_search_matches(vec![tuivory::text::TextRange { start: 10, end: 9 }])
            .is_err()
    );
}

#[cfg(feature = "syntax-sql")]
#[test]
fn sql_shared_cases_and_incomplete_prefixes() {
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("data/syntax-cases.json")).unwrap();
    let analyzer = tuivory::syntax_sql::SQLAnalyzer::new();
    for case in fixture["cases"].as_array().unwrap() {
        let source = case["source"].as_str().unwrap();
        let request = SyntaxRequest {
            language: case["language"].as_str().unwrap().into(),
            dialect: "oracle".into(),
        };
        let analysis = analyzer.analyze_syntax(source, &request).unwrap();
        let expected: Vec<SyntaxToken> = serde_json::from_value(case["tokens"].clone()).unwrap();
        assert_eq!(analysis.tokens, expected, "{}", case["name"]);
        assert_eq!(analysis.source, source);
        assert_eq!(analysis.language, request.language);
        assert_eq!(analysis.dialect, "oracle");
        let mut doc = TextDocument::editor(source);
        doc.set_syntax_analyzer(Some(Arc::new(analyzer.clone())), request)
            .unwrap();
        for (index, _) in source.char_indices() {
            let text = &source[..index];
            analyzer
                .analyze_syntax(text, &SyntaxRequest::default())
                .unwrap()
                .validate(text)
                .unwrap();
            doc.set_text(text);
            assert!(
                doc.syntax_error().is_none(),
                "{} prefix {}",
                case["name"],
                index
            );
        }
    }
    for request in [
        SyntaxRequest {
            language: "go".into(),
            dialect: String::new(),
        },
        SyntaxRequest {
            dialect: "postgresql".into(),
            ..Default::default()
        },
    ] {
        assert!(analyzer.analyze_syntax("SELECT 1", &request).is_err())
    }
}

#[cfg(all(feature = "syntax-sql", feature = "ratatui"))]
#[test]
fn sql_rendering_and_state_priority() {
    use tuivory::{
        ColorProfile, Theme,
        ui::{
            Terminal,
            backend::TestBackend,
            components::{Styles, TextWidget},
        },
    };
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let styles = Styles::new(theme, profile).unwrap();
            let mut doc = TextDocument::editor("SELECT '한글😀' FROM 표 WHERE id=:id");
            doc.line_numbers = false;
            doc.buffer.select(0, 0);
            doc.set_syntax_analyzer(
                Some(Arc::new(tuivory::syntax_sql::SQLAnalyzer::new())),
                SyntaxRequest::default(),
            )
            .unwrap();
            let mut terminal = Terminal::new(TestBackend::new(40, 5)).unwrap();
            terminal
                .draw(|f| {
                    f.render_widget(
                        TextWidget {
                            model: &mut doc,
                            styles: &styles,
                            focused: true,
                        },
                        f.area(),
                    )
                })
                .unwrap();
            assert_eq!(
                terminal.backend().buffer()[(1, 0)].bg,
                styles.role("surface").unwrap().bg.unwrap()
            );
            doc.buffer.select(0, 6);
            doc.set_search_matches(vec![tuivory::text::TextRange { start: 0, end: 6 }])
                .unwrap();
            terminal
                .draw(|f| {
                    f.render_widget(
                        TextWidget {
                            model: &mut doc,
                            styles: &styles,
                            focused: true,
                        },
                        f.area(),
                    )
                })
                .unwrap();
            assert_eq!(
                terminal.backend().buffer()[(1, 0)].bg,
                styles.role("selection").unwrap().bg.unwrap()
            );
            doc.buffer.state.disabled = true;
            terminal
                .draw(|f| {
                    f.render_widget(
                        TextWidget {
                            model: &mut doc,
                            styles: &styles,
                            focused: true,
                        },
                        f.area(),
                    )
                })
                .unwrap();
            assert_eq!(
                terminal.backend().buffer()[(1, 0)].fg,
                styles
                    .text_on_surface("disabled", "surface")
                    .unwrap()
                    .fg
                    .unwrap()
            );
        }
    }
}

#[cfg(feature = "syntax-sql")]
#[test]
fn sql_long_document() {
    let source = "SELECT NVL(:id, '한글😀'), 1e3 FROM 표; -- comment\n".repeat(10_000);
    let analyzer = tuivory::syntax_sql::SQLAnalyzer::new();
    let start = std::time::Instant::now();
    let analysis = analyzer
        .analyze_syntax(&source, &SyntaxRequest::default())
        .unwrap();
    analysis.validate(&source).unwrap();
    assert!(analysis.tokens.len() > 100_000);
    let mut doc = TextDocument::editor(&source);
    doc.set_syntax_analyzer(Some(Arc::new(analyzer)), SyntaxRequest::default())
        .unwrap();
    doc.scroll_y = 9_990;
    doc.buffer.select(0, 0);
    doc.layout(80, 20);
    assert_eq!(doc.buffer.text(), source);
    println!(
        "SQL 10000 lines, {} bytes, analysis+binding+layout {:?}",
        source.len(),
        start.elapsed()
    );
}
