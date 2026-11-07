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
  int bold, dim, underline, italic;
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
TuiRect tui_canvas_bounds(const TuiCanvas *canvas);
TuiResult tui_canvas_write(TuiCanvas *canvas, int x, int y, const char *text,
                           const char *role, int focused, int width);
TuiResult tui_canvas_fill(TuiCanvas *canvas, TuiRect rect, const char *role);
TuiRect tui_canvas_panel(TuiCanvas *canvas, TuiRect rect, const char *title,
                         int focused, int ascii);
void tui_canvas_cursor(TuiCanvas *canvas, int x, int y, int glyph_width);
/* Opaque cell copy with both-edge wide-glyph repair and cursor projection.
 * Coordinates within +/-1e9, sizes 0..1e9. Self-copy supported; copied text
 * owned. Clear a cursor intersecting rect, or unconditionally when rect is
 * NULL. */
void tui_canvas_clear_cursor(TuiCanvas *canvas, const TuiRect *rect);
TuiResult tui_canvas_blit(TuiCanvas *canvas, const TuiCanvas *source,
                          TuiRect region, int x, int y);
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
/* Cell geometry is pure and copies result IDs; extents <=1e9, 1024 items. */
typedef struct {
  int gap, padding, control_gap, compact_below;
} TuiSpacingTokens;
typedef struct {
  const char *id;
  int min, preferred, weight;
} TuiStackItem;
typedef struct {
  const char *id;
  int start, size;
} TuiStackSlot;
typedef struct TuiStackResult TuiStackResult;
typedef struct {
  const char *id;
  TuiRect rect;
} TuiNamedRect;
typedef struct TuiLayoutResult TuiLayoutResult;
typedef struct {
  TuiRect rect;
  int overlay;
} TuiDrawerPlacement;
TuiResult tui_spacing_tokens(const char *density, int columns,
                             TuiSpacingTokens *out);
TuiResult tui_rect_inset(TuiRect parent, int padding, TuiRect *out);
TuiResult tui_stack_layout(const TuiStackItem *items, size_t count, int total,
                           int gap, TuiStackResult **out);
size_t tui_stack_slot_count(const TuiStackResult *result);
const TuiStackSlot *tui_stack_slot_at(const TuiStackResult *result,
                                      size_t index);
size_t tui_stack_hidden_count(const TuiStackResult *result);
const char *tui_stack_hidden_at(const TuiStackResult *result, size_t index);
int tui_stack_gap(const TuiStackResult *result);
void tui_stack_free(TuiStackResult *result);
TuiResult tui_stack_rects(TuiRect parent, const TuiStackItem *items,
                          size_t count, TuiSpacingTokens tokens, int vertical,
                          TuiLayoutResult **out);
size_t tui_layout_rect_count(const TuiLayoutResult *result);
const TuiNamedRect *tui_layout_rect_at(const TuiLayoutResult *result,
                                       size_t index);
size_t tui_layout_hidden_count(const TuiLayoutResult *result);
const char *tui_layout_hidden_at(const TuiLayoutResult *result, size_t index);
void tui_layout_free(TuiLayoutResult *result);
TuiResult tui_drawer_layout(TuiRect parent, int preferred, int min_content,
                            TuiDrawerPlacement *out);
/* Supporting lines use owned FeedbackView values; free with tui_feedback_free.
 */
typedef struct {
  const char *id, *label;
  int has_count;
  unsigned long long count, limit;
  TuiState state;
} TuiBadge;
typedef struct {
  const char *id, *label;
  TuiState state;
  int removable;
} TuiChip;
TuiResult tui_badge_line(const TuiBadge *badge, int width,
                         TuiFeedbackView **view);
TuiResult tui_badge_draw(const TuiBadge *badge, TuiCanvas *canvas,
                         TuiRect rect);
TuiResult tui_chip_line(const TuiChip *chip, int width, TuiFeedbackView **view);
TuiResult tui_chip_draw(const TuiChip *chip, TuiCanvas *canvas, TuiRect rect);
TuiEvent tui_chip_request_remove(const TuiChip *chip);
typedef struct {
  const char *key, *text;
  int priority, disabled;
} TuiShortcut;
typedef struct TuiHelp TuiHelp;
TuiHelp *tui_help_new(const TuiShortcut *items, size_t count);
void tui_help_free(TuiHelp *help);
TuiResult tui_help_layout(const TuiHelp *help, int width, int height,
                          TuiFeedbackView **view);
