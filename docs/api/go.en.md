# Go API — source (0.6.0)

[한국어 (default)](go.md) · **English**

[API guide](README.en.md) · [Component guides](../components.en.md)

Generated public declarations and original source comments. Code, symbols and original comments are identical across language editions. See the API guide for component defaults, errors and event semantics. Inherited/trait APIs from external frameworks are documented by those frameworks.

## Functions and constants

```go
package tuivory // import "github.com/leechis7/tuivory/go"

Package tuivory provides reusable TUI components and styles through one import.
Component models and renderers manage internal interaction and presentation.
Hosts compose screens and supply scope order, global keys, data and actions.
New creates a Styler for existing widgets; shared components also accept the
candidate palette. Hosts retain terminal lifecycle and business I/O.

CONSTANTS

const (
	Canvas          = style.Canvas
	Panel           = style.Panel
	Field           = style.Field
	Footer          = style.Footer
	Editor          = style.Editor
	Body            = style.Body
	Hint            = style.Hint
	Accent          = style.Accent
	Warning         = style.Warning
	SyntaxKeyword   = style.SyntaxKeyword
	SyntaxFunction  = style.SyntaxFunction
	SyntaxType      = style.SyntaxType
	SyntaxString    = style.SyntaxString
	SyntaxNumber    = style.SyntaxNumber
	SyntaxComment   = style.SyntaxComment
	SyntaxParameter = style.SyntaxParameter
	TokenFormat     = tokens.Format
)

FUNCTIONS

func BorderColor(theme, profile string, styles Styles, focused bool, background tcell.Color) tcell.Color
    BorderColor selects a border color for the actual background and focus
    state.

func CandidateTokensJSON() string
    CandidateTokensJSON returns the shared draft candidate data.

func CellText(text string, width int) string
    CellText clips literal text at grapheme boundaries. A trailing ~ marks loss.

func ControlStyle(palette Palette, state ControlState, focused bool) (tcell.Style, error)
    ControlStyle resolves shared roles without replacing the host's data or
    focus. Markers are low-level state metadata; built-in views omit disabled
    prefixes.

func ControlStyleOnSurface(palette Palette, state ControlState, focused bool, surface string) (tcell.Style, error)
    ControlStyleOnSurface binds ordinary control text to a host-selected
    surface. Selection and edited backgrounds remain explicit; ControlStyle
    stays raw.

func DimRegion(screen tcell.Screen, rect CellRect)
    DimRegion draws a shadow over a clipped rectangle while preserving complete
    glyphs and clearing wide glyphs crossing either horizontal boundary. Outside
    styles are preserved; the caller draws the card afterwards and owns redraws.

func GridKey(e *tcell.EventKey) string
func MenuKey(e *tcell.EventKey) (string, string)
    MenuKey maps component-local keys only. Hosts assign F10, Alt and global
    keys.

func NavigationKey(e *tcell.EventKey) string
func ProfileForColors(count int, limited bool) string
    ProfileForColors translates host-reported color capability without terminal
    I/O.

func TextKey(e *tcell.EventKey) (string, string)
func TextOnSurface(palette Palette, role, surface string) (tcell.Style, error)
    TextOnSurface binds a text role to the actual surface without changing
    tokens. Use a better surface foreground below the role target (disabled 2:1,
    others 4.5:1). Use raw palette styles for explicit field, selection, edit or
    custom backgrounds.

func WideSafeScreen(screen tcell.Screen) tcell.Screen
    WideSafeScreen returns a tcell Screen that repairs overlapping wide glyphs
    before each positioned write. Pass it to the entire popup/card Draw call.
    SetContent, SetCell, Put, PutStr and PutStrStyled use the same repair. Init,
    Show, Sync, input and terminal ownership are forwarded to the host screen.
    An intersected glyph is replaced by spaces, including its cell just outside
    the drawn area, retaining its old style there. Redraw the background on
    close. Draw on the host UI goroutine; cell repairs are not a concurrent
    transaction.


TYPES
```

## Badge

```go
type Badge struct {
	ID, Label string
	Count     *uint64
	Limit     uint64
	State     ControlState
}

func (b Badge) Line(width int) ComponentLine
```

## BreadcrumbView

```go
type BreadcrumbView struct {
	*tview.Box
	Items []PathItem

	OnNavigate func(string)
	// Has unexported fields.
}

func NewBreadcrumbView(items []PathItem, palette Palette) (*BreadcrumbView, error)

func (v *BreadcrumbView) Draw(screen tcell.Screen)

func (v *BreadcrumbView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)

func (v *BreadcrumbView) SetPalette(palette Palette) error
```

## CellRect

```go
type CellRect struct{ X, Y, Width, Height int }

func MenuPlacement(anchor, viewport CellRect, width, height int) CellRect
    MenuPlacement clamps only the popup rectangle. Hosts choose anchors, panel
    padding and when/where the popup is shown; no backdrop or screen layout is
    owned.

func (r CellRect) Inset(padding int) CellRect
```

## CellState

```go
type CellState = style.CellState
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package style // import "github.com/leechis7/tuivory/go/internal/style"

type CellState struct {
	Row                               int
	CurrentRow, Null, Edited, InRange bool
}
    CellState describes display state without any database value or app object.
```

## Chip

```go
type Chip struct {
	ID, Label string
	State     ControlState
	Removable bool
}

func (c Chip) Line(width int) ComponentLine

func (c Chip) RequestRemove() ComponentEvent
```

## Choice

```go
type Choice = widgets.Choice
    Aliases keep state and method signatures usable without subpackage imports.

func NewChoice(label string, options []string, selected int, changed func(string, int)) *Choice
    NewChoice creates a drop-down preserving its style inside a Form. Apply
    Styler.Choice or Styler.Form before drawing it.

// Public alias: underlying declaration and methods.
package widgets // import "github.com/leechis7/tuivory/go/internal/widgets"

type Choice struct {
	*tview.DropDown
	// Has unexported fields.
}
    Choice preserves its own colors when a Form reapplies shared input
    attributes. Its open list uses the shared repair for both edges of
    overlapping wide glyphs.

func NewChoice(label string, options []string, selected int, changed func(string, int)) *Choice

func (c *Choice) Draw(screen tcell.Screen)

func (c *Choice) SetFormAttributes(width int, label, background, _, _ tcell.Color) tview.FormItem
```

## Colors

```go
type Colors = style.Colors
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package style // import "github.com/leechis7/tuivory/go/internal/style"

type Colors struct {
	Background, Surface, Footer, Field, Text, Muted, Accent, Button tcell.Color
	Editor, EditorText, FieldText                                   tcell.Color
	// SelectionText is a historical palette snapshot; SDK rendering reads Styles.SelectionFG.
	//
	// Deprecated: Use Styles.SelectionFG to configure or read the selected foreground.
	SelectionText        tcell.Color
	Placeholder, Warning tcell.Color
}
```

