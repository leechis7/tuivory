# Rust API — source (0.8.0)

**한국어 (기본)** · [English](rust.en.md)

[API 안내](README.md) · [컴포넌트 사용법](../components.md)

실제 소스에서 생성한 공개 선언과 원문 주석입니다. 코드·심볼·원문 주석은 두 언어판에서 동일하게 유지합니다. 기본값·오류·이벤트 의미는 API 안내의 컴포넌트별 명세를 참고하세요. 외부 프레임워크의 상속/trait API는 해당 프레임워크 문서를 참고합니다.

### tuivory::CANDIDATE_JSON

```rust
pub const CANDIDATE_JSON: &str = include_str!("data/candidate.json");
```




### tuivory::Color

```rust
pub enum Color {
    Indexed(u8),
    Rgb(u8, u8, u8),
}
```

ANSI indices stay distinct from reference RGB values and user palettes.


### tuivory::ColorProfile

```rust
pub enum ColorProfile {
    Ansi8,
    Ansi16,
    Indexed256,
    Truecolor,
}
```



#### tuivory::ColorProfile::as_str

```rust
pub fn as_str(self) -> &'static str;
```



### tuivory::Error

```rust
pub enum Error {
    Json(serde_json::Error),
    Invalid(String),
    UnknownPalette(String),
    UnknownRole(String),
}
```




### tuivory::Palette

```rust
pub struct Palette(pub(crate) BTreeMap<String, Style>);
```

An owned palette; styles carry no widget state or callbacks.

#### tuivory::Palette::style

```rust
pub fn style(&self, role: &str) -> Result<Style, Error>;
```



#### tuivory::Palette::styles

```rust
pub fn styles(&self) -> &BTreeMap<String, Style>;
```



### tuivory::Style

```rust
pub struct Style {
    pub foreground: Color,
    pub background: Color,
    pub bold: bool,
}
```




### tuivory::TOKEN_FORMAT

```rust
pub const TOKEN_FORMAT: &str = "tuivory.tokens.draft";
```




### tuivory::Theme

```rust
pub enum Theme {
    Dark,
    Light,
    Blackwhite,
}
```



#### tuivory::Theme::as_str

```rust
pub fn as_str(self) -> &'static str;
```



### tuivory::TokenDocument

```rust
pub struct TokenDocument(DocumentData);
```

A validated document. Mutation cannot bypass profile/role validation.

#### tuivory::TokenDocument::from_json

```rust
pub fn from_json(data: &str) -> Result<Self, Error>;
```



#### tuivory::TokenDocument::candidate

```rust
pub fn candidate() -> Result<Self, Error>;
```



#### tuivory::TokenDocument::roles

```rust
pub fn roles(&self) -> &[String];
```



#### tuivory::TokenDocument::palette_names

```rust
pub fn palette_names(&self) -> impl Iterator<Item = &str>;
```



#### tuivory::TokenDocument::tokens

```rust
pub fn tokens(&self, theme: Theme, profile: ColorProfile) -> Result<TokenPalette, Error>;
```

Return an independent raw palette suitable for cross-language checks.

#### tuivory::TokenDocument::palette

```rust
pub fn palette(&self, theme: Theme, profile: ColorProfile) -> Result<Palette, Error>;
```



### tuivory::TokenPair

```rust
pub struct TokenPair {
    pub foreground: String,
    pub background: String,
    pub reference_foreground: String,
    pub reference_background: String,
    pub font_weight: String,
}
```




### tuivory::TokenPalette

```rust
pub struct TokenPalette(#[serde(deserialize_with = "unique_map")] BTreeMap<String, TokenPair>);
```



#### tuivory::TokenPalette::pairs

```rust
pub fn pairs(&self) -> &BTreeMap<String, TokenPair>;
```



#### tuivory::TokenPalette::resolve

```rust
pub fn resolve(&self) -> Result<Palette, Error>;
```

Resolve checked colors without substituting reference RGB values.

### tuivory::collections::ListEvent

```rust
pub struct ListEvent {
    pub kind: String,
    pub id: String,
    pub query: String,
}
```




### tuivory::collections::ListItem

```rust
pub struct ListItem {
    pub id: String,
    pub label: String,
    pub secondary: String,
    pub shortcut: String,
    pub icon: String,
    pub ascii_icon: String,
    pub disabled: bool,
    pub separator: bool,
}
```




### tuivory::collections::ListModel

```rust
pub struct ListModel {
    pub focused: String,
    pub selected: String,
    pub query: String,
    pub empty: String,
    // Private fields omitted.
}
```



#### tuivory::collections::ListModel::new

```rust
pub fn new(items: Vec<ListItem>) -> Result<Self, Error>;
```



#### tuivory::collections::ListModel::items

```rust
pub fn items(&self) -> &[ListItem];
```



#### tuivory::collections::ListModel::set_items

```rust
pub fn set_items(&mut self, items: Vec<ListItem>) -> Result<(), Error>;
```



#### tuivory::collections::ListModel::focus

```rust
pub fn focus(&mut self, id: &str) -> bool;
```



#### tuivory::collections::ListModel::set_query

```rust
pub fn set_query(&mut self, query: &str) -> ListEvent;
```



#### tuivory::collections::ListModel::handle

```rust
pub fn handle(&mut self, action: &str, height: usize) -> ListEvent;
```



#### tuivory::collections::ListModel::layout

```rust
pub fn layout(&self, width: usize, height: usize, ascii: bool) -> Vec<ComponentLine>;
```



### tuivory::collections::SearchPicker

```rust
pub struct SearchPicker {
    pub list: ListModel,
    pub open: bool,
    pub value: String,
}
```



#### tuivory::collections::SearchPicker::new

```rust
pub fn new(items: Vec<ListItem>) -> Result<Self, Error>;
```



#### tuivory::collections::SearchPicker::handle

```rust
pub fn handle(&mut self, action: &str, text: &str, height: usize) -> ListEvent;
```



#### tuivory::collections::SearchPicker::click

```rust
pub fn click(&mut self, id: &str) -> ListEvent;
```



#### tuivory::collections::SearchPicker::layout

```rust
pub fn layout(&self, width: usize, height: usize, ascii: bool) -> Vec<ComponentLine>;
```



### tuivory::components::LineRun

```rust
pub struct LineRun {
    pub text: String,
    pub role: String,
    pub id: String,
    pub start: usize,
    pub width: usize,
}
```




### tuivory::components::PathItem

```rust
pub struct PathItem {
    pub id: String,
    pub label: String,
}
```




### tuivory::components::SplitLayout

```rust
pub struct SplitLayout {
    pub first: usize,
    pub divider: usize,
    pub second: usize,
    pub compact: bool,
}
```




### tuivory::components::SplitSpec

```rust
pub struct SplitSpec {
    pub first_min: usize,
    pub second_min: usize,
}
```



#### tuivory::components::SplitSpec::layout

```rust
pub fn layout(self, state: &SplitState, total: usize) -> SplitLayout;
```



#### tuivory::components::SplitSpec::resize

```rust
pub fn resize(self, state: &mut SplitState, total: usize, position: usize) -> bool;
```



### tuivory::components::SplitState

```rust
pub struct SplitState {
    pub preferred: usize,
}
```




### tuivory::components::StatusItem

```rust
pub struct StatusItem {
    pub id: String,
    pub text: String,
    pub role: String,
    pub priority: i32,
}
```




### tuivory::components::StatusLayout