TuiResult tui_help_draw(const TuiHelp *help, TuiCanvas *canvas, TuiRect rect);
/* Configured local layouts. Zero Track fields mean a default weighted track. */
typedef struct {
  int min, max, fixed, weight;
} TuiTrack;
typedef struct {
  const char *id;
  TuiTrack track;
  int row, column, row_span, column_span;
  int hidden, disabled;
  const char *drawer;
  int modal, centered;
  TuiRect area;
} TuiLayoutItem;
typedef struct {
  const char *kind;
  int gap, padding;
  const TuiTrack *rows;
  size_t row_count;
  const TuiTrack *columns;
  size_t column_count;
  int virtual_width, virtual_height;
} TuiContainerOptions;
/* NULL options or kind selects row. Results own IDs, freed with
 * tui_layout_free. */
TuiResult tui_compute_container(TuiRect bounds, const TuiLayoutItem *items,
                                size_t count,
                                const TuiContainerOptions *options,
                                TuiLayoutResult **out);
typedef struct TuiContainerState TuiContainerState;
TuiContainerState *tui_container_state_new(void);
void tui_container_state_free(TuiContainerState *state);
const char *tui_container_focused(const TuiContainerState *state);
const char *tui_container_captured(const TuiContainerState *state);
TuiResult tui_container_reconcile(TuiContainerState *state,
                                  const TuiLayoutItem *items, size_t count);
TuiResult tui_container_move_focus(TuiContainerState *state,
                                   const TuiLayoutItem *items, size_t count,
                                   int previous);
/* Hit IDs borrow layout. Pointer IDs belong to state, valid until its next
 * operation. */
const char *tui_container_hit(const TuiLayoutItem *items, size_t count,
                              const TuiLayoutResult *layout, int x, int y);
TuiResult tui_container_state_pointer(TuiContainerState *state,
                                      const TuiLayoutItem *items, size_t count,
                                      const TuiLayoutResult *layout, int x,
                                      int y, int press, int release,
                                      const char **id);
typedef struct TuiContainer TuiContainer;
typedef TuiResult (*TuiChildPainter)(void *context, const char *id,
                                     TuiCanvas *child, int focused);
/* Owns items, ID strings and options. Child canvas is callback-borrowed, local
 * (0,0). */
TuiContainer *tui_container_new(const TuiLayoutItem *items, size_t count,
                                const TuiContainerOptions *options);
void tui_container_free(TuiContainer *container);
TuiResult tui_container_set_items(TuiContainer *container,
                                  const TuiLayoutItem *items, size_t count,
                                  const TuiContainerOptions *options);
TuiContainerState *tui_container_state(TuiContainer *container);
TuiResult tui_container_scroll(TuiContainer *container, int x, int y);
TuiResult tui_container_draw(TuiContainer *container, TuiCanvas *canvas,
                             TuiRect bounds, TuiChildPainter painter,
                             void *context);
/* Latest layout is borrowed until draw/update/free. Coordinates are
 * virtual-local. */
const TuiLayoutResult *tui_container_layout(const TuiContainer *container);
TuiResult tui_container_pointer(TuiContainer *container, int x, int y,
                                int press, int release, const char **id);
/* Bind plain text to an actual surface; explicit control state backgrounds
 * remain. */
TuiResult tui_text_on_surface(const char *theme, const char *profile,
                              const char *role, const char *surface,
                              int focused, TuiStyle *out);
TuiResult tui_control_on_surface(const char *theme, const char *profile,
                                 TuiState state, const char *surface,
                                 int focused, TuiStyle *out);
/* Surface affects subsequent role-based painting, not already drawn cells. */
TuiResult tui_canvas_surface(TuiCanvas *canvas, const char *surface);
const char *tui_canvas_surface_role(const TuiCanvas *canvas);
TuiResult tui_canvas_write_style(TuiCanvas *canvas, int x, int y,
                                 const char *text, const TuiStyle *style,
                                 int width);