## ComponentEvent

```go
type ComponentEvent struct{ Kind, ID string }
```

## ComponentLine

```go
type ComponentLine struct {
	ID, Text, Role, Value string
	Focused               bool
	Spans                 []ComponentSpan
}
```

## ComponentSpan

```go
type ComponentSpan struct {
	Start, Width int
	Text, Role   string
	Focused      bool
}
    ComponentLine is literal presentation data; ID identifies a hit-tested item.
```

## ContainerChild

```go
type ContainerChild struct {
	Item  LayoutItem
	Child tview.Primitive
}
```

## ContainerOptions

```go
type ContainerOptions struct {
	Kind          string // row, column, grid, layers
	Gap, Padding  int
	Rows, Columns []Track
	VirtualWidth  int `json:"virtual_width"`
	VirtualHeight int `json:"virtual_height"`
}
```

## ContainerState

```go
type ContainerState struct {
	Focused, Captured string

	// Has unexported fields.
}
    ContainerState is a backend-neutral focus/hit/drag router. Modal layers
    block lower layers even when the pointer is outside the card. IDs survive
    reflow.

func (s *ContainerState) Eligible(items []LayoutItem) []string

func (s *ContainerState) Hit(items []LayoutItem, rects []NamedRect, x, y int) string

func (s *ContainerState) Move(items []LayoutItem, previous bool) string

func (s *ContainerState) Reconcile(items []LayoutItem)
```

## ContainerView

```go
type ContainerView struct {
	*tview.Box
	Options ContainerOptions
	State   ContainerState
	// CycleFocus enables Tab/Backtab within this container; disable it when a
	// child form owns Tab. Hosts can also call FocusID/MoveFocus explicitly.
	CycleFocus bool

	ScrollX, ScrollY int
	// Has unexported fields.
}

func NewColumn(children []ContainerChild, palette Palette) (*ContainerView, error)

func NewContainer(options ContainerOptions, children []ContainerChild, palette Palette) (*ContainerView, error)

func NewLayerStack(children []ContainerChild, palette Palette) (*ContainerView, error)

func NewLayoutGrid(rows, columns []Track, children []ContainerChild, palette Palette) (*ContainerView, error)

func NewRow(children []ContainerChild, palette Palette) (*ContainerView, error)

func (v *ContainerView) AtTabBoundary(previous bool) bool

func (v *ContainerView) Blur()

func (v *ContainerView) Draw(screen tcell.Screen)

func (v *ContainerView) Focus(delegate func(tview.Primitive))

func (v *ContainerView) FocusID(id string) bool

func (v *ContainerView) InputHandler() func(*tcell.EventKey, func(tview.Primitive))

func (v *ContainerView) Layout() ([]NamedRect, error)

func (v *ContainerView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)

func (v *ContainerView) MoveFocus(previous bool) string

func (v *ContainerView) PasteHandler() func(string, func(tview.Primitive))

func (v *ContainerView) SetChildren(children []ContainerChild) error

func (v *ContainerView) SetOptions(options ContainerOptions) error

func (v *ContainerView) SetPalette(p Palette) error

func (v *ContainerView) StyleChildren() []tview.Primitive
```

## Control

```go
type Control struct {
	*Form
	ID string
}
    Control is a standalone input, check, select or button backed by the same
    form model. Data, eligibility and activation remain host-owned.

func NewButton(id, label string) (*Control, error)

func NewCheck(id, label string, checked bool) (*Control, error)

func NewControl(field FormField) (*Control, error)

func NewInput(id, label, value string, secret bool) (*Control, error)

func NewSelect(id, label string, options []FormOption, choice string) (*Control, error)

func (c *Control) Layout(w, h int) []ComponentLine
```

## ControlState

```go
type ControlState struct {
	Disabled bool `json:"disabled"`
	ReadOnly bool `json:"read_only"`
	Busy     bool `json:"busy"`
	Selected bool `json:"selected"`
	Edited   bool `json:"edited"`
	Invalid  bool `json:"invalid"`
}
    ControlState describes independent host-owned states. Read-only and busy
    controls remain focusable so their contents and status can be inspected.

func (s ControlState) Visual() ControlVisual
    Visual preserves every state marker even when a higher-priority color wins.
```

## ControlVisual

```go
type ControlVisual struct {
	Role, Markers                    string
	Focusable, Activatable, Editable bool
}
```

## DataState

```go
type DataState struct{ Kind, Text, Detail string }
    DataState is a reusable loading/empty/error/ready view without fetching
    data.

func (s DataState) Layout(width int) []ComponentLine
```

## Density

```go
type Density string

const (
	DensityAuto        Density = "auto"
	DensityCompact     Density = "compact"
	DensityComfortable Density = "comfortable"
)
```

## DrawerPlacement

```go
type DrawerPlacement struct {
	Rect    CellRect
	Overlay bool
}

func DrawerLayout(parent CellRect, preferred, minContent int) DrawerPlacement
```

## FocusStack

```go
type FocusStack struct {
	// Has unexported fields.
}
    FocusStack is host-owned state for a root scope and modal popup scopes.
    It owns neither framework widgets nor a terminal/event loop. The zero value
    must be initialized with NewFocusStack before use.

func NewFocusStack(rootID string, targets []FocusTarget) (*FocusStack, error)

func (s *FocusStack) Close(id string) error
    Close requires the exact top ID, rejecting stale callbacks. The host may
    explicitly close a non-dismissible popup when its work is complete.

func (s *FocusStack) Depth() int

func (s *FocusStack) Focus(id string) bool
    Focus affects only the active scope, including for mouse input.

func (s *FocusStack) Focused() string

func (s *FocusStack) Move(backwards bool) string

func (s *FocusStack) Open(id string, targets []FocusTarget, initial string, dismissible bool) error
    Open captures the parent focus. Empty scopes still block background input.

func (s *FocusStack) RequestClose() *PopupCloseRequest
    RequestClose handles Escape without changing the stack. The host must
    approve and call Close; outside pointer input is only blocked, never
    auto-dismissed.

func (s *FocusStack) Route(targetScope string) InputRoute
    Route uses an empty target for keyboard input. A click must supply its hit
    scope ID; input aimed at an inactive/unknown scope is consumed by the host.

func (s *FocusStack) ScopeID() string

func (s *FocusStack) Targets() []FocusTarget

func (s *FocusStack) Update(scopeID string, targets []FocusTarget) error
    Update reconciles IDs after host data changes. Invalid updates are atomic.
```

## FocusTarget

```go
type FocusTarget struct {
	ID     string       `json:"id"`
	State  ControlState `json:"state"`
	Hidden bool         `json:"hidden"`
}
```

## Form