```rust
pub struct StatusLayout {
    pub runs: Vec<LineRun>,
    pub omitted: usize,
}
```




### tuivory::components::TabAction

```rust
pub enum TabAction {
    Previous,
    Next,
    First,
    Last,
    Activate,
    Close,
}
```




### tuivory::components::TabCell

```rust
pub struct TabCell {
    pub id: String,
    pub text: String,
    pub start: usize,
    pub width: usize,
    pub active: bool,
    pub focused: bool,
    pub disabled: bool,
}
```




### tuivory::components::TabEvent

```rust
pub enum TabEvent {
    Focus(String),
    Activate(String),
    Close(String),
}
```




### tuivory::components::TabItem

```rust
pub struct TabItem {
    pub id: String,
    pub title: String,
    pub edited: bool,
    pub closable: bool,
    pub disabled: bool,
}
```




### tuivory::components::TabLayout

```rust
pub struct TabLayout {
    pub cells: Vec<TabCell>,
    pub previous: bool,
    pub next: bool,
}
```




### tuivory::components::TabState

```rust
pub struct TabState {
    pub active: String,
    pub focused: String,
    pub first: usize,
}
```




### tuivory::components::Tabs

```rust
pub struct Tabs {

    // Private fields omitted.
}
```



#### tuivory::components::Tabs::new

```rust
pub fn new(items: Vec<TabItem>) -> Result<Self, String>;
```



#### tuivory::components::Tabs::reconcile

```rust
pub fn reconcile(&self, state: &mut TabState);
```



#### tuivory::components::Tabs::handle

```rust
pub fn handle(&self, state: &mut TabState, action: TabAction) -> Option<TabEvent>;
```



#### tuivory::components::Tabs::layout

```rust
pub fn layout(&self, state: &mut TabState, width: usize) -> TabLayout;
```



#### tuivory::components::Tabs::click

```rust
pub fn click(&self, state: &mut TabState, column: usize, width: usize) -> Option<TabEvent>;
```



### tuivory::components::breadcrumbs

```rust
pub fn breadcrumbs(items: &[PathItem], width: usize) -> Vec<LineRun>;
```




### tuivory::components::cell_text

```rust
pub fn cell_text(text: &str, width: usize) -> String;
```




### tuivory::components::cells

```rust
pub fn cells(text: &str) -> usize;
```




### tuivory::components::clean

```rust
pub fn clean(text: &str) -> String;
```




### tuivory::components::status_line

```rust
pub fn status_line(items: &[StatusItem], width: usize) -> StatusLayout;
```




### tuivory::containers::ContainerOptions

```rust
pub struct ContainerOptions {
    pub kind: String,
    pub gap: usize,
    pub padding: usize,
    pub rows: Vec<Track>,
    pub columns: Vec<Track>,
    pub virtual_width: usize,
    pub virtual_height: usize,
}
```




### tuivory::containers::ContainerState

```rust
pub struct ContainerState {
    pub focused: String,
    pub captured: String,
    // Private fields omitted.
}
```



#### tuivory::containers::ContainerState::eligible

```rust
pub fn eligible<'a>(&self, items: &'a [LayoutItem]) -> Vec<&'a str>;
```



#### tuivory::containers::ContainerState::reconcile

```rust
pub fn reconcile(&mut self, items: &[LayoutItem]);
```



#### tuivory::containers::ContainerState::move_focus

```rust
pub fn move_focus(&mut self, items: &[LayoutItem], previous: bool) -> &str;
```



#### tuivory::containers::ContainerState::hit

```rust
pub fn hit<'a>(
        &self,
        items: &[LayoutItem],
        rects: &'a [NamedRect],
        x: usize,
        y: usize,
    ) -> Option<&'a str>;
```



#### tuivory::containers::ContainerState::pointer

```rust
pub fn pointer(
        &mut self,
        items: &[LayoutItem],
        rects: &[NamedRect],
        x: usize,
        y: usize,
        press: bool,
        release: bool,
    ) -> Option<String>;
```

Call on pointer press/drag/release. Hosts deliver input to the returned ID.

### tuivory::containers::LayoutItem

```rust
pub struct LayoutItem {
    pub id: String,
    pub track: Track,
    pub row: usize,
    pub column: usize,
    pub row_span: usize,
    pub column_span: usize,
    pub hidden: bool,
    pub disabled: bool,
    pub drawer: String,
    pub modal: bool,
    pub centered: bool,
    pub area: CellRect,
}
```




### tuivory::containers::Track

```rust
pub struct Track {
    pub min: usize,
    pub max: usize,
    pub fixed: usize,
    pub weight: usize,
}
```




### tuivory::containers::compute_container

```rust
pub fn compute_container(
    bounds: CellRect,
    items: &[LayoutItem],
    options: &ContainerOptions,
) -> Result<Vec<NamedRect>, Error>;
```




### tuivory::controls::Control

```rust
pub struct Control {
    pub model: Form,
    pub id: String,
}
```



#### tuivory::controls::Control::new

```rust
pub fn new(field: FormField) -> Result<Self, Error>;
```



#### tuivory::controls::Control::input

```rust
pub fn input(id: &str, label: &str, value: &str, secret: bool) -> Result<Self, Error>;
```



#### tuivory::controls::Control::button

```rust
pub fn button(id: &str, label: &str) -> Result<Self, Error>;
```



#### tuivory::controls::Control::check

```rust
pub fn check(id: &str, label: &str, checked: bool) -> Result<Self, Error>;
```



#### tuivory::controls::Control::select

```rust
pub fn select(
        id: &str,
        label: &str,
        options: Vec<FormOption>,
        choice: &str,
    ) -> Result<Self, Error>;
```



#### tuivory::controls::Control::layout

```rust
pub fn layout(&self, width: usize, height: usize) -> Vec<ComponentLine>;
```



### tuivory::feedback::DataState

```rust
pub struct DataState {
    pub kind: String,
    pub text: String,
    pub detail: String,
}
```



#### tuivory::feedback::DataState::layout

```rust
pub fn layout(&self, width: usize) -> Vec<ComponentLine>;
```



### tuivory::feedback::Notice

```rust
pub struct Notice {
    pub id: String,
    pub text: String,
    pub detail: String,
    pub severity: String,
    pub priority: i32,
    pub persistent: bool,
    pub expires_at: u64,
    pub actions: Vec<NoticeAction>,
}
```




### tuivory::feedback::NoticeAction

```rust
pub struct NoticeAction {
    pub id: String,
    pub label: String,
    pub disabled: bool,
}
```




### tuivory::feedback::NoticeEvent

```rust
pub struct NoticeEvent {
    pub kind: String,
    pub id: String,
    pub action: String,
}
```




### tuivory::feedback::NoticeQueue

```rust
pub struct NoticeQueue {
    pub focused: String,
    // Private fields omitted.
}
```



#### tuivory::feedback::NoticeQueue::new

```rust
pub fn new(capacity: usize) -> Result<Self, Error>;
```



#### tuivory::feedback::NoticeQueue::push

```rust
pub fn push(&mut self, n: Notice) -> Result<(), Error>;
```



#### tuivory::feedback::NoticeQueue::visible

```rust
pub fn visible(&self, now: u64) -> Vec<Notice>;
```



#### tuivory::feedback::NoticeQueue::dismiss

```rust
pub fn dismiss(&mut self, id: &str) -> bool;
```



#### tuivory::feedback::NoticeQueue::expire