typedef struct {
  const char *role;
} TuiSurface;
typedef TuiResult (*TuiSurfacePainter)(void *context, TuiCanvas *child);
TuiResult tui_surface_draw(const TuiSurface *surface, TuiCanvas *canvas,
                           TuiRect bounds, TuiSurfacePainter painter,
                           void *context);
/* Optional visual-only popup shadow. NULL mode/options selects off; enabled
 * zero offsets default to right1/reserved row1 (auto/solid paint half-row
 * caps). */
typedef struct {
  const char *mode;
  int offset_x, offset_y;
} TuiShadowOptions;
typedef struct {
  TuiRect bounds, card, shadow;
} TuiPopupLayout;
TuiResult tui_shadow_layout(const TuiShadowOptions *options, TuiRect bounds,
                            TuiPopupLayout *out);
TuiResult tui_popup_placement(TuiRect anchor, TuiRect viewport, int width,
                              int height, const TuiShadowOptions *options,
                              TuiPopupLayout *out);
TuiResult tui_popup_shadow_regions(TuiPopupLayout layout, TuiRect out[2]);
int tui_popup_hit(const TuiPopupLayout *layout, int x, int y);
/* Painter receives only the card's borrowed child Canvas, with local (0,0).
 * Failed painting leaves the destination unchanged; out may be NULL. */
TuiResult tui_shadow_draw(const TuiShadowOptions *options, TuiCanvas *canvas,
                          TuiRect bounds, TuiSurfacePainter painter,
                          void *context, int ascii, TuiPopupLayout *out);
/* Literal dialog; buttons/labels are copied. A valid enabled cancel_id is the
 * initial/default focus. Activation/cancel returns requests, never closes it.
 */
typedef struct {
  const char *id, *label;
  int disabled;
} TuiDialogButton;
typedef struct {
  const char *id, *text;
  TuiRect rect;
  int disabled, focused;
} TuiDialogButtonCell;
typedef struct TuiDialog TuiDialog;
typedef struct TuiDialogLayout TuiDialogLayout;
TuiDialog *tui_dialog_new(const char *title, const char *message,
                          const TuiDialogButton *buttons, size_t count,
                          const char *cancel_id);
void tui_dialog_free(TuiDialog *dialog);
/* NULL title/message or cancel_id retains the corresponding existing value. */
TuiResult tui_dialog_set_text(TuiDialog *dialog, const char *title,
                              const char *message);
TuiResult tui_dialog_set_buttons(TuiDialog *dialog,
                                 const TuiDialogButton *buttons, size_t count,
                                 const char *cancel_id);
const char *tui_dialog_title(const TuiDialog *dialog);
const char *tui_dialog_message(const TuiDialog *dialog);
const char *tui_dialog_cancel_id(const TuiDialog *dialog);
const char *tui_dialog_focused(const TuiDialog *dialog);
size_t tui_dialog_button_count(const TuiDialog *dialog);
const TuiDialogButton *tui_dialog_button_at(const TuiDialog *dialog,
                                            size_t index);
int tui_dialog_focus(TuiDialog *dialog, const char *id);
/* Event IDs borrow buttons until set_buttons/free. */
TuiEvent tui_dialog_handle(TuiDialog *dialog, const char *action);
TuiEvent tui_dialog_click(TuiDialog *dialog, int x, int y);
/* Layout owns text/IDs and survives model changes/destruction. */
TuiResult tui_dialog_layout(const TuiDialog *dialog, int width, int height,
                            TuiDialogLayout **out);
void tui_dialog_layout_free(TuiDialogLayout *layout);
size_t tui_dialog_body_count(const TuiDialogLayout *layout);
const char *tui_dialog_body_at(const TuiDialogLayout *layout, size_t index);
size_t tui_dialog_cell_count(const TuiDialogLayout *layout);
const TuiDialogButtonCell *tui_dialog_cell_at(const TuiDialogLayout *layout,
                                              size_t index);
size_t tui_dialog_hidden_buttons(const TuiDialogLayout *layout);
int tui_dialog_body_truncated(const TuiDialogLayout *layout);
/* Screen coordinates match the Canvas used by draw. out is optional/owned. */
TuiResult tui_dialog_draw(TuiDialog *dialog, TuiCanvas *canvas, TuiRect bounds,
                          int focused, int ascii, TuiDialogLayout **out);
