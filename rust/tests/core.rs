use tuivory::{CANDIDATE_JSON, Color, ColorProfile, Theme, TokenDocument, profile_for_colors};

#[test]
fn embedded_document_resolves_all_palettes_and_preserves_color_kinds() {
    let d = TokenDocument::candidate().unwrap();
    assert_eq!(d.roles().len(), 16);
    assert_eq!(d.palette_names().count(), 12);
    for theme in [Theme::Dark, Theme::Light, Theme::Blackwhite] {
        for profile in [
            ColorProfile::Ansi8,
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
        ] {
            let raw = d.tokens(theme, profile).unwrap();
            let palette = d.palette(theme, profile).unwrap();
            assert_eq!(palette.styles().len(), 16);
            for role in d.roles() {
                let pair = &raw.pairs()[role];
                let style = palette.style(role).unwrap();
                assert_eq!(style.foreground, pair.foreground.parse::<Color>().unwrap());
                assert_eq!(style.background, pair.background.parse::<Color>().unwrap());
                assert_eq!(style.bold, pair.font_weight == "bold");
            }
        }
    }
    let palette = d.palette(Theme::Dark, ColorProfile::Ansi8).unwrap();
    assert!(matches!(
        palette.style("body").unwrap().foreground,
        Color::Indexed(_)
    ));
    assert!(palette.style("missing").is_err());
}

#[test]
fn profile_selection_matches_host_count_contract() {
    for (count, expected) in [
        (-1, ColorProfile::Truecolor),
        (0, ColorProfile::Truecolor),
        (1, ColorProfile::Ansi8),
        (8, ColorProfile::Ansi8),
        (9, ColorProfile::Ansi16),
        (16, ColorProfile::Ansi16),
        (17, ColorProfile::Indexed256),
        (256, ColorProfile::Indexed256),
        (257, ColorProfile::Truecolor),
        (16_777_216, ColorProfile::Truecolor),
    ] {
        assert_eq!(profile_for_colors(count, false), expected);
        assert_eq!(
            profile_for_colors(count, true),
            if (1..=8).contains(&count) {
                ColorProfile::Ansi8
            } else {
                ColorProfile::Ansi16
            }
        );
    }
}

#[test]
fn colors_are_strict_and_keep_indices_separate_from_rgb() {
    assert_eq!("255".parse::<Color>().unwrap(), Color::Indexed(255));
    assert_eq!("#aB00ff".parse::<Color>().unwrap(), Color::Rgb(171, 0, 255));
    for bad in [
        "",
        "-1",
        "256",
        "01",
        "+1",
        " 1",
        "#fff",
        "#gg0000",
        "#１２３４５６",
    ] {
        assert!(bad.parse::<Color>().is_err(), "accepted {bad:?}");
    }
}

fn rejects_edit(edit: impl FnOnce(&mut serde_json::Value)) {
    let mut d: serde_json::Value = serde_json::from_str(CANDIDATE_JSON).unwrap();
    edit(&mut d);
    assert!(TokenDocument::from_json(&d.to_string()).is_err());
}

#[test]
fn rejects_incomplete_unknown_and_out_of_range_data() {
    rejects_edit(|d| d["format"] = "unknown".into());
    rejects_edit(|d| d["roles"] = serde_json::json!([]));
    rejects_edit(|d| d["palettes"] = serde_json::json!({}));
    rejects_edit(|d| d["roles"][0] = "".into());
    rejects_edit(|d| d["roles"][1] = d["roles"][0].clone());
    rejects_edit(|d| {
        d["palettes"]["dark-8"]
            .as_object_mut()
            .unwrap()
            .remove("body");
    });
    rejects_edit(|d| d["palettes"]["dark-8"]["unknown"] = d["palettes"]["dark-8"]["body"].clone());
    rejects_edit(|d| d["unknown"] = true.into());
    rejects_edit(|d| d["palettes"]["dark-8"]["body"]["unknown"] = true.into());
    rejects_edit(|d| d["palettes"]["dark-8"]["body"]["foreground"] = "8".into());
    rejects_edit(|d| d["palettes"]["dark-16"]["body"]["background"] = "16".into());
    rejects_edit(|d| d["palettes"]["dark-256"]["body"]["background"] = "256".into());
    rejects_edit(|d| d["palettes"]["dark-8"]["body"]["foreground"] = "#ffffff".into());
    rejects_edit(|d| d["palettes"]["dark-truecolor"]["body"]["referenceForeground"] = "7".into());
    rejects_edit(|d| d["palettes"]["dark-truecolor"]["body"]["fontWeight"] = "dim".into());
    rejects_edit(|d| d["palettes"]["dark-auto"] = d["palettes"]["dark-8"].clone());
    rejects_edit(|d| d["palettes"]["unknown-8"] = d["palettes"]["dark-8"].clone());
}

#[test]
fn rejects_duplicate_json_keys_and_trailing_documents() {
    let raw: serde_json::Value = serde_json::from_str(CANDIDATE_JSON).unwrap();
    let pair = raw["palettes"]["dark-8"]["body"].to_string();
    let duplicated_roles = format!(
        r#"{{"format":"tuivory.tokens.draft","roles":["body"],"palettes":{{"dark-8":{{"body":{pair},"body":{pair}}}}}}}"#
    );
    for data in [
        CANDIDATE_JSON.replacen(
            "\"format\":",
            "\"format\": \"tuivory.tokens.draft\", \"format\":",
            1,
        ),
        CANDIDATE_JSON.replacen("\"dark-8\": {", "\"dark-8\": {}, \"dark-8\": {", 1),
        duplicated_roles,
        format!("{CANDIDATE_JSON} {{}}"),
    ] {
        assert!(TokenDocument::from_json(&data).is_err());
    }
}

#[test]
fn missing_palette_does_not_fall_back() {
    let mut raw: serde_json::Value = serde_json::from_str(CANDIDATE_JSON).unwrap();
    raw["palettes"].as_object_mut().unwrap().remove("light-8");
    let partial = TokenDocument::from_json(&raw.to_string()).unwrap();
    assert!(partial.palette(Theme::Light, ColorProfile::Ansi8).is_err());
    assert!(partial.palette(Theme::Dark, ColorProfile::Ansi8).is_ok());
}