```rust
pub fn expire(&mut self, now: u64) -> Vec<NoticeEvent>;
```



#### tuivory::feedback::NoticeQueue::handle

```rust
pub fn handle(&mut self, action: &str, now: u64, height: usize) -> NoticeEvent;
```



#### tuivory::feedback::NoticeQueue::layout

```rust
pub fn layout(&self, width: usize, height: usize, now: u64) -> Vec<ComponentLine>;
```



### tuivory::feedback::Progress

```rust
pub struct Progress {
    pub id: String,
    pub label: String,
    pub status: String,
    pub message: String,
    pub cancel_label: String,
    pub current: u64,
    pub total: u64,
    pub cancellable: bool,
}
```



#### tuivory::feedback::Progress::request_cancel

```rust
pub fn request_cancel(&self) -> NoticeEvent;
```



#### tuivory::feedback::Progress::layout

```rust
pub fn layout(&self, width: usize, frame: u64) -> Vec<ComponentLine>;
```



### tuivory::forms::ComponentLine

```rust
pub struct ComponentLine {
    pub id: String,
    pub text: String,
    pub role: String,
    pub value: String,
    pub focused: bool,
    pub spans: Vec<ComponentSpan>,
}
```




### tuivory::forms::ComponentSpan

```rust
pub struct ComponentSpan {
    pub start: usize,
    pub width: usize,
    pub text: String,
    pub role: String,
    pub focused: bool,
}
```




### tuivory::forms::Form

```rust
pub struct Form {

    // Private fields omitted.
}
```



#### tuivory::forms::Form::new

```rust
pub fn new(mut fields: Vec<FormField>) -> Result<Self, Error>;
```



#### tuivory::forms::Form::value

```rust
pub fn value(&self, id: &str) -> Option<&str>;
```

Explicit raw-value access, including password inputs.

#### tuivory::forms::Form::select_text

```rust
pub fn select_text(&mut self, id: &str, anchor: usize, cursor: usize) -> bool;
```



#### tuivory::forms::Form::fields

```rust
pub fn fields(&self) -> &[FormField];
```



#### tuivory::forms::Form::at_tab_boundary

```rust
pub fn at_tab_boundary(&self, previous: bool) -> bool;
```



#### tuivory::forms::Form::focused

```rust
pub fn focused(&self) -> &str;
```



#### tuivory::forms::Form::focus

```rust
pub fn focus(&mut self, id: &str) -> bool;
```



#### tuivory::forms::Form::set_state

```rust
pub fn set_state(&mut self, id: &str, state: ControlState) -> bool;
```



#### tuivory::forms::Form::set_feedback

```rust
pub fn set_feedback(&mut self, id: &str, help: &str, message: &str) -> bool;
```



#### tuivory::forms::Form::missing

```rust
pub fn missing(&self) -> Vec<String>;
```



#### tuivory::forms::Form::handle

```rust
pub fn handle(&mut self, action: &str, text: &str) -> FormEvent;
```



#### tuivory::forms::Form::click

```rust
pub fn click(&mut self, id: &str, option: &str) -> FormEvent;
```



#### tuivory::forms::Form::layout

```rust
pub fn layout(&self, width: usize, height: usize) -> Vec<ComponentLine>;
```



### tuivory::forms::FormEvent

```rust
pub struct FormEvent {
    pub kind: String,
    pub id: String,
    pub missing: Vec<String>,
    pub text: String,
}
```




### tuivory::forms::FormField

```rust
pub struct FormField {
    pub id: String,
    pub kind: String,
    pub label: String,
    pub help: String,
    pub error: String,
    pub value: String,
    pub choice: String,
    pub action: String,
    pub options: Vec<FormOption>,
    pub state: ControlState,
    pub required: bool,
    pub checked: bool,
    pub open: bool,
    pub pending: String,
    pub cursor: usize,
}
```




### tuivory::forms::FormOption

```rust
pub struct FormOption {
    pub id: String,
    pub label: String,
    pub disabled: bool,
}
```




### tuivory::grid::Grid

```rust
pub struct Grid {
    pub row_id: String,
    pub column_id: String,
    pub selected_row: String,
    pub selected_column: String,
    pub sort_column: String,
    pub sort_direction: String,
    pub whole_row: bool,
    pub empty: String,
    pub labels: BTreeMap<String, String>,
    pub status: GridDataStatus,
    // Private fields omitted.
}
```



#### tuivory::grid::Grid::options

```rust
pub fn options(&self) -> &GridOptions;
```



#### tuivory::grid::Grid::set_options

```rust
pub fn set_options(&mut self, o: GridOptions) -> Result<(), Error>;
```



#### tuivory::grid::Grid::set_column_options

```rust
pub fn set_column_options(&mut self, id: &str, o: GridColumnOptions) -> Result<(), Error>;
```



#### tuivory::grid::Grid::column_options

```rust
pub fn column_options(&self, id: &str) -> GridColumnOptions;
```



#### tuivory::grid::Grid::set_cell_info

```rust
pub fn set_cell_info(
        &mut self,
        info: impl Fn(&GridRecord, &GridColumn) -> GridCellInfo + 'static,
    );
```



#### tuivory::grid::Grid::clear_cell_info

```rust
pub fn clear_cell_info(&mut self);
```



#### tuivory::grid::Grid::selection_mode

```rust
pub fn selection_mode(&self) -> &str;
```



#### tuivory::grid::Grid::set_selection_mode

```rust
pub fn set_selection_mode(&mut self, mode: &str) -> Result<(), Error>;
```



#### tuivory::grid::Grid::select_range

```rust
pub fn select_range(&mut self, r: GridRange) -> bool;
```



#### tuivory::grid::Grid::selected_range

```rust
pub fn selected_range(&self) -> &GridRange;
```



#### tuivory::grid::Grid::revision

```rust
pub fn revision(&self) -> u64;
```



#### tuivory::grid::Grid::apply_source

```rust
pub fn apply_source(&mut self, revision: u64, source: Box<dyn GridSource>) -> bool;
```



#### tuivory::grid::Grid::request_page

```rust
pub fn request_page(&self) -> GridEvent;
```



#### tuivory::grid::Grid::auto_fit_column

```rust
pub fn auto_fit_column(&mut self, id: &str, height: usize) -> bool;
```



#### tuivory::grid::Grid::pointer

```rust
pub fn pointer(
        &mut self,
        action: &str,
        x: isize,
        y: isize,
        width: usize,
        height: usize,
        extend: bool,
    ) -> GridEvent;
```

Host-translated local coordinates. Capture down/move/up while dragging.

#### tuivory::grid::Grid::pointer_captured

```rust
pub fn pointer_captured(&self) -> bool;
```



#### tuivory::grid::Grid::geometry

```rust
pub fn geometry(&self, width: usize, height: usize) -> GridGeometry;
```



#### tuivory::grid::Grid::layout

```rust
pub fn layout(&self, width: usize, height: usize) -> Vec<ComponentLine>;
```



#### tuivory::grid::Grid::status_items

```rust
pub fn status_items(&self) -> Vec<StatusItem>;
```

Can also be composed with the public status_line/LineWidget API.

#### tuivory::grid::Grid::new

```rust
pub fn new(mut columns: Vec<GridColumn>, source: Box<dyn GridSource>) -> Result<Self, Error>;
```



#### tuivory::grid::Grid::columns

```rust
pub fn columns(&self) -> &[GridColumn];
```



