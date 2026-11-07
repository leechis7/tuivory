use tuivory::{
    dialog::{Dialog, DialogButton, DialogEvent},
    layout::CellRect,
};

fn model(labels: &[&str]) -> Dialog {
    Dialog::new(
        "Confirm",
        "Confirm operation?",
        labels
            .iter()
            .enumerate()
            .map(|(i, label)| DialogButton {
                id: i.to_string(),
                label: (*label).into(),
                disabled: false,
            })
            .collect(),
        &(labels.len() - 1).to_string(),
    )
    .unwrap()
}

#[test]
fn centered_rows_and_focus_at_small_heights() {
    for labels in [
        ["확인", "다시 연결한 다음 계속", "설정 열기", "취소"],
        ["OK", "Reconnect and continue", "Open settings", "Cancel"],
    ] {
        for count in 1..=labels.len() {
            let mut dialog = model(&labels[..count]);
            let focus = (count - 1).to_string();
            assert_eq!(
                dialog.handle("activate"),
                Some(DialogEvent::Activate(focus.clone()))
            );
            assert_eq!(
                dialog.handle("cancel"),
                Some(DialogEvent::Cancel(focus.clone()))
            );
            for width in [1, 36, 116] {
                for height in [1, 12] {
                    let area = CellRect {
                        x: 5,
                        y: 3,
                        width,
                        height,
                    };
                    let layout = dialog.layout(area);
                    assert!(layout.buttons.iter().any(|b| b.id == focus));
                    for row in area.y..area.y + height {
                        let buttons: Vec<_> =
                            layout.buttons.iter().filter(|b| b.rect.y == row).collect();
                        let (Some(first), Some(last)) = (buttons.first(), buttons.last()) else {
                            continue;
                        };
                        let end = last.rect.x + last.rect.width;
                        assert!(end <= area.x + width);
                        assert_eq!(first.rect.x - area.x, (width - (end - first.rect.x)) / 2);
                        for button in buttons {
                            assert_eq!(
                                dialog.click(&layout, button.rect.x, row),
                                Some(DialogEvent::Activate(button.id.clone()))
                            );
                        }
                    }
                    assert!(dialog.focus(&focus));
                }
            }
        }
    }
}

#[cfg(feature = "ratatui")]
#[test]
fn widget_and_mouse_use_the_clipped_output_buffer() {
    use ratatui::{buffer::Buffer, layout::Rect};
    use tuivory::{
        ColorProfile, Theme,
        ratatui::{DialogWidget, Styles},
    };
    let mut dialog = model(&[
        "Commit and connect",
        "Roll back changes and connect",
        "Cancel",
    ]);
    let styles = Styles::new(Theme::Dark, ColorProfile::Ansi8).unwrap();
    let area = Rect::new(0, 0, 40, 12);
    let mut buffer = Buffer::empty(area);
    let layout = DialogWidget {
        dialog: &dialog,
        styles: &styles,
        focused: true,
        ascii: false,
    }
    .draw(Rect::new(0, 0, 120, 12), &mut buffer);
    let cancel = layout.buttons.last().unwrap();
    let rect = cancel.rect;
    assert_eq!(rect.x, (40 - rect.width) / 2);
    let painted: String = (rect.x..rect.x + rect.width)
        .map(|x| buffer[(x as u16, rect.y as u16)].symbol())
        .collect();
    assert!(painted.contains("Cancel"));
    assert_eq!(dialog.click(&layout, rect.x - 1, rect.y), None);
    assert_eq!(
        dialog.click(&layout, rect.x, rect.y),
        Some(DialogEvent::Activate("2".into()))
    );
}
