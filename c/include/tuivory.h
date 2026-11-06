#ifndef TUIVORY_H
#define TUIVORY_H
/* Independent C11 API. All text is UTF-8; owned handles require matching free.
 */
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef enum { TUI_OK = 0, TUI_INVALID = 1, TUI_NOMEM = 2 } TuiResult;
typedef struct {
  int x, y, width, height;
} TuiRect;
/* RGB uses 0x1000000 | RRGGBB; other values are ANSI indices 0..255. */
typedef struct {
  unsigned foreground, background;
  int bold, dim, underline;
} TuiStyle;
typedef struct {
  int disabled, read_only, busy, selected, edited, invalid;
} TuiState;
typedef struct {
  const char *kind, *id;
} TuiEvent;
typedef struct TuiCanvas TuiCanvas;
typedef struct TuiTree TuiTree;
typedef struct {
  const char *id, *name, *parent, *secondary, *icon, *ascii_icon;
  int branch, has_count;
  unsigned long long count;
} TuiNode;

/* Palette rejects unknown theme/profile/role; no silent fallback. */
TuiResult tui_style(const char *theme, const char *profile, const char *role,
                    int focused, TuiStyle *out);
const char *tui_state_role(TuiState state);
/* Caller supplies at least 7 bytes (six markers and trailing NUL). */
TuiResult tui_state_markers(TuiState state, char out[7]);
int tui_state_focusable(TuiState state);
int tui_state_activatable(TuiState state);
int tui_state_editable(TuiState state);
/* Returns -1 for invalid UTF-8. Control characters occupy sanitized blank
 * cells. */
int tui_cells(const char *text);
TuiCanvas *tui_canvas_new(int width, int height, const char *theme,
                          const char *profile);
void tui_canvas_free(TuiCanvas *canvas);
TuiResult tui_canvas_write(TuiCanvas *canvas, int x, int y, const char *text,
                           const char *role, int focused, int width);
TuiResult tui_canvas_fill(TuiCanvas *canvas, TuiRect rect, const char *role);
TuiRect tui_canvas_panel(TuiCanvas *canvas, TuiRect rect, const char *title,
                         int focused, int ascii);
void tui_canvas_cursor(TuiCanvas *canvas, int x, int y, int glyph_width);
/* Returned strings are caller-owned; release with tui_string_free. */
char *tui_canvas_ansi(const TuiCanvas *canvas);
char *tui_canvas_line(const TuiCanvas *canvas, int y);
void tui_string_free(char *text);
/* Tree copies all input strings; stable IDs in events live until tree
 * destruction. */
TuiTree *tui_tree_new(const TuiNode *nodes, size_t count);
void tui_tree_free(TuiTree *tree);
TuiEvent tui_tree_handle(TuiTree *tree, const char *action, int height);
TuiEvent tui_tree_click(TuiTree *tree, int x, int y, int height);
const char *tui_tree_selected(const TuiTree *tree);
int tui_tree_expanded(const TuiTree *tree, const char *id);
int tui_tree_scroll(const TuiTree *tree);
int tui_tree_horizontal(const TuiTree *tree);
size_t tui_tree_visible(const TuiTree *tree, const char **ids, size_t capacity);
TuiResult tui_tree_draw(TuiTree *tree, TuiCanvas *canvas, TuiRect rect,
                        int focused, int ascii);
/* Workspace models own their input strings. Layout strings live until the next
 * layout call or model destruction. Returned lines are owned independently. */
char *tui_clip(const char *text, int width, int ellipsis);
typedef struct {
  const char *id, *title;
  int edited, closable, disabled;
} TuiTab;
typedef struct {
  const char *id, *text;
  int start, width, active, focused, disabled;
} TuiTabCell;
typedef struct TuiTabs TuiTabs;
TuiTabs *tui_tabs_new(const TuiTab *items, size_t count);
void tui_tabs_free(TuiTabs *tabs);
TuiEvent tui_tabs_handle(TuiTabs *tabs, const char *action);
TuiEvent tui_tabs_click(TuiTabs *tabs, int column, int width);
TuiResult tui_tabs_layout(TuiTabs *tabs, int width, TuiTabCell *out,
                          size_t capacity, size_t *count);
const char *tui_tabs_active(const TuiTabs *tabs);
const char *tui_tabs_focused(const TuiTabs *tabs);
int tui_tabs_first(const TuiTabs *tabs);
TuiResult tui_tabs_draw(TuiTabs *tabs, TuiCanvas *canvas, TuiRect area,
                        int focused);
typedef struct {
  int preferred, first_min, second_min;
} TuiSplit;
typedef struct {
  int first, divider, second, compact;
} TuiSplitLayout;
TuiSplitLayout tui_split_layout(TuiSplit split, int total);
int tui_split_resize(TuiSplit *split, int total, int position);
typedef struct {
  const char *id, *label;
} TuiPathItem;
typedef struct {
  const char *id, *text, *role;
  int priority;
} TuiStatusItem;
typedef struct {
  const char *text, *role, *id;
  int start, width;
} TuiLineRun;
typedef struct TuiLine TuiLine;
TuiLine *tui_breadcrumbs(const TuiPathItem *items, size_t count, int width);
TuiLine *tui_status_line(const TuiStatusItem *items, size_t count, int width);
void tui_line_free(TuiLine *line);
size_t tui_line_count(const TuiLine *line);
size_t tui_line_omitted(const TuiLine *line);
TuiLineRun tui_line_run(const TuiLine *line, size_t index);
const char *tui_line_hit(const TuiLine *line, int column);
char *tui_line_text(const TuiLine *line);
TuiResult tui_line_draw(const TuiLine *line, TuiCanvas *canvas, TuiRect area);
/* Literal grapheme text. value() is an explicit raw-value accessor; display()
 * returns an owned masked value for passwords. Event text is borrowed until the
 * next text operation. Failed byte ranges leave content/selection/history
 * intact. */