```go
type Form struct {
	// Has unexported fields.
}

func NewForm(fields []FormField) (*Form, error)

func (f *Form) AtTabBoundary(previous bool) bool

func (f *Form) Click(id, option string) FormEvent
    Click commits an enabled option, or activates a button/check/select.
    Text clicks focus only.

func (f *Form) Fields() []FormField

func (f *Form) Focus(id string) bool

func (f *Form) Focused() string

func (f *Form) Handle(action, text string) FormEvent

func (f *Form) Layout(width, height int) []ComponentLine
    Layout follows the focused field vertically. The visible caret is
    presentation only; it is never inserted into Value or copied data.

func (f *Form) Missing() []string

func (f *Form) SelectText(id string, anchor, cursor int) bool

func (f *Form) SetFeedback(id, help, message string) bool

func (f *Form) SetState(id string, state ControlState) bool

func (f *Form) Value(id string) (string, bool)
    Value is the explicit raw-value access path, including secret inputs.
```

## FormEvent

```go
type FormEvent struct {
	Kind, ID string
	Text     string // Non-secret clipboard request; the host performs clipboard I/O.
	Missing  []string
}

func FormKey(form *Form, e *tcell.EventKey) FormEvent
```

## FormField

```go
type FormField struct {
	ID, Kind, Label, Help, Error, Value, Choice, Action string
	Options                                             []FormOption
	State                                               ControlState
	Required, Checked, Open                             bool
	Pending                                             string
	Cursor                                              int // Grapheme index, never a byte offset.
}
```

## FormOption

```go
type FormOption struct {
	ID, Label string
	Disabled  bool
}
```

## Grid

```go
type Grid struct {
	RowID, ColumnID, SelectedRow, SelectedColumn, SortColumn, SortDirection string
	Row, Column, Top, Left                                                  int
	WholeRow                                                                bool
	Empty                                                                   string

	Labels map[string]string
	Status GridDataStatus

	// Has unexported fields.
}

func NewGrid(columns []GridColumn, source GridSource) (*Grid, error)

func (g *Grid) ApplySource(revision uint64, source GridSource) bool

func (g *Grid) AutoFitColumn(id string, height int) bool

func (g *Grid) Click(rowID, kind string, x, width, height int) GridEvent
    Click is the legacy row-ID and horizontal-coordinate mouse entry point.

    Deprecated: Use Pointer for local mouse coordinates, or Focus and Handle for
    programmatic selection/sorting.

func (g *Grid) ColumnOptions(id string) GridColumnOptions

func (g *Grid) Columns() []GridColumn

func (g *Grid) Focus(rowID, columnID string) bool

func (g *Grid) Geometry(width, height int) GridGeometry

func (g *Grid) Handle(action string, height int) GridEvent

func (g *Grid) Layout(width, height int) []ComponentLine

func (g *Grid) Options() GridOptions

func (g *Grid) Pointer(action string, x, y, width, height int, extend bool) GridEvent
    Pointer consumes local grid coordinates. Hosts translate their own mouse
    protocol; down/move/up support range dragging and header-divider resizing.

func (g *Grid) RequestFilter(query string) GridEvent

func (g *Grid) RequestPage() GridEvent

func (g *Grid) ResizeColumn(id string, width int) bool

func (g *Grid) Revision() uint64

func (g *Grid) SelectRange(r GridRange) bool

func (g *Grid) SelectedRange() GridRange

func (g *Grid) SelectionMode() string

func (g *Grid) SetCellInfo(info func(GridRecord, GridColumn) GridCellInfo)

func (g *Grid) SetColumnOptions(id string, o GridColumnOptions) error

func (g *Grid) SetOptions(o GridOptions) error

func (g *Grid) SetSelectionMode(mode string) error

func (g *Grid) SetSource(source GridSource)

func (g *Grid) StatusItems() []StatusItem
    StatusItems may be rendered separately by the public StatusView as well.
```

## GridCellInfo

```go
type GridCellInfo struct {
	Display                   string
	HasDisplay, Null, Numeric bool
	State                     ControlState
	Metadata                  string
}
    GridCellInfo is host presentation metadata. GridRecord.Cells remain raw
    values.
```

## GridColors

```go
type GridColors = style.GridColors
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package style // import "github.com/leechis7/tuivory/go/internal/style"

type GridColors struct{ Background, Stripe, Header, Current, RangeBG, Divider, Muted tcell.Color }
```

## GridColumn

```go
type GridColumn struct {
	ID, Label string
	Width     int
	Editable  bool
}
```

## GridColumnOptions

```go
type GridColumnOptions struct {
	Align              string // left, center, right, numeric (host-classified numeric cells).
	MinWidth, MaxWidth int
	AutoFit            bool // Measure only the displayed window; never scan the source.
	Expand             int
	Overflow           string // ellipsis (default), clip, scroll.
}
```

## GridDataStatus

```go
type GridDataStatus struct {
	TotalRows               int // 0: use loaded source length.
	Metadata, Filter, Error string
	Loading, HasMore        bool
}
```

## GridEvent

```go
type GridEvent struct{ Kind, RowID, ColumnID, Text, Direction string }
```

## GridGeometry

```go
type GridGeometry struct {
	Top, Left, Gutter, HeaderRows, FooterRows, BodyRows, Stride int
	Columns                                                     []GridSpan
}
```

## GridOptions

```go
type GridOptions struct {
	RowNumbers, HideMarkers, VerticalLines, HorizontalLines, Striped, UseSurface                 bool
	HideHeader, ScrollHeader, StatusBar, ASCII                                                   bool
	HighlightCell, HighlightRow, PreserveEdited, HideSelectionMarker, ShowCellMarkers            bool
	DisableKeyboard, DisableMouse, DisableEditing, DisableCopy, DisableResize, DisableHeaderSort bool
	Padding, RowSpacing, GutterWidth, MaxCopyCells                                               int
	Selection                                                                                    string   // Empty preserves the current mode; cell, row, or range.
	StatusFields                                                                                 []string // nil: all built-in status items.
}
    GridOptions configures the existing Grid; its zero value preserves v0.2.0.
    SetOptions never replaces data, IDs, column widths, or stored selections.

func GridPreset(name string) (GridOptions, error)

func (o GridOptions) WithDensity(name string) (GridOptions, error)
    WithDensity returns a spacing option bundle; other options are retained.
```

## GridRange

```go
type GridRange struct{ AnchorRow, AnchorColumn, EndRow, EndColumn string }
```

## GridRecord

```go
type GridRecord struct {
	ID    string
	Cells map[string]string
	State ControlState
}
```

## GridSource

```go
type GridSource interface {
	Len() int
	Row(int) GridRecord
	IndexOf(string) int
}
    GridSource enables lazy/windowed application data. IndexOf must locate
    stable IDs without a full scan for large sources; Row returns data only on
    demand.
```

## GridSpan

```go
type GridSpan struct {
	ID           string
	Start, Width int
}
```

## Help

```go
type Help struct {
	// Has unexported fields.
}

func NewHelp(items []Shortcut) (*Help, error)

func (h *Help) Layout(width, height int) []ComponentLine
```

## InputRoute