/* Document ranges use original grapheme indices; byte setters require exact
 * boundaries. */
typedef struct {
  size_t start, end;
} TuiDocumentRange;
typedef struct {
  size_t start, end;
  const char *role;
} TuiDocumentSpan;
typedef struct {
  int x;
  size_t index;
} TuiDocumentHit;
typedef struct {
  int x;
  const char *text;
  size_t index;
  int width;
  const char *role;
  int cursor;
} TuiDocumentGlyph;
typedef struct {
  int number;
  const char *prefix;
  const TuiDocumentGlyph *glyphs;
  size_t glyph_count;
  const TuiDocumentHit *hits;
  size_t hit_count;
} TuiDocumentLine;
typedef struct {
  int wrap, line_numbers, scroll_x, scroll_y;
} TuiDocumentOptions;
typedef struct TuiDocument TuiDocument;
typedef struct TuiDocumentLayout TuiDocumentLayout;
TuiDocument *tui_document_new(const char *text, int read_only);
void tui_document_free(TuiDocument *document);
/* Borrowed buffer; invalidated by set_text and document_free. Never free it. */
TuiText *tui_document_buffer(TuiDocument *document);
TuiDocumentOptions tui_document_options(const TuiDocument *document);
TuiResult tui_document_configure(TuiDocument *document,
                                 TuiDocumentOptions options);
TuiResult tui_document_set_text(TuiDocument *document, const char *text);
TuiResult tui_document_set_syntax(TuiDocument *document,
                                  const TuiDocumentSpan *spans, size_t count);
TuiResult tui_document_set_byte_syntax(TuiDocument *document,
                                       const TuiDocumentSpan *spans,
                                       size_t count);
TuiResult tui_document_set_search_matches(TuiDocument *document,
                                          const TuiDocumentRange *matches,
                                          size_t count);
TuiResult tui_document_set_markup(TuiDocument *document, const char *markup);
TuiResult tui_parse_markup(const char *markup, char **source,
                           TuiDocumentSpan **spans, size_t *count);
void tui_document_spans_free(TuiDocumentSpan *spans, size_t count);
void tui_document_reveal_cursor(TuiDocument *document);
TuiTextEvent tui_document_handle(TuiDocument *document, const char *action,
                                 const char *text);
TuiResult tui_document_layout(TuiDocument *document, int width, int height,
                              TuiDocumentLayout **out);
void tui_document_layout_free(TuiDocumentLayout *layout);
size_t tui_document_line_count(const TuiDocumentLayout *layout);
const TuiDocumentLine *tui_document_line_at(const TuiDocumentLayout *layout,
                                            size_t index);
TuiResult tui_document_draw(TuiDocument *document, TuiCanvas *canvas,
                            TuiRect bounds, int focused, int ascii);
TuiTextEvent tui_document_click(TuiDocument *document, int x, int y, int width,
                                int height, int extend);
/* Optional source-tagged syntax analysis; offsets are original UTF-8 bytes. */
typedef struct {
  size_t start, end;
  const char *role;
} TuiSyntaxToken;
typedef struct {
  const char *language, *dialect;
} TuiSyntaxRequest;
typedef struct {
  const char *source, *language, *dialect;
  const TuiSyntaxToken *tokens;
  size_t count;
} TuiSyntaxAnalysis;
/* Callback returns owned analysis created with
 * tui_syntax_analysis_new/sql_analyze. The library frees it on success or
 * failure. Context remains caller-owned. */
typedef TuiResult (*TuiSyntaxAnalyzer)(void *context, const char *text,
                                       const TuiSyntaxRequest *request,
                                       TuiSyntaxAnalysis **out);
TuiSyntaxAnalysis *tui_syntax_analysis_new(const char *source,
                                           const char *language,
                                           const char *dialect,
                                           const TuiSyntaxToken *tokens,
                                           size_t count);
void tui_syntax_analysis_free(TuiSyntaxAnalysis *analysis);
TuiResult tui_syntax_validate(const TuiSyntaxAnalysis *analysis,
                              const char *source);
const char *tui_syntax_role_style(const char *role);
const char *tui_syntax_palette_role(const char *role);
TuiResult tui_syntax_style(const char *theme, const char *profile,
                           const char *role, const char *surface,
                           TuiStyle *out);
