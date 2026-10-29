use crossterm::event::{KeyCode, KeyEvent, KeyModifiers, MouseButton, MouseEvent, MouseEventKind};
use ratatui::{
    Frame,
    layout::{Constraint, Layout, Rect},
    style::Modifier,
    text::Line,
    widgets::{Clear, List, ListItem, ListState, Paragraph, Row, Table, TableState, Wrap},
};
use tuivory::ratatui::Styles;
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
    Name,
    Choice,
    Check,
    Apply,
    Popup,
    Reset,
    List,
    Table,
}
const FOCUS: [Focus; 8] = [
    Focus::Name,
    Focus::Choice,
    Focus::Check,
    Focus::Apply,
    Focus::Popup,
    Focus::Reset,
    Focus::List,
    Focus::Table,
];
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
            styles: Styles::new(theme, profile)?,
            name: language.text("한글과 English", "Hello, world!").into(),
            choice: 0,
            checked: true,
            invalid: false,
            focus: Focus::Name,
            list: ListState::default().with_selected(Some(0)),
            table: TableState::default().with_selected(Some(0)),
            rows: vec![
                language.text("입력 예시", "Sample input").into(),
                language.text("선택과 포커스", "Selection and focus").into(),
                language.text("Enter로 편집", "Enter to edit").into(),
            ],
            edited: vec![false; 3],
            popup: None,
            page: 0,
            scroll: 0,
            message: language
                .text(
                    "DB·파일에 저장하지 않는 합성 예제입니다.",
                    "Synthetic example. Nothing is saved to a database or file.",
                )
                .into(),
            targets: vec![],
            popup_rect: Rect::default(),
            popup_action: Rect::default(),
            popup_action_focused: false,
            small: false,
        })
    }
    fn text<'a>(&self, ko: &'a str, en: &'a str) -> &'a str {
        self.language.text(ko, en)
    }
    fn role(&self, name: &str) -> ratatui::style::Style {
        self.styles.role(name).expect("bundled semantic role")
    }
    fn block<'a>(&self, title: &'a str, focused: bool) -> ratatui::widgets::Block<'a> {
        self.styles
            .block(title, focused)
            .expect("bundled semantic role")
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
                .select(Some((current as isize + delta).rem_euclid(3) as usize));
        } else if self.focus == Focus::Table {
            let current = self.table.selected().unwrap_or(0);
            self.table
                .select(Some((current as isize + delta).rem_euclid(3) as usize));
        }
    }
    fn activate(&mut self) -> Result<(), Error> {
        match self.focus {
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
            Focus::Table => {
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
                self.styles = Styles::new(self.theme, self.profile)?;
                return Ok(false);
            }
            KeyCode::F(3) => {
                let i = PROFILES.iter().position(|p| *p == self.profile).unwrap();
                self.profile = PROFILES[(i + 1) % 4];
                self.styles = Styles::new(self.theme, self.profile)?;
                return Ok(false);
            }
            _ => (),
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
                self.page = (self.page + 1) % 3;
                self.scroll = 0;
            }
            KeyCode::Up if self.page > 0 => self.scroll = self.scroll.saturating_sub(1),
            KeyCode::Down if self.page > 0 => self.scroll = self.scroll.saturating_add(1).min(30),
            _ if self.page > 0 => (),
            KeyCode::Tab | KeyCode::BackTab => {
                let i = FOCUS.iter().position(|f| *f == self.focus).unwrap();
                self.focus = FOCUS[(i + if event.code == KeyCode::Tab { 1 } else { 7 }) % 8];
            }
            KeyCode::Up => self.move_selection(-1),
            KeyCode::Down => self.move_selection(1),
            KeyCode::Enter => self.activate()?,
            KeyCode::Char(' ') if self.focus == Focus::Check => self.checked = !self.checked,
            KeyCode::Backspace if self.focus == Focus::Name => {
                self.name.pop();
            }
            KeyCode::Char(c)
                if self.focus == Focus::Name
                    && !event
                        .modifiers
                        .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT)
                    && !c.is_control() =>
            {
                self.name.push(c)
            }
            _ => (),
        }
        Ok(false)
    }
    pub fn mouse(&mut self, event: MouseEvent) -> Result<(), Error> {
        if self.small {
            return Ok(());
        }
        let position = (event.column, event.row).into();
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
        if self.page > 0 {
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
                if matches!(target, Focus::List | Focus::Table) {
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
                        usize::from(event.row.saturating_sub(rect.y + 1)).min(2),
                    )),
                    Focus::Table => self.table.select(Some(
                        usize::from(event.row.saturating_sub(rect.y + 2)).min(2),
                    )),
                    Focus::Name => (),
                    _ => self.activate()?,
                }
            }
        }
        Ok(())
    }
    fn help(&self) -> &str {
        self.text("Tab/Shift+Tab: 조작 대상 이동", "Tab/Shift+Tab: move focus")
    }
    pub fn draw(&mut self, f: &mut Frame<'_>) {
        self.targets.clear();
        let area = f.area();
        self.small = area.width < 80 || area.height < 24;
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
                " TUIVORY Rust · 직접 조작하는 스타일 견본",
                " TUIVORY Rust · Interactive style playground",
            ))
            .style(self.role("header")),
            rows[0],
        );
        f.render_widget(
            Paragraph::new(format!(
                " {}: {}   {}: {}   {}",
                self.text("테마", "Theme"),
                self.theme.as_str(),
                self.text("색상", "Colors"),
                self.profile.as_str(),
                self.text("공통 후보 팔레트", "Shared candidate palette")
            ))
            .style(self.role("surface")),
            rows[1],
        );
        f.render_widget(
            Paragraph::new(self.message.as_str()).style(self.role("hint")),
            rows[3],
        );
        f.render_widget(
            Paragraph::new(self.text(
                " Tab 이동 · F1 도움말 F2 테마 F3 색상 F4 팝업 F5 오류 F6 화면 · Ctrl+Q 종료",
                " Tab Focus · F1 Help F2 Theme F3 Colors F4 Popup F5 Error F6 View · Ctrl+Q Quit",
            ))
            .style(self.role("surface")),
            rows[4],
        );
        match self.page {
            1 => {
                let doc = tuivory::TokenDocument::candidate().expect("bundled tokens");
                let palette = doc.tokens(self.theme, self.profile).unwrap();
                let body = doc
                    .roles()
                    .iter()
                    .skip(usize::from(self.scroll))
                    .map(|role| {
                        let pair = &palette.pairs()[role];
                        Row::new(vec![
                            role.clone(),
                            pair.foreground.clone(),
                            pair.background.clone(),
                            " Aa ".into(),
                        ])
                        .style(self.role(role))
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
                    .block(self.block(self.text(" 색상 토큰 ", " Color tokens "), true)),
                    rows[2],
                );
            }
            2 => f.render_widget(
                Paragraph::new(self.guide())
                    .wrap(Wrap { trim: false })
                    .scroll((self.scroll, 0))
                    .style(self.role("surface"))
                    .block(self.block(self.text(" 조작 안내 ", " Controls "), true)),
                rows[2],
            ),
            _ => self.draw_components(f, rows[2]),
        }
        if self.popup.is_some() {
            self.draw_popup(f, area);
        }
    }
    fn guide(&self) -> String {
        format!("{}\n\n{}\n{}\n{}\n{}\n{}\n{}", self.text("데이터는 DB·파일에 저장하지 않습니다.", "Nothing is saved to a database or file."), self.help(), self.text("방향키: 목록·표·선택박스 탐색", "Arrows: navigate list/table/choices"), self.text("Enter: 실행·선택 펼침·셀 편집 / Space: 체크", "Enter: activate/open choice/edit cell / Space: checkbox"), self.text("F2/F3: 입력·선택·편집 상태를 유지하며 스타일 변경", "F2/F3: switch styles while preserving values and selections"), self.text("Esc: 팝업 닫기 / Ctrl+Q: 종료", "Esc: close popup / Ctrl+Q: quit"), self.text("편집: Enter로 저장 버튼 이동 후 Enter. Tab으로 전환.\n팝업 바깥 클릭은 배경에 전달하지 않습니다.", "Edit: Enter to focus Save, then Enter to save. Tab switches focus.\nOutside popup clicks do not reach the background."))
    }
    fn draw_components(&mut self, f: &mut Frame<'_>, area: Rect) {
        let bands = Layout::vertical([Constraint::Length(9), Constraint::Min(0)]).split(area);
        let top = Layout::horizontal([Constraint::Percentage(50), Constraint::Percentage(50)])
            .split(bands[0]);
        let bottom = Layout::horizontal([Constraint::Percentage(50), Constraint::Percentage(50)])
            .split(bands[1]);
        let fields = self.block(
            self.text(" 입력·선택 ", " Inputs · Choices "),
            matches!(self.focus, Focus::Name | Focus::Choice | Focus::Check),
        );
        let inner = fields.inner(top[0]);
        f.render_widget(fields, top[0]);
        let fields = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(0),
        ])
        .split(inner);
        let name = format!(
            "{}{}",
            if self.invalid {
                self.text("오류! 이름: ", "Error! Name: ")
            } else {
                self.text("이름: ", "Name: ")
            },
            self.name
        );
        let width = Line::raw(name.as_str()).width();
        let shift = width
            .saturating_sub(usize::from(fields[0].width.saturating_sub(1)))
            .min(usize::from(u16::MAX)) as u16;
        f.render_widget(
            Paragraph::new(name)
                .scroll((0, shift))
                .style(self.role("field").add_modifier(
                    if self.invalid || self.focus == Focus::Name {
                        Modifier::UNDERLINED
                    } else {
                        Modifier::empty()
                    },
                )),
            fields[0],
        );
        f.render_widget(
            Paragraph::new(format!(
                "{} {} ▾",
                self.text("선택:", "Choice:"),
                self.choices()[self.choice]
            ))
            .style(
                self.role("field")
                    .add_modifier(if self.focus == Focus::Choice {
                        Modifier::UNDERLINED
                    } else {
                        Modifier::empty()
                    }),
            ),
            fields[1],
        );
        f.render_widget(
            Paragraph::new(format!(
                "[{}] {}",
                if self.checked { 'x' } else { ' ' },
                self.text("선택 상태 유지", "Keep selection state")
            ))
            .style(
                self.role("surface")
                    .add_modifier(if self.focus == Focus::Check {
                        Modifier::UNDERLINED
                    } else {
                        Modifier::empty()
                    }),
            ),
            fields[2],
        );
        f.render_widget(
            Paragraph::new(self.text("비활성: 읽기 전용 예시", "Disabled: read-only example"))
                .style(self.role("disabled")),
            fields[3],
        );
        f.render_widget(
            Paragraph::new(self.text(
                "Tab 이동 · Enter 펼침 · Space 체크",
                "Tab Focus · Enter Open · Space Check",
            ))
            .style(self.role("hint"))
            .wrap(Wrap { trim: false }),
            fields[4],
        );
        for (rect, focus) in [
            (fields[0], Focus::Name),
            (fields[1], Focus::Choice),
            (fields[2], Focus::Check),
        ] {
            self.targets.push((rect, focus));
        }
        if self.focus == Focus::Name && self.popup.is_none() {
            f.set_cursor_position((
                fields[0].x
                    + width
                        .saturating_sub(usize::from(shift))
                        .min(usize::from(fields[0].width.saturating_sub(1)))
                        as u16,
                fields[0].y,
            ));
        }
        let actions = self.block(
            self.text(" 버튼·상태 ", " Buttons · States "),
            matches!(self.focus, Focus::Apply | Focus::Popup | Focus::Reset),
        );
        let inner = actions.inner(top[1]);
        f.render_widget(actions, top[1]);
        let action_rows = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(0),
            Constraint::Length(1),
        ])
        .split(inner);
        for (i, role, text) in [
            (
                0,
                "info",
                self.text(
                    "안내: 색과 문구로 의미를 표시합니다.",
                    "Info: meaning uses color and text.",
                ),
            ),
            (
                1,
                "success",
                self.text(
                    "정상: 직접 조작할 수 있습니다.",
                    "OK: this example is interactive.",
                ),
            ),
            (
                2,
                "warning",
                self.text(
                    "주의: 단말 능력은 바뀌지 않습니다.",
                    "Warning: terminal support is unchanged.",
                ),
            ),
            (
                3,
                "error",
                self.text(
                    "오류: F5로 입력 오류를 표시합니다.",
                    "Error: F5 toggles input errors.",
                ),
            ),
        ] {
            f.render_widget(
                Paragraph::new(text).style(self.styles.text_on_surface(role, "surface").unwrap()),
                action_rows[i],
            );
        }
        let buttons = Layout::horizontal([Constraint::Ratio(1, 3); 3]).split(action_rows[5]);
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
        let items = [
            self.text("입력창과 선택박스", "Inputs and choices"),
            self.text("버튼과 비활성 상태", "Buttons and disabled states"),
            self.text("선택과 포커스는 별개", "Selection differs from focus"),
        ];
        let list = List::new(items.into_iter().map(ListItem::new))
            .style(self.role("surface"))
            .highlight_style(self.role("selection"))
            .highlight_symbol("> ")
            .block(self.block(self.text(" 목록 ", " List "), self.focus == Focus::List));
        f.render_stateful_widget(list, bottom[0], &mut self.list);
        self.targets.push((bottom[0], Focus::List));
        let data: Vec<_> = self
            .rows
            .iter()
            .enumerate()
            .map(|(i, value)| {
                Row::new(vec![
                    (i + 1).to_string(),
                    value.clone(),
                    if self.edited[i] {
                        self.text("* 변경됨", "* Edited")
                    } else {
                        self.text("원본", "Original")
                    }
                    .into(),
                ])
                .style(self.role(if self.edited[i] {
                    "edited"
                } else {
                    "surface"
                }))
            })
            .collect();
        let table = Table::new(
            data,
            [
                Constraint::Length(3),
                Constraint::Min(8),
                Constraint::Length(10),
            ],
        )
        .header(
            Row::new(vec![
                "ID",
                self.text("이름", "Name"),
                self.text("상태", "State"),
            ])
            .style(self.role("header")),
        )
        .row_highlight_style(self.role("selection"))
        .highlight_symbol("> ")
        .block(self.block(
            self.text(" 표·Enter 편집 ", " Table · Enter to Edit "),
            self.focus == Focus::Table,
        ));
        f.render_stateful_widget(table, bottom[1], &mut self.table);
        self.targets.push((bottom[1], Focus::Table));
    }
    fn draw_popup(&mut self, f: &mut Frame<'_>, area: Rect) {
        let width = area.width.saturating_sub(6).min(76);
        let height = area.height.saturating_sub(4).min(18);
        self.popup_rect = Rect::new(
            area.x + (area.width - width) / 2,
            area.y + (area.height - height) / 2,
            width,
            height,
        );
        f.render_widget(Clear, self.popup_rect);
        let title = match self.popup.as_ref().unwrap() {
            Popup::Help => self.text(" 도움말 ", " Help "),
            Popup::Choice(_) => self.text(" 선택 ", " Choice "),
            Popup::Edit { .. } => self.text(" 셀 편집 ", " Edit Cell "),
            _ => self.text(" 현재 입력 미리보기 ", " Current Input Preview "),
        };
        let block = self.block(title, true);
        let inner = block.inner(self.popup_rect);
        f.render_widget(block, self.popup_rect);
        let parts = Layout::vertical([Constraint::Min(0), Constraint::Length(1)]).split(inner);
        self.popup_action = parts[1];
        let text = match self.popup.as_ref().unwrap() {
            Popup::Preview => format!("{} {}\n{} {}\n{} {}\n\n{}", self.text("이름:", "Name:"), self.name, self.text("선택:", "Choice:"), self.choices()[self.choice], self.text("체크:", "Checked:"), self.checked, self.text("F2/F3으로 테마·색상 변경\nEsc로 닫으면 이전 포커스로 돌아갑니다.\n데이터를 저장하지 않습니다.", "F2/F3 switches theme and colors.\nEsc restores the previous focus.\nNo data is saved.")),
            Popup::Help => self.guide(),
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
    use ratatui::{Terminal, backend::TestBackend};

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
                for _ in 0..4 {
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
        click(&mut app, rect.x + 2, rect.y + 3);
        assert_eq!(app.choice, 2);
        assert!(app.popup.is_none());
        draw(&mut app, 120, 36);
        let rect = app
            .targets
            .iter()
            .find(|(_, f)| *f == Focus::Table)
            .unwrap()
            .0;
        click(&mut app, rect.x + 2, rect.y + 3);
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