#### tuivory::grid::Grid::set_source

```rust
pub fn set_source(&mut self, source: Box<dyn GridSource>);
```



#### tuivory::grid::Grid::focus

```rust
pub fn focus(&mut self, row_id: &str, column_id: &str) -> bool;
```



#### tuivory::grid::Grid::resize_column

```rust
pub fn resize_column(&mut self, id: &str, width: usize) -> bool;
```



#### tuivory::grid::Grid::request_filter

```rust
pub fn request_filter(&self, query: &str) -> GridEvent;
```



#### tuivory::grid::Grid::handle

```rust
pub fn handle(&mut self, action: &str, height: usize) -> GridEvent;
```



#### tuivory::grid::Grid::click

```rust
pub fn click(
        &mut self,
        row_id: &str,
        kind: &str,
        x: usize,
        width: usize,
        height: usize,
    ) -> GridEvent;
```

Legacy row-ID and horizontal-coordinate mouse entry point.
Deprecated in unreleased source after 0.4.0; removal is not scheduled.
Use [`Grid::pointer`] for local mouse input, or [`Grid::focus`] and
[`Grid::handle`] for programmatic selection/sorting.
Deprecated: {'since': '0.5.0', 'note': 'Use Grid::pointer for mouse coordinates, or Grid::focus and Grid::handle for programmatic actions.'}

### tuivory::grid::GridCellInfo

```rust
pub struct GridCellInfo {
    pub display: String,
    pub has_display: bool,
    pub null: bool,
    pub numeric: bool,
    pub state: ControlState,
    pub metadata: String,
}
```




### tuivory::grid::GridColumn

```rust
pub struct GridColumn {
    pub id: String,
    pub label: String,
    pub width: usize,
    pub editable: bool,
}
```




### tuivory::grid::GridColumnOptions

```rust
pub struct GridColumnOptions {
    pub align: String,
    pub min_width: usize,
    pub max_width: usize,
    pub auto_fit: bool,
    pub expand: usize,
    pub overflow: String,
}
```




### tuivory::grid::GridDataStatus

```rust
pub struct GridDataStatus {
    pub total_rows: usize,
    pub metadata: String,
    pub filter: String,
    pub error: String,
    pub loading: bool,
    pub has_more: bool,
}
```




### tuivory::grid::GridEvent

```rust
pub struct GridEvent {
    pub kind: String,
    pub row_id: String,
    pub column_id: String,
    pub text: String,
    pub direction: String,
}
```




### tuivory::grid::GridGeometry

```rust
pub struct GridGeometry {
    pub top: usize,
    pub left: usize,
    pub gutter: usize,
    pub header_rows: usize,
    pub footer_rows: usize,
    pub body_rows: usize,
    pub stride: usize,
    pub columns: Vec<GridSpan>,
}
```




### tuivory::grid::GridOptions

```rust
pub struct GridOptions {
    pub row_numbers: bool,
    pub hide_markers: bool,
    pub vertical_lines: bool,
    pub horizontal_lines: bool,
    pub striped: bool,
    pub use_surface: bool,
    pub hide_header: bool,
    pub scroll_header: bool,
    pub status_bar: bool,
    pub ascii: bool,
    pub highlight_cell: bool,
    pub highlight_row: bool,
    pub preserve_edited: bool,
    pub hide_selection_marker: bool,
    pub show_cell_markers: bool,
    pub disable_keyboard: bool,
    pub disable_mouse: bool,
    pub disable_editing: bool,
    pub disable_copy: bool,
    pub disable_resize: bool,
    pub disable_header_sort: bool,
    pub padding: usize,
    pub row_spacing: usize,
    pub gutter_width: usize,
    pub max_copy_cells: usize,
    pub selection: String,
    pub status_fields: Option<Vec<String>>,
}
```

Options on the existing grid; defaults retain the simple v0.2 presentation.

#### tuivory::grid::GridOptions::with_density

```rust
pub fn with_density(mut self, density: &str) -> Result<Self, Error>;
```



### tuivory::grid::GridRange

```rust
pub struct GridRange {
    pub anchor_row: String,
    pub anchor_column: String,
    pub end_row: String,
    pub end_column: String,
}
```




### tuivory::grid::GridRecord

```rust
pub struct GridRecord {
    pub id: String,
    pub cells: BTreeMap<String, String>,
    pub state: ControlState,
}
```




### tuivory::grid::GridSource

```rust
pub trait GridSource {
    fn len(&self) -> usize;
    fn is_empty(&self) -> bool {
        self.len() == 0
    }
    fn row(&self, index: usize) -> GridRecord;
    fn index_of(&self, id: &str) -> Option<usize>;
}
```




### tuivory::grid::GridSpan

```rust
pub struct GridSpan {
    pub id: String,
    pub start: usize,
    pub width: usize,
}
```




### tuivory::grid::MemoryRows

```rust
pub struct MemoryRows {

    // Private fields omitted.
}
```



#### tuivory::grid::MemoryRows::new

```rust
pub fn new(rows: Vec<GridRecord>) -> Result<Self, Error>;
```



### tuivory::grid::grid_preset

```rust
pub fn grid_preset(name: &str) -> Result<GridOptions, Error>;
```




### tuivory::input::InputEvent

```rust
pub struct InputEvent {
    pub kind: String,
    pub key: String,
    pub text: String,
    pub modifiers: Vec<String>,
    pub phase: String,
    pub x: isize,
    pub y: isize,
    pub button: String,
    pub width: usize,
    pub height: usize,
}
```

Screen-cell coordinates, original UTF-8 text and ordered modifier names.
Hosts consume global keys before forwarding editing actions to a model.

#### tuivory::input::InputEvent::paste

```rust
pub fn paste(text: &str) -> Self;
```



#### tuivory::input::InputEvent::resize

```rust
pub fn resize(width: usize, height: usize) -> Self;
```



#### tuivory::input::InputEvent::editing_action

```rust
pub fn editing_action(&self) -> (String, String);
```

Returns requests only. Enter is newline; form hosts map it to activation.

#### tuivory::input::InputEvent::from_key

```rust
pub fn from_key(event: crate::ui::terminal::event::KeyEvent) -> Self;
```



#### tuivory::input::InputEvent::from_terminal

```rust
pub fn from_terminal(event: crate::ui::terminal::event::Event) -> Self;
```



### tuivory::interaction::ControlState

```rust
pub struct ControlState {
    pub disabled: bool,
    pub read_only: bool,
    pub busy: bool,
    pub selected: bool,
    pub edited: bool,
    pub invalid: bool,
}
```



#### tuivory::interaction::ControlState::visual

```rust
pub fn visual(self) -> ControlVisual;
```

Color precedence never removes non-color state markers.

### tuivory::interaction::ControlVisual

```rust
pub struct ControlVisual {
    pub role: &'static str,
    pub markers: String,
    pub focusable: bool,
    pub activatable: bool,
    pub editable: bool,
}
```




### tuivory::interaction::FocusStack

```rust
pub struct FocusStack {

    // Private fields omitted.
}
```

Own this value in the host. It does not own framework widgets or event loops.

#### tuivory::interaction::FocusStack::new

```rust
pub fn new(root_id: impl Into<String>, targets: Vec<FocusTarget>) -> Result<Self, Error>;
```



#### tuivory::interaction::FocusStack::scope_id

```rust
pub fn scope_id(&self) -> &str;
```