```go
type InputRoute struct {
	ScopeID string
	Blocked bool
}
```

## LayoutItem

```go
type LayoutItem struct {
	ID                      string
	Track                   Track
	Row, Column             int
	RowSpan                 int `json:"row_span"`
	ColumnSpan              int `json:"column_span"`
	Hidden, Modal, Centered bool
	Disabled                bool
	Drawer                  string // "left" or "right" for an edge-attached layer.
	// Layer size: zero expands to available space. Nonzero X/Y are inset offsets.
	Area CellRect
}
```

## LineRun

```go
type LineRun struct {
	Text, Role, ID string
	Start, Width   int
}
    LineRun is a literal cell range. Empty IDs are decorations, never actions.

func Breadcrumbs(items []PathItem, width int) []LineRun
```

## ListEvent

```go
type ListEvent struct{ Kind, ID, Query string }
```

## ListItem

```go
type ListItem struct {
	ID, Label, Secondary, Shortcut, Icon, ASCIIIcon string
	Disabled, Separator                             bool
}
```

## ListModel

```go
type ListModel struct {
	Focused, Selected, Query string
	Empty                    string
	// Has unexported fields.
}

func NewList(items []ListItem) (*ListModel, error)

func (m *ListModel) Focus(id string) bool

func (m *ListModel) Handle(action string, height int) ListEvent

func (m *ListModel) Items() []ListItem

func (m *ListModel) Layout(width, height int, ascii bool) []ComponentLine

func (m *ListModel) SetItems(items []ListItem) error

func (m *ListModel) SetQuery(query string) ListEvent
```

## MemoryRows

```go
type MemoryRows struct {
	// Has unexported fields.
}

func NewMemoryRows(rows []GridRecord) (*MemoryRows, error)

func (m *MemoryRows) IndexOf(id string) int

func (m *MemoryRows) Len() int

func (m *MemoryRows) Row(n int) GridRecord
```

## Menu

```go
type Menu struct {
	BackLabel, EmptyLabel string
	// Has unexported fields.
}

func NewMenu(items []MenuItem) (*Menu, error)

func (m *Menu) Back() MenuEvent

func (m *Menu) BarClick(x, width int) MenuEvent

func (m *Menu) BarFocusedID() string

func (m *Menu) BarLayout(width int) MenuBarLayout

func (m *Menu) Click(id string) MenuEvent

func (m *Menu) Close() MenuEvent

func (m *Menu) ContentSize() (int, int)
    ContentSize excludes the host panel's border/padding.

func (m *Menu) Focus(id string) bool

func (m *Menu) FocusedID() string

func (m *Menu) Handle(action, value string, height int) MenuEvent

func (m *Menu) HandleBar(action, value string) MenuEvent

func (m *Menu) Items() []MenuItem

func (m *Menu) Layout(width, height int, ascii bool) []ComponentLine

func (m *Menu) Open(id, returnID string) MenuEvent

func (m *Menu) Opened() bool

func (m *Menu) Path() []string

func (m *Menu) ReturnID() string

func (m *Menu) SetItems(items []MenuItem) (MenuEvent, error)
    SetItems validates atomically and preserves surviving IDs.
    A removed/disabled open ancestor closes the popup explicitly so the host can
    restore its caller.

func (m *Menu) Title() string
```

## MenuBarCell

```go
type MenuBarCell struct {
	ID, Text, Role string
	Start, Width   int
	Focused        bool
}
```

## MenuBarLayout

```go
type MenuBarLayout struct {
	Cells          []MenuBarCell
	Previous, Next bool
}
```

## MenuEvent

```go
type MenuEvent struct{ Kind, ID, ReturnID string }
```

## MenuItem

```go
type MenuItem struct {
	ID, Parent, Label, Secondary, Shortcut, Mnemonic, Icon, ASCIIIcon string
	Disabled, Separator                                               bool
}
    MenuItem is host-supplied content and eligibility. Parent IDs describe
    groups; Shortcut is display text, not an application-global key binding.
```

## MenuView

```go
type MenuView struct {
	*RowsView
	ASCII bool
}
    MenuView uses selection cues without separate focus decoration. NewPanelView
    renders a directly wrapped MenuView with a single border.

func NewMenuView(model *Menu, palette Palette, ascii bool, onEvent func(MenuEvent)) (*MenuView, error)
```

## NamedRect

```go
type NamedRect struct {
	ID   string
	Rect CellRect
}

func ComputeContainer(bounds CellRect, items []LayoutItem, options ContainerOptions) ([]NamedRect, error)

func StackRects(parent CellRect, items []StackItem, tokens SpacingTokens, vertical bool) ([]NamedRect, []string, error)
```

## Notice

```go
type Notice struct {
	ID, Text, Detail, Severity string
	Priority                   int
	Persistent                 bool
	ExpiresAt                  uint64
	Actions                    []NoticeAction
}
```

## NoticeAction

```go
type NoticeAction struct {
	ID, Label string
	Disabled  bool
}
```

## NoticeEvent

```go
type NoticeEvent struct{ Kind, ID, Action string }
```

## NoticeQueue

```go
type NoticeQueue struct {
	Focused string
	// Has unexported fields.
}

func NewNoticeQueue(capacity int) (*NoticeQueue, error)

func (q *NoticeQueue) Dismiss(id string) bool

func (q *NoticeQueue) Expire(now uint64) []NoticeEvent

func (q *NoticeQueue) Handle(action string, now uint64, height int) NoticeEvent

func (q *NoticeQueue) Layout(width, height int, now uint64) []ComponentLine

func (q *NoticeQueue) Push(n Notice) error

func (q *NoticeQueue) Visible(now uint64) []Notice
```

## Pair

```go
type Pair = style.Pair
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package style // import "github.com/leechis7/tuivory/go/internal/style"

type Pair struct {
	FG, BG tcell.Color
	Bold   bool
}

func (p Pair) Style() tcell.Style
```

## Palette

```go
type Palette = style.Palette
    Aliases keep state and method signatures usable without subpackage imports.

func GridPalette(palette Palette) Palette
    GridPalette returns derived semantic styles without changing shared token
    roles. Existing grid.* overrides in palette are retained.

func Resolve(source TokenPalette) (Palette, error)
    Resolve converts language-neutral palette values to terminal styles.

// Public alias: underlying declaration and methods.
package style // import "github.com/leechis7/tuivory/go/internal/style"

type Palette map[string]Pair

func Resolve(source tokens.Palette) (Palette, error)
    Resolve preserves ANSI indices instead of substituting reference RGB values.
```

## PanelView