/* Signature adapter for use directly as a TuiSyntaxAnalyzer callback. */
TuiResult tui_sql_analyzer(void *context, const char *text,
                           const TuiSyntaxRequest *request,
                           TuiSyntaxAnalysis **out);
TuiResult tui_sql_analyze(const char *text, const TuiSyntaxRequest *request,
                          TuiSyntaxAnalysis **out);
TuiResult tui_document_set_syntax_analysis(TuiDocument *document,
                                           const TuiSyntaxAnalysis *analysis);
TuiResult tui_document_set_syntax_analyzer(TuiDocument *document,
                                           TuiSyntaxAnalyzer analyzer,
                                           void *context,
                                           const TuiSyntaxRequest *request);
TuiResult tui_document_refresh_syntax(TuiDocument *document);
const char *tui_document_syntax_error(const TuiDocument *document);
/* Independent data grid. Handles own their copied inputs. Source callback
 * context remains caller-owned until set_source/set_rows/free. Callbacks may
 * not mutate or free the grid. A returned row is borrowed until the next
 * source callback; the grid copies it before calling index_of. */
typedef struct TuiGrid TuiGrid;
typedef struct TuiGridGeometry TuiGridGeometry;
typedef struct TuiGridViewState TuiGridViewState;
typedef struct TuiGridTSV TuiGridTSV;
typedef struct {
  const char *id, *label;
  int width, editable, hidden;
  const char *pin;
} TuiGridColumn;
typedef struct {
  const char *column_id, *text;
  int is_null;
  TuiState state;
} TuiGridCell;
typedef struct {
  const char *id;
  const TuiGridCell *cells;
  size_t cell_count;
  TuiState state;
} TuiGridRecord;
typedef struct {
  void *context;
  size_t count;
  TuiResult (*row)(void *context, size_t index, TuiGridRecord *out);
  TuiResult (*index_of)(void *context, const char *id, size_t *out);
} TuiGridSource;
typedef struct {
  const char *text;
  int is_null;
} TuiGridValue;
/* Return TUI_INVALID to deny preparation. out->text is borrowed until the
 * callback returns to the grid and is copied immediately. */
typedef TuiResult (*TuiGridPrepare)(void *context, const TuiGridRecord *row,
                                    const TuiGridColumn *column,
                                    TuiGridValue *out);
typedef struct {
  int enabled, start_typing, allow_null;
  TuiGridPrepare prepare;
  void *context;
} TuiGridEditOptions;
typedef struct {
  const char *display, *metadata;
  int has_display, is_null, numeric;
  TuiState state;
} TuiGridCellInfo;
typedef TuiResult (*TuiGridCellProvider)(void *context,
                                         const TuiGridRecord *row,
                                         const TuiGridColumn *column,
                                         TuiGridCellInfo *out);
typedef struct {
  int row_numbers, vertical_lines, horizontal_lines, striped, use_surface;
  int hide_header, status_bar, ascii, highlight_cell, highlight_row;
  int preserve_edited, show_cell_markers;
  int disable_keyboard, disable_mouse, disable_editing, disable_copy;
  int disable_resize, disable_header_sort;
  int padding, row_spacing, gutter_width, max_copy_cells;
  const char *selection;
  const char *const *status_fields;
  size_t status_field_count;
} TuiGridOptions;
typedef struct {
  const char *align;
  int min_width, max_width, auto_fit, expand;
  const char *overflow;
} TuiGridColumnOptions;
typedef struct {
  const char *anchor_row, *anchor_column, *end_row, *end_column;
} TuiGridRange;
typedef struct {
  const char *null_text, *loading, *empty, *range, *more;
} TuiGridLabels;
TuiResult tui_grid_set_labels(TuiGrid *grid, TuiGridLabels labels);
const TuiGridLabels *tui_grid_labels(const TuiGrid *grid);
typedef struct {
  size_t total_rows;
  const char *metadata, *filter, *error;
  int loading, has_more;
} TuiGridDataStatus;
typedef struct {
  const char *id;
  int x, width;
} TuiGridSpan;
typedef struct {
  size_t top;
  int left, gutter, header_rows, footer_rows, body_rows, stride;
} TuiGridGeometryInfo;
typedef struct {
  unsigned long long id, revision;
  const char *row_id, *column_id;
  TuiGridValue original, value;
  int pending;
  const char *error;
} TuiGridEditSession;
typedef struct {
  const char *row_id, *column_id;
  TuiGridValue value;
} TuiGridChange;
typedef struct {
  unsigned long long id, revision;
  const TuiGridChange *changes;
  size_t change_count;
} TuiGridPasteRequest;
/* Event strings and pending getters are borrowed until the next grid mutation.
 * Copy IDs/values before resolving, replacing inputs or freeing the grid. */