typedef struct TuiText TuiText;
typedef struct {
  const char *kind, *text;
  TuiResult result;
} TuiTextEvent;
TuiText *tui_text_new(const char *value);
void tui_text_free(TuiText *text);
const char *tui_text_value(const TuiText *text);
char *tui_text_display(const TuiText *text);
void tui_text_options(TuiText *text, TuiState state, int secret, int multiline);
void tui_text_select(TuiText *text, size_t anchor, size_t cursor);
size_t tui_text_cursor(const TuiText *text);
size_t tui_text_anchor(const TuiText *text);
TuiResult tui_text_selection_bytes(const TuiText *text, size_t *start,
                                   size_t *end);
TuiResult tui_text_select_bytes(TuiText *text, size_t anchor, size_t cursor);
TuiTextEvent tui_text_replace_bytes(TuiText *text, size_t start, size_t end,
                                    const char *addition);
TuiTextEvent tui_text_handle(TuiText *text, const char *action,
                             const char *addition);
TuiResult tui_text_draw(TuiText *text, TuiCanvas *canvas, TuiRect rect,
                        int focused);
TuiTextEvent tui_text_click(TuiText *text, int x, int y, int width, int height,
                            int extend);
/* Forms copy fields/options; raw password values are only exposed by value().
 */
typedef struct {
  const char *id, *label;
  int disabled;
} TuiFormOption;
typedef struct {
  const char *id, *kind, *label, *value, *help, *error, *choice, *action,
      *pending;
  const TuiFormOption *options;
  size_t option_count;
  TuiState state;
  int required, checked, open, height;
} TuiField;
typedef struct TuiForm TuiForm;
typedef struct {
  const char *kind, *id, *text;
  const char *const *missing;
  size_t missing_count;
  TuiResult result;
} TuiFormEvent;
typedef struct {
  const char *id, *text, *role, *option;
  int input, focused, source_row;
} TuiFormRow;
TuiForm *tui_form_new(const TuiField *fields, size_t count);
void tui_form_free(TuiForm *form);
const TuiField *tui_form_field(const TuiForm *form, const char *id);
const char *tui_form_value(const TuiForm *form, const char *id);
const char *tui_form_focused(const TuiForm *form);
int tui_form_focus(TuiForm *form, const char *id);
int tui_form_at_tab_boundary(const TuiForm *form, int previous);
TuiResult tui_form_set_state(TuiForm *form, const char *id, TuiState state);
TuiResult tui_form_set_feedback(TuiForm *form, const char *id, const char *help,
                                const char *error);
TuiResult tui_form_select_text(TuiForm *form, const char *id, size_t anchor,
                               size_t cursor);
TuiFormEvent tui_form_handle(TuiForm *form, const char *action,
                             const char *text);
TuiFormEvent tui_form_click_field(TuiForm *form, const char *id,
                                  const char *option);
TuiFormEvent tui_form_click(TuiForm *form, int x, int y, int height);
/* Layout rows and their strings are borrowed until the next layout or free. */
TuiResult tui_form_layout(TuiForm *form, int width, int height,
                          const TuiFormRow **rows, size_t *count);
TuiResult tui_form_draw(TuiForm *form, TuiCanvas *canvas, TuiRect rect,
                        int focused);
/* A standalone control is the same form model with one field. */
TuiForm *tui_control_new(TuiField field);
/* Host-owned focus scopes. All opened scopes route input exclusively to top. */
typedef struct {
  const char *id;
  TuiState state;
  int hidden;
} TuiFocusTarget;
typedef struct TuiFocus TuiFocus;
typedef struct {
  const char *scope_id;
  int blocked;
} TuiInputRoute;
typedef struct {
  const char *id, *reason;
} TuiPopupCloseRequest;
TuiFocus *tui_focus_new(const char *root, const TuiFocusTarget *targets,
                        size_t count);
void tui_focus_free(TuiFocus *focus);
const char *tui_focus_focused(const TuiFocus *focus);
const char *tui_focus_scope(const TuiFocus *focus);
size_t tui_focus_depth(const TuiFocus *focus);
int tui_focus_focus(TuiFocus *focus, const char *id);
const char *tui_focus_move(TuiFocus *focus, int previous);
TuiResult tui_focus_open(TuiFocus *focus, const char *id,
                         const TuiFocusTarget *targets, size_t count,
                         const char *initial, int dismissible);
TuiResult tui_focus_update(TuiFocus *focus, const char *id,
                           const TuiFocusTarget *targets, size_t count);
TuiResult tui_focus_close(TuiFocus *focus, const char *id);
TuiPopupCloseRequest tui_focus_request_close(const TuiFocus *focus);
TuiInputRoute tui_focus_route(const TuiFocus *focus, const char *target_scope);
#ifdef __cplusplus
}
#endif
#endif