```go
type PanelView struct {
	*tview.Box
	Child tview.Primitive

	ASCII bool
	// Has unexported fields.
}
    PanelView wraps a host-owned primitive; no content or event callbacks are
    replaced.

func NewPanelView(child tview.Primitive, palette Palette) (*PanelView, error)

func (v *PanelView) AtTabBoundary(previous bool) bool

func (v *PanelView) Blur()

func (v *PanelView) Draw(screen tcell.Screen)

func (v *PanelView) Focus(delegate func(tview.Primitive))

func (v *PanelView) GetBorder() bool

func (v *PanelView) HasFocus() bool

func (v *PanelView) InputHandler() func(*tcell.EventKey, func(tview.Primitive))

func (v *PanelView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)

func (v *PanelView) PasteHandler() func(string, func(tview.Primitive))

func (v *PanelView) SetBorder(show bool) *PanelView

func (v *PanelView) SetPalette(palette Palette) error

func (v *PanelView) StyleChildren() []tview.Primitive
```

## PathItem

```go
type PathItem struct{ ID, Label string }
```

## PopupCloseRequest

```go
type PopupCloseRequest struct{ ID, Reason string }
```

## PopupLayout

```go
type PopupLayout struct{ Bounds, Card, Shadow CellRect }
    PopupLayout describes the full allocation, interactive card, and shifted
    shadow. Card and Shadow fit Bounds. Only a wide glyph crossing an edge may
    be repaired in an adjacent cell, preserving the outside style.

func PopupPlacement(anchor, viewport CellRect, width, height int, shadow ShadowOptions) PopupLayout
    PopupPlacement positions the whole card+shadow footprint near a host anchor.
    width/height request the card size; clipping may shrink it on narrow
    screens. Existing MenuPlacement remains the no-shadow card-only helper.

func (l PopupLayout) ShadowRegions() [2]CellRect
    ShadowRegions returns disjoint right and bottom strips, excluding the card.
    Paint these instead of the full shifted rectangle so layered attributes do
    not leak into the child widget, especially with Dim-mode shadows.
```

## Progress

```go
type Progress struct {
	ID, Label, Status, Message, CancelLabel string
	Current, Total                          uint64
	Cancellable                             bool
}

func (p Progress) Layout(width int, frame uint64) []ComponentLine

func (p Progress) RequestCancel() NoticeEvent
```

## Roles

```go
type Roles = widgets.Roles
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package widgets // import "github.com/leechis7/tuivory/go/internal/widgets"

type Roles struct {
	Surfaces map[*tview.Box]style.Surface
	Text     map[*tview.TextView]style.TextRole
	Tree     map[*tview.TreeNode]style.TextRole
}
    Roles describes host-owned semantic roles. Missing entries use canvas/body.
    Reuse the same bindings when applying a new Styler; there is no global
    registry.
```

## RowsView

```go
type RowsView struct {
	*tview.Box
	Rows        func(int, int) []ComponentLine
	Key         func(*tcell.EventKey)
	Paste       func(string)
	TabBoundary func(bool) bool
	Click       func(ComponentLine)
	Pointer     func(ComponentLine, int)

	// PreserveBackgrounds keeps explicit row/span backgrounds for grid or custom composition.
	PreserveBackgrounds bool
	Mouse               func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)
	// Has unexported fields.
}
    RowsView renders literal, cell-clipped semantic lines and delegates actions.

func NewBadgeView(badge *Badge, palette Palette) (*RowsView, error)

func NewChipView(chip *Chip, palette Palette, onEvent func(ComponentEvent)) (*RowsView, error)

func NewControlView(control *Control, palette Palette, onEvent func(FormEvent)) (*RowsView, error)

func NewDataStateView(state *DataState, palette Palette) (*RowsView, error)

func NewEditorView(doc *TextDocument, palette Palette, onEvent func(TextEvent)) (*RowsView, error)
    NewEditorView and NewTextViewView share the same literal renderer. Read-only
    is a buffer state, not a second editor implementation. Clipboard events are
    delivered to the host and never executed by the library.

func NewFormView(form *Form, palette Palette, onEvent func(FormEvent)) (*RowsView, error)

func NewGridView(model *Grid, palette Palette, onEvent func(GridEvent)) (*RowsView, error)

func NewHelpView(help *Help, palette Palette) (*RowsView, error)

func NewListView(model *ListModel, palette Palette, ascii bool, onEvent func(ListEvent)) (*RowsView, error)

func NewMenuBarView(model *Menu, palette Palette, onEvent func(MenuEvent)) (*RowsView, error)

func NewNoticeView(queue *NoticeQueue, palette Palette, now func() uint64, onEvent func(NoticeEvent)) (*RowsView, error)

func NewProgressView(progress *Progress, palette Palette, frame func() uint64, onEvent func(NoticeEvent)) (*RowsView, error)

func NewRowsView(rows func(int, int) []ComponentLine, palette Palette) (*RowsView, error)

func NewSearchPickerView(model *SearchPicker, palette Palette, ascii bool, onEvent func(ListEvent)) (*RowsView, error)

func NewTextViewView(doc *TextDocument, palette Palette, onEvent func(TextEvent)) (*RowsView, error)

func (v *RowsView) AtTabBoundary(previous bool) bool

func (v *RowsView) Draw(screen tcell.Screen)

func (v *RowsView) InputHandler() func(*tcell.EventKey, func(tview.Primitive))

func (v *RowsView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)

func (v *RowsView) PasteHandler() func(string, func(tview.Primitive))

func (v *RowsView) SetPalette(palette Palette) error
```

## SearchPicker

```go
type SearchPicker struct {
	List  *ListModel
	Open  bool
	Value string
}
    SearchPicker composes query entry, a list and pending choice. The host owns
    remote search and popup placement; cancel never changes Value.

func NewSearchPicker(items []ListItem) (*SearchPicker, error)

func (p *SearchPicker) Click(id string) ListEvent

func (p *SearchPicker) Handle(action, text string, height int) ListEvent

func (p *SearchPicker) Layout(width, height int, ascii bool) []ComponentLine
```

## ShadowMode

```go
type ShadowMode string
    ShadowMode selects an optional popup shadow. The zero value is off.

const (
	ShadowOff   ShadowMode = "off"
	ShadowAuto  ShadowMode = "auto"
	ShadowSolid ShadowMode = "solid"
	ShadowDim   ShadowMode = "dim"
)
```

## ShadowOptions

```go
type ShadowOptions struct {
	Mode    ShadowMode `json:"mode"`
	OffsetX int        `json:"offsetX"`
	OffsetY int        `json:"offsetY"`
}
    ShadowOptions uses terminal cells. Auto/solid/dim with both offsets zero
    uses the default right-two/down-one offset; use Off to remove the shadow
    entirely.

func (o ShadowOptions) Layout(bounds CellRect) PopupLayout
    Layout reserves shadow space inside an assigned footprint, retaining at
    least one card cell per nonempty dimension. It performs no drawing or input
    routing.

func (o ShadowOptions) Validate() error
```

## ShadowView