typedef struct {
  TuiResult result;
  const char *kind, *row_id, *column_id, *text;
  unsigned long long id, revision;
  TuiGridValue value;
} TuiGridEvent;
TuiGrid *tui_grid_new(const TuiGridColumn *columns, size_t column_count,
                      const TuiGridRecord *rows, size_t row_count);
void tui_grid_free(TuiGrid *grid);
TuiResult tui_grid_set_rows(TuiGrid *grid, const TuiGridRecord *rows,
                            size_t row_count);
TuiResult tui_grid_set_source(TuiGrid *grid, TuiGridSource source);
const char *tui_grid_row_id(TuiGrid *grid);
const char *tui_grid_column_id(TuiGrid *grid);
unsigned long long tui_grid_revision(const TuiGrid *grid);
int tui_grid_focus(TuiGrid *grid, const char *row_id, const char *column_id);
TuiResult tui_grid_preset(const char *name, TuiGridOptions *out);
TuiResult tui_grid_density(TuiGridOptions *options, const char *density);
TuiResult tui_grid_configure(TuiGrid *grid, const TuiGridOptions *options);
/* Options are borrowed until the next configure/free. Copy the struct before
 * editing. */
const TuiGridOptions *tui_grid_options(const TuiGrid *grid);
TuiResult tui_grid_set_sort(TuiGrid *grid, const char *column_id,
                            const char *direction);
TuiResult tui_grid_set_column_options(TuiGrid *grid, const char *id,
                                      TuiGridColumnOptions options);
TuiResult tui_grid_set_column_layout(TuiGrid *grid, const TuiGridColumn *layout,
                                     size_t count);
TuiResult tui_grid_set_edit_options(TuiGrid *grid, TuiGridEditOptions options);
TuiResult tui_grid_set_cell_info(TuiGrid *grid, TuiGridCellProvider provider,
                                 void *context);
TuiResult tui_grid_set_status(TuiGrid *grid, TuiGridDataStatus status);
TuiResult tui_grid_set_selection(TuiGrid *grid, const TuiGridRange *range);
/* begin_edit first=NULL retains the prepared value. first="" replaces it with
 * a non-NULL empty value. Approval never updates application records itself. */
int tui_grid_begin_edit(TuiGrid *grid, const char *first);
const TuiGridEditSession *tui_grid_edit_session(TuiGrid *grid);
TuiText *tui_grid_edit_buffer(TuiGrid *grid);
TuiGridEvent tui_grid_handle(TuiGrid *grid, const char *action, int height,
                             const char *text);
int tui_grid_resolve_edit(TuiGrid *grid, unsigned long long id,
                          const char *error, const TuiGridSource *source);
TuiResult tui_grid_request_paste(TuiGrid *grid, const char *text, int max_cells,
                                 const char *null_text);
const TuiGridPasteRequest *tui_grid_pending_paste(const TuiGrid *grid);
int tui_grid_resolve_paste(TuiGrid *grid, unsigned long long id,
                           const TuiGridSource *source);
void tui_grid_cancel_paste(TuiGrid *grid);
int tui_grid_find(TuiGrid *grid, const char *query, int previous,
                  int case_sensitive, int use_display, int max_cells);
/* Caller owns copy text and details document; normal matching free applies. */
TuiResult tui_grid_copy(TuiGrid *grid, int display, const char *null_text,
                        char **out);
TuiDocument *tui_grid_details(TuiGrid *grid);
TuiGridEvent tui_grid_request(TuiGrid *grid, const char *kind,
                              const char *text);
int tui_grid_apply_source(TuiGrid *grid, unsigned long long revision,
                          TuiGridSource source);