#### tuivory::interaction::FocusStack::focused

```rust
pub fn focused(&self) -> &str;
```



#### tuivory::interaction::FocusStack::depth

```rust
pub fn depth(&self) -> usize;
```



#### tuivory::interaction::FocusStack::targets

```rust
pub fn targets(&self) -> &[FocusTarget];
```



#### tuivory::interaction::FocusStack::focus

```rust
pub fn focus(&mut self, id: &str) -> bool;
```



#### tuivory::interaction::FocusStack::move_focus

```rust
pub fn move_focus(&mut self, backwards: bool) -> &str;
```



#### tuivory::interaction::FocusStack::update

```rust
pub fn update(&mut self, scope_id: &str, targets: Vec<FocusTarget>) -> Result<(), Error>;
```

Preserve focus by ID; invalid updates leave all scopes unchanged.

#### tuivory::interaction::FocusStack::open

```rust
pub fn open(
        &mut self,
        id: impl Into<String>,
        targets: Vec<FocusTarget>,
        initial: &str,
        dismissible: bool,
    ) -> Result<(), Error>;
```

Empty scopes still consume input. At most 64 popup layers are accepted.

#### tuivory::interaction::FocusStack::request_close

```rust
pub fn request_close(&self) -> Option<PopupCloseRequest>;
```

Escape only requests dismissal. Outside pointer input never auto-closes.

#### tuivory::interaction::FocusStack::close

```rust
pub fn close(&mut self, id: &str) -> Result<(), Error>;
```

Reject stale callbacks; the host may explicitly close locked popups.

#### tuivory::interaction::FocusStack::route

```rust
pub fn route(&self, target_scope: &str) -> InputRoute<'_>;
```

Empty target means keyboard input. Pointer input supplies its hit scope.

### tuivory::interaction::FocusTarget

```rust
pub struct FocusTarget {
    pub id: String,
    pub state: ControlState,
    pub hidden: bool,
}
```




### tuivory::interaction::InputRoute

```rust
pub struct InputRoute<'a> {
    pub scope_id: &'a str,
    pub blocked: bool,
}
```




### tuivory::interaction::PopupCloseRequest

```rust
pub struct PopupCloseRequest {
    pub id: String,
    pub reason: &'static str,
}
```




### tuivory::layout::Badge

```rust
pub struct Badge {
    pub id: String,
    pub label: String,
    pub count: Option<u64>,
    pub limit: u64,
    pub state: ControlState,
}
```



#### tuivory::layout::Badge::line

```rust
pub fn line(&self, width: usize) -> ComponentLine;
```



### tuivory::layout::CellRect

```rust
pub struct CellRect {
    pub x: usize,
    pub y: usize,
    pub width: usize,
    pub height: usize,
}
```



#### tuivory::layout::CellRect::inset

```rust
pub fn inset(self, padding: usize) -> Self;
```



### tuivory::layout::Chip

```rust
pub struct Chip {
    pub id: String,
    pub label: String,
    pub state: ControlState,
    pub removable: bool,
}
```



#### tuivory::layout::Chip::line

```rust
pub fn line(&self, width: usize) -> ComponentLine;
```



#### tuivory::layout::Chip::request_remove

```rust
pub fn request_remove(&self) -> ComponentEvent;
```



### tuivory::layout::ComponentEvent

```rust
pub struct ComponentEvent {
    pub kind: String,
    pub id: String,
}
```




### tuivory::layout::Density

```rust
pub enum Density {
    Auto,
    Compact,
    Comfortable,
}
```




### tuivory::layout::DrawerPlacement

```rust
pub struct DrawerPlacement {
    pub rect: CellRect,
    pub overlay: bool,
}
```




### tuivory::layout::Help

```rust
pub struct Help {

    // Private fields omitted.
}
```



#### tuivory::layout::Help::new

```rust
pub fn new(mut items: Vec<Shortcut>) -> Result<Self, Error>;
```



#### tuivory::layout::Help::layout

```rust
pub fn layout(&self, width: usize, height: usize) -> Vec<ComponentLine>;
```



### tuivory::layout::NamedRect

```rust
pub struct NamedRect {
    pub id: String,
    pub rect: CellRect,
}
```




### tuivory::layout::Shortcut

```rust
pub struct Shortcut {
    pub key: String,
    pub text: String,
    pub priority: i32,
    pub disabled: bool,
}
```




### tuivory::layout::SpacingTokens

```rust
pub struct SpacingTokens {
    pub gap: usize,
    pub padding: usize,
    pub control_gap: usize,
    pub compact_below: usize,
}
```



#### tuivory::layout::SpacingTokens::for_width

```rust
pub fn for_width(density: Density, columns: usize) -> Self;
```



### tuivory::layout::StackItem

```rust
pub struct StackItem {
    pub id: String,
    pub min: usize,
    pub preferred: usize,
    pub weight: usize,
}
```




### tuivory::layout::StackResult

```rust
pub struct StackResult {
    pub slots: Vec<StackSlot>,
    pub hidden: Vec<String>,
    pub gap: usize,
}
```




### tuivory::layout::StackSlot

```rust
pub struct StackSlot {
    pub id: String,
    pub start: usize,
    pub size: usize,
}
```




### tuivory::layout::drawer_layout

```rust
pub fn drawer_layout(parent: CellRect, preferred: usize, min_content: usize) -> DrawerPlacement;
```




### tuivory::layout::stack_layout

```rust
pub fn stack_layout(
    items: &[StackItem],
    total: usize,
    mut gap: usize,
) -> Result<StackResult, Error>;
```




### tuivory::layout::stack_rects

```rust
pub fn stack_rects(
    parent: CellRect,
    items: &[StackItem],
    tokens: SpacingTokens,
    vertical: bool,
) -> Result<(Vec<NamedRect>, Vec<String>), Error>;
```




### tuivory::menu::Menu

```rust
pub struct Menu {
    pub back_label: String,
    pub empty_label: String,
    // Private fields omitted.
}
```



#### tuivory::menu::Menu::new

```rust
pub fn new(items: Vec<MenuItem>) -> Result<Self, Error>;
```



#### tuivory::menu::Menu::items

```rust
pub fn items(&self) -> &[MenuItem];
```



#### tuivory::menu::Menu::set_items

```rust
pub fn set_items(&mut self, items: Vec<MenuItem>) -> Result<Option<MenuEvent>, Error>;
```



#### tuivory::menu::Menu::opened

```rust
pub fn opened(&self) -> bool;
```



#### tuivory::menu::Menu::path

```rust
pub fn path(&self) -> &[String];
```



#### tuivory::menu::Menu::focused_id

```rust
pub fn focused_id(&self) -> &str;
```



#### tuivory::menu::Menu::return_id

```rust
pub fn return_id(&self) -> &str;
```



#### tuivory::menu::Menu::bar_focused_id

```rust
pub fn bar_focused_id(&self) -> &str;
```



#### tuivory::menu::Menu::title

```rust
pub fn title(&self) -> String;
```



#### tuivory::menu::Menu::open

```rust
pub fn open(&mut self, id: &str, return_id: &str) -> Option<MenuEvent>;
```



#### tuivory::menu::Menu::close

```rust
pub fn close(&mut self) -> Option<MenuEvent>;
```



#### tuivory::menu::Menu::back

```rust
pub fn back(&mut self) -> Option<MenuEvent>;
```



#### tuivory::menu::Menu::focus

