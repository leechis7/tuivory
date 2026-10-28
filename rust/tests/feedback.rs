use tuivory::feedback::{DataState, Notice, NoticeAction, NoticeQueue, Progress};
#[test]
fn lifetime_priority_and_requests() {
    let mut q = NoticeQueue::new(3).unwrap();
    q.push(Notice {
        id: "info".into(),
        text: "Transient".into(),
        severity: "info".into(),
        expires_at: 5,
        ..Default::default()
    })
    .unwrap();
    q.push(Notice {
        id: "error".into(),
        text: "Important".into(),
        severity: "error".into(),
        expires_at: 1,
        actions: vec![
            NoticeAction {
                id: "disabled".into(),
                disabled: true,
                ..Default::default()
            },
            NoticeAction {
                id: "retry".into(),
                label: "Retry".into(),
                disabled: false,
            },
        ],
        ..Default::default()
    })
    .unwrap();
    assert_eq!(q.visible(100).len(), 1);
    assert_eq!(q.visible(100)[0].id, "error");
    assert_eq!(q.layout(20, 1, 0)[0].role, "error");
    let e = q.handle("activate", 100, 2);
    assert_eq!((e.kind.as_str(), e.action.as_str()), ("action", "retry"));
    assert_eq!(q.handle("dismiss", 100, 2).kind, "dismiss");
    assert_eq!(q.visible(100).len(), 1);
    assert_eq!(q.expire(100).len(), 1);
    q.dismiss("error");
    assert!(q.visible(100).is_empty());
    let mut full = NoticeQueue::new(1).unwrap();
    full.push(Notice {
        id: "a".into(),
        severity: "error".into(),
        ..Default::default()
    })
    .unwrap();
    assert!(
        full.push(Notice {
            id: "b".into(),
            severity: "error".into(),
            ..Default::default()
        })
        .is_err()
    );
    assert_eq!(full.visible(0)[0].id, "a");
}
#[test]
fn progress_and_data_states() {
    let mut p = Progress {
        id: "p".into(),
        status: "loading".into(),
        cancellable: true,
        current: 200,
        total: 100,
        ..Default::default()
    };
    assert_eq!(p.request_cancel().kind, "cancel");
    assert_eq!(p.status, "loading");
    assert!(p.layout(40, 0)[1].text.contains("100%"));
    p.total = 0;
    assert_ne!(p.layout(40, 0)[1].text, p.layout(40, 1)[1].text);
    p.status = "success".into();
    assert!(p.request_cancel().kind.is_empty());
    assert!(
        p.layout(3, 0)
            .iter()
            .all(|r| tuivory::components::cells(&r.text) <= 3)
    );
    assert_eq!(
        DataState {
            kind: "error".into(),
            text: "failure".into(),
            ..Default::default()
        }
        .layout(20)[0]
            .role,
        "error"
    );
}