```go
type ShadowView struct {
	*tview.Box
	Child tview.Primitive

	ASCII bool
	// Has unexported fields.
}
    ShadowView wraps any host-owned primitive. Its rectangle includes reserved
    shadow space; Child receives only the card. Shadows never receive input.

func NewShadowView(child tview.Primitive, palette Palette, options ShadowOptions) (*ShadowView, error)

func (v *ShadowView) AtTabBoundary(previous bool) bool

func (v *ShadowView) Blur()

func (v *ShadowView) Draw(screen tcell.Screen)

func (v *ShadowView) Focus(delegate func(tview.Primitive))

func (v *ShadowView) HasFocus() bool

func (v *ShadowView) InRect(x, y int) bool
    InRect deliberately excludes the visual shadow, including for host hit
    tests.

func (v *ShadowView) InputHandler() func(*tcell.EventKey, func(tview.Primitive))

func (v *ShadowView) Layout() PopupLayout
    Layout exposes geometry without moving focus or changing child data.

func (v *ShadowView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)

func (v *ShadowView) PasteHandler() func(string, func(tview.Primitive))

func (v *ShadowView) SetPalette(palette Palette) error

func (v *ShadowView) SetShadow(options ShadowOptions) error

func (v *ShadowView) StyleChildren() []tview.Primitive
```

## Shortcut

```go
type Shortcut struct {
	Key, Text string
	Priority  int
	Disabled  bool
}
```

## SpacingTokens

```go
type SpacingTokens struct{ Gap, Padding, ControlGap, CompactBelow int }

func ResolveSpacing(density Density, columns int) (SpacingTokens, error)
```

## SplitLayout

```go
type SplitLayout struct {
	First, Divider, Second int
	Compact                bool
}
```

## SplitSpec

```go
type SplitSpec struct{ FirstMin, SecondMin int }

func (c SplitSpec) Layout(s *SplitState, total int) SplitLayout

func (c SplitSpec) Resize(s *SplitState, total, position int) bool
```

## SplitState

```go
type SplitState struct{ Preferred int }
    SplitState retains the user's preference even when the viewport is compact.
```

## SplitView

```go
type SplitView struct {
	*tview.Box
	First, Second             tview.Primitive
	Spec                      SplitSpec
	State                     *SplitState
	Rows, ActiveSecond, ASCII bool

	// Has unexported fields.
}
    SplitView supports columns or rows. Compact mode shows ActiveSecond's pane.
    Hosts route resize keys through ResizeKey when a child owns application
    focus.

func NewSplitView(first, second tview.Primitive, state *SplitState, spec SplitSpec, palette Palette) (*SplitView, error)

func (v *SplitView) Blur()

func (v *SplitView) Draw(screen tcell.Screen)

func (v *SplitView) Focus(delegate func(tview.Primitive))

func (v *SplitView) HasFocus() bool

func (v *SplitView) InputHandler() func(*tcell.EventKey, func(tview.Primitive))

func (v *SplitView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)

func (v *SplitView) ResizeKey(e *tcell.EventKey) bool

func (v *SplitView) SetPalette(palette Palette) error

func (v *SplitView) StyleChildren() []tview.Primitive
```

## StackItem

```go
type StackItem struct {
	ID                     string
	Min, Preferred, Weight int
}
```

## StackResult

```go
type StackResult struct {
	Slots  []StackSlot
	Hidden []string
	Gap    int
}

func StackLayout(items []StackItem, total, gap int) (StackResult, error)
```

## StackSlot

```go
type StackSlot struct {
	ID          string
	Start, Size int
}
```

## StatusItem

```go
type StatusItem struct {
	ID, Text, Role string
	Priority       int
}
```

## StatusLayout

```go
type StatusLayout struct {
	Runs    []LineRun
	Omitted int
}

func StatusLine(items []StatusItem, width int) StatusLayout
    StatusLine keeps high priority entries first and lower priority entries
    whole. Tiny widths preserve the highest priority cue before an omission
    counter.
```

## StatusView

```go
type StatusView struct {
	*tview.Box

	Omitted int
	// Has unexported fields.
}

func NewStatusView(items []StatusItem, palette Palette) (*StatusView, error)

func (v *StatusView) Draw(screen tcell.Screen)

func (v *StatusView) SetItems(items []StatusItem) error

func (v *StatusView) SetPalette(palette Palette) error
```

## StyleChildren

```go
type StyleChildren = widgets.StyleChildren
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package widgets // import "github.com/leechis7/tuivory/go/internal/widgets"

type StyleChildren interface{ StyleChildren() []tview.Primitive }
    StyleChildren lets host wrappers expose children without importing app
    types.
```

## Styler

```go
type Styler = widgets.Styler
    Aliases keep state and method signatures usable without subpackage imports.

func New(theme, profile string) (Styler, error)
    New creates a widget styler for an explicit theme and color profile.

// Public alias: underlying declaration and methods.
package widgets // import "github.com/leechis7/tuivory/go/internal/widgets"

type Styler struct{ Styles style.Styles }
    Styler is a value; create a new one and reapply it when switching themes.

func New(theme, profile string) (Styler, error)

func (s Styler) Apply(roles Roles, roots ...tview.Primitive)
    Apply recolors existing widgets, including hidden Pages and Form children.
    It does not rebuild widgets or change values, selection, focus, or scroll.
    Rich grids, tabs and footer buttons should be reapplied with their
    specialized methods afterward, since the host owns their state.

func (s Styler) Box(box *tview.Box, background, foreground tcell.Color)

func (s Styler) Button(button *tview.Button)

func (s Styler) Checkbox(box *tview.Checkbox)

func (s Styler) Choice(field *Choice)

func (s Styler) Comparison(table *tview.Table, currentColumn int, section func(row int) bool)
    Comparison styles a header/current-column/section table, such as the
    original keymap comparison. Column 0 is the label column. Section rows are
    host-defined.

func (s Styler) DropDown(field *tview.DropDown)

func (s Styler) Editor(editor *tview.TextArea)

func (s Styler) FooterButton(button *tview.Button)

func (s Styler) Form(form *tview.Form)
    Form owns the form items' DrawFunc hooks to reapply styles after tview's
    per-draw attributes. Apply before installing custom hooks, or use Input etc.

func (s Styler) Grid(table *tview.Table, state func(row, col int) style.CellState)
    Grid styles data only; hit testing, gutter geometry and app data stay in
    the host. state is called for body cells and must be safe for the displayed
    coordinates.

func (s Styler) Input(field *tview.InputField)

func (s Styler) List(list *tview.List)

func (s Styler) Modal(modal *tview.Modal)

func (s Styler) RefreshBorders(roots ...tview.Primitive)
    RefreshBorders uses each widget's current focus and actual background. Call
    after focus changes; it does not install or replace host event handlers.

func (s Styler) Tab(button *tview.Button, active bool)

func (s Styler) Table(table *tview.Table)
    Table styles a simple data table on the canvas.

    Deprecated: Use TableOn(table, tuivory.Canvas), which preserves the same
    styling.

func (s Styler) TableOn(table *tview.Table, surface style.Surface)

func (s Styler) Text(view *tview.TextView, surface style.Surface, role style.TextRole)

func (s Styler) Tree(tree *tview.TreeView, roles map[*tview.TreeNode]style.TextRole)
    Tree reads semantic node roles from the host; labels never determine a role.
```