```rust
pub fn focus(&mut self, id: &str) -> bool;
```



#### tuivory::menu::Menu::click

```rust
pub fn click(&mut self, id: &str) -> Option<MenuEvent>;
```



#### tuivory::menu::Menu::handle

```rust
pub fn handle(&mut self, action: &str, value: &str, height: usize) -> Option<MenuEvent>;
```



#### tuivory::menu::Menu::handle_bar

```rust
pub fn handle_bar(&mut self, action: &str, value: &str) -> Option<MenuEvent>;
```



#### tuivory::menu::Menu::content_size

```rust
pub fn content_size(&self) -> (usize, usize);
```



#### tuivory::menu::Menu::layout

```rust
pub fn layout(&mut self, width: usize, height: usize, ascii: bool) -> Vec<ComponentLine>;
```



#### tuivory::menu::Menu::bar_layout

```rust
pub fn bar_layout(&mut self, width: usize) -> MenuBarLayout;
```



#### tuivory::menu::Menu::bar_click

```rust
pub fn bar_click(&mut self, x: usize, width: usize) -> Option<MenuEvent>;
```



### tuivory::menu::MenuBarCell

```rust
pub struct MenuBarCell {
    pub id: String,
    pub text: String,
    pub role: String,
    pub start: usize,
    pub width: usize,
    pub focused: bool,
}
```




### tuivory::menu::MenuBarLayout

```rust
pub struct MenuBarLayout {
    pub cells: Vec<MenuBarCell>,
    pub previous: bool,
    pub next: bool,
}
```




### tuivory::menu::MenuEvent

```rust
pub struct MenuEvent {
    pub kind: String,
    pub id: String,
    pub return_id: String,
}
```




### tuivory::menu::MenuItem

```rust
pub struct MenuItem {
    pub id: String,
    pub parent: String,
    pub label: String,
    pub secondary: String,
    pub shortcut: String,
    pub mnemonic: String,
    pub icon: String,
    pub ascii_icon: String,
    pub disabled: bool,
    pub separator: bool,
}
```




### tuivory::menu::menu_placement

```rust
pub fn menu_placement(
    anchor: CellRect,
    viewport: CellRect,
    width: usize,
    height: usize,
) -> CellRect;
```

Pure popup geometry; the host owns its anchor, visibility and panel padding.


### tuivory::popup::PopupLayout

```rust
pub struct PopupLayout {
    pub bounds: CellRect,
    pub card: CellRect,
    pub shadow: CellRect,
}
```



#### tuivory::popup::PopupLayout::shadow_regions

```rust
pub fn shadow_regions(self) -> [CellRect; 2];
```

Disjoint right/bottom shadow strips, never the card itself.

### tuivory::popup::ShadowMode

```rust
pub enum ShadowMode {
    #[default]
    Off,
    Auto,
    Solid,
    Dim,
}
```



#### tuivory::popup::ShadowMode::as_str

```rust
pub fn as_str(self) -> &'static str;
```



### tuivory::popup::ShadowOptions

```rust
pub struct ShadowOptions {
    pub mode: ShadowMode,
    pub offset_x: usize,
    pub offset_y: usize,
}
```

Cell offsets; enabled modes with both offsets zero use right-two/down-one.

#### tuivory::popup::ShadowOptions::layout

```rust
pub fn layout(self, bounds: CellRect) -> PopupLayout;
```

Reserve the shadow inside an allocation; preserve a nonempty card if possible.

### tuivory::popup::popup_placement

```rust
pub fn popup_placement(
    anchor: CellRect,
    viewport: CellRect,
    width: usize,
    height: usize,
    shadow: ShadowOptions,
) -> PopupLayout;
```

Place a requested card plus optional shadow, clamping/flipping the full footprint.


### tuivory::profile_for_colors

```rust
pub fn profile_for_colors(count: i32, limited: bool) -> ColorProfile;
```

Resolve an explicit host-reported color count using the Go API's rules.
Zero/negative counts select Truecolor, or Ansi16 when limited is true.


### tuivory::ratatui::BadgeWidget

```rust
pub struct BadgeWidget<'a> {
    pub model: &'a crate::layout::Badge,
    pub styles: &'a Styles,
}
```




### tuivory::ratatui::ChipWidget

```rust
pub struct ChipWidget<'a> {
    pub model: &'a crate::layout::Chip,
    pub styles: &'a Styles,
    pub focused: bool,
}
```




### tuivory::ratatui::ContainerWidget

```rust
pub struct ContainerWidget<'a, F> {
    pub items: &'a [crate::containers::LayoutItem],
    pub options: &'a crate::containers::ContainerOptions,
    pub styles: &'a Styles,
    pub scroll_x: usize,
    pub scroll_y: usize,
    pub render_child: F,
}
```

Executes a language-neutral layout and clips each child to its viewport.
The factory chooses widgets by stable ID; it does not compute placement.


### tuivory::ratatui::ControlWidget

```rust
pub struct ControlWidget<'a> {
    pub model: &'a crate::controls::Control,
    pub styles: &'a Styles,
    pub focused: bool,
}
```




### tuivory::ratatui::DataStateWidget

```rust
pub struct DataStateWidget<'a> {
    pub model: &'a crate::feedback::DataState,
    pub styles: &'a Styles,
}
```




### tuivory::ratatui::FormWidget

```rust
pub struct FormWidget<'a> {
    pub form: &'a Form,
    pub styles: &'a Styles,
    pub focused: bool,
}
```




### tuivory::ratatui::GridWidget

```rust
pub struct GridWidget<'a> {
    pub model: &'a crate::grid::Grid,
    pub styles: &'a Styles,
    pub focused: bool,
}
```




### tuivory::ratatui::HelpWidget

```rust
pub struct HelpWidget<'a> {
    pub model: &'a crate::layout::Help,
    pub styles: &'a Styles,
}
```




### tuivory::ratatui::LineWidget

```rust
pub struct LineWidget<'a> {

    // Private fields omitted.
}
```



#### tuivory::ratatui::LineWidget::new

```rust
pub fn new(runs: Vec<LineRun>, styles: &'a Styles) -> Result<Self, crate::Error>;
```



### tuivory::ratatui::ListWidget

```rust
pub struct ListWidget<'a> {
    pub model: &'a crate::collections::ListModel,
    pub styles: &'a Styles,
    pub focused: bool,
    pub ascii: bool,
}
```




### tuivory::ratatui::MenuBarWidget

```rust
pub struct MenuBarWidget<'a> {
    pub model: &'a mut Menu,
    pub styles: &'a Styles,
    pub focused: bool,
}
```



#### tuivory::ratatui::MenuBarWidget::new

```rust
pub fn new(model: &'a mut Menu, styles: &'a Styles) -> Self;
```

Create a menu bar; the menu model determines open/selection state.

### tuivory::ratatui::MenuPopupWidget

```rust
pub struct MenuPopupWidget<'a> {
    pub model: &'a mut Menu,
    pub styles: &'a Styles,
    pub title: &'a str,
    pub ascii: bool,
    pub focused: bool,
    pub padding: u16,
}
```

A reusable menu popup surface/border, clipped to the host-assigned area.
Pre-clearing through RowsWidget repairs background glyphs at both edges.

#### tuivory::ratatui::MenuPopupWidget::new

```rust
pub fn new(model: &'a mut Menu, styles: &'a Styles, title: &'a str) -> Self;
```

Create a single-border popup with one cell of padding and Unicode drawing.