int tui_grid_resize_column(TuiGrid *grid, const char *id, int width);
int tui_grid_auto_fit_column(TuiGrid *grid, const char *id, int height);
TuiResult tui_grid_pan_cell(TuiGrid *grid, const char *id, int offset);
/* Geometry and saved view are independent owned snapshots. */
TuiResult tui_grid_geometry(TuiGrid *grid, int width, int height,
                            TuiGridGeometry **out);
TuiGridGeometryInfo tui_grid_geometry_info(const TuiGridGeometry *geometry);
size_t tui_grid_span_count(const TuiGridGeometry *geometry);
const TuiGridSpan *tui_grid_span_at(const TuiGridGeometry *geometry,
                                    size_t index);
void tui_grid_geometry_free(TuiGridGeometry *geometry);
TuiResult tui_grid_edit_cursor(TuiGrid *grid, int width, int height, int *x,
                               int *y, int *glyph_width);
TuiResult tui_grid_draw(TuiGrid *grid, TuiCanvas *canvas, TuiRect bounds,
                        int focused, int ascii);
TuiGridEvent tui_grid_click(TuiGrid *grid, int x, int y, int width, int height);
TuiGridViewState *tui_grid_save_view(TuiGrid *grid);
TuiResult tui_grid_restore_view(TuiGrid *grid, const TuiGridViewState *view);
void tui_grid_view_free(TuiGridViewState *view);
TuiResult tui_grid_parse_tsv(const char *text, int max_cells, TuiGridTSV **out);
size_t tui_grid_tsv_rows(const TuiGridTSV *table);
size_t tui_grid_tsv_columns(const TuiGridTSV *table);
const char *tui_grid_tsv_at(const TuiGridTSV *table, size_t row, size_t column);
TuiResult tui_grid_format_tsv(const TuiGridTSV *table, char **out);
void tui_grid_tsv_free(TuiGridTSV *table);
/* Request-only drag/drop. Request/layout handles are owned; view strings and
 * model metadata getters are borrowed until handle destruction. Hex revisions
 * have 16 lowercase digits. Apply returns a new owned model, never mutates
 * input. Optional reason receives a static error code, or an empty string on
 * success. Policies may inspect requests but must not mutate/free the source or
 * state. */
typedef struct TuiDropRequest {
  const char *source_id, *target_id, *position, *revision;
} TuiDropRequest;
typedef int (*TuiDropPolicy)(void *context, const TuiDropRequest *request);
typedef struct {
  int threshold, auto_scroll, hover_expand;
  const char *const *locked;
  size_t locked_count;
} TuiDragOptions;
typedef struct {
  const char *action;
  int x, y, width, height;
} TuiDragPointer;
typedef struct TuiDragState TuiDragState;
typedef struct {
  const char *phase, *result, *source_id, *target_id, *position, *reason;
  int allowed, captured;
} TuiDragView;
/* Preview owns these copied models; never install or free them separately.
 * Model scroll/expanded/first describe preview viewport; tabs layout is
 * borrowed from its copied model and does not follow the actual keyboard focus.
 */
typedef struct TuiDragLayout {
  TuiTree *tree;
  TuiTabs *tabs;
  const TuiTabCell *tab_cells;
  size_t tab_count;
} TuiDragLayout;
size_t tui_tree_count(const TuiTree *tree);
const TuiNode *tui_tree_node(const TuiTree *tree, size_t index);
size_t tui_tabs_count(const TuiTabs *tabs);
const TuiTab *tui_tabs_item(const TuiTabs *tabs, size_t index);
TuiResult tui_tree_drag_revision(const TuiTree *tree, char out[17]);
TuiResult tui_tabs_drag_revision(const TuiTabs *tabs, char out[17]);
void tui_drop_request_free(TuiDropRequest *request);
TuiDropRequest *tui_tree_request_drop(const TuiTree *tree, const char *source,
                                      const char *target, const char *position,
                                      const TuiDragOptions *options,
                                      TuiDropPolicy policy, void *context,
                                      const char **reason);
TuiDropRequest *tui_tabs_request_drop(const TuiTabs *tabs, const char *source,
                                      const char *target, const char *position,
                                      const TuiDragOptions *options,
                                      TuiDropPolicy policy, void *context,
                                      const char **reason);
TuiTree *tui_tree_apply_drop(const TuiTree *tree, const TuiDropRequest *request,
                             const char **reason);
