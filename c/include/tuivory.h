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
/* Owned Unicode17 C+F search key; no normalization or Turkic override. */
char *tui_casefold(const char *text);
/* Collections own item strings. IDs/query/layout views are borrowed. */
typedef struct {
  const char *id, *label, *secondary, *shortcut, *icon, *ascii_icon, *parent;
  int disabled, separator;
} TuiItem;
typedef struct {
  const char *id, *text, *role;
  int focused;
} TuiCollectionRow;
typedef struct {
  const char *kind, *id, *query;
  TuiResult result;
} TuiCollectionEvent;
typedef struct TuiList TuiList;
TuiList *tui_list_new(const TuiItem *items, size_t count);
void tui_list_free(TuiList *list);
TuiResult tui_list_set_items(TuiList *list, const TuiItem *items, size_t count);
const TuiItem *tui_list_items(const TuiList *list, size_t *count);
const char *tui_list_focused(const TuiList *list);
const char *tui_list_selected(const TuiList *list);
const char *tui_list_query(const TuiList *list);
TuiResult tui_list_empty(TuiList *list, const char *label);
int tui_list_focus(TuiList *list, const char *id);
TuiCollectionEvent tui_list_set_query(TuiList *list, const char *query);
TuiCollectionEvent tui_list_handle(TuiList *list, const char *action,
                                   int height);
TuiCollectionEvent tui_list_click_id(TuiList *list, const char *id);
TuiCollectionEvent tui_list_click(TuiList *list, int x, int y, int height);
TuiResult tui_list_layout(TuiList *list, int width, int height, int ascii,
                          const TuiCollectionRow **rows, size_t *count);
TuiResult tui_list_draw(TuiList *list, TuiCanvas *canvas, TuiRect rect,
                        int focused, int ascii);
typedef struct TuiSearchPicker TuiSearchPicker;
TuiSearchPicker *tui_picker_new(const TuiItem *items, size_t count);
void tui_picker_free(TuiSearchPicker *picker);
TuiList *tui_picker_list(TuiSearchPicker *picker);
int tui_picker_opened(const TuiSearchPicker *picker);
const char *tui_picker_value(const TuiSearchPicker *picker);
TuiCollectionEvent tui_picker_handle(TuiSearchPicker *picker,
                                     const char *action, const char *text,
                                     int height);
TuiCollectionEvent tui_picker_click_id(TuiSearchPicker *picker, const char *id);
TuiCollectionEvent tui_picker_click(TuiSearchPicker *picker, int x, int y,
                                    int height);
TuiResult tui_picker_layout(TuiSearchPicker *picker, int width, int height,
                            int ascii, const TuiCollectionRow **rows,
                            size_t *count);
TuiResult tui_picker_draw(TuiSearchPicker *picker, TuiCanvas *canvas,
                          TuiRect rect, int focused, int ascii);
/* Menu content/actions/anchors are host-owned. Rendering uses selection only.
 */
typedef struct {
  const char *id, *parent, *label, *secondary, *shortcut, *mnemonic, *icon,
      *ascii_icon;
  int disabled, separator;
} TuiMenuItem;
typedef struct TuiMenu TuiMenu;
typedef struct {
  const char *kind, *id, *return_id;
  TuiResult result;
} TuiMenuEvent;
typedef struct {
  int start, width;
  const char *text, *role;
} TuiMenuSpan;
typedef struct {
  const char *id, *text, *role;
  TuiMenuSpan spans[2];
  size_t span_count;
  int focused;
} TuiMenuRow;
typedef struct {
  const char *id, *text, *role;
  int start, width, focused;
} TuiMenuBarCell;
typedef struct {
  const TuiMenuBarCell *cells;
  size_t count;
  int previous, next;
} TuiMenuBarLayout;
TuiMenu *tui_menu_new(const TuiMenuItem *items, size_t count);
void tui_menu_free(TuiMenu *menu);
TuiMenuEvent tui_menu_set_items(TuiMenu *menu, const TuiMenuItem *items,
                                size_t count);
const TuiMenuItem *tui_menu_items(const TuiMenu *menu, size_t *count);
int tui_menu_opened(const TuiMenu *menu);
const char *tui_menu_focused(const TuiMenu *menu);
const char *tui_menu_return_id(const TuiMenu *menu);
const char *tui_menu_bar_focused(const TuiMenu *menu);
size_t tui_menu_path(const TuiMenu *menu, const char **ids, size_t capacity);
char *tui_menu_title(const TuiMenu *menu);
TuiResult tui_menu_labels(TuiMenu *menu, const char *back, const char *empty);
TuiMenuEvent tui_menu_open(TuiMenu *menu, const char *id,
                           const char *return_id);
TuiMenuEvent tui_menu_close(TuiMenu *menu);
TuiMenuEvent tui_menu_back(TuiMenu *menu);
int tui_menu_focus(TuiMenu *menu, const char *id);
TuiMenuEvent tui_menu_handle(TuiMenu *menu, const char *action,
                             const char *value, int height);
TuiMenuEvent tui_menu_handle_bar(TuiMenu *menu, const char *action,
                                 const char *value);
TuiMenuEvent tui_menu_click_id(TuiMenu *menu, const char *id);
TuiMenuEvent tui_menu_click(TuiMenu *menu, int x, int y, int height);
TuiResult tui_menu_content_size(const TuiMenu *menu, int *width, int *height);
TuiResult tui_menu_layout(TuiMenu *menu, int width, int height, int ascii,
                          const TuiMenuRow **rows, size_t *count);
