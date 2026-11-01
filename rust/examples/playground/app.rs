use tuivory::ui::components::Styles;
use tuivory::ui::terminal::event::{
    KeyCode, KeyEvent, KeyModifiers, MouseButton, MouseEvent, MouseEventKind,
};
use tuivory::ui::{
    Frame,
    layout::{Alignment, Constraint, Layout, Rect},
    style::Modifier,
    text::Line,
    widgets::{
        Cell, Clear, List, ListItem, ListState, Padding, Paragraph, Row, Table, TableState, Wrap,
    },
};
use tuivory::{ColorProfile, Error, Theme};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Language {
    Ko,
    En,
}
impl Language {
    pub fn text<'a>(self, ko: &'a str, en: &'a str) -> &'a str {
        if self == Self::En { en } else { ko }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Focus {
    Theme,
    Profile,
    Nav,
    Tokens,
    Guide,
    Name,
    Password,
    Choice,
    Check,
    Apply,
    Popup,
    Reset,
    List,
    Table,
}
const THEMES: [Theme; 3] = [Theme::Dark, Theme::Light, Theme::Blackwhite];
const PROFILES: [ColorProfile; 4] = [
    ColorProfile::Ansi8,
    ColorProfile::Ansi16,
    ColorProfile::Indexed256,
    ColorProfile::Truecolor,
];
#[derive(Debug)]
enum Popup {
    Preview,
    Help,
    Choice(usize),
    Selector {
        target: Focus,
        selected: usize,
    },
    Edit {
        row: usize,
        value: String,
        save: bool,
    },
}

pub struct App {
    pub language: Language,
    pub theme: Theme,
    pub profile: ColorProfile,
    styles: Styles,
    name: String,
    password: String,
    auto: bool,
    detected: ColorProfile,
    wide: bool,
    choice: usize,
    checked: bool,
    invalid: bool,
    focus: Focus,
    list: ListState,
    table: TableState,
    rows: Vec<String>,
    edited: Vec<bool>,
    popup: Option<Popup>,
    page: usize,
    scroll: u16,
    message: String,
    targets: Vec<(Rect, Focus)>,
    popup_rect: Rect,
    popup_action: Rect,
    popup_action_focused: bool,
    small: bool,
}

impl App {
    pub fn new(language: Language, theme: Theme, profile: ColorProfile) -> Result<Self, Error> {
        Ok(Self {
            language,
            theme,
            profile,
            styles: Self::styles(theme, profile)?,
            name: language.text("한글과 English", "Hello, world!").into(),
            password: "sample".into(),
            auto: false,
            detected: profile,
            wide: true,
            choice: 0,
            checked: true,
            invalid: false,
            focus: Focus::Name,
            list: ListState::default().with_selected(Some(0)),
            table: TableState::default()
                .with_selected(Some(0))
                .with_selected_column(Some(1)),
            rows: vec![
                language.text("한글 입력 예시", "Sample input").into(),
                language.text("선택과 포커스", "Selection and focus").into(),
                language.text("Enter로 편집", "Enter to edit").into(),
            ],
            edited: vec![false; 3],
            popup: None,
            page: 0,
            scroll: 0,
            message: language
                .text(
                    " 이름을 입력하거나 Tab으로 이동해 보세요. DB·파일에 저장하지 않습니다.",
                    " Enter a name or press Tab. Nothing is saved to a database or file.",
                )
                .into(),
            targets: vec![],
            popup_rect: Rect::default(),
            popup_action: Rect::default(),
            popup_action_focused: false,
            small: false,
        })
    }
    fn styles(theme: Theme, profile: ColorProfile) -> Result<Styles, Error> {
        let document = tuivory::TokenDocument::from_json(include_str!("go-palette.json"))?;
        Ok(Styles::from_palette(document.palette(theme, profile)?))
    }
    pub fn set_profile_mode(&mut self, auto: bool, detected: ColorProfile) {
        self.auto = auto;
        self.detected = detected;
    }
    fn focusables(&self) -> Vec<Focus> {
        let mut result = vec![Focus::Theme, Focus::Profile];
        if self.wide {
            result.push(Focus::Nav);
        }
        match self.page {
            1 => result.push(Focus::Tokens),
            2 => result.push(Focus::Guide),
            _ => result.extend([
                Focus::Name,
                Focus::Password,
                Focus::Choice,
                Focus::Check,
                Focus::Apply,
                Focus::Popup,
                Focus::Reset,
                Focus::List,
                Focus::Table,
            ]),
        }
        result
    }
    fn page_focus(&self) -> Focus {
        match self.page {
            1 => Focus::Tokens,
            2 => Focus::Guide,
            _ => Focus::Name,
        }
    }
    fn change_page(&mut self, page: usize) {
        self.page = page;
        self.scroll = 0;
        self.message = self
            .text(
                [
                    " 입력·목록·그리드를 직접 조작해 보세요.",
                    " 역할별 전경·배경과 실제 색상 견본입니다.",
                    " 방향키와 PgUp/PgDn으로 안내를 읽으세요.",
                ][page],
                [
                    " Try the inputs, list, and grid.",
                    " Foreground, background, and color samples by role.",
                    " Use arrow keys and PgUp/PgDn to read the guide.",
                ][page],
            )
            .into();
    }
    fn profile_index(&self) -> usize {
        if self.auto {
            0
        } else {
            1 + PROFILES.iter().position(|p| *p == self.profile).unwrap()
        }
    }
    fn select_profile(&mut self, index: usize) -> Result<(), Error> {
        self.auto = index == 0;
        self.profile = if self.auto {
            self.detected
        } else {
            PROFILES[index - 1]
        };
        self.styles = Self::styles(self.theme, self.profile)?;
        Ok(())
    }
    fn selector_labels(&self, target: Focus) -> Vec<&str> {
        if target == Focus::Theme {
            vec![
                self.text("다크", "Dark"),
                self.text("라이트", "Light"),
                self.text("흑백", "Monochrome"),
            ]
        } else {
            vec![
                self.text("자동", "Auto"),
                self.text("8색", "8 colors"),
                self.text("16색", "16 colors"),
                self.text("256색", "256 colors"),
                "True Color",
            ]
        }
    }
    fn text<'a>(&self, ko: &'a str, en: &'a str) -> &'a str {
        self.language.text(ko, en)
    }
    fn role(&self, name: &str) -> tuivory::ui::style::Style {
        self.styles.role(name).expect("bundled semantic role")
    }
    fn block<'a>(&self, title: &'a str, focused: bool) -> tuivory::ui::widgets::Block<'a> {
        self.styles
            .block(title, focused)
            .expect("bundled semantic role")
            .title_alignment(Alignment::Center)
            .border_style(self.role(if focused {
                "sample.border.focus"
            } else {
                "sample.border"
            }))
    }
    fn choices(&self) -> [&str; 3] {
        [
            self.text("개발 환경", "Development"),
            self.text("검토 환경", "Review"),
            self.text("운영 환경", "Production"),
        ]
    }
    pub fn preview(&mut self) {
        self.popup_action_focused = false;
        self.popup = Some(Popup::Preview);
        self.scroll = 0;
    }
    fn move_selection(&mut self, delta: isize) {
        if self.focus == Focus::List {
            let current = self.list.selected().unwrap_or(0);
            self.list
                .select(Some((current as isize + delta).rem_euclid(4) as usize));
        } else if self.focus == Focus::Table {
            let current = self.table.selected().unwrap_or(0);
            self.table
                .select(Some((current as isize + delta).rem_euclid(3) as usize));
        }
    }
    fn activate(&mut self) -> Result<(), Error> {
        match self.focus {
            Focus::Theme | Focus::Profile => {
                self.popup = Some(Popup::Selector {
                    target: self.focus,
                    selected: if self.focus == Focus::Theme {
                        THEMES.iter().position(|t| *t == self.theme).unwrap()
                    } else {
                        self.profile_index()
                    },
                })
            }
            Focus::Nav => self.focus = self.page_focus(),
            Focus::Choice => self.popup = Some(Popup::Choice(self.choice)),
            Focus::Check => self.checked = !self.checked,
            Focus::Apply => {
                self.message = format!(
                    "{}{}",
                    self.text("적용 예시: ", "Applied preview: "),
                    self.name
                )
            }
            Focus::Popup => self.preview(),
            Focus::Reset => {
                let new = Self::new(self.language, self.theme, self.profile)?;
                self.name = new.name;
                self.password = new.password;
                self.choice = new.choice;
                self.checked = new.checked;
                self.rows = new.rows;
                self.edited = new.edited;
                self.invalid = false;
                self.message = self
                    .text("견본 값을 초기화했습니다.", "Sample values reset.")
                    .into();
            }
            Focus::List => {
                self.message = format!(
                    "{} {}",
                    self.text("목록 선택:", "Selected item:"),
                    self.list.selected().unwrap_or(0) + 1
                )
            }
            Focus::Table if self.table.selected_column() == Some(1) => {
                let row = self.table.selected().unwrap_or(0);
                self.popup = Some(Popup::Edit {
                    row,
                    value: self.rows[row].clone(),
                    save: false,
                });
            }
            _ => (),
        }
        Ok(())
    }
    pub fn key(&mut self, event: KeyEvent) -> Result<bool, Error> {
        if event.code == KeyCode::Char('q') && event.modifiers.contains(KeyModifiers::CONTROL) {
            return Ok(true);
        }
        if self.small {
            return Ok(false);
        }
        match event.code {
            KeyCode::F(2) => {
                let i = THEMES.iter().position(|t| *t == self.theme).unwrap();
                self.theme = THEMES[(i + 1) % 3];
                self.styles = Self::styles(self.theme, self.profile)?;
                return Ok(false);
            }
            KeyCode::F(3) => {
                self.select_profile((self.profile_index() + 1) % 5)?;
                return Ok(false);
            }
            _ => (),
        }
        if let Some(Popup::Selector { target, selected }) = self.popup {
            let count = if target == Focus::Theme { 3 } else { 5 };
            match event.code {
                KeyCode::Up => {
                    self.popup = Some(Popup::Selector {
                        target,
                        selected: (selected + count - 1) % count,
                    })
                }
                KeyCode::Down => {
                    self.popup = Some(Popup::Selector {
                        target,
                        selected: (selected + 1) % count,
                    })
                }
                KeyCode::Enter => {
                    if target == Focus::Theme {
                        self.theme = THEMES[selected];
                        self.styles = Self::styles(self.theme, self.profile)?;
                    } else {
                        self.select_profile(selected)?;
                    }
                    self.popup = None;
                }
                KeyCode::Esc | KeyCode::Tab | KeyCode::BackTab => {
                    self.popup = None;
                    if event.code != KeyCode::Esc {
                        self.move_focus(event.code == KeyCode::BackTab);
                    }
                }
                _ => (),
            }
            return Ok(false);
        }
        if self.popup.is_some() {
            let mut close = event.code == KeyCode::Esc;
            match self.popup.as_mut().unwrap() {
                Popup::Choice(selected) => match event.code {
                    KeyCode::Up => *selected = (*selected + 2) % 3,
                    KeyCode::Down => *selected = (*selected + 1) % 3,
                    KeyCode::Enter => {
                        self.choice = *selected;
                        close = true;
                    }
                    _ => (),
                },
                Popup::Edit { row, value, save } => match event.code {
                    KeyCode::Tab | KeyCode::BackTab => *save = !*save,
                    KeyCode::Enter if *save => {
                        self.rows[*row] = value.clone();
                        self.edited[*row] = true;
                        close = true;
                    }
                    KeyCode::Enter => *save = true,
                    KeyCode::Backspace if !*save => {
                        value.pop();
                    }
                    KeyCode::Char(c)
                        if !*save
                            && !event
                                .modifiers
                                .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT)
                            && !c.is_control() =>
                    {
                        value.push(c)
                    }
                    _ => (),
                },
                _ => match event.code {
                    KeyCode::Up => self.scroll = self.scroll.saturating_sub(1),
                    KeyCode::Down => self.scroll = self.scroll.saturating_add(1).min(30),
                    KeyCode::Tab | KeyCode::BackTab => {
                        self.popup_action_focused = !self.popup_action_focused
                    }
                    KeyCode::Enter if self.popup_action_focused => close = true,
                    _ => (),
                },
            }
            if close {
                self.popup = None;
                self.popup_action_focused = false;
                self.scroll = 0;
            }
            return Ok(false);
        }
        match event.code {
            KeyCode::F(1) => {
                self.popup = Some(Popup::Help);
                self.scroll = 0;
            }
            KeyCode::F(4) => self.preview(),
            KeyCode::F(5) => self.invalid = !self.invalid,
            KeyCode::F(6) => {
                self.change_page((self.page + 1) % 3);
                self.focus = self.page_focus();
            }
            KeyCode::PageUp if matches!(self.focus, Focus::Guide | Focus::Tokens) => {
                self.scroll = self.scroll.saturating_sub(10)
            }
            KeyCode::PageDown if matches!(self.focus, Focus::Guide | Focus::Tokens) => {
                self.scroll = self.scroll.saturating_add(10).min(30)
            }
            KeyCode::Up if self.focus == Focus::Nav => self.change_page((self.page + 2) % 3),
            KeyCode::Down if self.focus == Focus::Nav => self.change_page((self.page + 1) % 3),
            KeyCode::Up if matches!(self.focus, Focus::Tokens | Focus::Guide) => {
                self.scroll = self.scroll.saturating_sub(1)
            }
            KeyCode::Down if matches!(self.focus, Focus::Tokens | Focus::Guide) => {
                self.scroll = self.scroll.saturating_add(1).min(30)
            }
            KeyCode::Tab | KeyCode::BackTab => self.move_focus(event.code == KeyCode::BackTab),
            KeyCode::Left | KeyCode::Right
                if matches!(self.focus, Focus::Apply | Focus::Popup | Focus::Reset) =>
            {
                let buttons = [Focus::Apply, Focus::Popup, Focus::Reset];
                let i = buttons.iter().position(|v| *v == self.focus).unwrap();
                self.focus = buttons[(i + if event.code == KeyCode::Right { 1 } else { 2 }) % 3];
            }
            KeyCode::Left | KeyCode::Right if self.focus == Focus::Table => {
                let i = self.table.selected_column().unwrap_or(1);
                self.table
                    .select_column(Some(if event.code == KeyCode::Right {
                        (i + 1).min(2)
                    } else {
                        i.saturating_sub(1)
                    }));
            }
            KeyCode::Up => self.move_selection(-1),
            KeyCode::Down => self.move_selection(1),
            KeyCode::Enter => self.activate()?,
            KeyCode::Char(' ') if self.focus == Focus::Check => self.checked = !self.checked,
            KeyCode::Backspace if matches!(self.focus, Focus::Name | Focus::Password) => {
                if self.focus == Focus::Name {
                    self.name.pop();
                } else {
                    self.password.pop();
                }
            }
            KeyCode::Char(c)
                if matches!(self.focus, Focus::Name | Focus::Password)
                    && !event
                        .modifiers
                        .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT)
                    && !c.is_control() =>
            {
                if self.focus == Focus::Name {
                    self.name.push(c)
                } else {
                    self.password.push(c)
                }
            }
            _ => (),
        }
        Ok(false)
    }
    fn move_focus(&mut self, backwards: bool) {
        let choices = self.focusables();
        let i = choices.iter().position(|v| *v == self.focus).unwrap_or(0);
        self.focus = choices[(i + if backwards { choices.len() - 1 } else { 1 }) % choices.len()];
    }
    pub fn mouse(&mut self, event: MouseEvent) -> Result<(), Error> {
        if self.small {
            return Ok(());
        }
        let position = (event.column, event.row).into();
        if let Some(Popup::Selector { target, .. }) = self.popup {
            if event.kind == MouseEventKind::Down(MouseButton::Left)
                && self.popup_rect.contains(position)
            {
                let selected = usize::from(event.row - self.popup_rect.y);
                if selected < self.selector_labels(target).len() {
                    if target == Focus::Theme {
                        self.theme = THEMES[selected];
                        self.styles = Self::styles(self.theme, self.profile)?;
                    } else {
                        self.select_profile(selected)?;
                    }
                    self.popup = None;
                }
            }
            return Ok(());
        }
        if matches!(self.popup, Some(Popup::Choice(_))) {
            if event.kind == MouseEventKind::Down(MouseButton::Left)
                && self.popup_rect.contains(position)
            {
                self.choice = usize::from(event.row - self.popup_rect.y).min(2);
                self.popup = None;
            }
            return Ok(());
        }
        if self.popup.is_some() {
            if !self.popup_rect.contains(position) {
                return Ok(());
            }
            if event.kind == MouseEventKind::Down(MouseButton::Left)
                && self.popup_action.contains(position)
            {
                if let Some(Popup::Edit { row, value, .. }) = &self.popup {
                    self.rows[*row] = value.clone();
                    self.edited[*row] = true;
                }
                if let Some(Popup::Choice(selected)) = &self.popup {
                    self.choice = *selected;
                }
                self.popup = None;
                self.popup_action_focused = false;
            } else if event.kind == MouseEventKind::Down(MouseButton::Left) {
                if let Some(Popup::Choice(_)) = self.popup {
                    let row = usize::from(event.row.saturating_sub(self.popup_rect.y + 1));
                    if row < 3 {
                        self.choice = row;
                        self.popup = None;
                    }
                } else if let Some(Popup::Edit { save, .. }) = self.popup.as_mut() {
                    *save = false;
                }
            } else if event.kind == MouseEventKind::ScrollDown {
                self.scroll = self.scroll.saturating_add(1).min(30);
            } else if event.kind == MouseEventKind::ScrollUp {
                self.scroll = self.scroll.saturating_sub(1);
            }
            return Ok(());
        }
        if let Some((rect, target)) = self
            .targets
            .iter()
            .find(|(rect, _)| rect.contains(position))
            .copied()
        {
            if matches!(
                event.kind,
                MouseEventKind::ScrollDown | MouseEventKind::ScrollUp
            ) {
                if target == Focus::Nav {
                    self.change_page(
                        (self.page
                            + if event.kind == MouseEventKind::ScrollDown {
                                1
                            } else {
                                2
                            })
                            % 3,
                    );
                } else if matches!(target, Focus::Guide | Focus::Tokens) {
                    self.scroll = if event.kind == MouseEventKind::ScrollDown {
                        self.scroll.saturating_add(1).min(30)
                    } else {
                        self.scroll.saturating_sub(1)
                    };
                } else if matches!(target, Focus::List | Focus::Table) {
                    self.focus = target;
                    self.move_selection(if event.kind == MouseEventKind::ScrollDown {
                        1
                    } else {
                        -1
                    });
                }
            } else if event.kind == MouseEventKind::Down(MouseButton::Left) {
                self.focus = target;
                match target {
                    Focus::List => self.list.select(Some(
                        usize::from(event.row.saturating_sub(rect.y + 1)).min(3),
                    )),
                    Focus::Table => {
                        self.table.select(Some(
                            usize::from(event.row.saturating_sub(rect.y + 2)).min(2),
                        ));
                        let offset = event.column.saturating_sub(rect.x + 2);
                        self.table.select_column(Some(if offset < 4 {
                            0
                        } else if event.column >= rect.right().saturating_sub(12) {
                            2
                        } else {
                            1
                        }));
                    }
                    Focus::Name | Focus::Password | Focus::Tokens | Focus::Guide => (),
                    Focus::Nav => {
                        self.change_page(usize::from(event.row.saturating_sub(rect.y + 1)).min(2))
                    }
                    _ => self.activate()?,
                }
            }
        }
        Ok(())
    }
    pub fn draw(&mut self, f: &mut Frame<'_>) {
        self.targets.clear();
        let area = f.area();
        self.small = area.width < 80 || area.height < 24;
        self.wide = area.width >= 100;
        if !self.wide && self.focus == Focus::Nav {
            self.focus = self.page_focus();
        }
        f.render_widget(Paragraph::new("").style(self.role("body")), area);
        if self.small {
            f.render_widget(
                Paragraph::new(self.text(
                    "TUIVORY\n\n터미널을 80×24 이상으로 넓혀 주세요.\nCtrl+Q 종료",
                    "TUIVORY\n\nResize the terminal to at least 80×24.\nCtrl+Q Quit",
                ))
                .style(self.role("body")),
                area,
            );
            return;
        }
        let rows = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(0),
            Constraint::Length(1),
            Constraint::Length(1),
        ])
        .split(area);
        f.render_widget(
            Paragraph::new(self.text(
                " TUIVORY  ·  직접 조작하는 TUI 스타일 실험실",
                " TUIVORY  ·  Interactive terminal UI style playground",
            ))
            .style(self.role("header")),
            rows[0],
        );
        let controls = Layout::horizontal([
            Constraint::Length(24),
            Constraint::Length(28),
            Constraint::Min(0),
        ])
        .split(rows[1]);
        for (i, target, label, selected) in [
            (
                0,
                Focus::Theme,
                self.text(" 테마 ", " Theme "),
                THEMES.iter().position(|t| *t == self.theme).unwrap(),
            ),
            (
                1,
                Focus::Profile,
                self.text(" 색상 ", " Colors "),
                self.profile_index(),
            ),
        ] {
            let labels = self.selector_labels(target);
            let line = Line::from(vec![
                tuivory::ui::text::Span::styled(label, self.role("surface")),
                tuivory::ui::text::Span::styled(
                    format!(" {} ▾ ", labels[selected]),
                    self.role(if self.focus == target {
                        "selection"
                    } else {
                        "sample.dropdown"
                    }),
                ),
            ]);
            f.render_widget(
                Paragraph::new(line).style(self.role("surface")),
                controls[i],
            );
            self.targets.push((controls[i], target));
        }
        f.render_widget(
            Paragraph::new(format!(
                " {} {} · {} {}",
                self.text("미리보기", "Preview"),
                self.profile.as_str(),
                self.text("단말", "Terminal"),
                self.detected.as_str()
            ))
            .style(self.role("body")),
            controls[2],
        );
        f.render_widget(
            Paragraph::new(self.message.as_str()).style(self.role("body")),
            rows[3],
        );
        f.render_widget(
            Paragraph::new(if area.width < 110 { self.text(
                " F1 도움말  F2 테마  F3 색상  F4 팝업  F5 오류  F6 화면  Ctrl+Q 종료",
                " F1 Help  F2 Theme  F3 Colors  F4 Popup  F5 Error  F6 View  Ctrl+Q Quit") } else { self.text(
                " Tab/Shift+Tab 이동 · F1 도움말 · F2 테마 · F3 색상 · F4 팝업 · F5 입력 오류 · F6 화면 전환 · Enter 셀 편집 · Ctrl+Q 종료",
                " Tab/Shift+Tab Focus · F1 Help · F2 Theme · F3 Colors · F4 Popup · F5 Error · F6 View · Enter Edit · Ctrl+Q Quit",
            ) })
            .style(self.role("surface")),
            rows[4],
        );
        let content = if self.wide {
            let columns =
                Layout::horizontal([Constraint::Length(21), Constraint::Min(0)]).split(rows[2]);
            let nav = List::new(
                [
                    self.text("컴포넌트 견본", "Components"),
                    self.text("색상 토큰", "Color tokens"),
                    self.text("조작 안내", "Controls"),
                ]
                .map(ListItem::new),
            )
            .style(self.role("surface"))
            .highlight_style(self.role("selection"))
            .block(self.block(
                self.text(" 둘러보기 ", " Explore "),
                self.focus == Focus::Nav,
            ));
            f.render_stateful_widget(
                nav,
                columns[0],
                &mut ListState::default().with_selected(Some(self.page)),
            );
            self.targets.push((columns[0], Focus::Nav));
            columns[1]
        } else {
            rows[2]
        };
        match self.page {
            1 => {
                let doc = tuivory::TokenDocument::from_json(include_str!("go-palette.json"))
                    .expect("Go example palette");
                let palette = doc.tokens(self.theme, self.profile).unwrap();
                let body = doc
                    .roles()
                    .iter()
                    .take(16)
                    .skip(usize::from(self.scroll))
                    .map(|role| {
                        let pair = &palette.pairs()[role];
                        Row::new(vec![
                            Cell::from(role.clone()),
                            Cell::from(pair.foreground.clone()),
                            Cell::from(pair.background.clone()),
                            Cell::from(self.text(" Aa 한글 ", " Aa Sample "))
                                .style(self.role(role)),
                        ])
                        .style(self.role("body"))
                    })
                    .collect::<Vec<_>>();
                f.render_widget(
                    Table::new(
                        body,
                        [
                            Constraint::Percentage(40),
                            Constraint::Percentage(20),
                            Constraint::Percentage(20),
                            Constraint::Percentage(20),
                        ],
                    )
                    .header(
                        Row::new(vec![
                            self.text("역할", "Role"),
                            self.text("전경", "Foreground"),
                            self.text("배경", "Background"),
                            self.text("견본", "Sample"),
                        ])
                        .style(self.role("header")),
                    )
                    .block(self.block(
                        self.text(" 의미별 색상 · 16개 역할 ", " Semantic colors · 16 roles "),
                        self.focus == Focus::Tokens,
                    )),
                    content,
                );
                self.targets.push((content, Focus::Tokens));
            }
            2 => f.render_widget(
                Paragraph::new(self.guide())
                    .wrap(Wrap { trim: false })
                    .scroll((self.scroll, 0))
                    .style(self.role("surface"))
                    .block(self.block(
                        self.text(" 조작 안내 ", " Controls "),
                        self.focus == Focus::Guide,
                    )),
                content,
            ),
            _ => self.draw_components(f, content),
        }
        if self.page == 2 {
            self.targets.push((content, Focus::Guide));
        }
        if let Some(Popup::Selector { target, selected }) = self.popup {
            let rect = self.targets.iter().find(|(_, t)| *t == target).unwrap().0;
            let labels: Vec<String> = self
                .selector_labels(target)
                .into_iter()
                .map(str::to_owned)
                .collect();
            self.popup_rect = Rect::new(rect.x, rect.y + 1, rect.width, labels.len() as u16);
            f.render_widget(Clear, self.popup_rect);
            f.render_stateful_widget(
                List::new(labels.into_iter().map(ListItem::new))
                    .style(self.role("sample.dropdown"))
                    .highlight_style(self.role("selection")),
                self.popup_rect,
                &mut ListState::default().with_selected(Some(selected)),
            );
        } else if self.popup.is_some() {
            self.draw_popup(f, area);
        }
    }
    fn guide(&self) -> String {
        self.text(
            r#"TUIVORY · 무엇을 볼 수 있나요?

1. 컴포넌트 견본
이름을 입력하고 암호 마스킹, 선택박스, 체크박스를 조작하세요.
적용/팝업/초기화 버튼을 눌러 상태와 모달을 확인합니다.
그리드 이름 열에서 Enter로 편집하고 저장하면 * 변경 표시가 남습니다.
이 예시는 DB나 파일에 저장하지 않습니다.

2. 테마와 색상
F2로 다크/라이트/흑백, F3로 자동/8/16/256/True Color를 전환합니다.
입력값·체크·선택·편집한 셀은 그대로 유지됩니다.
색상 선택은 토큰 미리보기이며 터미널 자체의 지원 능력을 바꾸지 않습니다.
실제 단말은 더 적은 색으로 근사할 수 있습니다.

3. 색상 토큰
F6 또는 왼쪽 메뉴로 이동합니다. 16개 의미별 역할의 전경/배경을 비교하세요.
Go 스타일 팔레트로 표시하며 공통 토큰은 역할 표시 순서에 사용합니다.

4. 조작
Tab/Shift+Tab: 조작 대상 이동
방향키: 목록·그리드 이동 / 버튼 좌우 이동
Enter: 버튼 실행·선택박스 펼침·이름 셀 편집
F1: 도움말 / F4: 팝업 / F5: 입력 오류 표시 / F6: 화면
Esc: 열린 선택박스나 팝업 닫기
Ctrl+Q: 종료

마우스로도 선택·버튼·팝업을 조작할 수 있습니다.
80×24 미만이면 터미널을 넓히라는 안내를 보여줍니다.
실제 ANSI 팔레트, 글꼴, 마우스 지원은 단말마다 다릅니다."#,
            r#"TUIVORY · What can you explore?

1. Components
Enter a name and try password masking, choices, and checkboxes.
Use Apply/Popup/Reset to explore states and modal behavior.
Press Enter in the grid's Name column, edit, and save to see an * marker.
This example does not save to a database or file.

2. Themes and colors
F2 cycles Dark/Light/Monochrome; F3 cycles Auto/8/16/256/True Color.
Input values, checkboxes, selections, and edited cells are preserved.
Color selection previews tokens; it does not change terminal capabilities.
Your terminal may approximate colors using a smaller palette.

3. Color tokens
Use F6 or the left menu. Compare foreground/background pairs for 16 roles.
The samples use the Go style palette; shared tokens provide role ordering.

4. Controls
Tab/Shift+Tab: move focus
Arrow keys: navigate lists/grids or move between buttons
Enter: activate buttons, open choices, or edit a name cell
F1: help / F4: popup / F5: input errors / F6: switch view
Esc: close the open choice or popup
Ctrl+Q: quit

Mouse interaction is available for choices, buttons, and popups.
Below 80×24, a message asks you to resize the terminal.
Actual ANSI palettes, fonts, and mouse support vary by terminal."#,
        )
        .into()
    }
    fn draw_components(&mut self, f: &mut Frame<'_>, area: Rect) {
        let bands = Layout::vertical([
            Constraint::Length((area.height / 2).clamp(9, 13)),
            Constraint::Min(0),
        ])
        .split(area);
        let top = Layout::horizontal([Constraint::Length(area.width / 2), Constraint::Min(0)])
            .split(bands[0]);
        let bottom = Layout::horizontal([Constraint::Length(area.width / 2), Constraint::Min(0)])
            .split(bands[1]);
        let fields = self.block(
            self.text(" 입력 · 선택 ", " Inputs · Choices "),
            matches!(
                self.focus,
                Focus::Name | Focus::Password | Focus::Choice | Focus::Check
            ),
        );
        let fields = fields.padding(Padding::horizontal(1));
        let inner = fields.inner(top[0]);
        f.render_widget(fields, top[0]);
        let fields = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(0),
        ])
        .split(inner);
        let label = if self.invalid {
            self.text("오류! 이름 ", "Error! Name ")
        } else {
            self.text("이름     ", "Name     ")
        };
        let label_width = Line::raw(label).width() as u16;
        let input = Rect::new(
            fields[0].x + label_width.min(fields[0].width),
            fields[0].y,
            fields[0].width.saturating_sub(label_width),
            1,
        );
        let width = Line::raw(self.name.as_str()).width();
        let shift = width
            .saturating_sub(usize::from(input.width.saturating_sub(1)))
            .min(usize::from(u16::MAX)) as u16;
        f.render_widget(Paragraph::new(label).style(self.role("surface")), fields[0]);
        let name_style = self.role("field");
        f.render_widget(
            Paragraph::new(self.name.as_str())
                .scroll((0, shift))
                .style(if self.invalid {
                    name_style.add_modifier(Modifier::UNDERLINED)
                } else {
                    name_style
                }),
            input,
        );
        let masked = "*".repeat(self.password.chars().count());
        f.render_widget(
            Paragraph::new(Line::from(vec![
                tuivory::ui::text::Span::styled(
                    self.text("암호 예시 ", "Password "),
                    self.role("surface"),
                ),
                tuivory::ui::text::Span::styled(masked, self.role("field")),
            ]))
            .style(self.role("surface")),
            fields[1],
        );
        f.render_widget(
            Paragraph::new(Line::from(vec![
                tuivory::ui::text::Span::styled(
                    self.text("선택     ", "Choice   "),
                    self.role("surface"),
                ),
                tuivory::ui::text::Span::styled(
                    format!(" {} ▾", self.choices()[self.choice]),
                    self.role(if self.focus == Focus::Choice {
                        "selection"
                    } else {
                        "sample.dropdown"
                    }),
                ),
            ]))
            .style(self.role("surface")),
            fields[2],
        );
        f.render_widget(
            Paragraph::new(Line::from(vec![
                tuivory::ui::text::Span::styled(
                    self.text("선택 상태를 유지합니다 ", "Keep selection state "),
                    self.role("surface"),
                ),
                tuivory::ui::text::Span::styled(
                    if self.checked { "[x]" } else { "[ ]" },
                    self.role(if self.focus == Focus::Check {
                        "selection"
                    } else {
                        "field"
                    }),
                ),
            ]))
            .style(self.role("surface")),
            fields[3],
        );
        f.render_widget(
            Paragraph::new(self.text(
                "비활성   입력할 수 없는 예시",
                "Disabled: read-only example",
            ))
            .style(self.role("disabled")),
            fields[4],
        );
        f.render_widget(
            Paragraph::new(self.text(
                "Tab 영역 이동 · 선택박스 Enter 펼침",
                "Tab: move focus · Enter: open choice",
            ))
            .style(self.role("hint"))
            .wrap(Wrap { trim: false }),
            fields[5],
        );
        for (rect, focus) in [
            (fields[0], Focus::Name),
            (fields[1], Focus::Password),
            (fields[2], Focus::Choice),
            (fields[3], Focus::Check),
        ] {
            self.targets.push((rect, focus));
        }
        if self.focus == Focus::Name && self.popup.is_none() {
            f.set_cursor_position((
                input.x
                    + width
                        .saturating_sub(usize::from(shift))
                        .min(usize::from(input.width.saturating_sub(1)))
                        as u16,
                fields[0].y,
            ));
        }
        let actions = self.block(
            self.text(" 버튼 · 상태 ", " Buttons · States "),
            matches!(self.focus, Focus::Apply | Focus::Popup | Focus::Reset),
        );
        let actions = actions.padding(Padding::horizontal(1));
        let inner = actions.inner(top[1]);
        f.render_widget(actions, top[1]);
        let action_rows = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(0),
        ])
        .split(inner);
        for (i, role, text) in [
            (
                0,
                "info",
                self.text(
                    "안내: 색 이외에 문구도 함께 표시합니다.",
                    "Info: states use text as well as color.",
                ),
            ),
            (
                1,
                "success",
                self.text(
                    "정상: 조작 가능한 견본입니다.",
                    "OK: this is an interactive example.",
                ),
            ),
            (
                2,
                "warning",
                self.text(
                    "주의: 미리보기는 단말 능력을 바꾸지 않습니다.",
                    "Warning: preview leaves terminal unchanged.",
                ),
            ),
            (
                3,
                "error",
                self.text(
                    "오류: F5로 입력 오류 상태를 켜 보세요.",
                    "Error: press F5 to toggle input errors.",
                ),
            ),
        ] {
            f.render_widget(
                Paragraph::new(text).style(self.styles.text_on_surface(role, "surface").unwrap()),
                action_rows[i],
            );
        }
        let buttons = Layout::horizontal([Constraint::Ratio(1, 4); 4]).split(action_rows[5]);
        for (i, focus, label) in [
            (0, Focus::Apply, self.text("적용", "Apply")),
            (1, Focus::Popup, self.text("팝업", "Popup")),
            (2, Focus::Reset, self.text("초기화", "Reset")),
        ] {
            f.render_widget(
                Paragraph::new(format!(" {label} "))
                    .centered()
                    .style(self.role(if self.focus == focus {
                        "button.focus"
                    } else {
                        "button"
                    })),
                buttons[i],
            );
            self.targets.push((buttons[i], focus));
        }
        f.render_widget(
            Paragraph::new(self.text("비활성", "Disabled"))
                .centered()
                .style(self.role("disabled")),
            buttons[3],
        );
        let items = [
            self.text("입력창과 선택박스", "Inputs and choices"),
            self.text("버튼과 비활성 상태", "Buttons and disabled states"),
            self.text("포커스와 선택은 별개", "Focus differs from selection"),
            self.text("팝업과 배경 입력 차단", "Popups block background input"),
        ];
        let list = List::new(items.into_iter().map(ListItem::new))
            .style(self.role("surface"))
            .highlight_style(self.role("selection"))
            .block(
                self.block(
                    self.text(" 목록 · 선택과 포커스 ", " List · Selection and Focus "),
                    self.focus == Focus::List,
                )
                .padding(Padding::horizontal(1)),
            );
        f.render_stateful_widget(list, bottom[0], &mut self.list);
        self.targets.push((bottom[0], Focus::List));
        let data: Vec<_> = self
            .rows
            .iter()
            .enumerate()
            .map(|(i, value)| {
                Row::new(vec![
                    (i + 1).to_string(),
                    "│".into(),
                    value.clone(),
                    "│".into(),
                    if self.edited[i] {
                        self.text("* 변경됨", "* Edited")
                    } else {
                        self.text("원본", "Original")
                    }
                    .into(),
                ])
                .style(self.role(if self.edited[i] {
                    "edited"
                } else if self.table.selected() == Some(i) {
                    "sample.grid.current"
                } else if i % 2 == 1 {
                    "sample.grid.stripe"
                } else {
                    "sample.grid.body"
                }))
            })
            .collect();
        let table = Table::new(
            data,
            [
                Constraint::Length(2),
                Constraint::Length(1),
                Constraint::Min(8),
                Constraint::Length(1),
                Constraint::Length(10),
            ],
        )
        .header(
            Row::new(vec![
                "ID",
                "│",
                self.text("이름", "Name"),
                "│",
                self.text("상태", "State"),
            ])
            .style(
                self.role("sample.grid.header")
                    .add_modifier(Modifier::UNDERLINED),
            ),
        )
        .column_spacing(0)
        .style(self.role("sample.grid.body"))
        .cell_highlight_style(
            if self.focus == Focus::Table {
                self.role("selection")
            } else {
                self.role("sample.grid.header")
            }
            .add_modifier(Modifier::UNDERLINED),
        )
        .block(
            self.block(
                self.text(" 그리드 · Enter 셀 편집 ", " Grid · Enter to Edit "),
                self.focus == Focus::Table,
            )
            .padding(Padding::horizontal(1))
            .style(self.role("sample.grid.body")),
        );
        let mut displayed = self.table;
        displayed.select_column(self.table.selected_column().map(|c| c * 2));
        f.render_stateful_widget(table, bottom[1], &mut displayed);
        self.targets.push((bottom[1], Focus::Table));
    }
    fn draw_popup(&mut self, f: &mut Frame<'_>, area: Rect) {
        if let Some(Popup::Choice(selected)) = self.popup {
            let field = self
                .targets
                .iter()
                .find(|(_, target)| *target == Focus::Choice)
                .unwrap()
                .0;
            self.popup_rect = Rect::new(field.x + 9, field.y + 1, field.width.saturating_sub(9), 3);
            f.render_widget(Clear, self.popup_rect);
            f.render_stateful_widget(
                List::new(self.choices().map(ListItem::new))
                    .style(self.role("sample.dropdown"))
                    .highlight_style(self.role("selection")),
                self.popup_rect,
                &mut ListState::default().with_selected(Some(selected)),
            );
            return;
        }
        for cell in &mut f.buffer_mut().content {
            cell.modifier.insert(Modifier::DIM);
        }
        let width = area.width.saturating_sub(6).min(76);
        let height =
            area.height
                .saturating_sub(4)
                .min(if matches!(self.popup, Some(Popup::Edit { .. })) {
                    10
                } else {
                    20
                });
        self.popup_rect = Rect::new(
            area.x + (area.width - width) / 2,
            area.y + (area.height - height) / 2,
            width,
            height,
        );
        f.render_widget(Clear, self.popup_rect);
        let title = match self.popup.as_ref().unwrap() {
            Popup::Help => self.text(" TUIVORY 조작 안내 ", " TUIVORY Controls "),
            Popup::Choice(_) => self.text(" 선택 ", " Choice "),
            Popup::Edit { .. } => {
                self.text(" 셀 편집 · 합성 데이터 ", " Edit Cell · Synthetic Data ")
            }
            _ => self.text(
                " 팝업 · 현재 입력 미리보기 ",
                " Popup · Current Input Preview ",
            ),
        };
        let block = self.block(title, true).padding(Padding::new(2, 2, 1, 1));
        let inner = block.inner(self.popup_rect);
        f.render_widget(block, self.popup_rect);
        let parts = Layout::vertical([Constraint::Min(0), Constraint::Length(1)]).split(inner);
        self.popup_action = parts[1];
        let text = match self.popup.as_ref().unwrap() {
            Popup::Preview => format!("{} {}\n{} {}\n{} {}\n\n{}", self.text("이름:", "Name:"), self.name, self.text("선택:", "Choice:"), self.choices()[self.choice], self.text("체크:", "Checked:"), self.checked, self.text("암호 예시는 표시하지 않습니다.\n\nTab/Shift+Tab은 팝업 안에서만 이동합니다.\n바깥 클릭은 뒤 화면을 조작하지 않습니다.\nF2/F3으로 팝업을 연 상태에서도 테마를 바꿀 수 있습니다.\nEsc로 닫으면 이전 포커스로 돌아갑니다.", "The password example is hidden.\n\nTab/Shift+Tab cycles within this popup.\nOutside clicks do not reach the background.\nF2/F3 changes styles while the popup is open.\nEsc closes it and restores the previous focus.")),
            Popup::Help => self.guide(),
            Popup::Selector { .. } => unreachable!("selectors are drawn at their field"),
            Popup::Choice(selected) => self.choices().iter().enumerate().map(|(i, c)| format!("{} {c}", if i == *selected { '>' } else { ' ' })).collect::<Vec<_>>().join("\n"),
            Popup::Edit { save, .. } => format!("{}\n\n\n\n{}", self.text("새 값:", "New value:"), if *save { self.text("저장 버튼 선택됨: Enter로 저장", "Save focused: press Enter to save") } else { self.text("입력 중: Enter/Tab으로 저장 버튼 이동", "Editing: Enter/Tab focuses Save") }),
        };
        f.render_widget(
            Paragraph::new(text)
                .style(self.role("surface"))
                .wrap(Wrap { trim: false })
                .scroll((self.scroll, 0)),
            parts[0],
        );
        if let Some(Popup::Edit { value, save, .. }) = &self.popup {
            let input = Rect::new(parts[0].x, parts[0].y + 2, parts[0].width, 1);
            let width = Line::raw(value.as_str()).width();
            let shift = width
                .saturating_sub(usize::from(input.width.saturating_sub(1)))
                .min(usize::from(u16::MAX)) as u16;
            f.render_widget(
                Paragraph::new(value.as_str())
                    .scroll((0, shift))
                    .style(self.role("field")),
                input,
            );
            if !save {
                f.set_cursor_position((
                    input.x
                        + width
                            .saturating_sub(usize::from(shift))
                            .min(usize::from(input.width.saturating_sub(1)))
                            as u16,
                    input.y,
                ));
            }
        }
        let action_focused = match self.popup {
            Some(Popup::Edit { save, .. }) => save,
            Some(Popup::Choice(_)) => true,
            _ => self.popup_action_focused,
        };
        let label = match self.popup {
            Some(Popup::Edit { .. }) => self.text("저장 / Esc 취소", "Save / Esc Cancel"),
            Some(Popup::Choice(_)) => self.text("선택 / Esc 취소", "Select / Esc Cancel"),
            _ => self.text("닫기 / Esc", "Close / Esc"),
        };
        f.render_widget(
            Paragraph::new(label)
                .centered()
                .style(self.role(if action_focused {
                    "button.focus"
                } else {
                    "button"
                })),
            self.popup_action,
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tuivory::ui::{Terminal, backend::TestBackend};

    fn key(app: &mut App, code: KeyCode) {
        app.key(KeyEvent::new(code, KeyModifiers::NONE)).unwrap();
    }
    fn draw(app: &mut App, width: u16, height: u16) -> Terminal<TestBackend> {
        let mut t = Terminal::new(TestBackend::new(width, height)).unwrap();
        t.draw(|f| app.draw(f)).unwrap();
        t
    }
    fn click(app: &mut App, x: u16, y: u16) {
        app.mouse(MouseEvent {
            kind: MouseEventKind::Down(MouseButton::Left),
            column: x,
            row: y,
            modifiers: KeyModifiers::NONE,
        })
        .unwrap();
    }
    #[test]
    fn go_layout_password_and_disabled_actions_across_palettes() {
        for language in [Language::Ko, Language::En] {
            for theme in THEMES {
                for profile in PROFILES {
                    let mut app = App::new(language, theme, profile).unwrap();
                    let terminal = draw(&mut app, 120, 36);
                    let buffer = terminal.backend().buffer();
                    let text: String = buffer.content.iter().map(|cell| cell.symbol()).collect();
                    assert!(text.contains("******"));
                    assert!(!text.contains("sample"));
                    let compact = text.replace(' ', "");
                    assert!(compact.contains(&app.text("둘러보기", "Explore").replace(' ', "")));
                    assert!(
                        compact.contains(
                            &app.text("팝업과 배경 입력 차단", "Popups block background input")
                                .replace(' ', "")
                        )
                    );
                    assert_eq!(
                        app.targets
                            .iter()
                            .find(|(_, t)| *t == Focus::Name)
                            .unwrap()
                            .0
                            .x,
                        23
                    );
                    let disabled = app.role("disabled");
                    assert_eq!(buffer[(23, 7)].fg, disabled.fg.unwrap());
                    assert_eq!(buffer[(23, 7)].bg, disabled.bg.unwrap());
                    assert_eq!(
                        buffer[(23, 7)].modifier.contains(Modifier::DIM),
                        profile == ColorProfile::Ansi8
                    );
                    let previous = (app.focus, app.checked, app.message.clone());
                    click(&mut app, 111, 8); // Go's disabled button position.
                    assert_eq!((app.focus, app.checked, app.message.clone()), previous);
                    let expected = app.focusables();
                    let first = expected.iter().position(|v| *v == Focus::Name).unwrap();
                    for step in 1..=expected.len() {
                        key(&mut app, KeyCode::Tab);
                        assert_eq!(app.focus, expected[(first + step) % expected.len()]);
                    }
                    draw(&mut app, 90, 28);
                    assert!(!app.focusables().contains(&Focus::Nav));
                    assert!(app.focusables().contains(&Focus::Password));
                }
            }
        }
    }
    #[test]
    fn go_theme_color_selectors_and_auto_round_trip() {
        let mut app = App::new(Language::En, Theme::Dark, ColorProfile::Indexed256).unwrap();
        app.set_profile_mode(true, ColorProfile::Indexed256);
        app.password = "secret".into();
        draw(&mut app, 120, 36);
        let theme = app
            .targets
            .iter()
            .find(|(_, t)| *t == Focus::Theme)
            .unwrap()
            .0;
        click(&mut app, theme.x, theme.y);
        key(&mut app, KeyCode::Down);
        key(&mut app, KeyCode::Enter);
        assert_eq!(app.theme, Theme::Light);
        let profile = app
            .targets
            .iter()
            .find(|(_, t)| *t == Focus::Profile)
            .unwrap()
            .0;
        click(&mut app, profile.x, profile.y);
        draw(&mut app, 120, 36);
        let choices = app.popup_rect;
        click(&mut app, choices.x, choices.y + 1);
        assert_eq!(app.profile, ColorProfile::Ansi8);
        assert!(!app.auto);
        for expected in [
            ColorProfile::Ansi16,
            ColorProfile::Indexed256,
            ColorProfile::Truecolor,
            ColorProfile::Indexed256,
        ] {
            key(&mut app, KeyCode::F(3));
            assert_eq!(app.profile, expected);
        }
        assert!(app.auto);
        assert_eq!(app.password, "secret");
        key(&mut app, KeyCode::F(6));
        assert_eq!(app.focus, Focus::Tokens);
        draw(&mut app, 120, 36);
        let nav = app
            .targets
            .iter()
            .find(|(_, t)| *t == Focus::Nav)
            .unwrap()
            .0;
        click(&mut app, nav.x + 1, nav.y + 3);
        assert_eq!(app.page, 2);
        key(&mut app, KeyCode::Enter);
        assert_eq!(app.focus, Focus::Guide);
    }
    #[test]
    fn theme_profile_round_trip_retains_values_selection_and_edits() {
        for language in [Language::Ko, Language::En] {
            let mut app = App::new(language, Theme::Dark, ColorProfile::Ansi8).unwrap();
            app.name = "보존할 한글 input".into();
            app.choice = 2;
            app.checked = false;
            app.list.select(Some(2));
            app.table.select(Some(1));
            app.focus = Focus::Table;
            key(&mut app, KeyCode::Enter);
            key(&mut app, KeyCode::Char('X'));
            key(&mut app, KeyCode::Enter);
            key(&mut app, KeyCode::Enter);
            assert!(app.popup.is_none());
            assert!(app.edited[1]);
            let saved = app.rows[1].clone();
            for _ in 0..3 {
                for _ in 0..5 {
                    key(&mut app, KeyCode::F(3));
                    draw(&mut app, 120, 36);
                    assert_eq!(app.name, "보존할 한글 input");
                    assert_eq!(app.choice, 2);
                    assert!(!app.checked);
                    assert_eq!(app.list.selected(), Some(2));
                    assert_eq!(app.table.selected(), Some(1));
                    assert_eq!(app.focus, Focus::Table);
                    assert_eq!(app.rows[1], saved);
                    assert!(app.edited[1]);
                }
                key(&mut app, KeyCode::F(2));
            }
            assert_eq!(app.theme, Theme::Dark);
            assert_eq!(app.profile, ColorProfile::Ansi8);
        }
    }
    #[test]
    fn popup_traps_focus_blocks_outside_clicks_and_survives_resize() {
        let mut app = App::new(Language::En, Theme::Dark, ColorProfile::Indexed256).unwrap();
        app.focus = Focus::Check;
        draw(&mut app, 120, 36);
        let check = app
            .targets
            .iter()
            .find(|(_, f)| *f == Focus::Check)
            .unwrap()
            .0;
        app.preview();
        draw(&mut app, 120, 36);
        for _ in 0..20 {
            key(&mut app, KeyCode::Tab);
        }
        assert!(app.popup.is_some());
        assert_eq!(app.focus, Focus::Check);
        click(&mut app, check.x, check.y);
        assert!(app.checked);
        assert!(app.popup.is_some());
        draw(&mut app, 60, 18);
        assert!(app.small);
        assert!(app.popup.is_some());
        key(&mut app, KeyCode::Tab);
        assert!(app.popup.is_some());
        draw(&mut app, 120, 36);
        assert!(!app.small);
        assert!(app.popup.is_some());
        key(&mut app, KeyCode::Esc);
        assert!(app.popup.is_none());
        assert_eq!(app.focus, Focus::Check);
    }
    #[test]
    fn mouse_operates_choice_check_buttons_list_and_table() {
        let mut app = App::new(Language::En, Theme::Dark, ColorProfile::Ansi16).unwrap();
        draw(&mut app, 120, 36);
        for target in [Focus::Check, Focus::Choice] {
            let rect = app.targets.iter().find(|(_, f)| *f == target).unwrap().0;
            click(&mut app, rect.x, rect.y);
        }
        assert!(!app.checked);
        assert!(matches!(app.popup, Some(Popup::Choice(_))));
        draw(&mut app, 120, 36);
        let rect = app.popup_rect;
        click(&mut app, rect.x + 2, rect.y + 2);
        assert_eq!(app.choice, 2);
        assert!(app.popup.is_none());
        draw(&mut app, 120, 36);
        let rect = app
            .targets
            .iter()
            .find(|(_, f)| *f == Focus::Table)
            .unwrap()
            .0;
        click(&mut app, rect.x + 7, rect.y + 3);
        assert_eq!(app.table.selected(), Some(1));
        key(&mut app, KeyCode::Enter);
        assert!(matches!(app.popup, Some(Popup::Edit { row: 1, .. })));
        key(&mut app, KeyCode::Esc);
        draw(&mut app, 120, 36);
        let reset = app
            .targets
            .iter()
            .find(|(_, f)| *f == Focus::Reset)
            .unwrap()
            .0;
        click(&mut app, reset.x, reset.y);
        assert!(app.checked);
        assert_eq!(app.choice, 0);
    }
    #[test]
    fn english_views_and_popups_contain_no_korean_defaults() {
        let mut app = App::new(Language::En, Theme::Light, ColorProfile::Truecolor).unwrap();
        let english = |app: &mut App, width, height| {
            let terminal = draw(app, width, height);
            for cell in &terminal.backend().buffer().content {
                assert!(
                    !cell
                        .symbol()
                        .chars()
                        .any(|c| ('\u{ac00}'..='\u{d7a3}').contains(&c)),
                    "{}",
                    cell.symbol()
                );
            }
        };
        for page in 0..3 {
            app.page = page;
            english(&mut app, 120, 36);
        }
        app.page = 0;
        key(&mut app, KeyCode::F(1));
        english(&mut app, 120, 36);
        key(&mut app, KeyCode::Esc);
        app.preview();
        english(&mut app, 120, 36);
        key(&mut app, KeyCode::Esc);
        app.focus = Focus::Table;
        key(&mut app, KeyCode::Enter);
        english(&mut app, 80, 24);
        english(&mut app, 60, 18);
        key(&mut app, KeyCode::Esc);
    }
}
