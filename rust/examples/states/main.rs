//! Render real component states for all twelve palettes; no terminal or DB needed.
#[path = "../playground/snapshot.rs"]
mod snapshot;
use std::{error::Error, path::PathBuf};
use tuivory::ui::{Terminal, backend::TestBackend, layout::Rect, widgets::Widget};
use tuivory::{
    ColorProfile, Theme,
    collections::{ListItem, ListModel},
    forms::{Form, FormField},
    interaction::ControlState,
    layout::{Help, Shortcut},
    ui::components::{FormWidget, HelpWidget, ListWidget, Styles},
};
fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    let en = args.windows(2).any(|v| v[0] == "--lang" && v[1] == "en");
    let output = PathBuf::from(
        args.windows(2)
            .find(|v| v[0] == "--snapshot")
            .ok_or("use --snapshot PATH [--lang ko|en]")?[1]
            .clone(),
    );
    let tr = |ko: &str, en_text: &str| {
        if en {
            en_text.to_owned()
        } else {
            ko.to_owned()
        }
    };
    let list = ListModel::new(vec![
        ListItem {
            id: "on".into(),
            label: tr("사용 가능한 항목", "Available item"),
            ..Default::default()
        },
        ListItem {
            id: "off".into(),
            label: tr("비활성 항목", "Disabled item"),
            disabled: true,
            ..Default::default()
        },
    ])?;
    let form = Form::new(vec![
        FormField {
            id: "on".into(),
            kind: "text".into(),
            label: tr("사용 가능한 입력", "Enabled input"),
            value: "Tuivory".into(),
            ..Default::default()
        },
        FormField {
            id: "off".into(),
            kind: "text".into(),
            label: tr("비활성 입력", "Disabled input"),
            value: "Tuivory".into(),
            state: ControlState {
                disabled: true,
                ..Default::default()
            },
            ..Default::default()
        },
        FormField {
            id: "run".into(),
            kind: "button".into(),
            label: tr("실행 가능", "Run"),
            ..Default::default()
        },
        FormField {
            id: "save".into(),
            kind: "button".into(),
            label: tr("저장 불가", "Save unavailable"),
            state: ControlState {
                disabled: true,
                ..Default::default()
            },
            ..Default::default()
        },
    ])?;
    let help = Help::new(vec![
        Shortcut {
            key: "Enter".into(),
            text: tr("항목 실행", "Activate item"),
            priority: 2,
            disabled: false,
        },
        Shortcut {
            key: "Ctrl+S".into(),
            text: tr("저장 불가", "Save unavailable"),
            priority: 1,
            disabled: true,
        },
    ])?;
    let mut terminal = Terminal::new(TestBackend::new(108, 72))?;
    terminal.draw(|frame| {
        for (y, (profile, name)) in [
            (ColorProfile::Ansi8, "8"),
            (ColorProfile::Ansi16, "16"),
            (ColorProfile::Indexed256, "256"),
            (ColorProfile::Truecolor, "True Color"),
        ]
        .into_iter()
        .enumerate()
        {
            for (x, (theme, label)) in [
                (Theme::Dark, "Dark"),
                (Theme::Light, "Light"),
                (Theme::Blackwhite, "Black & White"),
            ]
            .into_iter()
            .enumerate()
            {
                let styles = Styles::new(theme, profile).unwrap();
                let area = Rect::new(x as u16 * 36, y as u16 * 18, 36, 18);
                let title = format!(" {label} · {name} ");
                let block = styles.block(&title, false).unwrap();
                let inner = block.inner(area);
                block.render(area, frame.buffer_mut());
                frame.render_widget(
                    ListWidget {
                        model: &list,
                        styles: &styles,
                        focused: false,
                        ascii: false,
                    },
                    Rect::new(inner.x + 1, inner.y + 1, inner.width - 2, 2),
                );
                frame.render_widget(
                    FormWidget {
                        form: &form,
                        styles: &styles,
                        focused: false,
                    },
                    Rect::new(inner.x + 1, inner.y + 4, inner.width - 2, 8),
                );
                frame.render_widget(
                    HelpWidget {
                        model: &help,
                        styles: &styles,
                    },
                    Rect::new(inner.x + 1, inner.y + 13, inner.width - 2, 2),
                );
            }
        }
    })?;
    snapshot::write(&output, terminal.backend().buffer())?;
    Ok(())
}
