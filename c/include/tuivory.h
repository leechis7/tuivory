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
#ifdef __cplusplus
}
#endif
#endif