#### tuivory::ratatui::MenuPopupWidget::shadow

```rust
pub fn shadow(self, options: crate::popup::ShadowOptions) -> super::ShadowWidget<'a, Self>;
```

Wrap this popup with an optional shadow; the allocation includes the shadow.

#### tuivory::ratatui::MenuPopupWidget::ascii

```rust
pub fn ascii(mut self, ascii: bool) -> Self;
```

Select ASCII presentation without changing menu state.

#### tuivory::ratatui::MenuPopupWidget::padding

```rust
pub fn padding(mut self, padding: u16) -> Self;
```

Set padding inside the host-assigned popup rectangle.

### tuivory::ratatui::MenuWidget

```rust
pub struct MenuWidget<'a> {
    pub model: &'a mut Menu,
    pub styles: &'a Styles,
    pub ascii: bool,
    pub focused: bool,
}
```

Render a single menu level inside a host-owned panel; terminal/focus is host-owned.

#### tuivory::ratatui::MenuWidget::new

```rust
pub fn new(model: &'a mut Menu, styles: &'a Styles) -> Self;
```

Create a menu renderer without an ineffective focus flag.

#### tuivory::ratatui::MenuWidget::ascii

```rust
pub fn ascii(mut self, ascii: bool) -> Self;
```

Select ASCII presentation without changing menu state.

### tuivory::ratatui::NoticeWidget

```rust
pub struct NoticeWidget<'a> {
    pub model: &'a crate::feedback::NoticeQueue,
    pub styles: &'a Styles,
    pub focused: bool,
    pub now: u64,
}
```




### tuivory::ratatui::ProgressWidget

```rust
pub struct ProgressWidget<'a> {
    pub model: &'a crate::feedback::Progress,
    pub styles: &'a Styles,
    pub frame: u64,
}
```




### tuivory::ratatui::RawRowsWidget

```rust
pub struct RawRowsWidget<'a>(RowsWidget<'a>);
```

Explicit background preservation for grids or custom row composition.


### tuivory::ratatui::RowsWidget

```rust
pub struct RowsWidget<'a> {
    pub rows: &'a [ComponentLine],
    pub styles: &'a Styles,
    pub focused: bool,
}
```

Literal semantic rows; all semantic roles must exist in the supplied palette.

#### tuivory::ratatui::RowsWidget::preserve_backgrounds

```rust
pub fn preserve_backgrounds(self) -> RawRowsWidget<'a>;
```



### tuivory::ratatui::SearchPickerWidget

```rust
pub struct SearchPickerWidget<'a> {
    pub model: &'a crate::collections::SearchPicker,
    pub styles: &'a Styles,
    pub focused: bool,
    pub ascii: bool,
}
```




### tuivory::ratatui::ShadowWidget

```rust
pub struct ShadowWidget<'a, W> {

    // Private fields omitted.
}
```

Any widget with a visual-only shadow inside its assigned allocation.
The wrapped widget gets only the card rectangle. Hosts own hit testing/redraws.

#### tuivory::ratatui::ShadowWidget::new

```rust
pub fn new(widget: W, styles: &'a Styles, options: ShadowOptions) -> Self;
```



#### tuivory::ratatui::ShadowWidget::ascii

```rust
pub fn ascii(mut self, ascii: bool) -> Self;
```



### tuivory::ratatui::SplitRects

```rust
pub struct SplitRects {
    pub first: Rect,
    pub divider: Rect,
    pub second: Rect,
    pub compact: bool,
}
```




### tuivory::ratatui::StackRects

```rust
pub type StackRects = (Vec<(String, Rect)>, Vec<String>);
```




### tuivory::ratatui::Styles

```rust
pub struct Styles {

    // Private fields omitted.
}
```

An owned style palette for existing Ratatui widgets. The host retains
list/table/input state and chooses when to replace this value on theme change.

#### tuivory::ratatui::Styles::text_on_surface

```rust
pub fn text_on_surface(&self, role: &str, surface: &str) -> Result<Style, Error>;
```

Bind text to an actual surface without mutating the palette. Use the
surface foreground below the role target (disabled 2:1, others 4.5:1), if better.
Keep `role` for explicit field/selection/edit/custom backgrounds.

#### tuivory::ratatui::Styles::control_on_surface

```rust
pub fn control_on_surface(
        &self,
        state: ControlState,
        focused: bool,
        surface: &str,
    ) -> Result<Style, Error>;
```

Bind ordinary control text to a host-selected surface; preserve explicit
selected/edited backgrounds. The original `control` method stays raw.

#### tuivory::ratatui::Styles::control

```rust
pub fn control(
        &self,
        state: crate::interaction::ControlState,
        focused: bool,
    ) -> Result<Style, Error>;
```

Resolve common control states; the host draws visual().markers separately.

#### tuivory::ratatui::Styles::panel

```rust
pub fn panel<'a>(
        &self,
        title: &'a str,
        focused: bool,
        padding: u16,
        ascii: bool,
    ) -> Result<Block<'a>, Error>;
```

A padded panel using the same focus and ordinary-font fallback rules.

#### tuivory::ratatui::Styles::new

```rust
pub fn new(theme: Theme, profile: ColorProfile) -> Result<Self, Error>;
```

Load the shared candidate palette, distinct from Go's extracted styles.

#### tuivory::ratatui::Styles::from_palette

```rust
pub fn from_palette(palette: Palette) -> Self;
```



#### tuivory::ratatui::Styles::role

```rust
pub fn role(&self, name: &str) -> Result<Style, Error>;
```

Resolve a semantic role without replacing ANSI indices with RGB values.

#### tuivory::ratatui::Styles::block

```rust
pub fn block<'a>(&self, title: &'a str, focused: bool) -> Result<Block<'a>, Error>;
```

Create a panel border without modifying the host's focus callbacks.
Double borders preserve the focus cue even without color.

### tuivory::ratatui::SurfaceWidget

```rust
pub struct SurfaceWidget<'a, W> {

    // Private fields omitted.
}
```

Opaque borderless surface. The host supplies placement and routes input.

#### tuivory::ratatui::SurfaceWidget::new

```rust
pub fn new(child: W, styles: &'a Styles) -> Self;
```



#### tuivory::ratatui::SurfaceWidget::padding

```rust
pub fn padding(mut self, cells: u16) -> Self;
```



### tuivory::ratatui::TabsWidget

```rust
pub struct TabsWidget<'a> {
    pub focused: bool,
    // Private fields omitted.
}
```



#### tuivory::ratatui::TabsWidget::new

```rust
pub fn new(tabs: &'a Tabs, styles: &'a Styles) -> Result<Self, crate::Error>;
```



### tuivory::ratatui::TextWidget

```rust
pub struct TextWidget<'a> {
    pub model: &'a mut TextDocument,
    pub styles: &'a Styles,
    pub focused: bool,
}
```




### tuivory::ratatui::TreeWidget

```rust
pub struct TreeWidget<'a> {
    pub focused: bool,
    pub ascii: bool,
    // Private fields omitted.
}
```



#### tuivory::ratatui::TreeWidget::new

```rust
pub fn new(tree: &'a Tree, styles: &'a Styles) -> Result<Self, crate::Error>;
```



### tuivory::ratatui::split_rects

```rust
pub fn split_rects(
    area: Rect,
    spec: SplitSpec,
    state: &SplitState,
    rows: bool,
    active_second: bool,
) -> SplitRects;
```