TuiResult tui_menu_draw(TuiMenu *menu, TuiCanvas *canvas, TuiRect area,
                        int ascii);
/* Host-owned popup placement. content receives the rectangle for menu clicks.
 */
TuiResult tui_menu_draw_popup(TuiMenu *menu, TuiCanvas *canvas, TuiRect area,
                              const char *title, int padding, int ascii,
                              TuiRect *content);
TuiResult tui_menu_bar_layout(TuiMenu *menu, int width, TuiMenuBarLayout *out);
TuiMenuEvent tui_menu_bar_click(TuiMenu *menu, int x, int width);
TuiResult tui_menu_draw_bar(TuiMenu *menu, TuiCanvas *canvas, TuiRect area);
TuiRect tui_menu_placement(TuiRect anchor, TuiRect viewport, int width,
                           int height);
/* Feedback uses host monotonic clocks/frames in 0..2^53-1; no timers or I/O.
 * Queues copy source notices/actions. handle/click return requests only. */
typedef struct {
  const char *id, *label;
  int disabled;
} TuiNoticeAction;
typedef struct {
  const char *id, *text, *detail, *severity;
  int priority;
  unsigned long long expires_at;
  int persistent;
  const TuiNoticeAction *actions;
  size_t action_count;
} TuiNotice;
typedef struct {
  const char *kind, *id, *action;
  TuiResult result;
} TuiNoticeEvent;
typedef struct {
  int start, width;
  const char *text, *role, *action;
  int disabled;
} TuiFeedbackSpan;
typedef struct {
  const char *id, *text, *role;
  int focused;
  const TuiFeedbackSpan *spans;
  size_t span_count;
} TuiFeedbackRow;
typedef struct TuiFeedbackView TuiFeedbackView;
typedef struct TuiNoticeQueue TuiNoticeQueue;
typedef struct TuiNoticeEvents TuiNoticeEvents;
TuiNoticeQueue *tui_notice_queue_new(size_t capacity);
void tui_notice_queue_free(TuiNoticeQueue *queue);
TuiResult tui_notice_queue_push(TuiNoticeQueue *queue, const TuiNotice *notice);
const TuiNotice *tui_notice_queue_items(const TuiNoticeQueue *queue,
                                        size_t *count);
const char *tui_notice_queue_focused(const TuiNoticeQueue *queue);
int tui_notice_queue_focus(TuiNoticeQueue *queue, const char *id,
                           unsigned long long now);
TuiResult tui_notice_queue_visible(TuiNoticeQueue *queue,
                                   unsigned long long now,
                                   const TuiNotice **items, size_t *count);
int tui_notice_queue_dismiss(TuiNoticeQueue *queue, const char *id);
TuiResult tui_notice_queue_expire(TuiNoticeQueue *queue, unsigned long long now,
                                  TuiNoticeEvents **events);
size_t tui_notice_events_count(const TuiNoticeEvents *events);
TuiNoticeEvent tui_notice_events_at(const TuiNoticeEvents *events,
                                    size_t index);
void tui_notice_events_free(TuiNoticeEvents *events);
TuiNoticeEvent tui_notice_queue_request_action(TuiNoticeQueue *queue,
                                               const char *id,
                                               const char *action,
                                               unsigned long long now);
TuiNoticeEvent tui_notice_queue_handle(TuiNoticeQueue *queue,
                                       const char *action,
                                       unsigned long long now, int height);
/* Rows are borrowed until next layout/source change/destruction. */
TuiResult tui_notice_queue_layout(TuiNoticeQueue *queue, int width, int height,
                                  unsigned long long now,
                                  const TuiFeedbackRow **rows, size_t *count);
TuiNoticeEvent tui_notice_queue_click(TuiNoticeQueue *queue, int x, int y,
                                      unsigned long long now);
TuiResult tui_notice_queue_draw(TuiNoticeQueue *queue, TuiCanvas *canvas,
                                TuiRect rect, unsigned long long now);
typedef struct {
  const char *id, *label, *status, *message, *cancel_label;
  unsigned long long current, total;
  int cancellable;
} TuiProgress;
typedef struct {
  const char *kind, *text, *detail;
} TuiDataState;
TuiNoticeEvent tui_progress_request_cancel(const TuiProgress *progress);
/* Progress/data layouts are owned; free with tui_feedback_free. */
TuiResult tui_progress_layout(const TuiProgress *progress, int width,
                              unsigned long long frame, TuiFeedbackView **view);
TuiResult tui_progress_draw(const TuiProgress *progress, TuiCanvas *canvas,
                            TuiRect rect, unsigned long long frame);
TuiResult tui_data_state_layout(const TuiDataState *state, int width,
                                TuiFeedbackView **view);
TuiResult tui_data_state_draw(const TuiDataState *state, TuiCanvas *canvas,
                              TuiRect rect);
size_t tui_feedback_count(const TuiFeedbackView *view);
const TuiFeedbackRow *tui_feedback_row(const TuiFeedbackView *view,
                                       size_t index);
TuiResult tui_feedback_draw(const TuiFeedbackView *view, TuiCanvas *canvas,
                            TuiRect rect);
void tui_feedback_free(TuiFeedbackView *view);
#ifdef __cplusplus
}
#endif
#endif