TuiTabs *tui_tabs_apply_drop(const TuiTabs *tabs, const TuiDropRequest *request,
                             const char **reason);
TuiDropRequest *tui_tree_keyboard_drop(const TuiTree *tree,
                                       const char *direction,
                                       const TuiDragOptions *options,
                                       TuiDropPolicy policy, void *context,
                                       const char **reason);
TuiDropRequest *tui_tabs_keyboard_drop(const TuiTabs *tabs,
                                       const char *direction,
                                       const TuiDragOptions *options,
                                       TuiDropPolicy policy, void *context,
                                       const char **reason);
TuiDragState *tui_drag_new(int enabled);
void tui_drag_free(TuiDragState *state);
TuiResult tui_drag_enable(TuiDragState *state, int enabled);
TuiResult tui_drag_cancel(TuiDragState *state);
TuiDragView tui_drag_view(const TuiDragState *state);
TuiResult tui_drag_render_key(TuiDragState *state, const char *key);
/* Output is set NULL unless this up event produces an owned approval request.
 */
TuiResult tui_drag_tree_pointer(TuiDragState *state, const TuiTree *tree,
                                TuiDragPointer pointer,
                                const TuiDragOptions *options,
                                TuiDropPolicy policy, void *context,
                                TuiDropRequest **output);
TuiResult tui_drag_tabs_pointer(TuiDragState *state, const TuiTabs *tabs,
                                TuiDragPointer pointer,
                                const TuiDragOptions *options,
                                TuiDropPolicy policy, void *context,
                                TuiDropRequest **output);
TuiDragLayout *tui_drag_tree_preview(TuiDragState *state, const TuiTree *tree,
                                     int width, int height);
TuiDragLayout *tui_drag_tabs_preview(TuiDragState *state, const TuiTabs *tabs,
                                     int width, int height);
void tui_drag_layout_free(TuiDragLayout *layout);
TuiResult tui_drag_tree_draw(TuiDragState *state, TuiTree *tree,
                             TuiCanvas *canvas, TuiRect rect, int focused,
                             int ascii);
TuiResult tui_drag_tabs_draw(TuiDragState *state, TuiTabs *tabs,
                             TuiCanvas *canvas, TuiRect rect, int focused,
                             int ascii);

/* Optional incremental input and POSIX terminal session. Runtime models remain
 * platform independent. Decoder feed copies bytes. next/read set output NULL
 * when no complete event is available. Events own key/text; free explicitly.
 * text_length also represents literal NUL bytes in bracketed paste. */
typedef struct {
  const char *key, *text;
  size_t text_length;
  int x, y, button;
} TuiInputEvent;
typedef struct TuiInputDecoder TuiInputDecoder;
TuiInputDecoder *tui_input_decoder_new(void);
void tui_input_decoder_free(TuiInputDecoder *decoder);
TuiResult tui_input_feed(TuiInputDecoder *decoder, const void *bytes,
                         size_t length);
TuiResult tui_input_next(TuiInputDecoder *decoder, int flush_escape,
                         TuiInputEvent **output);
int tui_input_waiting_escape(const TuiInputDecoder *decoder);
void tui_input_event_free(TuiInputEvent *event);
typedef struct {
  int mouse, mouse_motion;
} TuiTerminalOptions;
typedef struct TuiTerminal TuiTerminal;
/* NULL options defaults to mouse enabled, motion disabled. File descriptors are
 * borrowed, never closed. open requires POSIX TTYs; other platforms reject it.
 * Hosts own signals/global keys. Session APIs are not thread safe. */
TuiTerminal *tui_terminal_new(int input_fd, int output_fd,
                              const TuiTerminalOptions *options);
void tui_terminal_free(TuiTerminal *terminal);
TuiResult tui_terminal_open(TuiTerminal *terminal);
TuiResult tui_terminal_close(TuiTerminal *terminal);
TuiResult tui_terminal_size(const TuiTerminal *terminal, int *columns,
                            int *rows);
TuiResult tui_terminal_write(TuiTerminal *terminal, const char *utf8);
TuiResult tui_terminal_read(TuiTerminal *terminal, int timeout_ms,
                            TuiInputEvent **output);

#ifdef __cplusplus
}
#endif
#endif