### tuivory::ratatui::stack_rects

```rust
pub fn stack_rects(
    area: Rect,
    items: &[crate::layout::StackItem],
    tokens: crate::layout::SpacingTokens,
    vertical: bool,
) -> Result<StackRects, crate::Error>;
```

Convert shared terminal-cell geometry into Ratatui rectangles.


### tuivory::text::SyntaxSpan

```rust
pub struct SyntaxSpan {
    pub start: usize,
    pub end: usize,
    pub role: String,
}
```




### tuivory::text::TextBuffer

```rust
pub struct TextBuffer {
    pub cursor: usize,
    pub anchor: usize,
    pub state: ControlState,
    pub secret: bool,
    pub single_line: bool,
    // Private fields omitted.
}
```



#### tuivory::text::TextBuffer::new

```rust
pub fn new(text: &str) -> Self;
```



#### tuivory::text::TextBuffer::text

```rust
pub fn text(&self) -> &str;
```



#### tuivory::text::TextBuffer::display

```rust
pub fn display(&self) -> String;
```



#### tuivory::text::TextBuffer::set_text

```rust
pub fn set_text(&mut self, text: &str);
```



#### tuivory::text::TextBuffer::select

```rust
pub fn select(&mut self, anchor: usize, cursor: usize);
```



#### tuivory::text::TextBuffer::selection

```rust
pub fn selection(&self) -> (usize, usize);
```



#### tuivory::text::TextBuffer::cursor_byte

```rust
pub fn cursor_byte(&self) -> usize;
```



#### tuivory::text::TextBuffer::handle

```rust
pub fn handle(&mut self, action: &str, text: &str) -> TextEvent;
```



### tuivory::text::TextDocument

```rust
pub struct TextDocument {
    pub buffer: TextBuffer,
    pub wrap: bool,
    pub line_numbers: bool,
    pub ascii: bool,
    pub scroll_x: usize,
    pub scroll_y: usize,
    pub syntax: Vec<SyntaxSpan>,
    // Private fields omitted.
}
```



#### tuivory::text::TextDocument::set_text

```rust
pub fn set_text(&mut self, text: &str);
```



#### tuivory::text::TextDocument::reveal_cursor

```rust
pub fn reveal_cursor(&mut self);
```



#### tuivory::text::TextDocument::set_syntax

```rust
pub fn set_syntax(&mut self, spans: Vec<SyntaxSpan>) -> Result<(), crate::Error>;
```



#### tuivory::text::TextDocument::editor

```rust
pub fn editor(text: &str) -> Self;
```



#### tuivory::text::TextDocument::viewer

```rust
pub fn viewer(text: &str) -> Self;
```



#### tuivory::text::TextDocument::handle

```rust
pub fn handle(&mut self, action: &str, text: &str) -> TextEvent;
```



#### tuivory::text::TextDocument::layout

```rust
pub fn layout(&mut self, width: usize, height: usize) -> Vec<ComponentLine>;
```



#### tuivory::text::TextDocument::point

```rust
pub fn point(&mut self, x: isize, y: isize, width: usize, height: usize, extend: bool);
```



#### tuivory::text::TextDocument::set_markup

```rust
pub fn set_markup(&mut self, markup: &str) -> Result<(), Error>;
```



#### tuivory::text::TextDocument::set_byte_syntax

```rust
pub fn set_byte_syntax(&mut self, spans: &[ByteSyntaxSpan]) -> Result<(), Error>;
```

Convert byte ranges atomically; host lexing/business semantics remain outside the SDK.

### tuivory::text::TextEvent

```rust
pub struct TextEvent {
    pub kind: String,
    pub text: String,
}
```




### tuivory::text_markup::parse_markup

```rust
pub fn parse_markup(markup: &str) -> Result<(String, Vec<SyntaxSpan>), Error>;
```

Explicit `[role]text[/]` styling; `[[` escapes `[`. Copies return plain logical
text. Literal text APIs never parse tags. Invalid markup leaves data intact.


### tuivory::text_offsets::ByteSyntaxSpan

```rust
pub struct ByteSyntaxSpan {
    pub start: usize,
    pub end: usize,
    pub role: String,
}
```

Half-open host lexer range in original UTF-8 bytes.


### tuivory::text_offsets::grapheme_index

```rust
pub fn grapheme_index(text: &str, byte_offset: usize) -> Result<usize, Error>;
```




### tuivory::tree::Tree

```rust
pub struct Tree {

    // Private fields omitted.
}
```



#### tuivory::tree::Tree::new

```rust
pub fn new(nodes: Vec<TreeNode>) -> Result<Self, String>;
```

IDs must be nonempty/unique; a parent must precede its children.
Nesting deeper than 128 levels is rejected rather than overflowing.

#### tuivory::tree::Tree::visible

```rust
pub fn visible(&self, state: &TreeState) -> Vec<TreeRow>;
```



#### tuivory::tree::Tree::reconcile

```rust
pub fn reconcile(&self, state: &mut TreeState, height: usize) -> Vec<TreeRow>;
```

Reconcile stable state after data replacement or resize. Hidden selected
children move to their nearest visible ancestor; removed IDs use row one.

#### tuivory::tree::Tree::handle

```rust
pub fn handle(
        &self,
        state: &mut TreeState,
        action: TreeAction,
        height: usize,
    ) -> Option<TreeEvent>;
```



#### tuivory::tree::Tree::click

```rust
pub fn click(
        &self,
        state: &mut TreeState,
        column: usize,
        row: usize,
        height: usize,
    ) -> Option<TreeEvent>;
```

Coordinates are relative to the inner tree viewport. Clicking the
disclosure toggles; other row clicks select without activation.

### tuivory::tree::TreeAction

```rust
pub enum TreeAction {
    Up,
    Down,
    Left,
    Right,
    Toggle,
    Activate,
    Home,
    End,
    PageUp,
    PageDown,
    PanLeft,
    PanRight,
}
```




### tuivory::tree::TreeEvent

```rust
pub enum TreeEvent {
    Select(String),
    Expand(String),
    Collapse(String),
    Activate(String),
}
```




### tuivory::tree::TreeNode

```rust
pub struct TreeNode {
    pub id: String,
    pub parent: String,
    pub name: String,
    pub secondary: String,
    pub icon: String,
    pub ascii_icon: String,
    pub count: Option<u64>,
    pub branch: bool,
}
```




### tuivory::tree::TreeRow

```rust
pub struct TreeRow {
    pub node: TreeNode,
    pub depth: usize,
}
```




### tuivory::tree::TreeState

```rust
pub struct TreeState {
    pub selected: String,
    pub expanded: BTreeSet<String>,
    pub scroll: usize,
    pub horizontal: usize,
}
```




### tuivory::ui::Session

```rust
pub struct Session {

    // Private fields omitted.
}
```

Opt-in stdout alternate-screen/raw-mode guard. Drop restores the terminal;
`finish` additionally reports cleanup errors. No process/global key policy.

#### tuivory::ui::Session::enter

```rust
pub fn enter(options: SessionOptions) -> std::io::Result<Self>;
```



#### tuivory::ui::Session::finish

```rust
pub fn finish(mut self) -> std::io::Result<()>;
```



### tuivory::ui::SessionOptions

```rust
pub struct SessionOptions {
    pub mouse: bool,
    pub bracketed_paste: bool,
}
```

Explicit terminal-session configuration; global keys remain host-owned.

