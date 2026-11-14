//! Database-free host connecting the public shared workspace components.
#[path = "../playground/snapshot.rs"]
mod snapshot;
use std::{
    error::Error,
    io::{self, IsTerminal},
    time::Duration,
};
use tuivory::ui::terminal::{
    cursor::Show,
    event::{
        self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind, KeyModifiers,
        MouseButton, MouseEventKind,
    },
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use tuivory::ui::{
    Frame, Terminal,
    backend::{CrosstermBackend, TestBackend},
    layout::{Constraint, Layout, Rect},
    widgets::Paragraph,
};
use tuivory::{
    ColorProfile, Theme,
    components::*,
    drag::{DragAction, DragMove, DragOptions, DragPointer, DragState, DropPosition, DropRequest},
    tree::{Tree, TreeAction, TreeNode, TreeState},
    ui::components::{
        LineWidget, SplitRects, Styles, TabsWidget, TreeWidget, draw_split_divider,
        split_controlled_rects,
    },
};
struct App {
    drag_enabled: bool,
    tab_drag: DragState,
    tree_drag: DragState,
    tab_area: Rect,
    drag_press: Option<(bool, u16, u16)>,
    en: bool,
    ascii: bool,
    theme: Theme,
    profile: ColorProfile,
    styles: Styles,
    tabs: Tabs,
    items: Vec<TabItem>,
    tab: TabState,
    tree: Tree,
    tree_state: TreeState,
    path: Vec<PathItem>,
    focus: usize,
    focus_order: [usize; 3],
    quit_key: char,
    active_second: bool,
    rows: bool,
    column: SplitState,
    row: SplitState,
    message: String,
    body: Rect,
    tree_inner: Rect,
    content_inner: Rect,
    rects: SplitRects,
    column_control: SplitControl,
    row_control: SplitControl,
    content_scroll: u16,
}
impl App {
    fn drop_options() -> DragOptions {
        DragOptions {
            auto_scroll: true,
            hover_expand: true,
            locked: vec!["root".into()],
            ..DragOptions::default()
        }
    }
    fn apply_drop(&mut self, tabs: bool, r: DropRequest) {
        let result = if tabs {
            self.tabs.apply_drop(&r).map(|next| {
                self.items = next.items().to_vec();
                self.tabs = next;
                self.tabs.reconcile(&mut self.tab);
            })
        } else {
            self.tree.apply_drop(&r).map(|next| {
                self.tree = next;
                if r.position == DropPosition::Inside {
                    self.tree_state.expanded.insert(r.target_id.clone());
                }
                self.tree
                    .reconcile(&mut self.tree_state, usize::from(self.tree_inner.height));
            })
        };
        self.message = if let Err(error) = result {
            format!("reject: {error}")
        } else {
            format!(
                "drop {}: {} {} {}",
                if tabs { "tabs" } else { "tree" },
                r.source_id,
                match r.position {
                    DropPosition::Before => "before",
                    DropPosition::After => "after",
                    DropPosition::Inside => "inside",
                },
                r.target_id
            )
        };
    }
    fn cancel_drop(&mut self) {
        self.tab_drag.cancel();
        self.tree_drag.cancel();
        self.drag_press = None;
    }
    fn drag_mouse(&mut self, mouse: tuivory::ui::terminal::event::MouseEvent) -> bool {
        if !self.drag_enabled {
            return false;
        }
        let action = match mouse.kind {
            MouseEventKind::Down(MouseButton::Left) => DragAction::Down,
            MouseEventKind::Drag(MouseButton::Left) | MouseEventKind::Moved => DragAction::Move,
            MouseEventKind::Up(MouseButton::Left) => DragAction::Up,
            _ => {
                if self.tab_drag.captured() || self.tree_drag.captured() {
                    self.cancel_drop()
                }
                return false;
            }
        };
        let point = (mouse.column, mouse.row).into();
        let tabs = if self.tab_drag.captured() {
            true
        } else if self.tree_drag.captured() {
            false
        } else if action == DragAction::Down && self.tab_area.contains(point) {
            true
        } else if action == DragAction::Down && self.tree_inner.contains(point) {
            false
        } else if action == DragAction::Up {
            if let Some((tabs, _, _)) = self.drag_press {
                tabs
            } else {
                return false;
            }
        } else {
            return false;
        };
        if action == DragAction::Down {
            self.drag_press = Some((tabs, mouse.column, mouse.row));
        }
        let area = if tabs { self.tab_area } else { self.tree_inner };
        let p = DragPointer {
            action,
            x: i32::from(mouse.column) - i32::from(area.x),
            y: i32::from(mouse.row) - i32::from(area.y),
            width: usize::from(area.width),
            height: usize::from(area.height),
        };
        let request = if tabs {
            self.tabs.drag(
                &mut self.tab,
                &mut self.tab_drag,
                p,
                &Self::drop_options(),
                None,
            )
        } else {
            self.tree.drag(
                &mut self.tree_state,
                &mut self.tree_drag,
                p,
                &Self::drop_options(),
                None,
            )
        };
        if let Some(r) = request {
            self.apply_drop(tabs, r)
        } else if action == DragAction::Up {
            let result = if tabs {
                &self.tab_drag.result
            } else {
                &self.tree_drag.result
            };
            let click = self
                .drag_press
                .is_some_and(|(_, x, y)| x.abs_diff(mouse.column) < 2 && y.abs_diff(mouse.row) < 2)
                && !matches!(result.as_str(), "stale" | "reject" | "drop")
                && area.contains(point);
            if click {
                if tabs {
                    let e = self.tabs.click(
                        &mut self.tab,
                        usize::from(mouse.column - area.x),
                        usize::from(area.width),
                    );
                    if e.is_some() {
                        self.focus = 0;
                    }
                    self.tab_event(e)
                } else {
                    self.focus = 1;
                    self.active_second = false;
                    if let Some(e) = self.tree.click(
                        &mut self.tree_state,
                        usize::from(mouse.column - area.x),
                        usize::from(mouse.row - area.y),
                        usize::from(area.height),
                    ) {
                        self.message = format!("{e:?}")
                    }
                }
            }
        }
        if action == DragAction::Up {
            self.drag_press = None;
        }
        true
    }
    fn text<'a>(&self, ko: &'a str, en: &'a str) -> &'a str {
        if self.en { en } else { ko }
    }
    fn spec(&self) -> SplitSpec {
        if self.rows {
            SplitSpec {
                first_min: 4,
                second_min: 4,
            }
        } else {
            SplitSpec {
                first_min: 20,
                second_min: 24,
            }
        }
    }
    fn split_state(&self) -> &SplitState {
        if self.rows { &self.row } else { &self.column }
    }
    fn control(&self) -> &SplitControl {
        if self.rows {
            &self.row_control
        } else {
            &self.column_control
        }
    }
    fn side(&self) -> SplitSide {
        if self.rows {
            SplitSide::Second
        } else {
            SplitSide::First
        }
    }
    fn split_total(&self) -> usize {
        usize::from(if self.rows {
            self.body.height
        } else {
            self.body.width
        })
    }
    fn split_parts(&mut self) -> (&mut SplitControl, &mut SplitState) {
        if self.rows {
            (&mut self.row_control, &mut self.row)
        } else {
            (&mut self.column_control, &mut self.column)
        }
    }
    fn sync_split_focus(&mut self) {
        if self.control().collapsed() != SplitSide::Neither {
            self.active_second = self.control().visible_focus(self.active_second);
            if self.focus != 0 {
                self.focus = if self.active_second { 2 } else { 1 };
            }
        }
    }
    fn cycle_focus(&mut self, forward: bool) {
        let at = self
            .focus_order
            .iter()
            .position(|f| *f == self.focus)
            .unwrap_or(0);
        let delta = if forward { 1 } else { 2 };
        for step in 1..=3 {
            let next = self.focus_order[(at + delta * step) % 3];
            if (next == 1 && self.control().collapsed() == SplitSide::First)
                || (next == 2 && self.control().collapsed() == SplitSide::Second)
            {
                continue;
            }
            self.focus = next;
            if next != 0 {
                self.active_second = next == 2;
            }
            break;
        }
    }
    fn toggle_split(&mut self) {
        let (spec, total, side) = (self.spec(), self.split_total(), self.side());
        let (control, state) = self.split_parts();
        control.toggle(spec, state, total, side);
        self.sync_split_focus();
    }
    fn resize(&mut self, position: usize) {
        let (spec, total) = (self.spec(), self.split_total());
        let (control, state) = self.split_parts();
        control.resize(spec, state, total, position);
    }
    fn tab_event(&mut self, event: Option<TabEvent>) {
        if let Some(event) = event {
            self.message = format!("{event:?}");
            match event {
                TabEvent::Close(id) => {
                    if let Some(index) = self.items.iter().position(|i| i.id == id) {
                        if self.items[index].edited {
                            self.message = self
                                .text(
                                    "변경된 문서: 앱이 닫기를 보류했습니다.",
                                    "Edited document: the host retained the tab.",
                                )
                                .into()
                        } else {
                            self.items.remove(index);
                            self.tabs = Tabs::new(self.items.clone()).unwrap();
                            self.tabs.reconcile(&mut self.tab);
                        }
                    }
                }
                TabEvent::Activate(_) => self.content_scroll = 0,
                TabEvent::Focus(_) => (),
            }
        }
    }
    fn tree_action(&mut self, action: TreeAction) {
        if let Some(event) = self.tree.handle(
            &mut self.tree_state,
            action,
            usize::from(self.tree_inner.height),
        ) {
            self.message = format!("{event:?}")
        }
    }
    fn draw(&mut self, frame: &mut Frame<'_>) {
        let area = frame.area();
        frame.render_widget(
            Paragraph::new("").style(self.styles.role("surface").unwrap()),
            area,
        );
        let layout = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(2),
            Constraint::Min(0),
            Constraint::Length(1),
            Constraint::Length(1),
        ])
        .split(area);
        frame.render_widget(
            Paragraph::new(format!(
                "TUIVORY Workspace · {} / {} · {}",
                self.theme.as_str(),
                self.profile.as_str(),
                self.text("이름·보조 설명·개수", "Name · Secondary · Count")
            ))
            .style(self.styles.text_on_surface("body", "surface").unwrap()),
            layout[0],
        );
        frame.render_widget(
            LineWidget::new(
                breadcrumbs(&self.path, usize::from(layout[1].width)),
                &self.styles,
            )
            .unwrap(),
            layout[1],
        );
        let mut tabs = TabsWidget::new(&self.tabs, &self.styles)
            .unwrap()
            .with_ascii(self.ascii);
        tabs.focused = self.focus == 0;
        self.tab_area = layout[2];
        if self.drag_enabled {
            tabs = tabs.with_drag(&mut self.tab_drag, self.ascii);
        }
        frame.render_stateful_widget(tabs, layout[2], &mut self.tab);
        self.body = layout[3];
        self.rects = split_controlled_rects(
            self.body,
            self.spec(),
            self.split_state(),
            self.control(),
            self.rows,
            self.active_second,
        );
        self.tree_inner = Rect::default();
        self.content_inner = Rect::default();
        if self.rects.first.width > 0 && self.rects.first.height > 0 {
            let block = self
                .styles
                .panel(
                    self.text("탐색", "Explorer"),
                    self.focus == 1,
                    1,
                    self.ascii,
                )
                .unwrap();
            self.tree_inner = block.inner(self.rects.first);
            frame.render_widget(block, self.rects.first);
            let mut tree = TreeWidget::new(&self.tree, &self.styles).unwrap();
            tree.focused = self.focus == 1;
            tree.ascii = self.ascii;
            if self.drag_enabled {
                tree = tree.with_drag(&mut self.tree_drag);
            }
            frame.render_stateful_widget(tree, self.tree_inner, &mut self.tree_state);
        }
        if self.rects.second.width > 0 && self.rects.second.height > 0 {
            let block = self
                .styles
                .panel(self.text("내용", "Content"), self.focus == 2, 1, self.ascii)
                .unwrap();
            self.content_inner = block.inner(self.rects.second);
            frame.render_widget(block, self.rects.second);
            let content=format!("{}: {}\n\n{}\n\n{}\n\n{}",self.text("활성 탭","Active tab"),self.tab.active,self.text("DB 없는 공통 컴포넌트 견본","Database-free shared component example"),self.text("탭에서 방향키는 포커스만 옮기고 Enter는 활성화합니다.\n수정된 문서의 닫기 요청은 앱이 보류합니다.","Tab arrows move focus; Enter activates.\nThe host retains edited documents on close requests."),self.text("Ctrl+방향키 또는 분할선 드래그로 크기를 조절하세요.\n좁은 화면에서는 마지막으로 선택한 패널만 보입니다.\n테마 변경 후에도 트리·탭·분할 상태를 유지합니다.","Resize with Ctrl+arrows or drag the divider.\nNarrow screens show the last selected panel.\nTree, tab, and split state survive theme changes."));
            frame.render_widget(
                Paragraph::new(content)
                    .style(self.styles.text_on_surface("body", "surface").unwrap())
                    .scroll((self.content_scroll, 0)),
                self.content_inner,
            );
        }
        let _ = draw_split_divider(
            self.rects.divider,
            frame.buffer_mut(),
            &self.styles,
            self.control(),
            self.rows,
            self.ascii,
            self.side(),
        );
        let statuses = vec![
            StatusItem {
                id: "message".into(),
                text: self.message.clone(),
                role: "info".into(),
                priority: 100,
            },
            StatusItem {
                id: "changed".into(),
                text: self
                    .text("변경 표시 * / 닫기 x", "Edited * / close x")
                    .into(),
                role: "edited".into(),
                priority: 20,
            },
            StatusItem {
                id: "help".into(),
                text: "F1 Help".into(),
                role: "hint".into(),
                priority: 1,
            },
        ];
        frame.render_widget(
            LineWidget::new(
                status_line(&statuses, usize::from(layout[4].width)).runs,
                &self.styles,
            )
            .unwrap(),
            layout[4],
        );
        let quit_label = if self.quit_key == 'x' {
            "Ctrl+X"
        } else {
            "Ctrl+Q"
        };
        frame.render_widget(Paragraph::new(self.text("Tab 이동 · F2 테마 · F3 색상 · F4 ASCII · F5 변경 · F6 분할 방향 · F7 접기/복원 · Ctrl+Q 종료","Tab focus · F2 theme · F3 colors · F4 ASCII · F5 edited · F6 split axis · F7 collapse/restore · Ctrl+Q quit").replace("Ctrl+Q",quit_label)).style(self.styles.role("hint").unwrap()),layout[5]);
        if self.drag_enabled {
            frame.render_widget(
                Paragraph::new(
                    self.text(
                        "드래그 이동 · Alt+Shift+방향키 이동 요청 · Esc 취소 · Ctrl+Q 종료",
                        "Drag to move / Alt+Shift+arrows request move / Esc cancel / Ctrl+Q quit",
                    )
                    .replace("Ctrl+Q", quit_label),
                )
                .style(self.styles.role("hint").unwrap()),
                layout[5],
            );
        }
    }
}
struct Session;
impl Drop for Session {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let _ = execute!(
            io::stdout(),
            DisableMouseCapture,
            LeaveAlternateScreen,
            Show
        );
    }
}
pub fn run(arguments: Vec<String>) -> Result<(), Box<dyn Error>> {
    let mut en = false;
    let mut ascii = false;
    let mut theme = Theme::Dark;
    let mut profile = ColorProfile::Indexed256;
    // App-owned policy; no change to the public component models is needed.
    let mut rows = false;
    let mut focus_order = [0, 1, 2];
    let mut quit_key = 'q';
    let mut snapshot = None;
    let mut drag_enabled = false;
    let mut args = arguments.into_iter();
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--lang" => {
                en = match args.next().as_deref() {
                    Some("en") => true,
                    Some("ko") => false,
                    _ => return Err("--lang requires ko or en".into()),
                }
            }
            "--theme" => theme = args.next().ok_or("missing theme")?.parse()?,
            "--colors" => profile = args.next().ok_or("missing colors")?.parse()?,
            "--ascii" => ascii = true,
            "--drag" => drag_enabled = true,
            "--layout" => {
                rows = match args.next().as_deref() {
                    Some("columns") => false,
                    Some("rows") => true,
                    _ => return Err("--layout requires columns or rows".into()),
                }
            }
            "--quit-key" => {
                quit_key = match args.next().as_deref() {
                    Some("ctrl-q") => 'q',
                    Some("ctrl-x") => 'x',
                    _ => return Err("--quit-key requires ctrl-q or ctrl-x".into()),
                }
            }
            "--focus-order" => {
                let value = args.next().ok_or("missing focus order")?;
                let order = value
                    .split(',')
                    .map(|s| match s {
                        "tabs" => Ok(0),
                        "tree" => Ok(1),
                        "content" => Ok(2),
                        _ => Err("--focus-order requires tabs,tree,content exactly once"),
                    })
                    .collect::<Result<Vec<_>, _>>()?;
                if order.len() != 3 || (0..3).any(|n| !order.contains(&n)) {
                    return Err("--focus-order requires tabs,tree,content exactly once".into());
                }
                focus_order.copy_from_slice(&order);
            }
            "--snapshot" => snapshot = Some(args.next().ok_or("missing file")?),
            "--help" => {
                println!(
                    "TUIVORY Workspace: --lang ko|en --theme dark|light|blackwhite --colors 8|16|256|truecolor --ascii --drag --layout columns|rows --focus-order tabs,tree,content --quit-key ctrl-q|ctrl-x --snapshot FILE.svg"
                );
                return Ok(());
            }
            _ => return Err(format!("unknown option: {arg}").into()),
        }
    }
    let text = |ko: &str, en_text: &str| {
        if en {
            en_text.to_string()
        } else {
            ko.to_string()
        }
    };
    let items = vec![
        TabItem {
            id: "overview".into(),
            title: text("개요", "Overview"),
            ..Default::default()
        },
        TabItem {
            id: "draft".into(),
            title: text(
                "변경된 한글 문서와 긴 제목",
                "Edited document with a long title",
            ),
            edited: true,
            closable: true,
            ..Default::default()
        },
        TabItem {
            id: "logs".into(),
            title: text("로그", "Logs"),
            closable: true,
            ..Default::default()
        },
        TabItem {
            id: "disabled".into(),
            title: text("비활성", "Disabled"),
            disabled: true,
            ..Default::default()
        },
    ];
    let node =
        |id: &str, parent: &str, name: String, secondary: String, icon: &str, ascii_icon: &str| {
            TreeNode {
                id: id.into(),
                parent: parent.into(),
                name,
                secondary,
                icon: icon.into(),
                ascii_icon: ascii_icon.into(),
                ..Default::default()
            }
        };
    let tree = Tree::new(vec![
        node(
            "root",
            "",
            text("프로젝트", "Project"),
            String::new(),
            "◇",
            "R",
        ),
        node(
            "src",
            "root",
            text("예제", "Examples"),
            String::new(),
            "□",
            "D",
        ),
        node(
            "go",
            "src",
            "Go".into(),
            text("공개 패키지", "Public package"),
            "",
            "",
        ),
        node(
            "rust",
            "src",
            "Rust".into(),
            text("공개 crate", "Public crate"),
            "",
            "",
        ),
        node(
            "notes",
            "root",
            text("긴 한글 경로와 이름 예시", "A long path and name example"),
            "[red] literal".into(),
            "",
            "",
        ),
    ])?;
    let path = vec![
        PathItem {
            id: "root".into(),
            label: text("작업 공간", "Workspace"),
        },
        PathItem {
            id: "project".into(),
            label: "Tuivory".into(),
        },
        PathItem {
            id: "folder".into(),
            label: text("공통 컴포넌트 예제", "Shared component examples"),
        },
        PathItem {
            id: "current".into(),
            label: text("현재 문서.md", "Current document.md"),
        },
    ];
    let mut app = App {
        drag_enabled,
        tab_drag: DragState::default(),
        tree_drag: DragState::default(),
        tab_area: Rect::default(),
        drag_press: None,
        en,
        ascii,
        theme,
        profile,
        styles: Styles::new(theme, profile)?,
        tabs: Tabs::new(items.clone())?,
        items,
        tab: TabState::default(),
        tree,
        tree_state: TreeState {
            expanded: ["root".into(), "src".into()].into(),
            ..Default::default()
        },
        path,
        focus: focus_order[0],
        focus_order,
        quit_key,
        active_second: focus_order[0] == 2,
        rows,
        column: SplitState { preferred: 32 },
        row: SplitState { preferred: 8 },
        message: text(
            "상태·포커스·분할 크기는 테마와 독립적입니다.",
            "State, focus and split sizes are independent of the theme.",
        ),
        body: Rect::default(),
        tree_inner: Rect::default(),
        content_inner: Rect::default(),
        rects: SplitRects {
            first: Rect::default(),
            divider: Rect::default(),
            second: Rect::default(),
            compact: true,
        },
        column_control: SplitControl::default(),
        row_control: SplitControl::default(),
        content_scroll: 0,
    };
    app.tabs.reconcile(&mut app.tab);
    if let Some(path) = snapshot {
        let mut terminal = Terminal::new(TestBackend::new(120, 32))?;
        terminal.draw(|f| app.draw(f))?;
        snapshot::write(std::path::Path::new(&path), terminal.backend().buffer())?;
        return Ok(());
    }
    if !io::stdin().is_terminal() || !io::stdout().is_terminal() {
        return Err("interactive example requires a terminal".into());
    }
    enable_raw_mode()?;
    let _session = Session;
    execute!(io::stdout(), EnterAlternateScreen, EnableMouseCapture)?;
    let mut terminal = Terminal::new(CrosstermBackend::new(io::stdout()))?;
    terminal.clear()?;
    loop {
        terminal.draw(|f| app.draw(f))?;
        if !event::poll(Duration::from_millis(200))? {
            continue;
        }
        match event::read()? {
            Event::Key(key) if matches!(key.kind, KeyEventKind::Press | KeyEventKind::Repeat) => {
                if key.code == KeyCode::Char(app.quit_key)
                    && key.modifiers.contains(KeyModifiers::CONTROL)
                {
                    break;
                }
                if app.drag_enabled {
                    if key.code == KeyCode::Esc {
                        app.cancel_drop();
                        continue;
                    }
                    if key
                        .modifiers
                        .contains(KeyModifiers::ALT | KeyModifiers::SHIFT)
                    {
                        let movement = match (app.focus, key.code) {
                            (0, KeyCode::Left) | (1, KeyCode::Up) => Some(DragMove::Previous),
                            (0, KeyCode::Right) | (1, KeyCode::Down) => Some(DragMove::Next),
                            (1, KeyCode::Right) => Some(DragMove::Inside),
                            (1, KeyCode::Left) => Some(DragMove::Outside),
                            _ => None,
                        };
                        if let Some(movement) = movement {
                            let result = if app.focus == 0 {
                                app.tabs.keyboard_drop(
                                    &app.tab,
                                    movement,
                                    &App::drop_options(),
                                    None,
                                )
                            } else {
                                app.tree.keyboard_drop(
                                    &app.tree_state,
                                    movement,
                                    &App::drop_options(),
                                    None,
                                )
                            };
                            app.cancel_drop();
                            match result {
                                Ok(r) => app.apply_drop(app.focus == 0, r),
                                Err(e) => app.message = format!("reject: {e}"),
                            };
                            continue;
                        }
                    }
                    app.cancel_drop();
                }
                if key.modifiers.contains(KeyModifiers::CONTROL) {
                    let delta = match (key.code, app.rows) {
                        (KeyCode::Left, false) | (KeyCode::Up, true) => -1,
                        (KeyCode::Right, false) | (KeyCode::Down, true) => 1,
                        _ => 0,
                    };
                    if delta != 0 {
                        let l =
                            app.control()
                                .layout(app.spec(), app.split_state(), app.split_total());
                        app.resize(l.first.saturating_add_signed(delta));
                        continue;
                    }
                }
                match key.code{KeyCode::Tab|KeyCode::BackTab=>app.cycle_focus(key.code==KeyCode::Tab),
                KeyCode::F(7)=>app.toggle_split(),
                KeyCode::F(1)=>app.message=app.text("탭: ←/→·Enter·x / 트리: 방향키·Space·Enter / Ctrl+방향키 크기 조절","Tabs: Left/Right, Enter, x / Tree: arrows, Space, Enter / Ctrl+arrows resize").into(),
                KeyCode::F(2)=>{app.theme=match app.theme{Theme::Dark=>Theme::Light,Theme::Light=>Theme::Blackwhite,Theme::Blackwhite=>Theme::Dark};app.styles=Styles::new(app.theme,app.profile)?},
                KeyCode::F(3)=>{app.profile=match app.profile{ColorProfile::Ansi8=>ColorProfile::Ansi16,ColorProfile::Ansi16=>ColorProfile::Indexed256,ColorProfile::Indexed256=>ColorProfile::Truecolor,ColorProfile::Truecolor=>ColorProfile::Ansi8};app.styles=Styles::new(app.theme,app.profile)?},
                KeyCode::F(4)=>app.ascii= !app.ascii,KeyCode::F(5)=>{for item in &mut app.items{if item.id==app.tab.active{item.edited= !item.edited}}app.tabs=Tabs::new(app.items.clone())?;app.tabs.reconcile(&mut app.tab)},KeyCode::F(6)=>{app.split_parts().0.cancel_pointer();app.rows= !app.rows;app.sync_split_focus()},
                _ if app.focus==0=>{let action=match key.code{KeyCode::Left=>Some(TabAction::Previous),KeyCode::Right=>Some(TabAction::Next),KeyCode::Home=>Some(TabAction::First),KeyCode::End=>Some(TabAction::Last),KeyCode::Enter=>Some(TabAction::Activate),KeyCode::Delete|KeyCode::Char('x')=>Some(TabAction::Close),_=>None};if let Some(action)=action{let event=app.tabs.handle(&mut app.tab,action);app.tab_event(event)}},
                _ if app.focus==1=>{let action=match key.code{KeyCode::Left if key.modifiers.contains(KeyModifiers::ALT)=>Some(TreeAction::PanLeft),KeyCode::Right if key.modifiers.contains(KeyModifiers::ALT)=>Some(TreeAction::PanRight),KeyCode::Left=>Some(TreeAction::Left),KeyCode::Right=>Some(TreeAction::Right),KeyCode::Up=>Some(TreeAction::Up),KeyCode::Down=>Some(TreeAction::Down),KeyCode::Home=>Some(TreeAction::Home),KeyCode::End=>Some(TreeAction::End),KeyCode::PageUp=>Some(TreeAction::PageUp),KeyCode::PageDown=>Some(TreeAction::PageDown),KeyCode::Enter=>Some(TreeAction::Activate),KeyCode::Char(' ')=>Some(TreeAction::Toggle),_=>None};if let Some(action)=action{app.tree_action(action)}},
                KeyCode::Up if app.focus==2=>app.content_scroll=app.content_scroll.saturating_sub(1),KeyCode::Down if app.focus==2=>app.content_scroll=app.content_scroll.saturating_add(1).min(20),_=>(),
            }
            }
            Event::Mouse(mouse) => {
                let position = (mouse.column, mouse.row).into();
                let action = match mouse.kind {
                    MouseEventKind::Down(MouseButton::Left) => "down",
                    MouseEventKind::Drag(MouseButton::Left) => "move",
                    MouseEventKind::Up(MouseButton::Left) => "up",
                    _ => "",
                };
                if !action.is_empty() && app.drag_press.is_none() {
                    let (spec, total, side) = (app.spec(), app.split_total(), app.side());
                    let offset = if app.rows {
                        mouse.row as isize - app.body.y as isize
                    } else {
                        mouse.column as isize - app.body.x as isize
                    };
                    let inside = app.body.contains(position);
                    let (control, state) = app.split_parts();
                    if control.pointer(spec, state, total, offset, inside, action, side) {
                        app.sync_split_focus();
                        continue;
                    }
                }
                if app.drag_mouse(mouse) {
                    continue;
                }
                if mouse.row == 2 && mouse.kind == MouseEventKind::Down(MouseButton::Left) {
                    app.focus = 0;
                    let event = app.tabs.click(
                        &mut app.tab,
                        usize::from(mouse.column),
                        usize::from(app.body.width),
                    );
                    app.tab_event(event)
                } else if mouse.row == 1 && mouse.kind == MouseEventKind::Down(MouseButton::Left) {
                    for run in breadcrumbs(&app.path, usize::from(app.body.width)) {
                        if !run.id.is_empty()
                            && usize::from(mouse.column) >= run.start
                            && usize::from(mouse.column) < run.start + run.width
                        {
                            app.message = format!(
                                "{}: {}",
                                app.text("경로 이동 요청", "Navigation request"),
                                run.id
                            );
                        }
                    }
                } else if app.tree_inner.contains(position) {
                    match mouse.kind {
                        MouseEventKind::Down(MouseButton::Left) => {
                            app.focus = 1;
                            app.active_second = false;
                            if let Some(event) = app.tree.click(
                                &mut app.tree_state,
                                usize::from(mouse.column - app.tree_inner.x),
                                usize::from(mouse.row - app.tree_inner.y),
                                usize::from(app.tree_inner.height),
                            ) {
                                app.message = format!("{event:?}")
                            }
                        }
                        MouseEventKind::ScrollUp => app.tree_action(TreeAction::Up),
                        MouseEventKind::ScrollDown => app.tree_action(TreeAction::Down),
                        _ => (),
                    }
                } else if app.content_inner.contains(position)
                    && mouse.kind == MouseEventKind::Down(MouseButton::Left)
                {
                    app.focus = 2;
                    app.active_second = true;
                }
            }
            Event::Resize(_, _) => {
                app.cancel_drop();
                app.split_parts().0.cancel_pointer();
            }
            _ => (),
        }
    }
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    run(std::env::args().skip(1).collect())
}