## Styles

```go
type Styles = style.Styles
    Aliases keep state and method signatures usable without subpackage imports.

func NewStyles(theme, profile string) (Styles, error)
    NewStyles resolves colors and state styles without creating widgets.

// Public alias: underlying declaration and methods.
package style // import "github.com/leechis7/tuivory/go/internal/style"

type Styles struct {
	Colors
	Selection, SelectionFG, Edited, EditedFG, Disabled, Focus tcell.Color
	// Has unexported fields.
}

func NewStyles(theme, profile string) (Styles, error)
    NewStyles resolves LazyOra-derived defaults independently of any screen or
    app.

func (s Styles) BorderStyle(focused bool, background tcell.Color) tcell.Style

func (s Styles) ButtonFocusStyle() tcell.Style

func (s Styles) ButtonStyle() tcell.Style

func (s Styles) ComparisonHeaderStyle(current bool) tcell.Style
    ComparisonHeaderStyle is the generic selected-column header used in
    LazyOra's keymap comparison. The host supplies which column is current.

func (s Styles) DisabledStyle() tcell.Style

func (s Styles) DropDownStyle() tcell.Style

func (s Styles) EditedStyle() tcell.Style

func (s Styles) EditorStyle() tcell.Style

func (s Styles) FieldStyle() tcell.Style
    FieldStyle returns the field text style.

    Deprecated: Use TextStyle(Field, Body), which has the same colors and
    attributes.

func (s Styles) FooterButtonStyle() tcell.Style
    FooterButtonStyle returns the footer text style.

    Deprecated: Use TextStyle(Footer, Body), which has the same colors and
    attributes.

func (s Styles) GridActiveStyle(focused, edited bool) tcell.Style

func (s Styles) GridCellStyle(state CellState) tcell.Style
    GridCellStyle retains LazyOra's composition: stripe, current row,
    null, edited, then range selection. State markers remain the host's
    responsibility.

func (s Styles) GridColors() GridColors

func (s Styles) GridDividerColor() tcell.Color

func (s Styles) GridGutterStyle() tcell.Style

func (s Styles) GridHeaderStyle(active bool) tcell.Style

func (s Styles) GridStatusStyle() tcell.Style

func (s Styles) PopupBackdrop(base tcell.Style, limited bool) tcell.Style
    PopupBackdrop preserves the original attributes and the original
    limited-mode override; limited is an explicit host preference, separate from
    color count.

func (s Styles) PopupCardStyle() tcell.Style
    PopupCardStyle returns panel body text style.

    Deprecated: Use TextStyle(Panel, Body), which returns the same style.

func (s Styles) PopupShadowStyle() tcell.Style

func (s Styles) Profile() string

func (s Styles) SelectionStyle() tcell.Style

func (s Styles) SplitterStyle() tcell.Style

func (s Styles) SurfaceColor(surface Surface) tcell.Color

func (s Styles) SurfaceText(surface Surface) tcell.Color

func (s Styles) SyntaxStyle(kind SyntaxKind, base tcell.Style) tcell.Style

func (s Styles) TabStyle(active bool) tcell.Style

func (s Styles) TextColor(role TextRole) tcell.Color

func (s Styles) TextStyle(surface Surface, role TextRole) tcell.Style

func (s Styles) Theme() string
```

## Surface

```go
type Surface = style.Surface
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package style // import "github.com/leechis7/tuivory/go/internal/style"

type Surface uint8

const (
	Canvas Surface = iota
	Panel
	Field
	Footer
	Editor
)
```

## SurfaceView

```go
type SurfaceView = PanelView
    SurfaceView is an opaque, borderless child container. The assigned rectangle
    is filled before the child is drawn. Hosts still choose placement and
    actions.

func NewSurfaceView(child tview.Primitive, palette Palette) (*SurfaceView, error)
```

## SyntaxKind

```go
type SyntaxKind = style.SyntaxKind
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package style // import "github.com/leechis7/tuivory/go/internal/style"

type SyntaxKind uint8
    SyntaxKind is supplied by the host lexer; TUIVORY does not parse source
    code.

const (
	SyntaxKeyword SyntaxKind = iota + 1
	SyntaxFunction
	SyntaxType
	SyntaxString
	SyntaxNumber
	SyntaxComment
	SyntaxParameter
)
```

## SyntaxSpan

```go
type SyntaxSpan struct {
	Start, End int
	Role       string
}
    SyntaxSpan offsets are grapheme indices in the original text, never bytes.

func ParseMarkup(markup string) (string, []SyntaxSpan, error)
    ParseMarkup is an explicit opt-in to [role]text[/] styling. [[ escapes [.
    It returns plain logical text and grapheme spans; ordinary SetText/Layout
    never interprets markup. Unknown/unbalanced tags return an error atomically.
```

## TabAction

```go
type TabAction uint8

const (
	TabPrevious TabAction = iota
	TabNext
	TabFirst
	TabLast
	TabActivate
	TabClose
)
```

## TabCell

```go
type TabCell struct {
	ID, Text                  string
	Start, Width              int
	Active, Focused, Disabled bool
}
```

## TabEvent

```go
type TabEvent struct{ Kind, ID string }
```

## TabItem

```go
type TabItem struct {
	ID, Title                  string
	Edited, Closable, Disabled bool
}
```

## TabLayout

```go
type TabLayout struct {
	Cells          []TabCell
	Previous, Next bool
}
```

## TabState

```go
type TabState struct {
	Active, Focused string
	First           int
}
```

## TabView

```go
type TabView struct {
	*tview.Box

	OnEvent func(TabEvent)
	// Has unexported fields.
}

func NewTabView(tabs *Tabs, state *TabState, palette Palette) (*TabView, error)

func (v *TabView) Draw(screen tcell.Screen)

func (v *TabView) InputHandler() func(*tcell.EventKey, func(tview.Primitive))

func (v *TabView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)

func (v *TabView) SetPalette(palette Palette) error

func (v *TabView) SetTabs(tabs *Tabs) error
```

## Tabs

```go
type Tabs struct {
	// Has unexported fields.
}

func NewTabs(items []TabItem) (*Tabs, error)

func (t *Tabs) Click(s *TabState, column, width int) TabEvent
    Click requests closing only on the x marker; removal/unsaved confirmation is
    a host decision. Overflow arrows move focus without changing the active tab.

func (t *Tabs) Handle(s *TabState, action TabAction) TabEvent

func (t *Tabs) Layout(s *TabState, width int) TabLayout

func (t *Tabs) Reconcile(s *TabState)
```

## TextBuffer

