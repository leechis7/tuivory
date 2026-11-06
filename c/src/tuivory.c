#include "tuivory.h"
#include "tuivory_data.h"
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char *copy(const char *s) {
  size_t n = strlen(s ? s : "") + 1;
  char *p = malloc(n);
  if (p)
    memcpy(p, s ? s : "", n);
  return p;
}
static int min(int a, int b) { return a < b ? a : b; }
static int max(int a, int b) { return a > b ? a : b; }
static int range(unsigned c, const unsigned (*table)[2], size_t n) {
  size_t lo = 0, hi = n;
  while (lo < hi) {
    size_t m = (lo + hi) / 2;
    if (c < table[m][0])
      hi = m;
    else if (c > table[m][1])
      lo = m + 1;
    else
      return 1;
  }
  return 0;
}
static int decode(const unsigned char *s, size_t size, size_t *pos,
                  unsigned *out) {
  unsigned c;
  int n, i;
  size_t p = *pos;
  if (p >= size)
    return 0;
  c = s[p++];
  if (c < 128) {
    *pos = p;
    *out = c;
    return 1;
  }
  if (c >= 0xf5)
    return 0;
  n = c >= 0xf0 ? 3 : c >= 0xe0 ? 2 : c >= 0xc2 ? 1 : 0;
  if (!n || p + (size_t)n > size)
    return 0;
  c &= (1u << (6 - n)) - 1;
  for (i = 0; i < n; i++) {
    if ((s[p] & 0xc0) != 0x80)
      return 0;
    c = (c << 6) | (s[p++] & 63);
  }
  if (c > 0x10ffff || (c >= 0xd800 && c <= 0xdfff) || (n == 1 && c < 128) ||
      (n == 2 && c < 0x800) || (n == 3 && c < 0x10000))
    return 0;
  *pos = p;
  *out = c;
  return 1;
}
static int cp_width(unsigned c) {
  if (c < 32 || (c >= 127 && c < 160))
    return 1;
  return range(c, tui_zero, sizeof(tui_zero) / sizeof(tui_zero[0]))   ? 0
         : range(c, tui_wide, sizeof(tui_wide) / sizeof(tui_wide[0])) ? 2
                                                                      : 1;
}
enum Gcb {
  G_OTHER,
  G_CR,
  G_LF,
  G_CONTROL,
  G_EXTEND,
  G_ZWJ,
  G_RI,
  G_PREPEND,
  G_SPACING,
  G_L,
  G_V,
  G_T,
  G_LV,
  G_LVT
};
static enum Gcb property(unsigned c) {
#define PROP(name, value)                                                      \
  if (range(c, tui_##name, sizeof(tui_##name) / sizeof(tui_##name[0])))        \
    return value;
  PROP(grapheme_cr, G_CR)
  PROP(grapheme_lf, G_LF)
  PROP(grapheme_control, G_CONTROL)
  PROP(grapheme_extend, G_EXTEND)
  PROP(grapheme_zwj, G_ZWJ)
  PROP(grapheme_regional_indicator, G_RI)
  PROP(grapheme_prepend, G_PREPEND)
  PROP(grapheme_spacingmark, G_SPACING)
  PROP(grapheme_l, G_L)
  PROP(grapheme_v, G_V) PROP(grapheme_t, G_T) PROP(grapheme_lv, G_LV)
      PROP(grapheme_lvt, G_LVT)
#undef PROP
          return G_OTHER;
}
static int pictographic(unsigned c) {
  return range(c, tui_extended_pictographic,
               sizeof(tui_extended_pictographic) /
                   sizeof(tui_extended_pictographic[0]));
}
static int consonant(unsigned c) {
  return range(c, tui_incb_consonant,
               sizeof(tui_incb_consonant) / sizeof(tui_incb_consonant[0]));
}
static int linker(unsigned c) {
  return range(c, tui_incb_linker,
               sizeof(tui_incb_linker) / sizeof(tui_incb_linker[0]));
}
static int incb_extend(unsigned c) {
  return range(c, tui_incb_extend,
               sizeof(tui_incb_extend) / sizeof(tui_incb_extend[0]));
}
static int measure(const char *s, size_t start, size_t end) {
  size_t pos = start;
  int total = 0, cluster_width = 0, last_width = 0, available = 0, virama = 0,
      ri_run = 0;
  unsigned base = 0, cp;
#define IN(name, c)                                                            \
  range(c, tui_##name, sizeof(tui_##name) / sizeof(tui_##name[0]))
  while (pos < end) {
    int w, ri_before = ri_run;
    if (!decode((const unsigned char *)s, end, &pos, &cp))
      return -1;
    if (cp < 32 || (cp >= 127 && cp < 160))
      cp = 32;
    ri_run = cp >= 0x1f1e6 && cp <= 0x1f1ff ? ri_run + 1 : 0;
    if (cp == 0x200d) {
      if (!virama && pos < end) {
        if (!decode((const unsigned char *)s, end, &pos, &cp))
          return -1;
        last_width = 0;
        ri_run = 0;
      }
      continue;
    }
    if (cp == 0xfe0f && available) {
      if (IN(vs16, base))
        cluster_width = 2;
      available = 0;
      continue;
    }
    if (cp == 0xfe0e && available) {
      if (last_width == 2 && IN(vs15, base))
        total--;
      available = 0;
      continue;
    }
    if (cp >= 0x1f1e6 && cp <= 0x1f1ff) {
      if (ri_before % 2) {
        base = cp;
        continue;
      }
    } else if (cp >= 0x1f3fb && cp <= 0x1f3ff && IN(pictographic, base))
      continue;
    w = cp_width(cp);
    if (w) {
      if (virama)
        cluster_width = 2;
      else {
        total += cluster_width;
        cluster_width = w;
      }
      base = cp;
      last_width = w;
      available = 1;
      virama = 0;
    } else if (IN(virama, cp))
      virama = 1;
    else if (available && IN(spacing_mc, cp)) {
      cluster_width = 2;
      available = 0;
      virama = 0;
    } else
      virama = 0;
  }
#undef IN
  return total + cluster_width;
}
static int cluster(const char *s, size_t size, size_t start, size_t *end,
                   int *width) {
  size_t p = start, q;
  unsigned cp;
  enum Gcb previous;
  int w, ri, ep_tail, ep_zwj = 0, incb_base, incb_linker = 0;
  if (!decode((const unsigned char *)s, size, &p, &cp))
    return 0;
  previous = cp < 32 || (cp >= 127 && cp < 160) ? G_OTHER : property(cp);
  w = cp_width(cp);
  ri = previous == G_RI;
  ep_tail = pictographic(cp);
  incb_base = consonant(cp);
  while (p < size) {
    enum Gcb current;
    int join = 0, tail;
    q = p;
    if (!decode((const unsigned char *)s, size, &q, &cp))
      return 0;
    current = cp < 32 || (cp >= 127 && cp < 160) ? G_OTHER : property(cp);
    if (previous == G_CR && current == G_LF)
      join = 1;
    else if (previous == G_CR || previous == G_LF || previous == G_CONTROL ||
             current == G_CR || current == G_LF || current == G_CONTROL)
      join = 0;
    else if (previous == G_L && (current == G_L || current == G_V ||
                                 current == G_LV || current == G_LVT))
      join = 1;
    else if ((previous == G_LV || previous == G_V) &&
             (current == G_V || current == G_T))
      join = 1;
    else if ((previous == G_LVT || previous == G_T) && current == G_T)
      join = 1;
    else if (current == G_EXTEND || current == G_ZWJ || current == G_SPACING ||
             previous == G_PREPEND)
      join = 1;
    else if (consonant(cp) && incb_base && incb_linker)
      join = 1;
    else if (previous == G_ZWJ && ep_zwj && pictographic(cp))
      join = 1;
    else if (previous == G_RI && current == G_RI && ri % 2)
      join = 1;
    if (!join)
      break;
    w = max(w, cp_width(cp));
    if (cp == 0xfe0f || (previous == G_ZWJ && ep_zwj && pictographic(cp)) ||
        (previous == G_RI && current == G_RI))
      w = max(w, 2);
    tail = ep_tail;
    ep_zwj = current == G_ZWJ && tail;
    if (current != G_EXTEND)
      ep_tail = pictographic(cp);
    if (consonant(cp)) {
      incb_base = 1;
      incb_linker = 0;
    } else if (linker(cp)) {
      if (incb_base)
        incb_linker = 1;
    } else if (!incb_extend(cp)) {
      incb_base = 0;
      incb_linker = 0;
    }
    ri = current == G_RI ? (previous == G_RI ? ri + 1 : 1) : 0;
    previous = current;
    p = q;
  }
  *end = p;
  *width = measure(s, start, p);
  return 1;
}
int tui_cells(const char *s) {
  size_t p = 0, end, n;
  int total = 0, w;
  if (!s)
    return -1;
  n = strlen(s);
  if (n > 16 * 1024 * 1024)
    return -1;
  while (p < n) {
    if (!cluster(s, n, p, &end, &w))
      return -1;
    if (total > INT_MAX - w)
      return -1;
    total += w;
    p = end;
  }
  return total;
}
const char *tui_state_role(TuiState s) {
  return s.disabled   ? "disabled"
         : s.invalid  ? "error"
         : s.selected ? "selection"
         : s.edited   ? "edited"
                      : "body";
}
TuiResult tui_state_markers(TuiState s, char out[7]) {
  size_t i = 0;
  if (!out)
    return TUI_INVALID;
  if (s.disabled)
    out[i++] = '-';
  if (s.invalid)
    out[i++] = '!';
  if (s.selected)
    out[i++] = '>';
  if (s.edited)
    out[i++] = '*';
  if (s.busy)
    out[i++] = '~';
  if (s.read_only)
    out[i++] = '=';
  out[i] = 0;
  return TUI_OK;
}
int tui_state_focusable(TuiState s) { return !s.disabled; }
int tui_state_activatable(TuiState s) { return !s.disabled && !s.busy; }
int tui_state_editable(TuiState s) {
  return tui_state_activatable(s) && !s.read_only;
}
TuiResult tui_style(const char *theme, const char *profile, const char *role,
                    int focused, TuiStyle *out) {
  int t, p, r;
  if (!theme || !profile || !role || !out)
    return TUI_INVALID;
  t = !strcmp(theme, "dark")         ? 0
      : !strcmp(theme, "light")      ? 1
      : !strcmp(theme, "blackwhite") ? 2
                                     : -1;
  p = !strcmp(profile, "8")           ? 0
      : !strcmp(profile, "16")        ? 1
      : !strcmp(profile, "256")       ? 2
      : !strcmp(profile, "truecolor") ? 3
                                      : -1;
  for (r = 0; r < 16; r++)
    if (!strcmp(role, tui_roles[r]))
      break;
  if (t < 0 || p < 0 || r == 16)
    return TUI_INVALID;
  {
    const unsigned *v = tui_palette_data[(t * 4 + p) * 16 + r];
    *out =
        (TuiStyle){v[0], v[1], (int)v[2], !strcmp(role, "disabled"), focused};
  }
  return TUI_OK;
}
typedef struct {
  char *text;
  TuiStyle style;
  int owner;
} Cell;
struct TuiCanvas {
  int width, height, cursor_x, cursor_y;
  char theme[12], profile[12];
  Cell *cells;
};
TuiCanvas *tui_canvas_new(int w, int h, const char *theme,
                          const char *profile) {
  TuiCanvas *c;
  TuiStyle style;
  size_t i;
  if (w < 0 || h < 0 || (long long)w * h > 1000000 ||
      tui_style(theme, profile, "surface", 0, &style) != TUI_OK)
    return NULL;
  c = calloc(1, sizeof(*c));
  if (!c)
    return NULL;
  c->width = w;
  c->height = h;
  c->cursor_x = c->cursor_y = -1;
  strcpy(c->theme, theme);
  strcpy(c->profile, profile);
  c->cells = calloc((size_t)w * h + 1, sizeof(Cell));
  if (!c->cells) {
    free(c);
    return NULL;
  }
  for (i = 0; i < (size_t)w * h; i++) {
    c->cells[i].style = style;
    c->cells[i].owner = -1;
  }
  return c;
}
void tui_canvas_free(TuiCanvas *c) {
  size_t i;
  if (!c)
    return;
  for (i = 0; i < (size_t)c->width * c->height; i++)
    free(c->cells[i].text);
  free(c->cells);
  free(c);
}
static void erase(TuiCanvas *c, int x, int y) {
  Cell *row = c->cells + (size_t)y * c->width;
  int start = row[x].owner >= 0 ? row[x].owner : x, end = start + 1, i;
  while (end < c->width && row[end].owner == start)
    end++;
  for (i = start; i < end; i++) {
    free(row[i].text);
    row[i].text = NULL;
    row[i].owner = -1;
  }
}
TuiResult tui_canvas_write(TuiCanvas *c, int x, int y, const char *text,
                           const char *role, int focused, int width) {
  TuiStyle style, base;
  size_t p = 0, end, n;
  int w, limit, i;
  if (!c || !text || width < 0 ||
      tui_style(c->theme, c->profile, role, focused, &style) != TUI_OK ||
      tui_cells(text) < 0)
    return TUI_INVALID;
  if (y < 0 || y >= c->height)
    return TUI_OK;
  limit = min(c->width, x + width);
  n = strlen(text);
  if (!strcmp(role, "body") || !strcmp(role, "hint") || !strcmp(role, "info") ||
      !strcmp(role, "success") || !strcmp(role, "warning") ||
      !strcmp(role, "error") || !strcmp(role, "header")) {
    tui_style(c->theme, c->profile, "surface", 0, &base);
    style.background = base.background;
  }
  while (p < n) {
    char *value;

    if (!cluster(text, n, p, &end, &w))
      return TUI_INVALID;
    if (!w) {
      p = end;
      continue;
    }
    if (x >= limit)
      break;
    if (x < 0 || x + w > limit) {
      for (i = max(0, x); i < min(limit, x + w); i++) {
        erase(c, i, y);
        c->cells[(size_t)y * c->width + i].style = style;
      }
      x += w;
      p = end;
      continue;
    }
    value = malloc(end - p + 1);
    if (!value)
      return TUI_NOMEM;
    {
      size_t source = p, dest = 0;
      while (source < end) {
        size_t begin = source;
        unsigned cp;
        if (!decode((const unsigned char *)text, n, &source, &cp)) {
          free(value);
          return TUI_INVALID;
        }
        if (cp < 32 || (cp >= 127 && cp < 160))
          value[dest++] = ' ';
        else {
          memcpy(value + dest, text + begin, source - begin);
          dest += source - begin;
        }
      }
      value[dest] = 0;
    }
    for (i = x; i < x + w; i++)
      erase(c, i, y);
    c->cells[(size_t)y * c->width + x] = (Cell){value, style, -1};
    for (i = x + 1; i < x + w; i++)
      c->cells[(size_t)y * c->width + i] = (Cell){NULL, style, x};
    x += w;
    p = end;
  }
  return TUI_OK;
}
TuiResult tui_canvas_fill(TuiCanvas *c, TuiRect r, const char *role) {
  char *spaces;
  int y;
  TuiResult result = TUI_OK;
  if (!c || r.width < 0 || r.height < 0 || r.width > 1000000)
    return TUI_INVALID;
  spaces = malloc((size_t)r.width + 1);
  if (!spaces)
    return TUI_NOMEM;
  memset(spaces, ' ', r.width);
  spaces[r.width] = 0;
  for (y = max(0, r.y); y < min(c->height, r.y + r.height); y++) {
    result = tui_canvas_write(c, r.x, y, spaces, role, 0, r.width);
    if (result != TUI_OK)
      break;
  }
  free(spaces);
  return result;
}
TuiRect tui_canvas_panel(TuiCanvas *c, TuiRect r, const char *title,
                         int focused, int ascii) {
  const char **b;
  const char *a[] = {"+", "+", "+", "+", "-", "|"},
             *d[] = {"╔", "╗", "╚", "╝", "═", "║"},
             *s[] = {"┌", "┐", "└", "┘", "─", "│"};
  const char *role = focused ? "focus.border" : "hint";
  int x, y;
  tui_canvas_fill(c, r, "surface");
  if (r.width < 2 || r.height < 2)
    return (TuiRect){r.x, r.y, 0, 0};
  b = ascii ? a : focused ? d : s;
  tui_canvas_write(c, r.x, r.y, b[0], role, 0, 1);
  tui_canvas_write(c, r.x + r.width - 1, r.y, b[1], role, 0, 1);
  tui_canvas_write(c, r.x, r.y + r.height - 1, b[2], role, 0, 1);
  tui_canvas_write(c, r.x + r.width - 1, r.y + r.height - 1, b[3], role, 0, 1);
  for (x = 1; x < r.width - 1; x++) {
    tui_canvas_write(c, r.x + x, r.y, b[4], role, 0, 1);
    tui_canvas_write(c, r.x + x, r.y + r.height - 1, b[4], role, 0, 1);
  }
  for (y = 1; y < r.height - 1; y++) {
    tui_canvas_write(c, r.x, r.y + y, b[5], role, 0, 1);
    tui_canvas_write(c, r.x + r.width - 1, r.y + y, b[5], role, 0, 1);
  }
  tui_canvas_write(c, r.x + 2, r.y, title, role, 0, max(0, r.width - 4));
  return (TuiRect){r.x + 1, r.y + 1, r.width - 2, r.height - 2};
}
void tui_canvas_cursor(TuiCanvas *c, int x, int y, int w) {
  if (!c)
    return;
  if (x >= 0 && x + max(1, w) <= c->width && y >= 0 && y < c->height) {
    c->cursor_x = x;
    c->cursor_y = y;
  } else
    c->cursor_x = c->cursor_y = -1;
}
void tui_string_free(char *s) { free(s); }
typedef struct {
  char *s;
  size_t len, capacity;
  int failed;
} Buffer;
static void append(Buffer *b, const char *s) {
  size_t n = strlen(s), cap;
  char *p;
  if (b->failed)
    return;
  if (b->len + n + 1 > b->capacity) {
    cap = max(128, (int)(b->len + n + 1)) * 2;
    p = realloc(b->s, cap);
    if (!p) {
      b->failed = 1;
      return;
    }
    b->s = p;
    b->capacity = cap;
  }
  memcpy(b->s + b->len, s, n + 1);
  b->len += n;
}
static void color(Buffer *b, unsigned c, int bg) {
  char s[64];
  if (c & 0x1000000)
    snprintf(s, sizeof(s), "%d;2;%u;%u;%u", bg ? 48 : 38, (c >> 16) & 255,
             (c >> 8) & 255, c & 255);
  else if (c < 8)
    snprintf(s, sizeof(s), "%u", (bg ? 40 : 30) + c);
  else if (c < 16)
    snprintf(s, sizeof(s), "%u", (bg ? 100 : 90) + c - 8);
  else
    snprintf(s, sizeof(s), "%d;5;%u", bg ? 48 : 38, c);
  append(b, s);
}
char *tui_canvas_line(const TuiCanvas *c, int y) {
  Buffer b = {0};
  int x;
  if (!c || y < 0 || y >= c->height)
    return NULL;
  append(&b, "");
  for (x = 0; x < c->width; x++) {
    const Cell *cell = &c->cells[(size_t)y * c->width + x];
    if (cell->owner < 0)
      append(&b, cell->text ? cell->text : " ");
  }
  if (b.failed) {
    free(b.s);
    return NULL;
  }
  return b.s;
}
char *tui_canvas_ansi(const TuiCanvas *c) {
  Buffer b = {0};
  int x, y;
  char seq[64];
  if (!c)
    return NULL;
  append(&b, "\033[?25l");
  for (y = 0; y < c->height; y++) {
    snprintf(seq, sizeof(seq), "\033[%d;1H", y + 1);
    append(&b, seq);
    for (x = 0; x < c->width; x++) {
      const Cell *cell = &c->cells[(size_t)y * c->width + x];
      if (cell->owner >= 0)
        continue;
      append(&b, "\033[0;");
      color(&b, cell->style.foreground, 0);
      append(&b, ";");
      color(&b, cell->style.background, 1);
      if (cell->style.bold)
        append(&b, ";1");
      if (cell->style.dim)
        append(&b, ";2");
      if (cell->style.underline)
        append(&b, ";4");
      append(&b, "m");
      append(&b, cell->text ? cell->text : " ");
    }
  }
  append(&b, "\033[0m");
  if (c->cursor_x >= 0) {
    snprintf(seq, sizeof(seq), "\033[%d;%dH\033[?25h", c->cursor_y + 1,
             c->cursor_x + 1);
    append(&b, seq);
  }
  if (b.failed) {
    free(b.s);
    return NULL;
  }
  return b.s;
}
struct TuiTree {
  TuiNode *nodes;
  int *parent, *depth, *branch, *expanded;
  size_t count;
  int selected, scroll, horizontal;
};
void tui_tree_free(TuiTree *t) {
  size_t i;
  if (!t)
    return;
  for (i = 0; i < t->count; i++) {
    free((void *)t->nodes[i].id);
    free((void *)t->nodes[i].name);
    free((void *)t->nodes[i].parent);
    free((void *)t->nodes[i].secondary);
    free((void *)t->nodes[i].icon);
    free((void *)t->nodes[i].ascii_icon);
  }
  free(t->nodes);
  free(t->parent);
  free(t->depth);
  free(t->branch);
  free(t->expanded);
  free(t);
}
TuiTree *tui_tree_new(const TuiNode *nodes, size_t count) {
  TuiTree *t;
  size_t i, j;
  int stack[129], nstack = 0;
  if ((count && !nodes) || count > 1000000)
    return NULL;
  t = calloc(1, sizeof(*t));
  if (!t)
    return NULL;
  t->nodes = calloc(count + 1, sizeof(TuiNode));
  t->parent = calloc(count + 1, sizeof(int));
  t->depth = calloc(count + 1, sizeof(int));
  t->branch = calloc(count + 1, sizeof(int));
  t->expanded = calloc(count + 1, sizeof(int));
  if (!t->nodes || !t->parent || !t->depth || !t->branch || !t->expanded) {
    tui_tree_free(t);
    return NULL;
  }
  t->count = count;
  t->selected = count ? 0 : -1;
  for (i = 0; i < count; i++) {
    TuiNode *n = &t->nodes[i];
    if (!nodes[i].id || !*nodes[i].id)
      goto fail;
    for (j = 0; j < i; j++)
      if (!strcmp(nodes[i].id, t->nodes[j].id))
        goto fail;
    n->id = copy(nodes[i].id);
    n->name = copy(nodes[i].name);
    n->parent = copy(nodes[i].parent);
    n->secondary = copy(nodes[i].secondary);
    n->icon = copy(nodes[i].icon);
    n->ascii_icon = copy(nodes[i].ascii_icon);
    n->has_count = nodes[i].has_count;
    n->count = nodes[i].count;
    t->branch[i] = nodes[i].branch;
    if (!n->id || !n->name || !n->parent || !n->secondary || !n->icon ||
        !n->ascii_icon)
      goto fail;
    t->parent[i] = -1;
    if (*n->parent) {
      for (j = 0; j < (size_t)nstack; j++)
        if (!strcmp(t->nodes[stack[j]].id, n->parent))
          break;
      if (j == (size_t)nstack)
        goto fail;
      nstack = (int)j + 1;
      t->parent[i] = stack[j];
      t->branch[stack[j]] = 1;
    } else
      nstack = 0;
    if (nstack > 128)
      goto fail;
    t->depth[i] = nstack;
    stack[nstack++] = (int)i;
  }
  return t;
fail:
  tui_tree_free(t);
  return NULL;
}
static int visible(const TuiTree *t, int i) {
  int p = t->parent[i];
  while (p >= 0) {
    if (!t->expanded[p])
      return 0;
    p = t->parent[p];
  }
  return 1;
}
size_t tui_tree_visible(const TuiTree *t, const char **ids, size_t cap) {
  size_t i, n = 0;
  if (!t)
    return 0;
  for (i = 0; i < t->count; i++)
    if (visible(t, (int)i)) {
      if (ids && n < cap)
        ids[n] = t->nodes[i].id;
      n++;
    }
  return n;
}
static int reconcile(TuiTree *t, int height) {
  int i, index = 0, count = 0;
  while (t->selected >= 0 && !visible(t, t->selected))
    t->selected = t->parent[t->selected];
  if (t->selected < 0 && t->count)
    t->selected = 0;
  for (i = 0; i < (int)t->count; i++)
    if (visible(t, i)) {
      if (i == t->selected)
        index = count;
      count++;
    }
  height = max(1, height);
  t->scroll = max(0, min(t->scroll, count - height));
  if (index < t->scroll)
    t->scroll = index;
  if (index >= t->scroll + height)
    t->scroll = index - height + 1;
  return index;
}
const char *tui_tree_selected(const TuiTree *t) {
  return t && t->selected >= 0 ? t->nodes[t->selected].id : "";
}
int tui_tree_expanded(const TuiTree *t, const char *id) {
  size_t i;
  if (t && id)
    for (i = 0; i < t->count; i++)
      if (!strcmp(t->nodes[i].id, id))
        return t->expanded[i];
  return 0;
}
int tui_tree_scroll(const TuiTree *t) { return t ? t->scroll : 0; }
int tui_tree_horizontal(const TuiTree *t) { return t ? t->horizontal : 0; }
TuiEvent tui_tree_handle(TuiTree *t, const char *action, int height) {
  int old, index, target, count = 0, i, at = 0;
  TuiEvent none = {"", ""};
  if (!t || !action || !t->count)
    return none;
  index = reconcile(t, height);
  old = t->selected;
  target = index;
  for (i = 0; i < (int)t->count; i++)
    if (visible(t, i))
      count++;
  if (!strcmp(action, "up"))
    target--;
  else if (!strcmp(action, "down"))
    target++;
  else if (!strcmp(action, "home"))
    target = 0;
  else if (!strcmp(action, "end"))
    target = count - 1;
  else if (!strcmp(action, "page_up"))
    target -= max(1, height);
  else if (!strcmp(action, "page_down"))
    target += max(1, height);
  else if (!strcmp(action, "pan_left"))
    t->horizontal = max(0, t->horizontal - 4);
  else if (!strcmp(action, "pan_right"))
    t->horizontal = min(65535, t->horizontal + 4);
  else if (!strcmp(action, "activate"))
    return (TuiEvent){"activate", t->nodes[old].id};
  else if (!strcmp(action, "left")) {
    if (t->expanded[old]) {
      t->expanded[old] = 0;
      reconcile(t, height);
      return (TuiEvent){"collapse", t->nodes[old].id};
    }
    if (t->parent[old] >= 0)
      t->selected = t->parent[old];
  } else if ((!strcmp(action, "right") || !strcmp(action, "toggle")) &&
             t->branch[old]) {
    if (!strcmp(action, "toggle") && t->expanded[old]) {
      t->expanded[old] = 0;
      reconcile(t, height);
      return (TuiEvent){"collapse", t->nodes[old].id};
    }
    if (!t->expanded[old]) {
      t->expanded[old] = 1;
      reconcile(t, height);
      return (TuiEvent){"expand", t->nodes[old].id};
    }
    if (old + 1 < (int)t->count && t->parent[old + 1] == old)
      target++;
  }
  target = max(0, min(count - 1, target));
  if (target != index) {
    for (i = 0; i < (int)t->count; i++)
      if (visible(t, i)) {
        if (at++ == target) {
          t->selected = i;
          break;
        }
      }
  }
  reconcile(t, height);
  return old != t->selected ? (TuiEvent){"select", t->nodes[t->selected].id}
                            : none;
}
TuiEvent tui_tree_click(TuiTree *t, int x, int y, int height) {
  int i, index = 0, old;
  TuiEvent none = {"", ""};
  if (!t || y < 0 || y >= height)
    return none;
  reconcile(t, height);
  old = t->selected;
  for (i = 0; i < (int)t->count; i++)
    if (visible(t, i)) {
      if (index++ == t->scroll + y) {
        t->selected = i;
        if (x >= 2 && x + t->horizontal == 2 + 2 * t->depth[i]) {
          TuiEvent e = tui_tree_handle(t, "toggle", height);
          if (*e.kind)
            return e;
        }
        return old != i ? (TuiEvent){"select", t->nodes[i].id} : none;
      }
    }
  return none;
}
TuiResult tui_tree_draw(TuiTree *t, TuiCanvas *c, TuiRect r, int focused,
                        int ascii) {
  int i, index = 0, y = 0;
  TuiResult result;
  if (!t || !c)
    return TUI_INVALID;
  result = tui_canvas_fill(c, r, "surface");
  if (result != TUI_OK)
    return result;
  reconcile(t, r.height);
  for (i = 0; i < (int)t->count && y < r.height; i++)
    if (visible(t, i)) {
      Buffer b = {0};
      int k;
      char count[64];
      if (index++ < t->scroll)
        continue;
      append(&b, t->selected == i ? "> " : "  ");
      for (k = 0; k < t->depth[i]; k++)
        append(&b, "  ");
      append(&b, t->branch[i] ? t->expanded[i] ? ascii ? "v" : "▾"
                                : ascii        ? ">"
                                               : "▸"
                              : " ");
      append(&b, " ");
      {
        const char *icon = ascii ? t->nodes[i].ascii_icon : t->nodes[i].icon;
        if (*icon) {
          append(&b, icon);
          append(&b, " ");
        }
      }
      append(&b, t->nodes[i].name);
      if (*t->nodes[i].secondary) {
        append(&b, "  ");
        append(&b, t->nodes[i].secondary);
      }
      if (t->nodes[i].has_count) {
        snprintf(count, sizeof(count), " (%llu)", t->nodes[i].count);
        append(&b, count);
      }
      if (b.failed) {
        free(b.s);
        return TUI_NOMEM;
      }
      {
        Buffer rendered = {0};
        size_t start = 2, end, length = strlen(b.s);
        int skipped = 0, used = 0, glyph_width;
        int body_width = max(0, r.width - 2), truncated;
        while (start < length && skipped < t->horizontal) {
          if (!cluster(b.s, length, start, &end, &glyph_width)) {
            free(b.s);
            return TUI_INVALID;
          }
          skipped += glyph_width;
          start = end;
        }
        truncated = tui_cells(b.s + start) > body_width;
        append(&rendered, t->selected == i ? "> " : "  ");
        while (start < length) {
          char saved;
          if (!cluster(b.s, length, start, &end, &glyph_width)) {
            free(rendered.s);
            free(b.s);
            return TUI_INVALID;
          }
          if (used + glyph_width > body_width - (truncated && body_width > 0))
            break;
          saved = b.s[end];
          b.s[end] = 0;
          append(&rendered, b.s + start);
          b.s[end] = saved;
          used += glyph_width;
          start = end;
        }
        if (truncated && body_width > 0)
          append(&rendered, "~");
        if (rendered.failed) {
          free(rendered.s);
          free(b.s);
          return TUI_NOMEM;
        }
        result = tui_canvas_write(c, r.x, r.y + y, rendered.s,
                                  t->selected == i ? "selection" : "body",
                                  focused && t->selected == i, r.width);
        free(rendered.s);
      }
      free(b.s);
      if (result != TUI_OK)
        return result;
      y++;
    }
  return TUI_OK;
}
static char *clean_copy(const char *s) {
  size_t n, pos = 0, dest = 0;
  char *out;
  if (!s || tui_cells(s) < 0)
    return NULL;
  n = strlen(s);
  out = malloc(n + 1);
  if (!out)
    return NULL;
  while (pos < n) {
    size_t start = pos;
    unsigned cp;
    if (!decode((const unsigned char *)s, n, &pos, &cp)) {
      free(out);
      return NULL;
    }
    if (cp < 32 || (cp >= 127 && cp < 160))
      out[dest++] = ' ';
    else {
      memcpy(out + dest, s + start, pos - start);
      dest += pos - start;
    }
  }
  out[dest] = 0;
  return out;
}
char *tui_clip(const char *text, int width, int ellipsis) {
  Buffer b = {0};
  size_t pos = 0, end, n;
  int used = 0, w, total;
  if (!text || width < 0 || (total = tui_cells(text)) < 0)
    return NULL;
  append(&b, "");
  n = strlen(text);
  while (pos < n) {
    char *part;
    if (!cluster(text, n, pos, &end, &w)) {
      free(b.s);
      return NULL;
    }
    if (used + w > width - (ellipsis && total > width && width > 0))
      break;
    part = malloc(end - pos + 1);
    if (!part) {
      free(b.s);
      return NULL;
    }
    memcpy(part, text + pos, end - pos);
    part[end - pos] = 0;
    {
      char *safe = clean_copy(part);
      free(part);
      if (!safe) {
        free(b.s);
        return NULL;
      }
      append(&b, safe);
      free(safe);
    }
    used += w;
    pos = end;
  }
  if (ellipsis && total > width && width > 0)
    append(&b, "~");
  if (b.failed) {
    free(b.s);
    return NULL;
  }
  return b.s;
}
struct TuiTabs {
  TuiTab *items;
  size_t count, view_count;
  int active, focused, first;
  TuiTabCell *views;
};
static void tabs_clear_views(TuiTabs *t) {
  size_t i;
  for (i = 0; i < t->view_count; i++)
    free((void *)t->views[i].text);
  t->view_count = 0;
}
void tui_tabs_free(TuiTabs *t) {
  size_t i;
  if (!t)
    return;
  tabs_clear_views(t);
  for (i = 0; i < t->count; i++) {
    free((void *)t->items[i].id);
    free((void *)t->items[i].title);
  }
  free(t->items);
  free(t->views);
  free(t);
}
static void tabs_reconcile(TuiTabs *t) {
  int first = -1;
  size_t i;
  for (i = 0; i < t->count; i++)
    if (!t->items[i].disabled) {
      first = (int)i;
      break;
    }
  if (t->active < 0 || (size_t)t->active >= t->count ||
      t->items[t->active].disabled)
    t->active = first;
  if (t->focused < 0 || (size_t)t->focused >= t->count ||
      t->items[t->focused].disabled)
    t->focused = t->active;
}
TuiTabs *tui_tabs_new(const TuiTab *items, size_t count) {
  TuiTabs *t;
  size_t i, j;
  if ((count && !items) || count > 1000000)
    return NULL;
  t = calloc(1, sizeof(*t));
  if (!t)
    return NULL;
  t->active = t->focused = -1;
  t->items = calloc(count + 1, sizeof(TuiTab));
  t->views = calloc(count + 1, sizeof(TuiTabCell));
  if (!t->items || !t->views) {
    tui_tabs_free(t);
    return NULL;
  }
  t->count = count;
  for (i = 0; i < count; i++) {
    if (!items[i].id || !*items[i].id ||
        tui_cells(items[i].title ? items[i].title : "") < 0) {
      tui_tabs_free(t);
      return NULL;
    }
    for (j = 0; j < i; j++)
      if (!strcmp(items[i].id, t->items[j].id)) {
        tui_tabs_free(t);
        return NULL;
      }
    t->items[i] = items[i];
    t->items[i].id = copy(items[i].id);
    t->items[i].title = copy(items[i].title);
    if (!t->items[i].id || !t->items[i].title) {
      tui_tabs_free(t);
      return NULL;
    }
  }
  tabs_reconcile(t);
  return t;
}
const char *tui_tabs_active(const TuiTabs *t) {
  return t && t->active >= 0 ? t->items[t->active].id : "";
}
const char *tui_tabs_focused(const TuiTabs *t) {
  return t && t->focused >= 0 ? t->items[t->focused].id : "";
}
int tui_tabs_first(const TuiTabs *t) { return t ? t->first : 0; }
TuiEvent tui_tabs_handle(TuiTabs *t, const char *action) {
  TuiEvent none = {"", ""};
  int i, target;
  if (!t || !action)
    return none;
  tabs_reconcile(t);
  if (t->focused < 0)
    return none;
  i = target = t->focused;
  if (!strcmp(action, "activate")) {
    t->active = i;
    return (TuiEvent){"activate", t->items[i].id};
  }
  if (!strcmp(action, "close"))
    return t->items[i].closable ? (TuiEvent){"close", t->items[i].id} : none;
  if (!strcmp(action, "first")) {
    for (target = 0; target < (int)t->count && t->items[target].disabled;
         target++) {
    };
  } else if (!strcmp(action, "last")) {
    for (target = (int)t->count - 1; target >= 0 && t->items[target].disabled;
         target--) {
    };
  } else if (!strcmp(action, "previous")) {
    target = i - 1;
    while (target >= 0 && t->items[target].disabled)
      target--;
    if (target < 0)
      target = i;
  } else if (!strcmp(action, "next")) {
    target = i + 1;
    while (target < (int)t->count && t->items[target].disabled)
      target++;
    if (target == (int)t->count)
      target = i;
  }
  if (target != i) {
    t->focused = target;
    return (TuiEvent){"focus", t->items[target].id};
  }
  return none;
}
static int tab_width(const TuiTab *item) {
  return min(24, max(6, tui_cells(item->title) + 5));
}
static int tab_sum(const TuiTabs *t, int start, int target) {
  int width = 0, i;
  for (i = start; i <= target; i++)
    width += tab_width(&t->items[i]);
  return width;
}
TuiResult tui_tabs_layout(TuiTabs *t, int width, TuiTabCell *out,
                          size_t capacity, size_t *count) {
  int target, x;
  size_t i;
  if (!t || !count || width < 0 || (!out && capacity))
    return TUI_INVALID;
  *count = 0;
  tabs_clear_views(t);
  tabs_reconcile(t);
  if (width <= 2 || !t->count)
    return TUI_OK;
  target = max(0, t->focused);
  t->first = min(max(0, t->first), target);
  while (t->first < target && tab_sum(t, t->first, target) > width - 2)
    t->first++;
  while (t->first > 0 && tab_sum(t, t->first - 1, target) <= width - 2)
    t->first--;
  x = 1;
  for (i = (size_t)t->first; i < t->count && x < width - 1; i++) {
    const TuiTab *item = &t->items[i];
    int w = min(tab_width(item), width - 1 - x), active = (int)i == t->active,
        focused = (int)i == t->focused;
    Buffer b = {0};
    char *label, *text;
    int suffix = (item->edited ? 2 : 0) + (item->closable ? 2 : 0);
    if (w < 4 && t->view_count)
      break;
    label = tui_clip(item->title, max(0, w - 3 - suffix), 1);
    if (!label)
      return TUI_NOMEM;
    append(&b, focused ? ">" : " ");
    append(&b, active ? "[" : " ");
    append(&b, label);
    free(label);
    if (item->edited)
      append(&b, " *");
    if (item->closable)
      append(&b, " x");
    append(&b, active ? "]" : " ");
    if (b.failed) {
      free(b.s);
      return TUI_NOMEM;
    }
    text = tui_clip(b.s, w, 1);
    free(b.s);
    if (!text)
      return TUI_NOMEM;
    t->views[t->view_count++] =
        (TuiTabCell){item->id, text, x, w, active, focused, item->disabled};
    x += w;
  }
  for (i = 0; out && i < capacity && i < t->view_count; i++)
    out[i] = t->views[i];
  *count = t->view_count;
  return TUI_OK;
}
TuiEvent tui_tabs_click(TuiTabs *t, int x, int width) {
  TuiEvent none = {"", ""};
  size_t count, i;
  if (!t || x < 0 || x >= width ||
      tui_tabs_layout(t, width, NULL, 0, &count) != TUI_OK)
    return none;
  if (x == 0 && t->first > 0)
    return tui_tabs_handle(t, "previous");
  if (x == width - 1 && (size_t)t->first + count < t->count)
    return tui_tabs_handle(t, "next");
  for (i = 0; i < count; i++) {
    TuiTabCell *v = &t->views[i];
    if (x >= v->start && x < v->start + v->width && !v->disabled) {
      size_t n = strlen(v->text);
      int close = n >= 2 && (!strcmp(v->text + n - 2, "x]") ||
                             !strcmp(v->text + n - 2, "x "));
      size_t j;
      for (j = 0; j < t->count; j++)
        if (!strcmp(t->items[j].id, v->id))
          break;
      t->focused = (int)j;
      if (close && t->items[j].closable &&
          x == v->start + tui_cells(v->text) - 2)
        return (TuiEvent){"close", v->id};
      t->active = t->focused;
      return (TuiEvent){"activate", v->id};
    }
  }
  return none;
}
TuiResult tui_tabs_draw(TuiTabs *t, TuiCanvas *c, TuiRect r, int focused) {
  size_t n, i;
  TuiResult result;
  if (!t || !c)
    return TUI_INVALID;
  result = tui_canvas_fill(c, r, "surface");
  if (result != TUI_OK)
    return result;
  result = tui_tabs_layout(t, r.width, NULL, 0, &n);
  if (result != TUI_OK)
    return result;
  if (t->first > 0)
    tui_canvas_write(c, r.x, r.y, "<", "hint", 0, 1);
  if ((size_t)t->first + n < t->count && r.width > 0)
    tui_canvas_write(c, r.x + r.width - 1, r.y, ">", "hint", 0, 1);
  for (i = 0; i < n; i++) {
    const TuiTabCell *v = &t->views[i];
    char spaces[25];
    memset(spaces, ' ', v->width);
    spaces[v->width] = 0;
    result = tui_canvas_write(c, r.x + v->start, r.y, spaces,
                              v->disabled ? "disabled"
                              : v->active ? "selection"
                                          : "body",
                              focused && v->focused, v->width);
    if (result != TUI_OK)
      return result;
    result = tui_canvas_write(c, r.x + v->start, r.y, v->text,
                              v->disabled ? "disabled"
                              : v->active ? "selection"
                                          : "body",
                              focused && v->focused, v->width);
    if (result != TUI_OK)
      return result;
  }
  return TUI_OK;
}
TuiSplitLayout tui_split_layout(TuiSplit s, int total) {
  int a = max(1, s.first_min), b = max(1, s.second_min), first;
  if (total < 0)
    return (TuiSplitLayout){0, 0, 0, 1};
  if ((long long)total < (long long)a + b + 1)
    return (TuiSplitLayout){0, 0, total, 1};
  first = min(total - 1 - b,
              max(a, s.preferred > 0 ? s.preferred : (total - 1) / 2));
  return (TuiSplitLayout){first, 1, total - first - 1, 0};
}
int tui_split_resize(TuiSplit *s, int total, int position) {
  TuiSplitLayout old;
  if (!s)
    return 0;
  old = tui_split_layout(*s, total);
  if (old.compact)
    return 0;
  s->preferred = min(total - 1 - max(1, s->second_min),
                     max(max(1, s->first_min), position));
  return s->preferred != old.first;
}
struct TuiLine {
  TuiLineRun *runs;
  size_t count, capacity, omitted;
  int width;
};
static int line_add(TuiLine *line, const char *text, const char *role,
                    const char *id) {
  TuiLineRun run;
  TuiLineRun *next;
  size_t cap;
  if (line->count == line->capacity) {
    cap = line->capacity ? line->capacity * 2 : 8;
    next = realloc(line->runs, cap * sizeof(*next));
    if (!next)
      return 0;
    line->runs = next;
    line->capacity = cap;
  }
  run = (TuiLineRun){clean_copy(text), copy(role && *role ? role : "body"),
                     copy(id), line->width, tui_cells(text)};
  if (!run.text || !run.role || !run.id || run.width < 0) {
    free((void *)run.text);
    free((void *)run.role);
    free((void *)run.id);
    return 0;
  }
  line->runs[line->count++] = run;
  line->width += run.width;
  return 1;
}
void tui_line_free(TuiLine *line) {
  size_t i;
  if (!line)
    return;
  for (i = 0; i < line->count; i++) {
    free((void *)line->runs[i].text);
    free((void *)line->runs[i].role);
    free((void *)line->runs[i].id);
  }
  free(line->runs);
  free(line);
}
size_t tui_line_count(const TuiLine *line) { return line ? line->count : 0; }
size_t tui_line_omitted(const TuiLine *line) {
  return line ? line->omitted : 0;
}
TuiLineRun tui_line_run(const TuiLine *line, size_t index) {
  return line && index < line->count ? line->runs[index]
                                     : (TuiLineRun){"", "body", "", 0, 0};
}
const char *tui_line_hit(const TuiLine *line, int x) {
  size_t i;
  if (line)
    for (i = 0; i < line->count; i++)
      if (x >= line->runs[i].start &&
          x < line->runs[i].start + line->runs[i].width)
        return line->runs[i].id;
  return "";
}
char *tui_line_text(const TuiLine *line) {
  Buffer b = {0};
  size_t i;
  if (!line)
    return NULL;
  append(&b, "");
  for (i = 0; i < line->count; i++)
    append(&b, line->runs[i].text);
  if (b.failed) {
    free(b.s);
    return NULL;
  }
  return b.s;
}
TuiResult tui_line_draw(const TuiLine *line, TuiCanvas *c, TuiRect r) {
  size_t i;
  TuiResult result;
  if (!line || !c)
    return TUI_INVALID;
  result = tui_canvas_fill(c, r, "surface");
  if (result != TUI_OK)
    return result;
  for (i = 0; i < line->count; i++) {
    const TuiLineRun *v = &line->runs[i];
    result = tui_canvas_write(c, r.x + v->start, r.y, v->text, v->role, 0,
                              max(0, r.width - v->start));
    if (result != TUI_OK)
      return result;
  }
  return TUI_OK;
}
static char *tail_text(const char *text, int width) {
  int total = tui_cells(text), removed = 0, w;
  size_t pos = 0, end, n;
  if (total < 0 || width < 0)
    return NULL;
  if (total <= width)
    return copy(text);
  if (width == 0)
    return copy("");
  n = strlen(text);
  while (pos < n && total - removed > width - 1) {
    if (!cluster(text, n, pos, &end, &w))
      return NULL;
    removed += w;
    pos = end;
  }
  {
    Buffer b = {0};
    append(&b, "~");
    append(&b, text + pos);
    if (b.failed) {
      free(b.s);
      return NULL;
    }
    return b.s;
  }
}
TuiLine *tui_breadcrumbs(const TuiPathItem *items, size_t count, int width) {
  TuiLine *line;
  size_t i;
  long long full;
  char *tail;
  const char *prefix = "";
  if ((count && !items) || count > 1000000 || width < 0)
    return NULL;
  line = calloc(1, sizeof(*line));
  if (!line)
    return NULL;
  if (!count || !width)
    return line;
  full = 3LL * (long long)(count - 1);
  for (i = 0; i < count; i++) {
    int n = tui_cells(items[i].label);
    if (n < 0)
      goto fail;
    full += n;
  }
  if (full <= width) {
    for (i = 0; i < count; i++) {
      if (i && !line_add(line, " / ", "hint", ""))
        goto fail;
      if (!line_add(line, items[i].label, i + 1 == count ? "body" : "hint",
                    items[i].id))
        goto fail;
    }
    return line;
  }
  if (count > 2 &&
      tui_cells(items[0].label) + 9 + tui_cells(items[count - 1].label) <=
          width) {
    if (!line_add(line, items[0].label, "hint", items[0].id))
      goto fail;
    prefix = " / ... / ";
  } else if (count > 1 && width >= 7)
    prefix = "... / ";
  if (!line_add(line, prefix, "hint", ""))
    goto fail;
  tail = tail_text(items[count - 1].label, width - line->width);
  if (!tail)
    goto fail;
  {
    int ok = line_add(line, tail, "body", items[count - 1].id);
    free(tail);
    if (!ok)
      goto fail;
  }
  return line;
fail:
  tui_line_free(line);
  return NULL;
}
TuiLine *tui_status_line(const TuiStatusItem *items, size_t count, int width) {
  TuiLine *line;
  size_t *order, i, j, included = 0;
  if ((count && !items) || count > 1000000 || width < 0)
    return NULL;
  line = calloc(1, sizeof(*line));
  if (!line)
    return NULL;
  line->omitted = count;
  if (!width || !count)
    return line;
  order = malloc(count * sizeof(size_t));
  if (!order) {
    tui_line_free(line);
    return NULL;
  }
  for (i = 0; i < count; i++) {
    if (!items[i].text || !items[i].role || tui_cells(items[i].text) < 0)
      goto fail;
    order[i] = i;
    for (j = i;
         j > 0 && items[order[j]].priority > items[order[j - 1]].priority;
         j--) {
      size_t tmp = order[j];
      order[j] = order[j - 1];
      order[j - 1] = tmp;
    }
  }
  for (i = 0; i < count; i++) {
    const TuiStatusItem *item = &items[order[i]];
    char marker[32], *text, *clipped;
    int reserve = 0, needed;
    const char *sep = included ? " | " : "",
               *prefix = !strcmp(item->role, "error") ||
                                 !strcmp(item->role, "warning")
                             ? "! "
                         : !strcmp(item->role, "edited")  ? "* "
                         : !strcmp(item->role, "success") ? "+ "
                         : !strcmp(item->role, "info")    ? "i "
                                                          : "";
    Buffer b = {0};
    if (i + 1 < count) {
      snprintf(marker, sizeof(marker), " +%zu", count - i - 1);
      reserve = (int)strlen(marker);
    }
    append(&b, prefix);
    append(&b, item->text);
    if (b.failed) {
      free(b.s);
      goto fail;
    }
    text = b.s;
    needed = tui_cells(sep) + tui_cells(text);
    if (needed + reserve > width - line->width) {
      int available;
      if (included) {
        free(text);
        break;
      }
      available = width - reserve > 0 ? width - reserve : width;
      if (available == 1 && *prefix) {
        char one[2] = {prefix[0], 0};
        clipped = copy(one);
      } else
        clipped = tui_clip(text, available, 1);
      free(text);
      if (!clipped)
        goto fail;
      text = clipped;
      sep = "";
    }
    if (*sep && !line_add(line, sep, "hint", "")) {
      free(text);
      goto fail;
    }
    if (!line_add(line, text, item->role, item->id)) {
      free(text);
      goto fail;
    }
    free(text);
    included++;
    if (needed + reserve > width)
      break;
  }
  line->omitted = count - included;
  if (line->omitted) {
    char marker[32];
    snprintf(marker, sizeof(marker), " +%zu", line->omitted);
    if (line->width + (int)strlen(marker) <= width &&
        !line_add(line, marker, "hint", ""))
      goto fail;
  }
  free(order);
  return line;
fail:
  free(order);
  tui_line_free(line);
  return NULL;
}