```go
type TextBuffer struct {
	Cursor, Anchor     int
	State              ControlState
	Secret, SingleLine bool
	// Has unexported fields.
}
    TextBuffer uses extended grapheme indices, including newlines, for
    selection. Text is retrieved explicitly. Secret buffers never expose copy
    requests or plaintext through formatting/JSON. History retains at most 128
    edits in memory.

func NewTextBuffer(text string) *TextBuffer

func (b *TextBuffer) CursorByte() int

func (b *TextBuffer) Format(s fmt.State, _ rune)

func (b *TextBuffer) Handle(action, text string) TextEvent

func (b *TextBuffer) MarshalJSON() ([]byte, error)

func (b *TextBuffer) Select(anchor, cursor int)

func (b *TextBuffer) Selection() (int, int)

func (b *TextBuffer) SetText(text string)

func (b *TextBuffer) String() string

func (b *TextBuffer) Text() string
```

## TextDocument

```go
type TextDocument struct {
	Buffer                   *TextBuffer
	Wrap, LineNumbers, ASCII bool
	ScrollX, ScrollY         int
	Syntax                   []SyntaxSpan

	// Has unexported fields.
}

func NewEditor(text string) *TextDocument

func NewTextView(text string) *TextDocument

func (d *TextDocument) Handle(action, text string) TextEvent
    Handle adds viewport scrolling; copy/cut are host clipboard requests.

func (d *TextDocument) Layout(width, height int) []ComponentLine
    Layout renders literal text; markup is not inferred. Call SetText to replace
    data and provide syntax roles separately. No lexer, clipboard or file I/O.

func (d *TextDocument) Point(x, y, width, height int, extend bool)
    Point hit-tests a cell coordinate relative to the content viewport. Extend
    keeps the selection anchor for a captured drag, even outside the viewport.

func (d *TextDocument) RevealCursor()

func (d *TextDocument) SetMarkup(markup string) error

func (d *TextDocument) SetSyntax(spans []SyntaxSpan) error

func (d *TextDocument) SetText(text string)
```

## TextEvent

```go
type TextEvent struct{ Kind, Text string }
    TextEvent carries requests only. Text is populated only for non-secret
    copy/cut.
```

## TextRole

```go
type TextRole = style.TextRole
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package style // import "github.com/leechis7/tuivory/go/internal/style"

type TextRole uint8

const (
	Body TextRole = iota
	Hint
	Accent
	Warning
)
```

## TokenDocument

```go
type TokenDocument = tokens.Document
    Aliases keep state and method signatures usable without subpackage imports.

func CandidateTokens() (*TokenDocument, error)
    CandidateTokens loads the shared draft JSON candidate, which is distinct
    from the actual LazyOra-derived styles returned by New and NewStyles.

func ParseTokens(data []byte) (*TokenDocument, error)
    ParseTokens validates a complete language-neutral token document.

// Public alias: underlying declaration and methods.
package tokens // import "github.com/leechis7/tuivory/go/internal/tokens"

type Document struct {
	Format   string             `json:"format"`
	Roles    []string           `json:"roles"`
	Palettes map[string]Palette `json:"palettes"`
}

func Candidate() (*Document, error)
    Candidate returns a fresh document so one caller cannot mutate another's
    theme.

func Parse(data []byte) (*Document, error)
    Parse validates a complete document. It performs no terminal or filesystem
    I/O.

func (d *Document) Palette(theme, profile string) (Palette, error)
    Palette resolves an explicit theme/profile pair. Detection belongs to the
    host.
```

## TokenPair

```go
type TokenPair = tokens.Pair
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package tokens // import "github.com/leechis7/tuivory/go/internal/tokens"

type Pair struct {
	Foreground          string `json:"foreground"`
	Background          string `json:"background"`
	ReferenceForeground string `json:"referenceForeground"`
	ReferenceBackground string `json:"referenceBackground"`
	FontWeight          string `json:"fontWeight"`
}
    Pair keeps terminal indices separate from their reference RGB values.
```

## TokenPalette

```go
type TokenPalette = tokens.Palette
    Aliases keep state and method signatures usable without subpackage imports.

// Public alias: underlying declaration and methods.
package tokens // import "github.com/leechis7/tuivory/go/internal/tokens"

type Palette map[string]Pair
```

## Track

```go
type Track struct{ Min, Max, Fixed, Weight int }
    Track constraints are terminal cells; Max=0 means unbounded. Fixed>0
    overrides weight. On tiny screens minimums shrink in declaration order.
```

## Tree

```go
type Tree struct {
	// Has unexported fields.
}

func NewTree(nodes []TreeNode) (*Tree, error)

func (t *Tree) Click(s *TreeState, column, row, height int) TreeEvent
    Click coordinates are relative to the inner tree viewport.

func (t *Tree) Handle(s *TreeState, action TreeAction, height int) TreeEvent

func (t *Tree) Reconcile(s *TreeState, height int) []TreeRow
    Reconcile retains stable IDs after data changes; a hidden selection moves to
    its nearest visible ancestor. Removed selections fall back to the first row.

func (t *Tree) Visible(s *TreeState) []TreeRow
```

## TreeAction

```go
type TreeAction uint8

const (
	TreeUp TreeAction = iota
	TreeDown
	TreeLeft
	TreeRight
	TreeToggle
	TreeActivate
	TreeHome
	TreeEnd
	TreePageUp
	TreePageDown
	TreePanLeft
	TreePanRight
)
```

## TreeEvent

```go
type TreeEvent struct{ Kind, ID string }
    TreeEvent describes an application action; the library never loads data.
    Kind is "select", "expand", "collapse", "activate", or empty for no action.
```

## TreeNode

```go
type TreeNode struct {
	ID, Parent, Name, Secondary, Icon, ASCIIIcon string
	Count                                        *uint64
	Branch                                       bool
}
    TreeNode is application-supplied data. Parents must precede children; IDs
    are unique and stable across replacement. Branch permits unloaded children.
```

## TreeRow

```go
type TreeRow struct {
	Node  TreeNode
	Depth int
}
```

## TreeState

```go
type TreeState struct {
	Selected           string
	Expanded           map[string]bool
	Scroll, Horizontal int
}
    TreeState is owned by the host, independently of palette or input focus.
```

## TreeView

```go
type TreeView struct {
	*tview.Box

	ASCII   bool
	OnEvent func(TreeEvent)
	// Has unexported fields.
}
    TreeView adapts the shared model to tview, preserving the host's TreeState.
    SetPalette changes styles only. It does not replace input/focus callbacks.

func NewTreeView(tree *Tree, state *TreeState, palette Palette) (*TreeView, error)

func (v *TreeView) Draw(screen tcell.Screen)

func (v *TreeView) InputHandler() func(*tcell.EventKey, func(tview.Primitive))

func (v *TreeView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)

func (v *TreeView) SetPalette(palette Palette) error

func (v *TreeView) SetTree(tree *Tree) error
```
