#include "tuivory.h"
#include "tuivory_data.h"
#include "tuivory_fold.h"
#include "tuivory_sql_words.h"
#include "tuivory_syntax_unicode.h"
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
static long long min64(long long a, long long b) { return a < b ? a : b; }
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
  PROP(grapheme_v, G_V)
  PROP(grapheme_t, G_T)
  PROP(grapheme_lv, G_LV)
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
static int cluster_mode(const char *s, size_t size, size_t start, size_t *end,
                        int *width, int raw) {
  size_t p = start, q;
  unsigned cp;
  enum Gcb previous;
  int w, ri, ep_tail, ep_zwj = 0, incb_base, incb_linker = 0;
  if (!decode((const unsigned char *)s, size, &p, &cp))
    return 0;
  previous =
      !raw && (cp < 32 || (cp >= 127 && cp < 160)) ? G_OTHER : property(cp);
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
    current =
        !raw && (cp < 32 || (cp >= 127 && cp < 160)) ? G_OTHER : property(cp);
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
static int cluster(const char *s, size_t n, size_t p, size_t *end, int *w) {
  return cluster_mode(s, n, p, end, w, 0);
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
    *out = (TuiStyle){v[0],    v[1], (int)v[2], !strcmp(role, "disabled"),
                      focused, 0};
  }
  return TUI_OK;
}
static int plain_text_role(const char *role) {
  return role && (!strcmp(role, "body") || !strcmp(role, "hint") ||
                  !strcmp(role, "disabled") || !strcmp(role, "info") ||
                  !strcmp(role, "success") || !strcmp(role, "warning") ||
                  !strcmp(role, "error"));
}
static int style_rgb(unsigned color, int out[3]) {
  static const int ansi[16][3] = {
      {0, 0, 0},       {128, 0, 0},   {0, 128, 0},   {128, 128, 0},
      {0, 0, 128},     {128, 0, 128}, {0, 128, 128}, {192, 192, 192},
      {128, 128, 128}, {255, 0, 0},   {0, 255, 0},   {255, 255, 0},
      {0, 0, 255},     {255, 0, 255}, {0, 255, 255}, {255, 255, 255}};
  if (color & 0x1000000) {
    if (color > 0x1ffffff)
      return 0;
    out[0] = (color >> 16) & 255;
    out[1] = (color >> 8) & 255;
    out[2] = color & 255;
  } else if (color > 255)
    return 0;
  else if (color < 16) {
    out[0] = ansi[color][0];
    out[1] = ansi[color][1];
    out[2] = ansi[color][2];
  } else if (color >= 232)
    out[0] = out[1] = out[2] = 8 + (color - 232) * 10;
  else {
    static const int cube[] = {0, 95, 135, 175, 215, 255};
    unsigned n = color - 16;
    out[0] = cube[n / 36];
    out[1] = cube[(n / 6) % 6];
    out[2] = cube[n % 6];
  }
  return 1;
}
static double style_luminance(unsigned color) {
  int rgb[3] = {0};
  style_rgb(color, rgb);
  return .2126 * tui_luminance[rgb[0]] + .7152 * tui_luminance[rgb[1]] +
         .0722 * tui_luminance[rgb[2]];
}
static double style_contrast(unsigned a, unsigned b) {
  double x = style_luminance(a), y = style_luminance(b);
  return ((x > y ? x : y) + .05) / ((x < y ? x : y) + .05);
}
TuiResult tui_text_on_surface(const char *theme, const char *profile,
                              const char *role, const char *surface,
                              int focused, TuiStyle *out) {
  TuiStyle text, base;
  if (!out || !role || !surface ||
      tui_style(theme, profile, role, 0, &text) != TUI_OK ||
      tui_style(theme, profile, surface, 0, &base) != TUI_OK)
    return TUI_INVALID;
  double current = style_contrast(text.foreground, base.background);
  text.background = base.background;
  if (current < (!strcmp(role, "disabled") ? 2 : 4.5) &&
      style_contrast(base.foreground, base.background) > current)
    text.foreground = base.foreground;
  if (!strcmp(role, "disabled")) {
    text.bold = 0;
    text.dim = 1;
  }
  text.underline = !!focused && strcmp(role, "disabled") != 0;
  *out = text;
  return TUI_OK;
}
TuiResult tui_control_on_surface(const char *theme, const char *profile,
                                 TuiState state, const char *surface,
                                 int focused, TuiStyle *out) {
  const char *role = tui_state_role(state);
  return plain_text_role(role)
             ? tui_text_on_surface(theme, profile, role, surface,
                                   focused && !state.disabled, out)
             : tui_style(theme, profile, role, focused && !state.disabled, out);
}
typedef struct {
  char *text;
  TuiStyle style;
  int owner;
} Cell;
struct TuiCanvas {
  int width, height, cursor_x, cursor_y, cursor_width;
  char theme[12], profile[12], surface[32];
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
  strcpy(c->surface, "surface");
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
TuiRect tui_canvas_bounds(const TuiCanvas *c) {
  return c ? (TuiRect){0, 0, c->width, c->height} : (TuiRect){0};
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
  {
    TuiRect r = {start, y, end - start, 1};
    tui_canvas_clear_cursor(c, &r);
  }
  for (i = start; i < end; i++) {
    free(row[i].text);
    row[i].text = NULL;
    row[i].owner = -1;
  }
}
TuiResult tui_canvas_surface(TuiCanvas *c, const char *surface) {
  TuiStyle style;
  if (!c || !surface || strlen(surface) >= sizeof c->surface ||
      tui_style(c->theme, c->profile, surface, 0, &style) != TUI_OK)
    return TUI_INVALID;
  strcpy(c->surface, surface);
  return TUI_OK;
}
const char *tui_canvas_surface_role(const TuiCanvas *c) {
  return c ? c->surface : "";
}
TuiResult tui_canvas_write(TuiCanvas *c, int x, int y, const char *text,
                           const char *role, int focused, int width) {
  TuiStyle style;
  if (!c || !role)
    return TUI_INVALID;
  const char *actual = !strcmp(role, "surface") ? c->surface : role;
  TuiResult result =
      plain_text_role(role)
          ? tui_text_on_surface(c->theme, c->profile, role, c->surface, focused,
                                &style)
          : tui_style(c->theme, c->profile, actual, focused, &style);
  if (result != TUI_OK)
    return result;
  return tui_canvas_write_style(c, x, y, text, &style, width);
}
TuiResult tui_canvas_write_style(TuiCanvas *c, int x, int y, const char *text,
                                 const TuiStyle *raw, int width) {
  TuiStyle style;
  size_t p = 0, end, n;
  int w, limit, i, rgb[3];
  if (!c || !raw || !text || width < 0 || width > 1000000000 ||
      x < -1000000000 || x > 1000000000 || tui_cells(text) < 0 ||
      !style_rgb(raw->foreground, rgb) || !style_rgb(raw->background, rgb))
    return TUI_INVALID;
  if (y < 0 || y >= c->height)
    return TUI_OK;
  style = *raw;
  limit = min(c->width, x + width);
  n = strlen(text);
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
  TuiStyle style;
  if (!c)
    return (TuiRect){r.x, r.y, 0, 0};
  if (tui_text_on_surface(c->theme, c->profile, role, c->surface, 0, &style) !=
      TUI_OK)
    return (TuiRect){r.x, r.y, 0, 0};
  tui_canvas_fill(c, r, "surface");
  if (r.width < 2 || r.height < 2)
    return (TuiRect){r.x, r.y, 0, 0};
  b = ascii ? a : focused ? d : s;
  tui_canvas_write_style(c, r.x, r.y, b[0], &style, 1);
  tui_canvas_write_style(c, r.x + r.width - 1, r.y, b[1], &style, 1);
  tui_canvas_write_style(c, r.x, r.y + r.height - 1, b[2], &style, 1);
  tui_canvas_write_style(c, r.x + r.width - 1, r.y + r.height - 1, b[3], &style,
                         1);
  for (x = 1; x < r.width - 1; x++) {
    tui_canvas_write_style(c, r.x + x, r.y, b[4], &style, 1);
    tui_canvas_write_style(c, r.x + x, r.y + r.height - 1, b[4], &style, 1);
  }
  for (y = 1; y < r.height - 1; y++) {
    tui_canvas_write_style(c, r.x, r.y + y, b[5], &style, 1);
    tui_canvas_write_style(c, r.x + r.width - 1, r.y + y, b[5], &style, 1);
  }
  tui_canvas_write_style(c, r.x + 2, r.y, title, &style, max(0, r.width - 4));
  return (TuiRect){r.x + 1, r.y + 1, r.width - 2, r.height - 2};
}
void tui_canvas_cursor(TuiCanvas *c, int x, int y, int w) {
  if (!c)
    return;
  c->cursor_width = max(1, w);
  if (x >= 0 && (long long)x + max(1, w) <= c->width && y >= 0 &&
      y < c->height) {
    c->cursor_x = x;
    c->cursor_y = y;
  } else
    c->cursor_x = c->cursor_y = -1;
}
void tui_canvas_clear_cursor(TuiCanvas *c, const TuiRect *r) {
  if (!c)
    return;
  if (!r ||
      (c->cursor_x >= 0 && r->width > 0 && (long long)r->y <= c->cursor_y &&
       c->cursor_y < (long long)r->y + r->height &&
       (long long)r->x < c->cursor_x + (long long)c->cursor_width &&
       c->cursor_x < (long long)r->x + r->width))
    c->cursor_x = c->cursor_y = -1;
}
TuiResult tui_canvas_blit(TuiCanvas *c, const TuiCanvas *source, TuiRect r,
                          int x, int y) {
  int left, top, right, bottom, sx, sy, cx, cy, cw;
  Cell *copy;
  size_t count, index;
  if (!c || !source || r.width < 0 || r.height < 0)
    return TUI_INVALID;
  {
    int values[] = {r.x, r.y, r.width, r.height, x, y};
    size_t i;
    for (i = 0; i < 6; i++)
      if (values[i] < -1000000000 || values[i] > 1000000000)
        return TUI_INVALID;
  }
  left = max(0, max(r.x, r.x - x));
  top = max(0, max(r.y, r.y - y));
  right = (int)min64(
      (long long)source->width,
      min64((long long)r.x + r.width, (long long)r.x + c->width - x));
  bottom = (int)min64(
      (long long)source->height,
      min64((long long)r.y + r.height, (long long)r.y + c->height - y));
  if (left >= right || top >= bottom)
    return TUI_OK;
  cx = source->cursor_x;
  cy = source->cursor_y;
  cw = source->cursor_width;
  count = (size_t)(right - left) * (bottom - top);
  copy = calloc(count, sizeof(Cell));
  if (!copy)
    return TUI_NOMEM;
  for (sy = top; sy < bottom; sy++)
    for (sx = left; sx < right; sx++) {
      const Cell *row = source->cells + (size_t)sy * source->width,
                 *cell = row + sx;
      int start = cell->owner >= 0 ? cell->owner : sx, end = start + 1;
      Cell *out = copy + (size_t)(sy - top) * (right - left) + sx - left;
      while (end < source->width && row[end].owner == start)
        end++;
      out->style = cell->style;
      out->owner = -1;
      if (start >= left && end <= right) {
        if (cell->owner >= 0)
          out->owner = x + start - r.x;
        if (cell->text) {
          size_t len = strlen(cell->text);
          out->text = malloc(len + 1);
          if (!out->text) {
            for (index = 0; index < count; index++)
              free(copy[index].text);
            free(copy);
            return TUI_NOMEM;
          }
          memcpy(out->text, cell->text, len + 1);
        }
      }
    }
  for (sy = top; sy < bottom; sy++)
    for (sx = left; sx < right; sx++)
      erase(c, x + sx - r.x, y + sy - r.y);
  for (sy = top; sy < bottom; sy++)
    for (sx = left; sx < right; sx++)
      c->cells[(size_t)(y + sy - r.y) * c->width + x + sx - r.x] =
          copy[(size_t)(sy - top) * (right - left) + sx - left];
  free(copy);
  if (cx >= left && cx + cw <= right && cy >= top && cy < bottom)
    tui_canvas_cursor(c, x + cx - r.x, y + cy - r.y, cw);
  return TUI_OK;
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
    TuiStyle previous = {0};
    int has_previous = 0;
    snprintf(seq, sizeof(seq), "\033[%d;1H", y + 1);
    append(&b, seq);
    for (x = 0; x < c->width; x++) {
      const Cell *cell = &c->cells[(size_t)y * c->width + x];
      if (cell->owner >= 0)
        continue;
      if (!has_previous || previous.foreground != cell->style.foreground ||
          previous.background != cell->style.background ||
          previous.bold != cell->style.bold ||
          previous.dim != cell->style.dim ||
          previous.underline != cell->style.underline ||
          previous.italic != cell->style.italic) {
        append(&b, "\033[0;");
        color(&b, cell->style.foreground, 0);
        append(&b, ";");
        color(&b, cell->style.background, 1);
        if (cell->style.bold)
          append(&b, ";1");
        if (cell->style.dim)
          append(&b, ";2");
        if (cell->style.italic)
          append(&b, ";3");
        if (cell->style.underline)
          append(&b, ";4");
        append(&b, "m");
        previous = cell->style;
        has_previous = 1;
      }
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

/* Text retains literal raw UTF-8 independently of display sanitization. */
typedef struct {
  char *value;
  size_t cursor, anchor;
} TextSnapshot;
struct TuiText {
  char *value, *event;
  size_t cursor, anchor;
  TuiState state;
  int secret, multiline, scroll_x, scroll_y;
  TextSnapshot undo[128], redo[128];
  size_t undo_n, redo_n;
};
static int raw_offsets(const char *s, size_t **out, size_t *count) {
  size_t n, p = 0, end, used = 0;
  int w;
  size_t *items;
  if (!s || strlen(s) > 16 * 1024 * 1024)
    return 0;
  n = strlen(s);
  items = malloc((n + 1) * sizeof(size_t));
  if (!items)
    return -1;
  items[used++] = 0;
  while (p < n) {
    if (!cluster_mode(s, n, p, &end, &w, 1)) {
      free(items);
      return 0;
    }
    p = end;
    items[used++] = p;
  }
  *out = items;
  *count = used - 1;
  return 1;
}
static TuiTextEvent text_event(TuiText *t, const char *kind, TuiResult result) {
  TuiTextEvent e = {kind, t && t->event ? t->event : "", result};
  return e;
}
static void snapshots_clear(TextSnapshot *s, size_t *n) {
  for (size_t i = 0; i < *n; i++)
    free(s[i].value);
  *n = 0;
}
TuiText *tui_text_new(const char *value) {
  size_t *o, n;
  TuiText *t;
  if (raw_offsets(value, &o, &n) != 1)
    return NULL;
  free(o);
  t = calloc(1, sizeof(*t));
  if (!t)
    return NULL;
  t->value = copy(value);
  if (!t->value) {
    free(t);
    return NULL;
  }
  t->cursor = t->anchor = n;
  t->multiline = 1;
  return t;
}
void tui_text_free(TuiText *t) {
  if (!t)
    return;
  free(t->value);
  free(t->event);
  snapshots_clear(t->undo, &t->undo_n);
  snapshots_clear(t->redo, &t->redo_n);
  free(t);
}
const char *tui_text_value(const TuiText *t) { return t ? t->value : ""; }
size_t tui_text_cursor(const TuiText *t) { return t ? t->cursor : 0; }
size_t tui_text_anchor(const TuiText *t) { return t ? t->anchor : 0; }
char *tui_text_display(const TuiText *t) {
  size_t *o, n;
  char *out;
  if (!t)
    return NULL;
  if (!t->secret)
    return copy(t->value);
  if (raw_offsets(t->value, &o, &n) != 1)
    return NULL;
  free(o);
  out = malloc(n + 1);
  if (out) {
    memset(out, '*', n);
    out[n] = 0;
  }
  return out;
}
void tui_text_options(TuiText *t, TuiState state, int secret, int multiline) {
  if (t) {
    t->state = state;
    t->secret = !!secret;
    t->multiline = !!multiline;
  }
}
void tui_text_select(TuiText *t, size_t a, size_t c) {
  size_t *o, n;
  if (!t || raw_offsets(t->value, &o, &n) != 1)
    return;
  free(o);
  t->anchor = a < n ? a : n;
  t->cursor = c < n ? c : n;
}
TuiResult tui_text_selection_bytes(const TuiText *t, size_t *a, size_t *b) {
  size_t *o, n, lo, hi;
  int ok;
  if (!t || !a || !b)
    return TUI_INVALID;
  ok = raw_offsets(t->value, &o, &n);
  if (ok != 1)
    return ok < 0 ? TUI_NOMEM : TUI_INVALID;
  lo = t->anchor < t->cursor ? t->anchor : t->cursor;
  hi = t->anchor > t->cursor ? t->anchor : t->cursor;
  *a = o[lo < n ? lo : n];
  *b = o[hi < n ? hi : n];
  free(o);
  return TUI_OK;
}
static int offset_index(const size_t *o, size_t n, size_t byte, size_t *out) {
  for (size_t i = 0; i <= n; i++)
    if (o[i] == byte) {
      *out = i;
      return 1;
    }
  return 0;
}
TuiResult tui_text_select_bytes(TuiText *t, size_t a, size_t c) {
  size_t *o, n, ai, ci;
  int ok;
  if (!t)
    return TUI_INVALID;
  ok = raw_offsets(t->value, &o, &n);
  if (ok != 1)
    return ok < 0 ? TUI_NOMEM : TUI_INVALID;
  ok = offset_index(o, n, a, &ai) && offset_index(o, n, c, &ci);
  free(o);
  if (!ok)
    return TUI_INVALID;
  t->anchor = ai;
  t->cursor = ci;
  return TUI_OK;
}
static void push_snapshot(TextSnapshot *s, size_t *n, TextSnapshot v) {
  if (*n == 128) {
    free(s[0].value);
    memmove(s, s + 1, 127 * sizeof(*s));
    (*n)--;
  }
  s[(*n)++] = v;
}
static TuiTextEvent text_replace(TuiText *t, size_t a, size_t b,
                                 const char *addition) {
  size_t *o, *next_o, n, next_n, len, prefix, at = 0;
  char *next;
  TextSnapshot old;
  int ok;
  if (!t || !addition || a > b)
    return text_event(t, "", TUI_INVALID);
  ok = raw_offsets(t->value, &o, &n);
  if (ok != 1)
    return text_event(t, "", ok < 0 ? TUI_NOMEM : TUI_INVALID);
  if (b > n) {
    free(o);
    return text_event(t, "", TUI_INVALID);
  }
  prefix = o[a] + strlen(addition);
  len = prefix + strlen(t->value) - o[b];
  if (len > 16 * 1024 * 1024) {
    free(o);
    return text_event(t, "", TUI_INVALID);
  }
  next = malloc(len + 1);
  if (!next) {
    free(o);
    return text_event(t, "", TUI_NOMEM);
  }
  memcpy(next, t->value, o[a]);
  memcpy(next + o[a], addition, strlen(addition));
  strcpy(next + prefix, t->value + o[b]);
  free(o);
  ok = raw_offsets(next, &next_o, &next_n);
  if (ok != 1) {
    free(next);
    return text_event(t, "", ok < 0 ? TUI_NOMEM : TUI_INVALID);
  }
  while (at < next_n && next_o[at] < prefix)
    at++;
  free(next_o);
  if (!tui_state_editable(t->state) || (a == b && !*addition)) {
    free(next);
    return text_event(t, "", TUI_OK);
  }
  old = (TextSnapshot){t->value, t->cursor, t->anchor};
  push_snapshot(t->undo, &t->undo_n, old);
  snapshots_clear(t->redo, &t->redo_n);
  t->value = next;
  t->cursor = t->anchor = at;
  t->state.edited = 1;
  return text_event(t, "change", TUI_OK);
}
TuiTextEvent tui_text_replace_bytes(TuiText *t, size_t a, size_t b,
                                    const char *s) {
  size_t *o, n, ai, bi;
  int ok;
  if (!t || a > b)
    return text_event(t, "", TUI_INVALID);
  free(t->event);
  t->event = NULL;
  ok = raw_offsets(t->value, &o, &n);
  if (ok != 1)
    return text_event(t, "", ok < 0 ? TUI_NOMEM : TUI_INVALID);
  ok = offset_index(o, n, a, &ai) && offset_index(o, n, b, &bi);
  free(o);
  if (!ok)
    return text_event(t, "", TUI_INVALID);
  return text_replace(t, ai, bi, s);
}
static int raw_break(const char *s, size_t a, size_t b) {
  return (b - a == 1 && (s[a] == '\r' || s[a] == '\n')) ||
         (b - a == 2 && s[a] == '\r' && s[a + 1] == '\n');
}
static char *text_clean(const char *s, int multiline) {
  size_t n, p = 0, q, used = 0;
  unsigned cp;
  char *out;
  if (!s)
    return NULL;
  n = strlen(s);
  if (n > 16 * 1024 * 1024)
    return NULL;
  out = malloc(n + 1);
  if (!out)
    return NULL;
  while (p < n) {
    q = p;
    if (!decode((const unsigned char *)s, n, &p, &cp)) {
      free(out);
      return NULL;
    }
    if (cp == '\r') {
      if (p < n && s[p] == '\n')
        p++;
      if (multiline)
        out[used++] = '\n';
    } else if (cp == '\n') {
      if (multiline)
        out[used++] = '\n';
    } else if (cp == '\t')
      out[used++] = ' ';
    else if (cp >= 32 && !(cp >= 127 && cp < 160)) {
      memcpy(out + used, s + q, p - q);
      used += p - q;
    }
  }
  out[used] = 0;
  return out;
}
TuiTextEvent tui_text_handle(TuiText *t, const char *action,
                             const char *addition) {
  size_t *o, n, lo, hi, at, start, end, target = 0;
  int ok, extend, movement = 1;
  const char *move;
  char *cleaned;
  TuiTextEvent e;
  if (!t || !action)
    return text_event(t, "", TUI_INVALID);
  free(t->event);
  t->event = NULL;
  if (t->state.disabled)
    return text_event(t, "", TUI_OK);
  ok = raw_offsets(t->value, &o, &n);
  if (ok != 1)
    return text_event(t, "", ok < 0 ? TUI_NOMEM : TUI_INVALID);
  if (t->anchor > n)
    t->anchor = n;
  if (t->cursor > n)
    t->cursor = n;
  lo = t->anchor < t->cursor ? t->anchor : t->cursor;
  hi = t->anchor > t->cursor ? t->anchor : t->cursor;
  at = t->cursor;
  start = end = at;
  while (start && !raw_break(t->value, o[start - 1], o[start]))
    start--;
  while (end < n && !raw_break(t->value, o[end], o[end + 1]))
    end++;
  extend = !strncmp(action, "select_", 7);
  move = extend ? action + 7 : action;
  if (extend && !strcmp(move, "all")) {
    t->anchor = 0;
    t->cursor = n;
    free(o);
    return text_event(t, "select", TUI_OK);
  }
  if (!strcmp(move, "left"))
    target = !extend && lo != hi ? lo : at ? at - 1 : 0;
  else if (!strcmp(move, "right"))
    target = !extend && lo != hi ? hi : at < n ? at + 1 : n;
  else if (!strcmp(move, "home"))
    target = start;
  else if (!strcmp(move, "end"))
    target = end;
  else if (!strcmp(move, "up")) {
    size_t p = start ? start - 1 : 0;
    while (p && !raw_break(t->value, o[p - 1], o[p]))
      p--;
    target =
        start ? (p + at - start < start - 1 ? p + at - start : start - 1) : at;
  } else if (!strcmp(move, "down")) {
    size_t p = end < n ? end + 1 : n;
    while (p < n && !raw_break(t->value, o[p], o[p + 1]))
      p++;
    target =
        end < n ? (end + 1 + at - start < p ? end + 1 + at - start : p) : at;
  } else
    movement = 0;
  if (movement) {
    t->cursor = target;
    if (!extend)
      t->anchor = target;
    free(o);
    return text_event(t, "select", TUI_OK);
  }
  if (!strcmp(action, "copy") || !strcmp(action, "cut")) {
    if (t->secret || lo == hi ||
        (!strcmp(action, "cut") && !tui_state_editable(t->state))) {
      free(o);
      return text_event(t, "", TUI_OK);
    }
    t->event = malloc(o[hi] - o[lo] + 1);
    if (!t->event) {
      free(o);
      return text_event(t, "", TUI_NOMEM);
    }
    memcpy(t->event, t->value + o[lo], o[hi] - o[lo]);
    t->event[o[hi] - o[lo]] = 0;
    free(o);
    if (!strcmp(action, "cut")) {
      e = text_replace(t, lo, hi, "");
      if (e.result != TUI_OK) {
        free(t->event);
        t->event = NULL;
        return text_event(t, "", e.result);
      }
    }
    return text_event(t, !strcmp(action, "copy") ? "copy" : "cut", TUI_OK);
  }
  free(o);
  if (!tui_state_editable(t->state))
    return text_event(t, "", TUI_OK);
  if (!strcmp(action, "undo") || !strcmp(action, "redo")) {
    int undo = !strcmp(action, "undo");
    TextSnapshot *src = undo ? t->undo : t->redo,
                 *dst = undo ? t->redo : t->undo;
    size_t *sn = undo ? &t->undo_n : &t->redo_n,
           *dn = undo ? &t->redo_n : &t->undo_n;
    TextSnapshot old;
    if (!*sn)
      return text_event(t, "", TUI_OK);
    old = src[--(*sn)];
    push_snapshot(dst, dn, (TextSnapshot){t->value, t->cursor, t->anchor});
    t->value = old.value;
    t->cursor = old.cursor;
    t->anchor = old.anchor;
    t->state.edited = 1;
    return text_event(t, "change", TUI_OK);
  }
  if (!strcmp(action, "backspace")) {
    if (lo == hi && lo)
      lo--;
    return text_replace(t, lo, hi, "");
  }
  if (!strcmp(action, "delete")) {
    if (lo == hi && hi < n)
      hi++;
    return text_replace(t, lo, hi, "");
  }
  if (strcmp(action, "insert") && strcmp(action, "paste") &&
      strcmp(action, "newline"))
    return text_event(t, "", TUI_OK);
  cleaned = text_clean(!strcmp(action, "newline") ? "\n"
                       : addition                 ? addition
                                                  : "",
                       t->multiline);
  if (!cleaned)
    return text_event(t, "", TUI_INVALID);
  e = text_replace(t, lo, hi, cleaned);
  free(cleaned);
  return e;
}
TuiResult tui_text_draw(TuiText *t, TuiCanvas *c, TuiRect r, int focused) {
  size_t *o, n;
  int cy = 0, cx = 0, cw = 1, y = 0, x = 0;
  const char *role;
  TuiResult result = TUI_OK;
  if (!t || !c)
    return TUI_INVALID;
  if (raw_offsets(t->value, &o, &n) != 1)
    return TUI_NOMEM;
  role = t->state.disabled ? "disabled" : t->state.read_only ? "body" : "field";
  tui_canvas_fill(c, r, role);
  if (r.width <= 0 || r.height <= 0) {
    free(o);
    return TUI_OK;
  }
  for (size_t i = 0; i < n; i++) {
    int br = t->multiline && raw_break(t->value, o[i], o[i + 1]);
    char *glyph = malloc(o[i + 1] - o[i] + 1);
    int w;
    if (!glyph) {
      result = TUI_NOMEM;
      break;
    }
    memcpy(glyph, t->value + o[i], o[i + 1] - o[i]);
    glyph[o[i + 1] - o[i]] = 0;
    w = t->secret ? 1 : tui_cells(glyph);
    free(glyph);
    if (i < t->cursor) {
      if (br) {
        cy++;
        cx = 0;
      } else
        cx += w;
    } else if (i == t->cursor && !br)
      cw = max(1, w);
  }
  t->scroll_y = max(0, max(min(t->scroll_y, cy), cy - r.height + 1));
  t->scroll_x =
      max(0, max(min(t->scroll_x, cx), cx + min(cw, r.width) - r.width));
  for (size_t i = 0; i < n && result == TUI_OK; i++) {
    size_t lo = t->anchor < t->cursor ? t->anchor : t->cursor,
           hi = t->anchor > t->cursor ? t->anchor : t->cursor;
    char *glyph;
    int w, local;
    if (t->multiline && raw_break(t->value, o[i], o[i + 1])) {
      y++;
      x = 0;
      continue;
    }
    glyph = malloc(o[i + 1] - o[i] + 1);
    if (!glyph) {
      result = TUI_NOMEM;
      break;
    }
    memcpy(glyph, t->value + o[i], o[i + 1] - o[i]);
    glyph[o[i + 1] - o[i]] = 0;
    if (t->secret) {
      glyph[0] = '*';
      glyph[1] = 0;
    }
    w = tui_cells(glyph);
    local = x - t->scroll_x;
    if (y >= t->scroll_y && y < t->scroll_y + r.height && local >= 0 &&
        local + w <= r.width)
      result = tui_canvas_write(c, r.x + local, r.y + y - t->scroll_y, glyph,
                                lo <= i && i < hi ? "selection" : role, 0, w);
    x += w;
    free(glyph);
  }
  if (focused && tui_state_editable(t->state) && cw <= r.width)
    tui_canvas_cursor(c, r.x + cx - t->scroll_x, r.y + cy - t->scroll_y, cw);
  free(o);
  return result;
}
TuiTextEvent tui_text_click(TuiText *t, int x, int y, int width, int height,
                            int extend) {
  size_t *o, n, target = 0;
  int row = 0, cell = 0;
  if (!t || t->state.disabled || x < 0 || y < 0 || x >= width || y >= height)
    return text_event(t, "", TUI_OK);
  if (raw_offsets(t->value, &o, &n) != 1)
    return text_event(t, "", TUI_NOMEM);
  target = n;
  for (size_t i = 0; i < n; i++) {
    if (t->multiline && raw_break(t->value, o[i], o[i + 1])) {
      if (row == y + t->scroll_y) {
        target = i;
        break;
      }
      row++;
      cell = 0;
      continue;
    }
    if (row == y + t->scroll_y) {
      char *glyph = malloc(o[i + 1] - o[i] + 1);
      int w;
      if (!glyph) {
        free(o);
        return text_event(t, "", TUI_NOMEM);
      }
      memcpy(glyph, t->value + o[i], o[i + 1] - o[i]);
      glyph[o[i + 1] - o[i]] = 0;
      w = t->secret ? 1 : tui_cells(glyph);
      free(glyph);
      if (x + t->scroll_x < cell + w) {
        target = i;
        break;
      }
      cell += w;
    }
  }
  free(o);
  tui_text_select(t, extend ? t->anchor : target, target);
  return text_event(t, "select", TUI_OK);
}

struct TuiForm {
  TuiField *fields;
  TuiText **inputs;
  size_t count, focused;
  const char **missing;
  TuiFormRow *rows;
  size_t row_count, visible_start, visible_count;
  int layout_width;
};
static const char *nn(const char *s) { return s ? s : ""; }
static int field_index(const TuiForm *f, const char *id, size_t *out) {
  if (!f || !id)
    return 0;
  for (size_t i = 0; i < f->count; i++)
    if (!strcmp(f->fields[i].id, id)) {
      *out = i;
      return 1;
    }
  return 0;
}
static void form_eligible(TuiForm *f) {
  if (f->focused < f->count && tui_state_focusable(f->fields[f->focused].state))
    return;
  f->focused = f->count;
  for (size_t i = 0; i < f->count; i++)
    if (tui_state_focusable(f->fields[i].state)) {
      f->focused = i;
      break;
    }
}
static int owned_string(const char **target, const char *source) {
  char *next = copy(nn(source));
  if (!next)
    return 0;
  free((void *)*target);
  *target = next;
  return 1;
}
static void form_rows_clear(TuiForm *f) {
  for (size_t i = 0; i < f->row_count; i++)
    free((void *)f->rows[i].text);
  free(f->rows);
  f->rows = NULL;
  f->row_count = f->visible_count = f->visible_start = 0;
}
void tui_form_free(TuiForm *f) {
  if (!f)
    return;
  form_rows_clear(f);
  if (f->fields)
    for (size_t i = 0; i < f->count; i++) {
      TuiField *v = &f->fields[i];
      free((void *)v->id);
      free((void *)v->kind);
      free((void *)v->label);
      free((void *)v->value);
      free((void *)v->help);
      free((void *)v->error);
      free((void *)v->choice);
      free((void *)v->action);
      free((void *)v->pending);
      if (v->options)
        for (size_t j = 0; j < v->option_count; j++) {
          free((void *)v->options[j].id);
          free((void *)v->options[j].label);
        }
      free((void *)v->options);
      if (f->inputs)
        tui_text_free(f->inputs[i]);
    }
  free(f->fields);
  free(f->inputs);
  free(f->missing);
  free(f);
}
TuiForm *tui_form_new(const TuiField *fields, size_t count) {
  TuiForm *f;
  size_t total_options = 0;
  if ((count && !fields) || count > 4096)
    return NULL;
  f = calloc(1, sizeof(*f));
  if (!f)
    return NULL;
  f->count = count;
  f->focused = count;
  f->fields = calloc(count ? count : 1, sizeof(*f->fields));
  f->inputs = calloc(count ? count : 1, sizeof(*f->inputs));
  f->missing = calloc(count ? count : 1, sizeof(*f->missing));
  if (!f->fields || !f->inputs || !f->missing) {
    tui_form_free(f);
    return NULL;
  }
  for (size_t i = 0; i < count; i++) {
    const TuiField *s = &fields[i];
    TuiField *d = &f->fields[i];
    const char *kind = s->kind && *s->kind ? s->kind : "text";
    int valid = 0;
    const char *kinds[] = {"text",  "textarea", "password", "checkbox",
                           "radio", "select",   "button"};
    if (!s->id || !*s->id || s->open || s->option_count > 4096 ||
        (s->option_count && !s->options))
      goto bad;
    total_options += s->option_count;
    if (total_options > 65536)
      goto bad;
    for (size_t j = 0; j < i; j++)
      if (!strcmp(s->id, f->fields[j].id))
        goto bad;
    for (size_t j = 0; j < 7; j++)
      if (!strcmp(kind, kinds[j]))
        valid = 1;
    if (!valid)
      goto bad;
#define FORM_COPY(name, source)                                                \
  if (!owned_string(&d->name, source) || tui_cells(d->name) < 0)               \
  goto bad
    FORM_COPY(id, s->id);
    FORM_COPY(kind, kind);
    FORM_COPY(label, s->label);
    FORM_COPY(value, s->value);
    FORM_COPY(help, s->help);
    FORM_COPY(error, s->error);
    FORM_COPY(choice, s->choice);
    FORM_COPY(action, s->action);
    FORM_COPY(pending, s->pending);
#undef FORM_COPY
    d->state = s->state;
    d->required = s->required;
    d->checked = s->checked;
    d->height = s->height > 0 ? s->height : 3;
    if (s->option_count) {
      TuiFormOption *options = calloc(s->option_count, sizeof(*options));
      if (!options)
        goto bad;
      d->options = options;
      d->option_count = s->option_count;
      for (size_t j = 0; j < s->option_count; j++) {
        if (!s->options[j].id || !*s->options[j].id)
          goto bad;
        for (size_t k = 0; k < j; k++)
          if (!strcmp(options[k].id, s->options[j].id))
            goto bad;
        options[j].id = copy(s->options[j].id);
        options[j].label = copy(nn(s->options[j].label));
        options[j].disabled = s->options[j].disabled;
        if (!options[j].id || !options[j].label ||
            tui_cells(options[j].label) < 0)
          goto bad;
      }
    }
    if (*d->choice) {
      valid = 0;
      for (size_t j = 0; j < d->option_count; j++)
        if (!strcmp(d->choice, d->options[j].id))
          valid = 1;
      if (!valid)
        goto bad;
    }
    if (!strcmp(kind, "text") || !strcmp(kind, "textarea") ||
        !strcmp(kind, "password")) {
      char *display;
      f->inputs[i] = tui_text_new(d->value);
      if (!f->inputs[i])
        goto bad;
      tui_text_options(f->inputs[i], d->state, !strcmp(kind, "password"),
                       !strcmp(kind, "textarea"));
      display = tui_text_display(f->inputs[i]);
      if (!display)
        goto bad;
      free((void *)d->value);
      d->value = display;
    }
  }
  form_eligible(f);
  return f;
bad:
  tui_form_free(f);
  return NULL;
}
TuiForm *tui_control_new(TuiField field) { return tui_form_new(&field, 1); }
const TuiField *tui_form_field(const TuiForm *f, const char *id) {
  size_t i;
  return field_index(f, id, &i) ? &f->fields[i] : NULL;
}
const char *tui_form_value(const TuiForm *f, const char *id) {
  size_t i;
  if (!field_index(f, id, &i))
    return NULL;
  return f->inputs[i] ? tui_text_value(f->inputs[i]) : f->fields[i].value;
}
const char *tui_form_focused(const TuiForm *f) {
  return f && f->focused < f->count ? f->fields[f->focused].id : "";
}
int tui_form_focus(TuiForm *f, const char *id) {
  size_t i;
  if (!field_index(f, id, &i) || !tui_state_focusable(f->fields[i].state))
    return 0;
  for (size_t j = 0; j < f->count; j++)
    f->fields[j].open = 0;
  f->focused = i;
  return 1;
}
int tui_form_at_tab_boundary(const TuiForm *f, int previous) {
  size_t first = f ? f->count : 0, last = first;
  if (!f)
    return 1;
  for (size_t i = 0; i < f->count; i++)
    if (tui_state_focusable(f->fields[i].state)) {
      if (first == f->count)
        first = i;
      last = i;
    }
  return first == f->count || f->focused == (previous ? first : last);
}
TuiResult tui_form_set_state(TuiForm *f, const char *id, TuiState state) {
  size_t i;
  if (!field_index(f, id, &i))
    return TUI_INVALID;
  f->fields[i].state = state;
  if (!tui_state_editable(state))
    f->fields[i].open = 0;
  form_eligible(f);
  return TUI_OK;
}
TuiResult tui_form_set_feedback(TuiForm *f, const char *id, const char *help,
                                const char *error) {
  size_t i;
  char *h, *e;
  if (!field_index(f, id, &i) || tui_cells(nn(help)) < 0 ||
      tui_cells(nn(error)) < 0)
    return TUI_INVALID;
  h = copy(nn(help));
  e = copy(nn(error));
  if (!h || !e) {
    free(h);
    free(e);
    return TUI_NOMEM;
  }
  free((void *)f->fields[i].help);
  free((void *)f->fields[i].error);
  f->fields[i].help = h;
  f->fields[i].error = e;
  f->fields[i].state.invalid = !!*e;
  return TUI_OK;
}
TuiResult tui_form_select_text(TuiForm *f, const char *id, size_t a, size_t c) {
  size_t i;
  if (!field_index(f, id, &i) || !f->inputs[i])
    return TUI_INVALID;
  tui_text_select(f->inputs[i], a, c);
  return TUI_OK;
}
static TuiFormEvent form_event(TuiForm *f, const char *kind, const char *id,
                               const char *text, size_t missing,
                               TuiResult result) {
  TuiFormEvent e = {kind, id, text, f ? f->missing : NULL, missing, result};
  return e;
}
static int whitespace(unsigned cp) {
  return (cp >= 9 && cp <= 13) || cp == 32 || cp == 0x85 || cp == 0xa0 ||
         cp == 0x1680 || (cp >= 0x2000 && cp <= 0x200a) || cp == 0x2028 ||
         cp == 0x2029 || cp == 0x202f || cp == 0x205f || cp == 0x3000;
}
static int text_empty(const char *s) {
  size_t p = 0, n = strlen(s);
  unsigned cp;
  while (p < n)
    if (!decode((const unsigned char *)s, n, &p, &cp) || !whitespace(cp))
      return 0;
  return 1;
}
static size_t form_missing(TuiForm *f) {
  size_t count = 0;
  for (size_t i = 0; i < f->count; i++) {
    TuiField *v = &f->fields[i];
    int empty = f->inputs[i] ? text_empty(tui_text_value(f->inputs[i]))
                : !strcmp(v->kind, "checkbox") ? !v->checked
                : (!strcmp(v->kind, "select") || !strcmp(v->kind, "radio"))
                    ? !*v->choice
                    : 0;
    if (!v->state.disabled &&
        (v->state.invalid || *v->error || (v->required && empty)))
      f->missing[count++] = v->id;
  }
  return count;
}
TuiFormEvent tui_form_handle(TuiForm *f, const char *action, const char *text) {
  TuiField *v;
  size_t i;
  int changed = 0;
  if (!f || !action)
    return form_event(f, "", "", "", 0, TUI_INVALID);
  text = nn(text);
  form_eligible(f);
  if (!strcmp(action, "next") || !strcmp(action, "previous")) {
    int previous = !strcmp(action, "previous");
    if (f->focused < f->count)
      for (size_t step = 1; step <= f->count; step++) {
        size_t at = previous ? (f->focused + f->count - step) % f->count
                             : (f->focused + step) % f->count;
        if (tui_state_focusable(f->fields[at].state)) {
          tui_form_focus(f, f->fields[at].id);
          break;
        }
      }
    return form_event(f, "", "", "", 0, TUI_OK);
  }
  if (!strcmp(action, "submit")) {
    size_t n = form_missing(f);
    return form_event(f, n ? "invalid" : "submit", "", "", n, TUI_OK);
  }
  if (f->focused >= f->count)
    return form_event(f, "", "", "", 0, TUI_OK);
  i = f->focused;
  v = &f->fields[i];
  if (!strcmp(action, "cancel")) {
    if (v->open) {
      v->open = 0;
      return form_event(f, "", "", "", 0, TUI_OK);
    }
    return form_event(f, "cancel", v->id, "", 0, TUI_OK);
  }
  if (!strcmp(action, "insert") && !strcmp(text, " ") && !f->inputs[i])
    action = "toggle";
  if (f->inputs[i]) {
    TuiText *t = f->inputs[i];
    TuiTextEvent e;
    char *display;
    t->state = v->state;
    if (!strcmp(action, "activate") && strcmp(v->kind, "textarea"))
      return tui_state_activatable(v->state)
                 ? tui_form_handle(f, "submit", "")
                 : form_event(f, "", "", "", 0, TUI_OK);
    e = tui_text_handle(t, !strcmp(action, "activate") ? "newline" : action,
                        text);
    display = tui_text_display(t);
    if (!display)
      return form_event(f, "", v->id, "", 0, TUI_NOMEM);
    free((void *)v->value);
    v->value = display;
    v->state = t->state;
    return form_event(f, e.kind, v->id, e.text, 0, e.result);
  }
  if (!strcmp(v->kind, "button") &&
      (!strcmp(action, "left") || !strcmp(action, "right")) &&
      !v->state.disabled)
    return tui_form_handle(f, !strcmp(action, "left") ? "previous" : "next",
                           "");
  if (!tui_state_activatable(v->state))
    return form_event(f, "", "", "", 0, TUI_OK);
  if (!strcmp(v->kind, "button") &&
      (!strcmp(action, "activate") || !strcmp(action, "toggle"))) {
    if (!strcmp(v->action, "submit"))
      return tui_form_handle(f, "submit", "");
    return form_event(f, !strcmp(v->action, "cancel") ? "cancel" : "activate",
                      v->id, "", 0, TUI_OK);
  }
  if (!tui_state_editable(v->state))
    return form_event(f, "", "", "", 0, TUI_OK);
  if (!strcmp(v->kind, "checkbox") &&
      (!strcmp(action, "activate") || !strcmp(action, "toggle"))) {
    v->checked = !v->checked;
    changed = 1;
  } else if (!strcmp(v->kind, "radio") || !strcmp(v->kind, "select")) {
    if (!strcmp(v->kind, "select") &&
        (!strcmp(action, "activate") || !strcmp(action, "toggle"))) {
      if (v->open) {
        if (!owned_string(&v->choice, v->pending))
          return form_event(f, "", "", "", 0, TUI_NOMEM);
        v->open = 0;
        changed = 1;
      } else {
        const char *pending = v->choice;
        if (!*pending)
          for (size_t j = 0; j < v->option_count; j++)
            if (!v->options[j].disabled) {
              pending = v->options[j].id;
              break;
            }
        if (!owned_string(&v->pending, pending))
          return form_event(f, "", "", "", 0, TUI_NOMEM);
        v->open = 1;
        return form_event(f, "", "", "", 0, TUI_OK);
      }
    } else if (!strcmp(action, "left") || !strcmp(action, "right") ||
               !strcmp(action, "up") || !strcmp(action, "down") ||
               !strcmp(action, "activate") || !strcmp(action, "toggle")) {
      size_t *ids, count = 0, at = 0, target;
      int found = 0,
          previous = !strcmp(action, "left") || !strcmp(action, "up");
      const char *current = v->open ? v->pending : v->choice;
      if (!strcmp(v->kind, "select") && !v->open)
        return form_event(f, "", "", "", 0, TUI_OK);
      ids = malloc((v->option_count ? v->option_count : 1) * sizeof(*ids));
      if (!ids)
        return form_event(f, "", "", "", 0, TUI_NOMEM);
      for (size_t j = 0; j < v->option_count; j++)
        if (!v->options[j].disabled) {
          ids[count] = j;
          if (!strcmp(v->options[j].id, current)) {
            at = count;
            found = 1;
          }
          count++;
        }
      if (!count) {
        free(ids);
        return form_event(f, "", "", "", 0, TUI_OK);
      }
      target = previous ? (at + count - 1) % count
               : found  ? (at + 1) % count
                        : 0;
      if (!owned_string(!strcmp(v->kind, "select") ? &v->pending : &v->choice,
                        v->options[ids[target]].id)) {
        free(ids);
        return form_event(f, "", "", "", 0, TUI_NOMEM);
      }
      free(ids);
      changed = strcmp(v->kind, "select") != 0;
    }
  }
  if (changed) {
    v->state.edited = 1;
    return form_event(f, "change", v->id, "", 0, TUI_OK);
  }
  return form_event(f, "", "", "", 0, TUI_OK);
}
TuiFormEvent tui_form_click_field(TuiForm *f, const char *id,
                                  const char *option) {
  size_t i;
  TuiField *v;
  if (!field_index(f, id, &i))
    return form_event(f, "", "", "", 0, TUI_OK);
  option = nn(option);
  v = &f->fields[i];
  if (v->state.disabled)
    return form_event(f, "", "", "", 0, TUI_OK);
  for (size_t j = 0; j < v->option_count; j++)
    if (!strcmp(v->options[j].id, option) && v->options[j].disabled)
      return form_event(f, "", "", "", 0, TUI_OK);
  if (f->focused != i)
    tui_form_focus(f, id);
  if (!strcmp(v->kind, "button"))
    return tui_form_handle(f, "activate", "");
  if (!tui_state_editable(v->state))
    return form_event(f, "", "", "", 0, TUI_OK);
  if (!strcmp(v->kind, "select") && !v->open)
    return tui_form_handle(f, "activate", "");
  if (*option && (!strcmp(v->kind, "radio") || !strcmp(v->kind, "select"))) {
    for (size_t j = 0; j < v->option_count; j++)
      if (!strcmp(v->options[j].id, option) && !v->options[j].disabled) {
        if (!owned_string(&v->choice, option))
          return form_event(f, "", "", "", 0, TUI_NOMEM);
        v->open = 0;
        v->state.edited = 1;
        return form_event(f, "change", v->id, "", 0, TUI_OK);
      }
    return form_event(f, "", "", "", 0, TUI_OK);
  }
  return (!strcmp(v->kind, "checkbox") || !strcmp(v->kind, "select"))
             ? tui_form_handle(f, "activate", "")
             : form_event(f, "", "", "", 0, TUI_OK);
}
static int form_row(TuiForm *f, const TuiField *v, const char *text,
                    const char *role, const char *option, int input,
                    int focused, int source) {
  TuiFormRow *next = realloc(f->rows, (f->row_count + 1) * sizeof(*next));
  char *owned;
  if (!next)
    return 0;
  f->rows = next;
  owned = copy(text);
  if (!owned)
    return 0;
  f->rows[f->row_count++] =
      (TuiFormRow){v->id, owned, role, option, input, focused, source};
  return 1;
}
TuiResult tui_form_layout(TuiForm *f, int width, int height,
                          const TuiFormRow **rows, size_t *count) {
  size_t anchor = 0;
  if (!f || !rows || !count)
    return TUI_INVALID;
  form_rows_clear(f);
  width = max(0, width);
  height = max(0, height);
  f->layout_width = width;
  for (size_t i = 0; i < f->count; i++) {
    TuiField *v = &f->fields[i];
    int current = i == f->focused;
    const char *role = v->state.disabled ? "disabled"
                       : *v->error || v->state.invalid
                           ? "error"
                           : tui_state_role(v->state);
    char markers[7];
    Buffer b = {0};
    if (current)
      anchor = f->row_count;
    tui_state_markers(v->state, markers);
    append(&b, current ? "> " : "  ");
    append(&b, v->label);
    if (v->required)
      append(&b, " *");
    if (*(markers + (v->state.disabled ? 1 : 0))) {
      append(&b, " ");
      append(&b, markers + (v->state.disabled ? 1 : 0));
    }
    if (b.failed || !form_row(f, v, b.s, role, "", 0, current, 0)) {
      free(b.s);
      goto nomem;
    }
    free(b.s);
    if (f->inputs[i]) {
      size_t *offsets, n, start = 0;
      int line = 0;
      char *display = tui_text_display(f->inputs[i]);
      if (!display)
        goto nomem;
      if (raw_offsets(display, &offsets, &n) != 1) {
        free(display);
        goto nomem;
      }
      for (size_t j = 0; j <= n; j++) {
        int br = j == n || (!strcmp(v->kind, "textarea") &&
                            raw_break(display, offsets[j], offsets[j + 1]));
        if (br) {
          size_t len = offsets[j] - start;
          char *row = malloc(len + 3);
          if (!row) {
            free(offsets);
            free(display);
            goto nomem;
          }
          memcpy(row, "  ", 2);
          memcpy(row + 2, display + start, len);
          row[len + 2] = 0;
          if (!form_row(f, v, row, v->state.disabled ? "disabled" : "field", "",
                        1, 0, line)) {
            free(row);
            free(offsets);
            free(display);
            goto nomem;
          }
          free(row);
          line++;
          if (strcmp(v->kind, "textarea") || line >= max(1, v->height) ||
              j == n)
            break;
          start = offsets[j + 1];
        }
      }
      free(offsets);
      free(display);
    } else if (!strcmp(v->kind, "checkbox")) {
      if (!form_row(f, v, v->checked ? "  [x]" : "  [ ]", role, "", 0, 0, 0))
        goto nomem;
    } else if (!strcmp(v->kind, "button")) {
      Buffer button = {0};
      append(&button, "  [ ");
      append(&button, v->label);
      if (v->state.busy)
        append(&button, " ~");
      append(&button, " ]");
      if (button.failed || !form_row(f, v, button.s,
                                     v->state.disabled ? "disabled"
                                     : v->state.busy   ? "hint"
                                                       : "button",
                                     "", 0, current, 0)) {
        free(button.s);
        goto nomem;
      }
      free(button.s);
    } else
      for (size_t j = 0; j < v->option_count; j++) {
        const TuiFormOption *o = &v->options[j];
        Buffer option = {0};
        if (!strcmp(v->kind, "select") && !v->open && strcmp(o->id, v->choice))
          continue;
        append(&option, !strcmp(o->id, v->open ? v->pending : v->choice)
                            ? "  (*) "
                            : "  ( ) ");
        append(&option, o->label);
        if (option.failed ||
            !form_row(f, v, option.s,
                      o->disabled || v->state.disabled ? "disabled" : role,
                      o->id, 0, 0, 0)) {
          free(option.s);
          goto nomem;
        }
        free(option.s);
      }
    if (*v->error || *v->help) {
      Buffer feedback = {0};
      append(&feedback, *v->error ? "! " : "  ");
      append(&feedback, *v->error ? v->error : v->help);
      if (feedback.failed ||
          !form_row(f, v, feedback.s, *v->error ? "error" : "hint", "", 0, 0,
                    0)) {
        free(feedback.s);
        goto nomem;
      }
      free(feedback.s);
    }
  }
  f->visible_start = (size_t)min(max(0, (int)anchor - max(0, height - 2)),
                                 max(0, (int)f->row_count - height));
  f->visible_count =
      (size_t)min(height, (int)(f->row_count - f->visible_start));
  for (size_t i = f->visible_start; i < f->visible_start + f->visible_count;
       i++) {
    char *clipped = tui_clip(f->rows[i].text, width, 0);
    if (!clipped)
      goto nomem;
    free((void *)f->rows[i].text);
    f->rows[i].text = clipped;
  }
  *rows = f->rows ? f->rows + f->visible_start : NULL;
  *count = f->visible_count;
  return TUI_OK;
nomem:
  form_rows_clear(f);
  *rows = NULL;
  *count = 0;
  return TUI_NOMEM;
}
TuiFormEvent tui_form_click(TuiForm *f, int x, int y, int height) {
  if (!f || x < 0 || x >= f->layout_width || y < 0 || y >= height ||
      (size_t)y >= f->visible_count)
    return form_event(f, "", "", "", 0, TUI_OK);
  const TuiFormRow *r = &f->rows[f->visible_start + (size_t)y];
  if (r->input && x >= 2) {
    size_t i;
    if (!field_index(f, r->id, &i) || f->fields[i].state.disabled)
      return form_event(f, "", "", "", 0, TUI_OK);
    if (f->focused != i)
      tui_form_focus(f, r->id);
    int first = -1, count = 0;
    for (size_t j = 0; j < f->visible_count; j++) {
      const TuiFormRow *row = &f->rows[f->visible_start + j];
      if (row->input && !strcmp(row->id, r->id)) {
        if (first < 0)
          first = (int)j;
        count++;
      }
    }
    TuiTextEvent e = tui_text_click(f->inputs[i], x - 2, y - first,
                                    max(0, f->layout_width - 2), count, 0);
    return form_event(f, e.kind, r->id, e.text, 0, e.result);
  }
  return tui_form_click_field(f, r->id, r->option);
}
TuiResult tui_form_draw(TuiForm *f, TuiCanvas *c, TuiRect r, int focused) {
  const TuiFormRow *rows;
  size_t count;
  TuiResult result;
  if (!f || !c)
    return TUI_INVALID;
  result = tui_form_layout(f, r.width, r.height, &rows, &count);
  if (result != TUI_OK)
    return result;
  tui_canvas_fill(c, r, "surface");
  for (size_t i = 0; i < count; i++) {
    result = tui_canvas_write(c, r.x, r.y + (int)i, rows[i].text, rows[i].role,
                              focused && rows[i].focused, r.width);
    if (result != TUI_OK)
      return result;
  }
  for (size_t i = 0; i < f->count; i++)
    if (f->inputs[i]) {
      int first = -1, height = 0;
      for (size_t j = 0; j < count; j++)
        if (rows[j].input && !strcmp(rows[j].id, f->fields[i].id)) {
          if (first < 0)
            first = (int)j;
          height++;
        }
      if (first >= 0) {
        f->inputs[i]->state = f->fields[i].state;
        result = tui_text_draw(f->inputs[i], c,
                               (TuiRect){r.x + min(2, r.width), r.y + first,
                                         max(0, r.width - 2), height},
                               focused && f->focused == i);
        if (result != TUI_OK)
          return result;
      }
    }
  return TUI_OK;
}

typedef struct {
  char *id, *restore;
  TuiFocusTarget *targets;
  size_t count, focused;
  int dismissible;
} FocusScope;
struct TuiFocus {
  FocusScope *scopes[65];
  size_t count;
};
static void scope_free(FocusScope *s) {
  if (!s)
    return;
  for (size_t i = 0; i < s->count; i++)
    free((void *)s->targets[i].id);
  free(s->targets);
  free(s->id);
  free(s->restore);
  free(s);
}
static int scope_focus(FocusScope *s, const char *id) {
  for (size_t i = 0; i < s->count; i++)
    if (!s->targets[i].hidden && tui_state_focusable(s->targets[i].state) &&
        !strcmp(s->targets[i].id, id)) {
      s->focused = i;
      return 1;
    }
  return 0;
}
static const char *scope_focused(const FocusScope *s) {
  return s->focused < s->count ? s->targets[s->focused].id : "";
}
static FocusScope *scope_new(const char *id, const TuiFocusTarget *targets,
                             size_t count, const char *initial, int dismissible,
                             const char *restore, TuiResult *result) {
  FocusScope *s;
  *result = TUI_INVALID;
  if (!id || !*id || tui_cells(id) < 0 || count > 4096 || (count && !targets))
    return NULL;
  for (size_t i = 0; i < count; i++) {
    if (!targets[i].id || !*targets[i].id || tui_cells(targets[i].id) < 0)
      return NULL;
    for (size_t j = 0; j < i; j++)
      if (!strcmp(targets[j].id, targets[i].id))
        return NULL;
  }
  *result = TUI_NOMEM;
  s = calloc(1, sizeof(*s));
  if (!s)
    return NULL;
  s->id = copy(id);
  s->restore = copy(nn(restore));
  s->targets = calloc(count ? count : 1, sizeof(*s->targets));
  if (!s->id || !s->restore || !s->targets) {
    scope_free(s);
    return NULL;
  }
  s->count = count;
  s->focused = count;
  s->dismissible = !!dismissible;
  for (size_t i = 0; i < count; i++) {
    s->targets[i] = targets[i];
    s->targets[i].id = copy(targets[i].id);
    if (!s->targets[i].id) {
      scope_free(s);
      return NULL;
    }
    if (s->focused == count && !targets[i].hidden &&
        tui_state_focusable(targets[i].state))
      s->focused = i;
  }
  if (initial && *initial && !scope_focus(s, initial)) {
    scope_free(s);
    *result = TUI_INVALID;
    return NULL;
  }
  *result = TUI_OK;
  return s;
}
TuiFocus *tui_focus_new(const char *root, const TuiFocusTarget *targets,
                        size_t count) {
  TuiResult result;
  FocusScope *s = scope_new(root, targets, count, "", 0, "", &result);
  TuiFocus *f;
  if (!s)
    return NULL;
  f = calloc(1, sizeof(*f));
  if (!f) {
    scope_free(s);
    return NULL;
  }
  f->scopes[f->count++] = s;
  return f;
}
void tui_focus_free(TuiFocus *f) {
  if (!f)
    return;
  for (size_t i = 0; i < f->count; i++)
    scope_free(f->scopes[i]);
  free(f);
}
const char *tui_focus_focused(const TuiFocus *f) {
  return f && f->count ? scope_focused(f->scopes[f->count - 1]) : "";
}
const char *tui_focus_scope(const TuiFocus *f) {
  return f && f->count ? f->scopes[f->count - 1]->id : "";
}
size_t tui_focus_depth(const TuiFocus *f) {
  return f && f->count ? f->count - 1 : 0;
}
int tui_focus_focus(TuiFocus *f, const char *id) {
  return f && f->count && id ? scope_focus(f->scopes[f->count - 1], id) : 0;
}
const char *tui_focus_move(TuiFocus *f, int previous) {
  FocusScope *s;
  size_t at, eligible_count = 0;
  if (!f || !f->count)
    return "";
  s = f->scopes[f->count - 1];
  for (size_t i = 0; i < s->count; i++)
    if (!s->targets[i].hidden && tui_state_focusable(s->targets[i].state))
      eligible_count++;
  if (!eligible_count) {
    s->focused = s->count;
    return "";
  }
  at = s->focused < s->count ? s->focused : previous ? 0 : s->count - 1;
  for (size_t step = 0; step < s->count; step++) {
    at = previous ? (at + s->count - 1) % s->count : (at + 1) % s->count;
    if (!s->targets[at].hidden && tui_state_focusable(s->targets[at].state)) {
      s->focused = at;
      break;
    }
  }
  return scope_focused(s);
}
TuiResult tui_focus_open(TuiFocus *f, const char *id,
                         const TuiFocusTarget *targets, size_t count,
                         const char *initial, int dismissible) {
  TuiResult result;
  FocusScope *s;
  if (!f || !id || !*id || f->count >= 65)
    return TUI_INVALID;
  for (size_t i = 0; i < f->count; i++)
    if (!strcmp(f->scopes[i]->id, id))
      return TUI_INVALID;
  s = scope_new(id, targets, count, nn(initial), dismissible,
                tui_focus_focused(f), &result);
  if (!s)
    return result;
  f->scopes[f->count++] = s;
  return TUI_OK;
}
TuiResult tui_focus_update(TuiFocus *f, const char *id,
                           const TuiFocusTarget *targets, size_t count) {
  TuiResult result;
  FocusScope *next, *old;
  if (!f || !id)
    return TUI_INVALID;
  for (size_t i = 0; i < f->count; i++)
    if (!strcmp(f->scopes[i]->id, id)) {
      old = f->scopes[i];
      next = scope_new(id, targets, count, "", old->dismissible, old->restore,
                       &result);
      if (!next)
        return result;
      scope_focus(next, scope_focused(old));
      f->scopes[i] = next;
      scope_free(old);
      return TUI_OK;
    }
  return TUI_INVALID;
}
TuiResult tui_focus_close(TuiFocus *f, const char *id) {
  FocusScope *old;
  if (!f || f->count <= 1 || !id || strcmp(tui_focus_scope(f), id))
    return TUI_INVALID;
  old = f->scopes[--f->count];
  scope_focus(f->scopes[f->count - 1], old->restore);
  scope_free(old);
  return TUI_OK;
}
TuiPopupCloseRequest tui_focus_request_close(const TuiFocus *f) {
  TuiPopupCloseRequest request = {"", ""};
  if (f && f->count > 1 && f->scopes[f->count - 1]->dismissible) {
    request.id = tui_focus_scope(f);
    request.reason = "escape";
  }
  return request;
}
TuiInputRoute tui_focus_route(const TuiFocus *f, const char *target) {
  TuiInputRoute route = {tui_focus_scope(f),
                         target && *target &&
                             strcmp(target, tui_focus_scope(f))};
  return route;
}

char *tui_casefold(const char *text) {
  if (!text || strlen(text) > 16 * 1024 * 1024)
    return NULL;
  size_t n = strlen(text), p = 0;
  Buffer out = {0};
  append(&out, "");
  while (p < n) {
    size_t start = p, left = 0,
           right = sizeof(tui_fold_data) / sizeof(tui_fold_data[0]);
    unsigned cp;
    if (!decode((const unsigned char *)text, n, &p, &cp)) {
      free(out.s);
      return NULL;
    }
    while (left < right) {
      size_t m = (left + right) / 2;
      if (tui_fold_data[m].cp < cp)
        left = m + 1;
      else
        right = m;
    }
    if (left < sizeof(tui_fold_data) / sizeof(tui_fold_data[0]) &&
        tui_fold_data[left].cp == cp)
      append(&out, tui_fold_data[left].text);
    else {
      char glyph[5] = {0};
      memcpy(glyph, text + start, p - start);
      append(&out, glyph);
    }
  }
  if (out.failed) {
    free(out.s);
    return NULL;
  }
  return out.s;
}

struct TuiList {
  TuiItem *items;
  size_t count, focused;
  const char *selected, *query, *folded, *empty;
  TuiCollectionRow *rows;
  size_t row_count, start, visible_count;
  int width;
};
static void collection_rows_free(TuiCollectionRow *rows, size_t count) {
  for (size_t i = 0; i < count; i++)
    free((void *)rows[i].text);
  free(rows);
}
static void list_rows_clear(TuiList *l) {
  collection_rows_free(l->rows, l->row_count);
  l->rows = NULL;
  l->row_count = l->start = l->visible_count = 0;
}
static void list_items_free(TuiItem *items, size_t count) {
  if (!items)
    return;
  for (size_t i = 0; i < count; i++) {
    free((void *)items[i].id);
    free((void *)items[i].label);
    free((void *)items[i].secondary);
    free((void *)items[i].shortcut);
    free((void *)items[i].icon);
    free((void *)items[i].ascii_icon);
    free((void *)items[i].parent);
  }
  free(items);
}
static TuiResult list_items_copy(const TuiItem *items, size_t count,
                                 TuiItem **out) {
  TuiItem *next;
  *out = NULL;
  if ((count && !items) || count > 65536)
    return TUI_INVALID;
  for (size_t i = 0; i < count; i++) {
    if (!items[i].id || !*items[i].id)
      return TUI_INVALID;
    for (size_t j = 0; j < i; j++)
      if (!strcmp(items[i].id, items[j].id))
        return TUI_INVALID;
    const char *texts[] = {items[i].id,        items[i].label,
                           items[i].secondary, items[i].shortcut,
                           items[i].icon,      items[i].ascii_icon,
                           items[i].parent};
    for (size_t j = 0; j < 7; j++)
      if (tui_cells(nn(texts[j])) < 0)
        return TUI_INVALID;
    if (strlen(nn(items[i].label)) + strlen(nn(items[i].secondary)) + 1 >
        16 * 1024 * 1024)
      return TUI_INVALID;
  }
  next = calloc(count ? count : 1, sizeof(*next));
  if (!next)
    return TUI_NOMEM;
  for (size_t i = 0; i < count; i++) {
#define ITEM_COPY(name)                                                        \
  next[i].name = copy(nn(items[i].name));                                      \
  if (!next[i].name) {                                                         \
    list_items_free(next, count);                                              \
    return TUI_NOMEM;                                                          \
  }
    ITEM_COPY(id);
    ITEM_COPY(label);
    ITEM_COPY(secondary);
    ITEM_COPY(shortcut);
    ITEM_COPY(icon);
    ITEM_COPY(ascii_icon);
    ITEM_COPY(parent);
#undef ITEM_COPY
    next[i].disabled = items[i].disabled;
    next[i].separator = items[i].separator;
  }
  *out = next;
  return TUI_OK;
}
static int list_matches(const TuiList *l, size_t i) {
  Buffer label = {0};
  char *key;
  int result;
  if (!*l->query)
    return 1;
  if (l->items[i].separator)
    return 0;
  append(&label, l->items[i].label);
  append(&label, " ");
  append(&label, l->items[i].secondary);
  if (label.failed) {
    free(label.s);
    return -1;
  }
  key = tui_casefold(label.s);
  free(label.s);
  if (!key)
    return -1;
  result = strstr(key, l->folded) != NULL;
  free(key);
  return result;
}
static TuiResult list_indices(const TuiList *l, int eligible, size_t **out,
                              size_t *count) {
  size_t *ids = malloc((l->count ? l->count : 1) * sizeof(*ids)), used = 0;
  if (!ids)
    return TUI_NOMEM;
  for (size_t i = 0; i < l->count; i++) {
    int matches = list_matches(l, i);
    if (matches < 0) {
      free(ids);
      return TUI_NOMEM;
    }
    if (matches &&
        (!eligible || (!l->items[i].disabled && !l->items[i].separator)))
      ids[used++] = i;
  }
  *out = ids;
  *count = used;
  return TUI_OK;
}
static TuiResult list_reconcile(TuiList *l) {
  size_t *ids, count;
  TuiResult result = list_indices(l, 1, &ids, &count);
  int found = 0;
  if (result != TUI_OK)
    return result;
  for (size_t i = 0; i < count; i++)
    if (ids[i] == l->focused)
      found = 1;
  if (!found)
    l->focused = count ? ids[0] : l->count;
  free(ids);
  return TUI_OK;
}
void tui_list_free(TuiList *l) {
  if (!l)
    return;
  list_rows_clear(l);
  list_items_free(l->items, l->count);
  free((void *)l->selected);
  free((void *)l->query);
  free((void *)l->folded);
  free((void *)l->empty);
  free(l);
}
TuiList *tui_list_new(const TuiItem *items, size_t count) {
  TuiList *l = calloc(1, sizeof(*l));
  if (!l)
    return NULL;
  l->selected = copy("");
  l->query = copy("");
  l->folded = copy("");
  l->empty = copy("(empty)");
  if (!l->selected || !l->query || !l->folded || !l->empty ||
      tui_list_set_items(l, items, count) != TUI_OK) {
    tui_list_free(l);
    return NULL;
  }
  return l;
}
TuiResult tui_list_set_items(TuiList *l, const TuiItem *items, size_t count) {
  TuiItem *next;
  TuiResult result;
  TuiList candidate;
  size_t focused = count;
  int selected = 0;
  char *empty = NULL;
  if (!l)
    return TUI_INVALID;
  result = list_items_copy(items, count, &next);
  if (result != TUI_OK)
    return result;
  for (size_t i = 0; i < count; i++) {
    if (l->focused < l->count && !strcmp(next[i].id, l->items[l->focused].id))
      focused = i;
    if (!strcmp(next[i].id, l->selected))
      selected = 1;
  }
  if (!selected) {
    empty = copy("");
    if (!empty) {
      list_items_free(next, count);
      return TUI_NOMEM;
    }
  }
  candidate = *l;
  candidate.items = next;
  candidate.count = count;
  candidate.focused = focused;
  result = list_reconcile(&candidate);
  if (result != TUI_OK) {
    free(empty);
    list_items_free(next, count);
    return result;
  }
  list_rows_clear(l);
  list_items_free(l->items, l->count);
  l->items = next;
  l->count = count;
  l->focused = candidate.focused;
  if (!selected) {
    free((void *)l->selected);
    l->selected = empty;
  }
  return TUI_OK;
}
const TuiItem *tui_list_items(const TuiList *l, size_t *count) {
  if (count)
    *count = l ? l->count : 0;
  return l ? l->items : NULL;
}
const char *tui_list_focused(const TuiList *l) {
  return l && l->focused < l->count ? l->items[l->focused].id : "";
}
const char *tui_list_selected(const TuiList *l) { return l ? l->selected : ""; }
const char *tui_list_query(const TuiList *l) { return l ? l->query : ""; }
TuiResult tui_list_empty(TuiList *l, const char *label) {
  if (!l || tui_cells(nn(label)) < 0)
    return TUI_INVALID;
  return owned_string(&l->empty, label) ? TUI_OK : TUI_NOMEM;
}
int tui_list_focus(TuiList *l, const char *id) {
  if (!l || !id)
    return 0;
  for (size_t i = 0; i < l->count; i++)
    if (!strcmp(l->items[i].id, id) && !l->items[i].disabled &&
        !l->items[i].separator && list_matches(l, i) == 1) {
      l->focused = i;
      return 1;
    }
  return 0;
}
static TuiCollectionEvent list_event(const TuiList *l, const char *kind,
                                     const char *id, int query,
                                     TuiResult result) {
  TuiCollectionEvent e = {kind, id, query && l ? l->query : "", result};
  return e;
}
static char *query_clean(const char *text) {
  size_t p = 0, n;
  Buffer out = {0};
  unsigned cp;
  if (!text || strlen(text) > 16 * 1024 * 1024)
    return NULL;
  n = strlen(text);
  append(&out, "");
  while (p < n) {
    size_t start = p;
    if (!decode((const unsigned char *)text, n, &p, &cp)) {
      free(out.s);
      return NULL;
    }
    if (cp >= 32 && !(cp >= 127 && cp < 160)) {
      char glyph[5] = {0};
      memcpy(glyph, text + start, p - start);
      append(&out, glyph);
    }
  }
  if (out.failed) {
    free(out.s);
    return NULL;
  }
  return out.s;
}
TuiCollectionEvent tui_list_set_query(TuiList *l, const char *query) {
  char *next, *folded;
  TuiList candidate;
  TuiResult result;
  if (!l || !query || tui_cells(query) < 0)
    return list_event(l, "", "", 0, TUI_INVALID);
  next = query_clean(query);
  if (!next)
    return list_event(l, "", "", 0, TUI_NOMEM);
  folded = tui_casefold(next);
  if (!folded) {
    free(next);
    return list_event(l, "", "", 0, TUI_NOMEM);
  }
  candidate = *l;
  candidate.query = next;
  candidate.folded = folded;
  result = list_reconcile(&candidate);
  if (result != TUI_OK) {
    free(next);
    free(folded);
    return list_event(l, "", "", 0, result);
  }
  free((void *)l->query);
  free((void *)l->folded);
  l->query = next;
  l->folded = folded;
  l->focused = candidate.focused;
  return list_event(l, "query", "", 1, TUI_OK);
}
TuiCollectionEvent tui_list_handle(TuiList *l, const char *action, int height) {
  size_t *ids, count, at = 0;
  TuiResult result;
  if (!l || !action)
    return list_event(l, "", "", 0, TUI_INVALID);
  result = list_reconcile(l);
  if (result != TUI_OK)
    return list_event(l, "", "", 0, result);
  result = list_indices(l, 1, &ids, &count);
  if (result != TUI_OK)
    return list_event(l, "", "", 0, result);
  if (!count) {
    free(ids);
    return list_event(l, "", "", 0, TUI_OK);
  }
  for (size_t i = 0; i < count; i++)
    if (ids[i] == l->focused)
      at = i;
  if (!strcmp(action, "activate") || !strcmp(action, "select")) {
    free(ids);
    if (!owned_string(&l->selected, tui_list_focused(l)))
      return list_event(l, "", "", 0, TUI_NOMEM);
    return list_event(l, !strcmp(action, "activate") ? "activate" : "select",
                      tui_list_focused(l), 0, TUI_OK);
  }
  if (!strcmp(action, "up") || !strcmp(action, "previous"))
    at = at ? at - 1 : 0;
  else if (!strcmp(action, "down") || !strcmp(action, "next"))
    at = at + 1 < count ? at + 1 : count - 1;
  else if (!strcmp(action, "home") || !strcmp(action, "first"))
    at = 0;
  else if (!strcmp(action, "end") || !strcmp(action, "last"))
    at = count - 1;
  else if (!strcmp(action, "page_up")) {
    size_t step = (size_t)(height > 1 ? height - 1 : 1);
    at = at > step ? at - step : 0;
  } else if (!strcmp(action, "page_down")) {
    size_t step = (size_t)(height > 1 ? height - 1 : 1);
    at = at + step < count ? at + step : count - 1;
  } else {
    free(ids);
    return list_event(l, "", "", 0, TUI_OK);
  }
  l->focused = ids[at];
  free(ids);
  return list_event(l, "focus", tui_list_focused(l), 0, TUI_OK);
}
TuiCollectionEvent tui_list_click_id(TuiList *l, const char *id) {
  return tui_list_focus(l, id) ? tui_list_handle(l, "activate", 10)
                               : list_event(l, "", "", 0, TUI_OK);
}
TuiCollectionEvent tui_list_click(TuiList *l, int x, int y, int height) {
  if (!l || x < 0 || x >= l->width || y < 0 || y >= height ||
      (size_t)y >= l->visible_count)
    return list_event(l, "", "", 0, TUI_OK);
  return tui_list_click_id(l, l->rows[l->start + (size_t)y].id);
}
static int collection_row(TuiCollectionRow **rows, size_t *count,
                          const char *id, const char *text, const char *role,
                          int focused) {
  TuiCollectionRow *next = realloc(*rows, (*count + 1) * sizeof(*next));
  char *owned;
  if (!next)
    return 0;
  *rows = next;
  owned = copy(text);
  if (!owned)
    return 0;
  (*rows)[(*count)++] = (TuiCollectionRow){id, owned, role, focused};
  return 1;
}
TuiResult tui_list_layout(TuiList *l, int width, int height, int ascii,
                          const TuiCollectionRow **rows, size_t *count) {
  size_t *ids, n, anchor = 0;
  TuiResult result;
  if (!l || !rows || !count)
    return TUI_INVALID;
  list_rows_clear(l);
  width = max(0, width);
  height = max(0, height);
  result = list_indices(l, 0, &ids, &n);
  if (result != TUI_OK)
    return result;
  for (size_t j = 0; j < n; j++) {
    const TuiItem *i = &l->items[ids[j]];
    int current = ids[j] == l->focused;
    const char *role = i->disabled                   ? "disabled"
                       : !strcmp(i->id, l->selected) ? "selection"
                                                     : "body",
               *icon = ascii ? i->ascii_icon : i->icon;
    Buffer text = {0};
    if (current)
      anchor = l->row_count;
    if (i->separator) {
      append(&text, "--- ");
      append(&text, i->label);
      append(&text, " ---");
    } else {
      append(&text, current ? "> " : "  ");
      if (!strcmp(i->id, l->selected))
        append(&text, "* ");
      if (*icon) {
        append(&text, icon);
        append(&text, " ");
      }
      append(&text, i->label);
      if (*i->shortcut) {
        append(&text, " [");
        append(&text, i->shortcut);
        append(&text, "]");
      }
    }
    if (text.failed || !collection_row(&l->rows, &l->row_count, i->id, text.s,
                                       i->separator ? "hint" : role,
                                       current && !i->separator)) {
      free(text.s);
      free(ids);
      goto nomem;
    }
    free(text.s);
    if (*i->secondary && !i->separator) {
      Buffer secondary = {0};
      append(&secondary, "    ");
      append(&secondary, i->secondary);
      if (secondary.failed ||
          !collection_row(&l->rows, &l->row_count, i->id, secondary.s,
                          i->disabled ? "disabled" : "hint", 0)) {
        free(secondary.s);
        free(ids);
        goto nomem;
      }
      free(secondary.s);
    }
  }
  free(ids);
  if (!l->row_count &&
      !collection_row(&l->rows, &l->row_count, "", l->empty, "hint", 0))
    goto nomem;
  l->width = width;
  l->start = (size_t)min(max(0, (int)anchor - max(0, height - 2)),
                         max(0, (int)l->row_count - height));
  l->visible_count = (size_t)min(height, (int)(l->row_count - l->start));
  for (size_t j = l->start; j < l->start + l->visible_count; j++) {
    char *clipped = tui_clip(l->rows[j].text, width, 1);
    if (!clipped)
      goto nomem;
    free((void *)l->rows[j].text);
    l->rows[j].text = clipped;
  }
  *rows = l->rows + l->start;
  *count = l->visible_count;
  return TUI_OK;
nomem:
  list_rows_clear(l);
  *rows = NULL;
  *count = 0;
  return TUI_NOMEM;
}
TuiResult tui_list_draw(TuiList *l, TuiCanvas *c, TuiRect r, int focused,
                        int ascii) {
  const TuiCollectionRow *rows;
  size_t count;
  TuiResult result;
  if (!l || !c)
    return TUI_INVALID;
  result = tui_list_layout(l, r.width, r.height, ascii, &rows, &count);
  if (result != TUI_OK)
    return result;
  tui_canvas_fill(c, r, "surface");
  for (size_t y = 0; y < count; y++) {
    tui_canvas_fill(c, (TuiRect){r.x, r.y + (int)y, r.width, 1}, rows[y].role);
    result = tui_canvas_write(c, r.x, r.y + (int)y, rows[y].text, rows[y].role,
                              focused && rows[y].focused, r.width);
    if (result != TUI_OK)
      return result;
  }
  return TUI_OK;
}
struct TuiSearchPicker {
  TuiList *list;
  const char *value;
  int open, width, height;
  TuiCollectionRow *rows;
  size_t count;
};
TuiSearchPicker *tui_picker_new(const TuiItem *items, size_t count) {
  TuiSearchPicker *p = calloc(1, sizeof(*p));
  if (!p)
    return NULL;
  p->value = copy("");
  p->list = tui_list_new(items, count);
  if (!p->value || !p->list) {
    tui_picker_free(p);
    return NULL;
  }
  return p;
}
void tui_picker_free(TuiSearchPicker *p) {
  if (!p)
    return;
  collection_rows_free(p->rows, p->count);
  tui_list_free(p->list);
  free((void *)p->value);
  free(p);
}
TuiList *tui_picker_list(TuiSearchPicker *p) { return p ? p->list : NULL; }
int tui_picker_opened(const TuiSearchPicker *p) { return p ? p->open : 0; }
const char *tui_picker_value(const TuiSearchPicker *p) {
  return p ? p->value : "";
}
TuiCollectionEvent tui_picker_handle(TuiSearchPicker *p, const char *action,
                                     const char *text, int height) {
  TuiCollectionEvent e;
  if (!p || !action)
    return list_event(NULL, "", "", 0, TUI_INVALID);
  if (!strcmp(action, "open")) {
    e = tui_list_set_query(p->list, "");
    if (e.result != TUI_OK)
      return e;
    p->open = 1;
    tui_list_focus(p->list, p->value);
    return list_event(p->list, "open", "", 0, TUI_OK);
  }
  if (!strcmp(action, "cancel")) {
    p->open = 0;
    return list_event(p->list, "cancel", "", 0, TUI_OK);
  }
  if (!strcmp(action, "insert") || !strcmp(action, "backspace")) {
    Buffer query = {0};
    if (!p->open) {
      e = tui_picker_handle(p, "open", "", height);
      if (e.result != TUI_OK)
        return e;
    }
    append(&query, p->list->query);
    if (!strcmp(action, "insert"))
      append(&query, nn(text));
    else {
      size_t *offsets, n;
      if (raw_offsets(query.s, &offsets, &n) != 1) {
        free(query.s);
        return list_event(p->list, "", "", 0, TUI_NOMEM);
      }
      if (n)
        query.s[offsets[n - 1]] = 0;
      free(offsets);
    }
    if (query.failed) {
      free(query.s);
      return list_event(p->list, "", "", 0, TUI_NOMEM);
    }
    e = tui_list_set_query(p->list, query.s);
    free(query.s);
    return e;
  }
  if (!strcmp(action, "activate")) {
    if (!p->open)
      return tui_picker_handle(p, "open", "", height);
    e = tui_list_handle(p->list, "activate", height);
    if (*e.id && e.result == TUI_OK) {
      if (!owned_string(&p->value, e.id))
        return list_event(p->list, "", "", 0, TUI_NOMEM);
      p->open = 0;
      e.kind = "change";
    }
    return e;
  }
  return p->open ? tui_list_handle(p->list, action, height)
                 : list_event(p->list, "", "", 0, TUI_OK);
}
TuiCollectionEvent tui_picker_click_id(TuiSearchPicker *p, const char *id) {
  return p && tui_list_focus(p->list, id)
             ? tui_picker_handle(p, "activate", "", 10)
             : list_event(p ? p->list : NULL, "", "", 0, TUI_OK);
}
TuiCollectionEvent tui_picker_click(TuiSearchPicker *p, int x, int y,
                                    int height) {
  TuiCollectionEvent e;
  if (!p || x < 0 || x >= p->width || y < 0 || y >= min(height, p->height))
    return list_event(p ? p->list : NULL, "", "", 0, TUI_OK);
  if (!p->open)
    return tui_picker_handle(p, "open", "", height);
  if (y == 0)
    return list_event(p->list, "", "", 0, TUI_OK);
  e = tui_list_click(p->list, x, y - 1, max(0, height - 1));
  if (*e.id && e.result == TUI_OK) {
    if (!owned_string(&p->value, e.id))
      return list_event(p->list, "", "", 0, TUI_NOMEM);
    p->open = 0;
    e.kind = "change";
  }
  return e;
}
static char *query_tail(const char *text, int width) {
  int total = tui_cells(text), w;
  size_t pos = 0, end, n = strlen(text);
  width = max(0, width);
  while (pos < n && total > width) {
    if (!cluster(text, n, pos, &end, &w))
      return NULL;
    pos = end;
    total -= w;
  }
  return copy(text + pos);
}
TuiResult tui_picker_layout(TuiSearchPicker *p, int width, int height,
                            int ascii, const TuiCollectionRow **rows,
                            size_t *count) {
  const TuiCollectionRow *body;
  size_t n;
  TuiResult result;
  Buffer header = {0};
  char *query;
  if (!p || !rows || !count)
    return TUI_INVALID;
  collection_rows_free(p->rows, p->count);
  p->rows = NULL;
  p->count = 0;
  p->width = max(0, width);
  p->height = max(0, height);
  width = p->width;
  height = p->height;
  if (height <= 0) {
    *rows = NULL;
    *count = 0;
    return TUI_OK;
  }
  if (!p->open) {
    const char *label = p->list->empty;
    for (size_t i = 0; i < p->list->count; i++)
      if (!strcmp(p->list->items[i].id, p->value))
        label = p->list->items[i].label;
    append(&header, "v ");
    append(&header, label);
  } else {
    query = query_tail(p->list->query, max(0, width - 3));
    if (!query)
      return TUI_NOMEM;
    append(&header, "? ");
    append(&header, query);
    free(query);
  }
  if (header.failed)
    goto nomem;
  query = tui_clip(header.s, width, 0);
  free(header.s);
  header.s = NULL;
  if (!query)
    goto nomem;
  if (!collection_row(&p->rows, &p->count, p->value, query, "field", 0)) {
    free(query);
    goto nomem;
  }
  free(query);
  if (p->open) {
    result =
        tui_list_layout(p->list, width, max(0, height - 1), ascii, &body, &n);
    if (result != TUI_OK)
      goto nomem;
    for (size_t i = 0; i < n; i++)
      if (!collection_row(&p->rows, &p->count, body[i].id, body[i].text,
                          body[i].role, body[i].focused))
        goto nomem;
  }
  *rows = p->rows;
  *count = p->count;
  return TUI_OK;
nomem:
  free(header.s);
  collection_rows_free(p->rows, p->count);
  p->rows = NULL;
  p->count = 0;
  *rows = NULL;
  *count = 0;
  return TUI_NOMEM;
}
TuiResult tui_picker_draw(TuiSearchPicker *p, TuiCanvas *c, TuiRect r,
                          int focused, int ascii) {
  const TuiCollectionRow *rows;
  size_t count;
  TuiResult result;
  if (!p || !c)
    return TUI_INVALID;
  result = tui_picker_layout(p, r.width, r.height, ascii, &rows, &count);
  if (result != TUI_OK)
    return result;
  tui_canvas_fill(c, r, "surface");
  if (!p->open) {
    if (count) {
      tui_canvas_fill(c, (TuiRect){r.x, r.y, r.width, 1}, "field");
      return tui_canvas_write(c, r.x, r.y, rows[0].text, "field", 0, r.width);
    }
    return TUI_OK;
  }
  if (r.height > 0) {
    tui_canvas_fill(c, (TuiRect){r.x, r.y, r.width, 1}, "field");
    tui_canvas_write(c, r.x, r.y, "? ", "field", 0, r.width);
    if (r.width > 2) {
      TuiText *query = tui_text_new(p->list->query);
      if (!query)
        return TUI_NOMEM;
      tui_text_options(query, (TuiState){0}, 0, 0);
      result = tui_text_draw(query, c, (TuiRect){r.x + 2, r.y, r.width - 2, 1},
                             focused);
      tui_text_free(query);
      if (result != TUI_OK)
        return result;
    }
  }
  return r.height > 1
             ? tui_list_draw(p->list, c,
                             (TuiRect){r.x, r.y + 1, r.width, r.height - 1},
                             focused, ascii)
             : TUI_OK;
}

#define MENU_NONE (-1)
#define MENU_BACK (-2)
#define MENU_SEPARATOR (-3)
struct TuiMenu {
  TuiList *storage;
  TuiMenuItem *items;
  int *parents, *focus, *tops;
  size_t count;
  int path[32], depth, opened, context, bar, bar_first, width;
  const char *caller, *back_label, *empty_label;
  TuiMenuRow *rows;
  size_t row_count;
  TuiMenuBarCell *bar_cells;
  size_t bar_count;
};
static int menu_lower(int c) {
  return c >= 'A' && c <= 'Z' ? c + 'a' - 'A' : c;
}
static int menu_mnemonic(const char *s) {
  return s && s[0] && !s[1] &&
         ((s[0] >= 'A' && s[0] <= 'Z') || (s[0] >= 'a' && s[0] <= 'z') ||
          (s[0] >= '0' && s[0] <= '9'));
}
static int menu_index(const TuiMenu *m, const char *id) {
  if (!id)
    return MENU_NONE;
  if (!strcmp(id, "@back"))
    return MENU_BACK;
  for (size_t i = 0; i < m->count; i++)
    if (!strcmp(m->items[i].id, id))
      return (int)i;
  return MENU_NONE;
}
static const char *menu_id(const TuiMenu *m, int i) {
  return i == MENU_BACK                   ? "@back"
         : i >= 0 && (size_t)i < m->count ? m->items[i].id
                                          : "";
}
static int menu_parent(const TuiMenu *m) {
  return m->depth ? m->path[m->depth - 1] : MENU_NONE;
}
static int menu_back_allowed(const TuiMenu *m) {
  return m->depth > 1 || (m->context && m->depth > 0);
}
static int menu_usable(const TuiMenu *m, int i, int parent) {
  return i >= 0 && (size_t)i < m->count && m->parents[i] == parent &&
         !m->items[i].disabled && !m->items[i].separator;
}
static int menu_children(const TuiMenu *m, int parent) {
  int count = 0;
  for (size_t i = 0; i < m->count; i++)
    if (m->parents[i] == parent)
      count++;
  return count;
}
static int menu_first(const TuiMenu *m, int parent) {
  for (size_t i = 0; i < m->count; i++)
    if (menu_usable(m, (int)i, parent))
      return (int)i;
  return MENU_NONE;
}
static void menu_reconcile(TuiMenu *m) {
  int p = menu_parent(m), id = m->focus[p + 1];
  if (id == MENU_BACK && menu_back_allowed(m))
    return;
  if (!menu_usable(m, id, p)) {
    id = menu_first(m, p);
    m->focus[p + 1] = id == MENU_NONE && menu_back_allowed(m) ? MENU_BACK : id;
  }
}
static TuiMenuEvent menu_event(const TuiMenu *m, const char *kind, int id,
                               int caller, TuiResult result) {
  TuiMenuEvent e = {kind, m ? menu_id(m, id) : "", caller && m ? m->caller : "",
                    result};
  return e;
}
static void menu_rows_clear(TuiMenu *m) {
  for (size_t i = 0; i < m->row_count; i++) {
    free((void *)m->rows[i].text);
    for (size_t j = 0; j < m->rows[i].span_count; j++)
      free((void *)m->rows[i].spans[j].text);
  }
  free(m->rows);
  m->rows = NULL;
  m->row_count = 0;
}
static void menu_bar_clear(TuiMenu *m) {
  for (size_t i = 0; i < m->bar_count; i++)
    free((void *)m->bar_cells[i].text);
  free(m->bar_cells);
  m->bar_cells = NULL;
  m->bar_count = 0;
}
static void menu_clear(TuiMenu *m) {
  menu_rows_clear(m);
  menu_bar_clear(m);
  if (m->items)
    for (size_t i = 0; i < m->count; i++)
      free((void *)m->items[i].mnemonic);
  free(m->items);
  free(m->parents);
  free(m->focus);
  free(m->tops);
  tui_list_free(m->storage);
  free((void *)m->caller);
  free((void *)m->back_label);
  free((void *)m->empty_label);
}
void tui_menu_free(TuiMenu *m) {
  if (m) {
    menu_clear(m);
    free(m);
  }
}
TuiMenu *tui_menu_new(const TuiMenuItem *items, size_t count) {
  TuiMenu *m;
  TuiItem *plain;
  if ((count && !items) || count > 10000)
    return NULL;
  m = calloc(1, sizeof(*m));
  plain = calloc(count ? count : 1, sizeof(*plain));
  if (!m || !plain) {
    free(m);
    free(plain);
    return NULL;
  }
  m->bar = MENU_NONE;
  m->caller = copy("");
  m->back_label = copy("Back");
  m->empty_label = copy("(empty)");
  if (!m->caller || !m->back_label || !m->empty_label)
    goto bad;
  for (size_t i = 0; i < count; i++) {
    if (!items[i].id || !*items[i].id || items[i].id[0] == '@')
      goto bad;
    plain[i] =
        (TuiItem){items[i].id,       items[i].label,    items[i].secondary,
                  items[i].shortcut, items[i].icon,     items[i].ascii_icon,
                  items[i].parent,   items[i].disabled, items[i].separator};
    const char *key = nn(items[i].mnemonic);
    if (*key) {
      if (!menu_mnemonic(key) || items[i].separator)
        goto bad;
      for (size_t j = 0; j < i; j++)
        if (!strcmp(nn(items[i].parent), nn(items[j].parent)) &&
            *nn(items[j].mnemonic) &&
            menu_lower(key[0]) == menu_lower(items[j].mnemonic[0]))
          goto bad;
    }
  }
  m->storage = tui_list_new(plain, count);
  if (!m->storage)
    goto bad;
  m->items = calloc(count ? count : 1, sizeof(*m->items));
  m->parents = malloc((count ? count : 1) * sizeof(*m->parents));
  m->focus = malloc((count + 1) * sizeof(*m->focus));
  m->tops = calloc(count + 1, sizeof(*m->tops));
  if (!m->items || !m->parents || !m->focus || !m->tops)
    goto bad;
  m->count = count;
  for (size_t i = 0; i <= count; i++)
    m->focus[i] = MENU_NONE;
  for (size_t i = 0; i < count; i++) {
    const TuiItem *s = &m->storage->items[i];
    m->items[i] = (TuiMenuItem){
        s->id, s->parent, s->label,      s->secondary, s->shortcut,
        NULL,  s->icon,   s->ascii_icon, s->disabled,  s->separator};
    m->items[i].mnemonic = copy(nn(items[i].mnemonic));
    if (!m->items[i].mnemonic)
      goto bad;
  }
  for (size_t i = 0; i < count; i++) {
    m->parents[i] =
        *m->items[i].parent ? menu_index(m, m->items[i].parent) : MENU_NONE;
    if (*m->items[i].parent && m->parents[i] < 0)
      goto bad;
    if (m->parents[i] >= 0 && m->items[m->parents[i]].separator)
      goto bad;
  }
  for (size_t i = 0; i < count; i++) {
    int at = (int)i, depth = 0;
    while (at >= 0) {
      if (++depth > 32)
        goto bad;
      at = m->parents[at];
    }
    if (m->items[i].separator && menu_children(m, (int)i))
      goto bad;
  }
  m->bar = menu_first(m, MENU_NONE);
  free(plain);
  return m;
bad:
  free(plain);
  tui_menu_free(m);
  return NULL;
}
const TuiMenuItem *tui_menu_items(const TuiMenu *m, size_t *count) {
  if (count)
    *count = m ? m->count : 0;
  return m ? m->items : NULL;
}
int tui_menu_opened(const TuiMenu *m) { return m ? m->opened : 0; }
const char *tui_menu_focused(const TuiMenu *m) {
  return m ? menu_id(m, m->focus[menu_parent(m) + 1]) : "";
}
const char *tui_menu_return_id(const TuiMenu *m) { return m ? m->caller : ""; }
const char *tui_menu_bar_focused(const TuiMenu *m) {
  return m ? menu_id(m, m->bar) : "";
}
size_t tui_menu_path(const TuiMenu *m, const char **ids, size_t capacity) {
  if (!m)
    return 0;
  for (size_t i = 0; i < (size_t)m->depth && i < capacity; i++)
    if (ids)
      ids[i] = menu_id(m, m->path[i]);
  return (size_t)m->depth;
}
char *tui_menu_title(const TuiMenu *m) {
  Buffer b = {0};
  if (!m)
    return NULL;
  append(&b, "");
  for (int i = 0; i < m->depth; i++) {
    char *label = clean_copy(m->items[m->path[i]].label);
    if (!label) {
      free(b.s);
      return NULL;
    }
    if (i)
      append(&b, " / ");
    append(&b, label);
    free(label);
  }
  if (b.failed) {
    free(b.s);
    return NULL;
  }
  return b.s;
}
TuiResult tui_menu_labels(TuiMenu *m, const char *back, const char *empty) {
  char *b, *e;
  if (!m || tui_cells(nn(back)) < 0 || tui_cells(nn(empty)) < 0)
    return TUI_INVALID;
  b = copy(nn(back));
  e = copy(nn(empty));
  if (!b || !e) {
    free(b);
    free(e);
    return TUI_NOMEM;
  }
  free((void *)m->back_label);
  free((void *)m->empty_label);
  m->back_label = b;
  m->empty_label = e;
  return TUI_OK;
}
TuiMenuEvent tui_menu_set_items(TuiMenu *m, const TuiMenuItem *items,
                                size_t count) {
  TuiMenu *next;
  TuiMenu old;
  int invalid = 0;
  if (!m)
    return menu_event(NULL, "", MENU_NONE, 0, TUI_INVALID);
  next = tui_menu_new(items, count);
  if (!next)
    return menu_event(m, "", MENU_NONE, 0, TUI_INVALID);
  for (int p = MENU_NONE; p < (int)m->count; p++) {
    int np = p < 0 ? MENU_NONE : menu_index(next, m->items[p].id);
    if (p >= 0 && np < 0)
      continue;
    int oldfocus = m->focus[p + 1];
    next->focus[np + 1] =
        oldfocus >= 0 ? menu_index(next, m->items[oldfocus].id) : oldfocus;
    next->tops[np + 1] = m->tops[p + 1];
  }
  next->opened = m->opened;
  next->context = m->context;
  next->bar_first = m->bar_first;
  next->bar = menu_index(next, menu_id(m, m->bar));
  if (!menu_usable(next, next->bar, MENU_NONE))
    next->bar = menu_first(next, MENU_NONE);
  for (int n = 0; n < m->depth; n++) {
    int id = menu_index(next, menu_id(m, m->path[n]));
    if (!menu_usable(next, id, n ? next->path[n - 1] : MENU_NONE) ||
        !menu_children(next, id)) {
      invalid = 1;
      break;
    }
    next->path[next->depth++] = id;
  }
  free((void *)next->caller);
  free((void *)next->back_label);
  free((void *)next->empty_label);
  next->caller = m->caller;
  next->back_label = m->back_label;
  next->empty_label = m->empty_label;
  m->caller = m->back_label = m->empty_label = NULL;
  old = *m;
  *m = *next;
  free(next);
  menu_clear(&old);
  if (invalid && m->opened) {
    m->opened = 0;
    m->depth = 0;
    return menu_event(m, "close", MENU_NONE, 1, TUI_OK);
  }
  if (m->opened)
    menu_reconcile(m);
  return menu_event(m, "", MENU_NONE, 0, TUI_OK);
}
static TuiMenuEvent menu_finish(TuiMenu *m, const char *kind, int id) {
  m->opened = 0;
  m->depth = 0;
  menu_rows_clear(m);
  return menu_event(m, kind, id, 1, TUI_OK);
}
TuiMenuEvent tui_menu_open(TuiMenu *m, const char *id, const char *caller) {
  int path[32], depth = 0, at;
  char *owned;
  if (!m || !id || tui_cells(nn(caller)) < 0)
    return menu_event(m, "", MENU_NONE, 0, TUI_INVALID);
  at = *id ? menu_index(m, id) : MENU_NONE;
  if (*id && at < 0)
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  while (at >= 0) {
    if (m->items[at].disabled || m->items[at].separator)
      return menu_event(m, "", MENU_NONE, 0, TUI_OK);
    if (depth >= 32)
      return menu_event(m, "", MENU_NONE, 0, TUI_INVALID);
    path[depth++] = at;
    at = m->parents[at];
  }
  owned = copy(nn(caller));
  if (!owned)
    return menu_event(m, "", MENU_NONE, 0, TUI_NOMEM);
  free((void *)m->caller);
  m->caller = owned;
  m->depth = depth;
  for (int n = 0; n < depth; n++)
    m->path[n] = path[depth - 1 - n];
  for (int n = 0; n < depth; n++)
    m->focus[(n ? m->path[n - 1] : MENU_NONE) + 1] = m->path[n];
  menu_rows_clear(m);
  m->context = !*id;
  m->opened = 1;
  if (depth)
    m->bar = m->path[0];
  at = *id ? menu_index(m, id) : MENU_NONE;
  if (at >= 0 && !menu_children(m, at))
    return menu_finish(m, "activate", at);
  menu_reconcile(m);
  return menu_event(m, "open", at, 1, TUI_OK);
}
TuiMenuEvent tui_menu_close(TuiMenu *m) {
  return m && m->opened ? menu_finish(m, "close", MENU_NONE)
                        : menu_event(m, "", MENU_NONE, 0, TUI_OK);
}
TuiMenuEvent tui_menu_back(TuiMenu *m) {
  if (!m || !m->opened)
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  if (!menu_back_allowed(m))
    return tui_menu_close(m);
  m->depth--;
  menu_reconcile(m);
  return menu_event(m, "back", menu_parent(m), 1, TUI_OK);
}
int tui_menu_focus(TuiMenu *m, const char *id) {
  int n;
  if (!m || !m->opened || !id)
    return 0;
  n = menu_index(m, id);
  if ((n == MENU_BACK && menu_back_allowed(m)) ||
      menu_usable(m, n, menu_parent(m))) {
    m->focus[menu_parent(m) + 1] = n;
    return 1;
  }
  return 0;
}
static TuiMenuEvent menu_enter(TuiMenu *m, int id) {
  if (m->depth >= 32)
    return menu_event(m, "", MENU_NONE, 0, TUI_INVALID);
  m->path[m->depth++] = id;
  menu_reconcile(m);
  return menu_event(m, "open", id, 1, TUI_OK);
}
static TuiMenuEvent menu_switch_root(TuiMenu *m, int next) {
  int *ids = malloc((m->count ? m->count : 1) * sizeof(*ids));
  size_t count = 0, at = 0, step;
  if (!ids)
    return menu_event(m, "", MENU_NONE, 0, TUI_NOMEM);
  for (size_t i = 0; i < m->count; i++)
    if (menu_usable(m, (int)i, MENU_NONE)) {
      if ((int)i == m->bar)
        at = count;
      ids[count++] = (int)i;
    }
  if (!count) {
    free(ids);
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  }
  step = next ? 1 : count - 1;
  for (size_t n = 0; n < count; n++) {
    at = (at + step) % count;
    if (ids[at] != m->bar && menu_children(m, ids[at])) {
      int id = ids[at];
      free(ids);
      return tui_menu_open(m, menu_id(m, id), m->caller);
    }
  }
  free(ids);
  return menu_event(m, "", MENU_NONE, 0, TUI_OK);
}
TuiMenuEvent tui_menu_handle(TuiMenu *m, const char *action, const char *value,
                             int height) {
  int p, id, *ids;
  size_t count = 0, at = 0, step = (size_t)(height > 1 ? height - 1 : 1);
  if (!m || !action)
    return menu_event(m, "", MENU_NONE, 0, TUI_INVALID);
  if (!m->opened)
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  menu_reconcile(m);
  p = menu_parent(m);
  id = m->focus[p + 1];
  value = nn(value);
  if (!strcmp(action, "cancel") || !strcmp(action, "back"))
    return tui_menu_back(m);
  if (!strcmp(action, "close"))
    return tui_menu_close(m);
  if (!strcmp(action, "left"))
    return menu_back_allowed(m) ? tui_menu_back(m)
           : m->context         ? menu_event(m, "", MENU_NONE, 0, TUI_OK)
                                : menu_switch_root(m, 0);
  if (!strcmp(action, "right")) {
    if (menu_usable(m, id, p) && menu_children(m, id))
      return menu_enter(m, id);
    return !menu_back_allowed(m) && !m->context
               ? menu_switch_root(m, 1)
               : menu_event(m, "", MENU_NONE, 0, TUI_OK);
  }
  if (!strcmp(action, "activate")) {
    if (id == MENU_BACK)
      return tui_menu_back(m);
    if (!menu_usable(m, id, p))
      return menu_event(m, "", MENU_NONE, 0, TUI_OK);
    return menu_children(m, id) ? menu_enter(m, id)
                                : menu_finish(m, "activate", id);
  }
  if (!strcmp(action, "mnemonic")) {
    if (!menu_mnemonic(value))
      return menu_event(m, "", MENU_NONE, 0, TUI_OK);
    for (size_t i = 0; i < m->count; i++)
      if (menu_usable(m, (int)i, p) && *m->items[i].mnemonic &&
          menu_lower(m->items[i].mnemonic[0]) == menu_lower(value[0])) {
        m->focus[p + 1] = (int)i;
        return tui_menu_handle(m, "activate", "", height);
      }
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  }
  ids = malloc((m->count + 1) * sizeof(*ids));
  if (!ids)
    return menu_event(m, "", MENU_NONE, 0, TUI_NOMEM);
  if (menu_back_allowed(m))
    ids[count++] = MENU_BACK;
  for (size_t i = 0; i < m->count; i++)
    if (menu_usable(m, (int)i, p))
      ids[count++] = (int)i;
  if (!count) {
    free(ids);
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  }
  for (size_t i = 0; i < count; i++)
    if (ids[i] == id)
      at = i;
  if (!strcmp(action, "previous") || !strcmp(action, "up"))
    at = (at + count - 1) % count;
  else if (!strcmp(action, "next") || !strcmp(action, "down"))
    at = (at + 1) % count;
  else if (!strcmp(action, "first") || !strcmp(action, "home"))
    at = 0;
  else if (!strcmp(action, "last") || !strcmp(action, "end"))
    at = count - 1;
  else if (!strcmp(action, "page_up"))
    at = at > step ? at - step : 0;
  else if (!strcmp(action, "page_down"))
    at = at + step < count ? at + step : count - 1;
  else {
    free(ids);
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  }
  m->focus[p + 1] = ids[at];
  id = ids[at];
  free(ids);
  return menu_event(m, "focus", id, 1, TUI_OK);
}
TuiMenuEvent tui_menu_handle_bar(TuiMenu *m, const char *action,
                                 const char *value) {
  int *ids, id;
  size_t count = 0, at = 0;
  if (!m || !action)
    return menu_event(m, "", MENU_NONE, 0, TUI_INVALID);
  ids = malloc((m->count ? m->count : 1) * sizeof(*ids));
  if (!ids)
    return menu_event(m, "", MENU_NONE, 0, TUI_NOMEM);
  for (size_t i = 0; i < m->count; i++)
    if (menu_usable(m, (int)i, MENU_NONE)) {
      if ((int)i == m->bar)
        at = count;
      ids[count++] = (int)i;
    }
  if (!count) {
    free(ids);
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  }
  if (!strcmp(action, "previous") || !strcmp(action, "left"))
    at = (at + count - 1) % count;
  else if (!strcmp(action, "next") || !strcmp(action, "right"))
    at = (at + 1) % count;
  else if (!strcmp(action, "first") || !strcmp(action, "home"))
    at = 0;
  else if (!strcmp(action, "last") || !strcmp(action, "end"))
    at = count - 1;
  else if (!strcmp(action, "activate") || !strcmp(action, "down")) {
    id = ids[at];
    free(ids);
    return menu_event(m, "open_request", id, 0, TUI_OK);
  } else if (!strcmp(action, "mnemonic")) {
    if (menu_mnemonic(nn(value)))
      for (size_t i = 0; i < count; i++)
        if (*m->items[ids[i]].mnemonic &&
            menu_lower(m->items[ids[i]].mnemonic[0]) == menu_lower(value[0])) {
          m->bar = id = ids[i];
          free(ids);
          return menu_event(m, "open_request", id, 0, TUI_OK);
        }
    free(ids);
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  } else {
    free(ids);
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  }
  m->bar = id = ids[at];
  free(ids);
  return menu_event(m, "focus", id, 0, TUI_OK);
}
TuiMenuEvent tui_menu_click_id(TuiMenu *m, const char *id) {
  return tui_menu_focus(m, id) ? tui_menu_handle(m, "activate", "", 1)
                               : menu_event(m, "", MENU_NONE, 0, TUI_OK);
}
TuiMenuEvent tui_menu_click(TuiMenu *m, int x, int y, int height) {
  if (!m || !m->opened || x < 0 || x >= m->width || y < 0 || y >= height ||
      (size_t)y >= m->row_count)
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  return tui_menu_click_id(m, m->rows[y].id);
}
static char *menu_label(const TuiMenuItem *i) {
  Buffer b = {0};
  append(&b, nn(i->label));
  if (*nn(i->mnemonic)) {
    char key[2] = {(char)(i->mnemonic[0] >= 'a' && i->mnemonic[0] <= 'z'
                              ? i->mnemonic[0] - ('a' - 'A')
                              : i->mnemonic[0]),
                   0};
    append(&b, " (");
    append(&b, key);
    append(&b, ")");
  }
  if (b.failed) {
    free(b.s);
    return NULL;
  }
  return b.s;
}
static TuiResult menu_row_ids(const TuiMenu *m, int **out, size_t *count) {
  int *ids = malloc((m->count + 2) * sizeof(*ids));
  size_t n = 0;
  if (!ids)
    return TUI_NOMEM;
  if (menu_back_allowed(m)) {
    ids[n++] = MENU_BACK;
    ids[n++] = MENU_SEPARATOR;
  }
  for (size_t i = 0; i < m->count; i++)
    if (m->parents[i] == menu_parent(m))
      ids[n++] = (int)i;
  *out = ids;
  *count = n;
  return TUI_OK;
}
TuiResult tui_menu_content_size(const TuiMenu *m, int *width, int *height) {
  int *ids, w = 12;
  size_t n;
  TuiResult result;
  if (!m || !width || !height)
    return TUI_INVALID;
  result = menu_row_ids(m, &ids, &n);
  if (result != TUI_OK)
    return result;
  for (size_t j = 0; j < n; j++) {
    int id = ids[j];
    TuiMenuItem back = {.id = "@back", .label = m->back_label};
    const TuiMenuItem *i = id >= 0 ? &m->items[id] : &back;
    char *label = menu_label(i);
    if (!label) {
      free(ids);
      return TUI_NOMEM;
    }
    w = max(w, tui_cells(label) + tui_cells(nn(i->secondary)) +
                   tui_cells(nn(i->shortcut)) + tui_cells(nn(i->icon)) + 8);
    free(label);
  }
  free(ids);
  *width = min(w, 4096);
  *height = max(1, (int)n);
  return TUI_OK;
}
static TuiResult menu_add_row(TuiMenu *m, TuiMenuRow row) {
  TuiMenuRow *next = realloc(m->rows, (m->row_count + 1) * sizeof(*next));
  if (!next) {
    free((void *)row.text);
    for (size_t i = 0; i < row.span_count; i++)
      free((void *)row.spans[i].text);
    return TUI_NOMEM;
  }
  m->rows = next;
  m->rows[m->row_count++] = row;
  return TUI_OK;
}
TuiResult tui_menu_layout(TuiMenu *m, int width, int height, int ascii,
                          const TuiMenuRow **rows, size_t *count) {
  int *ids = NULL, at = 0, p, top;
  size_t n = 0;
  TuiResult result;
  if (!m || !rows || !count)
    return TUI_INVALID;
  menu_rows_clear(m);
  m->width = width = max(0, min(65535, width));
  height = max(0, min(4096, height));
  *rows = NULL;
  *count = 0;
  if (!m->opened || !width || !height)
    return TUI_OK;
  menu_reconcile(m);
  result = menu_row_ids(m, &ids, &n);
  if (result != TUI_OK)
    return result;
  if (!n) {
    char *text = tui_clip(m->empty_label, width, 1);
    free(ids);
    if (!text)
      return TUI_NOMEM;
    result =
        menu_add_row(m, (TuiMenuRow){.id = "", .text = text, .role = "hint"});
    if (result != TUI_OK)
      return result;
    *rows = m->rows;
    *count = m->row_count;
    return TUI_OK;
  }
  p = menu_parent(m);
  for (size_t i = 0; i < n; i++)
    if (ids[i] == m->focus[p + 1])
      at = (int)i;
  top = min(m->tops[p + 1], at);
  if (at >= top + height)
    top = at - height + 1;
  top = min(top, max(0, (int)n - height));
  m->tops[p + 1] = top;
  for (int j = top; j < min(top + height, (int)n); j++) {
    int id = ids[j];
    TuiMenuItem back = {.id = "@back", .label = m->back_label};
    const TuiMenuItem *i = id >= 0 ? &m->items[id] : &back;
    TuiMenuRow row = {0};
    Buffer text = {0}, tail = {0}, combined = {0};
    char *label = NULL, *shortcut = NULL, *left = NULL, *right = NULL;
    int separator = id == MENU_SEPARATOR || (id >= 0 && i->separator),
        current = id == m->focus[p + 1], reserve, tw;
    const char *role, *icon, *suffix;
    if (separator) {
      for (int x = 0; x < width; x++)
        append(&text, ascii ? "-" : "─");
      if (text.failed) {
        free(text.s);
        result = TUI_NOMEM;
        goto failed;
      }
      result = menu_add_row(
          m, (TuiMenuRow){.id = "", .text = text.s, .role = "hint"});
      if (result != TUI_OK)
        goto failed;
      continue;
    }
    role = i->disabled ? "disabled" : current ? "selection" : "surface";
    icon = ascii ? (*nn(i->ascii_icon) ? i->ascii_icon
                    : *nn(i->icon)     ? "*"
                                       : "")
                 : nn(i->icon);
    append(&text, current ? "> " : "  ");
    if (*icon) {
      append(&text, icon);
      append(&text, " ");
    }
    if (id == MENU_BACK) {
      append(&text, "< ");
      append(&text, i->label);
    } else {
      label = menu_label(i);
      if (!label)
        goto row_nomem;
      append(&text, label);
    }
    if (*nn(i->secondary)) {
      append(&text, "  ");
      append(&text, i->secondary);
    }
    suffix = id >= 0 && menu_children(m, id) ? (ascii ? " >" : " ›") : "";
    shortcut = clean_copy(nn(i->shortcut));
    if (!shortcut)
      goto row_nomem;
    reserve = min(width / 3, tui_cells(shortcut));
    if (reserve) {
      char *clipped = tui_clip(shortcut, reserve, 0);
      if (!clipped)
        goto row_nomem;
      append(&tail, " ");
      append(&tail, clipped);
      free(clipped);
    }
    append(&tail, suffix);
    if (text.failed || tail.failed)
      goto row_nomem;
    tw = min(width, tui_cells(tail.s));
    left = tui_clip(text.s, width - tw, 1);
    right = tui_clip(tail.s, tw, 0);
    if (!left || !right)
      goto row_nomem;
    append(&combined, left);
    for (int spaces = width - tw - tui_cells(left); spaces > 0; spaces--)
      append(&combined, " ");
    append(&combined, right);
    if (combined.failed)
      goto row_nomem;
    row.id = menu_id(m, id);
    row.text = combined.s;
    combined.s = NULL;
    row.role = role;
    row.focused = current;
    row.spans[0] = (TuiMenuSpan){0, width, left, role};
    left = NULL;
    row.span_count = 1;
    if (tw) {
      row.spans[1] = (TuiMenuSpan){width - tw, tw, right,
                                   !strcmp(role, "surface") ? "hint" : role};
      right = NULL;
      row.span_count = 2;
    }
    result = menu_add_row(m, row);
    free(label);
    free(shortcut);
    free(left);
    free(right);
    free(text.s);
    free(tail.s);
    if (result != TUI_OK)
      goto failed;
    continue;
  row_nomem:
    free(label);
    free(shortcut);
    free(left);
    free(right);
    free(text.s);
    free(tail.s);
    free(combined.s);
    result = TUI_NOMEM;
    goto failed;
  }
  free(ids);
  *rows = m->rows;
  *count = m->row_count;
  return TUI_OK;
failed:
  free(ids);
  menu_rows_clear(m);
  return result;
}
TuiResult tui_menu_draw(TuiMenu *m, TuiCanvas *c, TuiRect r, int ascii) {
  const TuiMenuRow *rows;
  size_t count;
  TuiResult result;
  if (!m || !c)
    return TUI_INVALID;
  if (!m->opened)
    return TUI_OK;
  result = tui_menu_layout(m, r.width, r.height, ascii, &rows, &count);
  if (result != TUI_OK)
    return result;
  tui_canvas_fill(c, r, "surface");
  for (size_t y = 0; y < count; y++) {
    const TuiMenuRow *row = &rows[y];
    tui_canvas_fill(c, (TuiRect){r.x, r.y + (int)y, r.width, 1}, row->role);
    if (!row->span_count) {
      result = tui_canvas_write(c, r.x, r.y + (int)y, row->text, row->role, 0,
                                r.width);
      if (result != TUI_OK)
        return result;
    }
    for (size_t j = 0; j < row->span_count; j++) {
      const TuiMenuSpan *s = &row->spans[j];
      result = tui_canvas_write(c, r.x + s->start, r.y + (int)y, s->text,
                                s->role, 0, s->width);
      if (result != TUI_OK)
        return result;
    }
  }
  return TUI_OK;
}
TuiResult tui_menu_draw_popup(TuiMenu *m, TuiCanvas *c, TuiRect r,
                              const char *title, int padding, int ascii,
                              TuiRect *content) {
  if (!m || !c || !content || !title)
    return TUI_INVALID;
  *content = (TuiRect){r.x, r.y, 0, 0};
  if (!m->opened)
    return TUI_OK;
  TuiRect inner = tui_canvas_panel(c, r, title, 0, ascii);
  if (padding < 0)
    padding = 0;
  if (padding > 4096)
    padding = 4096;
  int px = padding < inner.width / 2 ? padding : inner.width / 2;
  int py = padding < inner.height / 2 ? padding : inner.height / 2;
  *content = (TuiRect){inner.x + px, inner.y + py, inner.width - 2 * px,
                       inner.height - 2 * py};
  return tui_menu_draw(m, c, *content, ascii);
}
TuiResult tui_menu_bar_layout(TuiMenu *m, int width, TuiMenuBarLayout *out) {
  int *ids = NULL, *sizes = NULL;
  size_t n = 0;
  int target = 0, last, x = 1, total;
  TuiResult result = TUI_OK;
  if (!m || !out)
    return TUI_INVALID;
  menu_bar_clear(m);
  *out = (TuiMenuBarLayout){0};
  width = max(0, min(65535, width));
  if (width < 3)
    return TUI_OK;
  ids = malloc((m->count ? m->count : 1) * sizeof(*ids));
  sizes = malloc((m->count ? m->count : 1) * sizeof(*sizes));
  if (!ids || !sizes)
    goto nomem;
  for (size_t i = 0; i < m->count; i++)
    if (m->parents[i] == MENU_NONE && !m->items[i].separator) {
      char *label = menu_label(&m->items[i]);
      if (!label)
        goto nomem;
      ids[n] = (int)i;
      sizes[n] = min(24, tui_cells(label) + 2);
      free(label);
      if ((int)i == m->bar)
        target = (int)n;
      n++;
    }
  if (!n) {
    free(ids);
    free(sizes);
    return TUI_OK;
  }
  m->bar_first = min(m->bar_first, target);
  while (m->bar_first < target) {
    total = 0;
    for (int j = m->bar_first; j <= target; j++)
      total += sizes[j];
    if (total <= width - 2)
      break;
    m->bar_first++;
  }
  while (m->bar_first > 0) {
    total = 0;
    for (int j = m->bar_first - 1; j <= target; j++)
      total += sizes[j];
    if (total > width - 2)
      break;
    m->bar_first--;
  }
  last = m->bar_first;
  for (int j = m->bar_first; j < (int)n && x < width - 1; j++) {
    const TuiMenuItem *i = &m->items[ids[j]];
    int w = min(sizes[j], width - 1 - x), current = ids[j] == m->bar;
    const char *role = i->disabled ? "disabled"
                       : current   ? "selection"
                                   : "header";
    Buffer text = {0};
    char *label = menu_label(i), *clipped;
    TuiMenuBarCell *next;
    if (!label)
      goto nomem;
    append(&text, " ");
    append(&text, label);
    append(&text, " ");
    free(label);
    if (text.failed) {
      free(text.s);
      goto nomem;
    }
    clipped = tui_clip(text.s, w, 1);
    free(text.s);
    if (!clipped)
      goto nomem;
    next = realloc(m->bar_cells, (m->bar_count + 1) * sizeof(*next));
    if (!next) {
      free(clipped);
      goto nomem;
    }
    m->bar_cells = next;
    m->bar_cells[m->bar_count++] =
        (TuiMenuBarCell){i->id, clipped, role, x, w, current};
    x += w;
    last = j + 1;
  }
  out->cells = m->bar_cells;
  out->count = m->bar_count;
  out->previous = m->bar_first > 0;
  out->next = last < (int)n;
  free(ids);
  free(sizes);
  return result;
nomem:
  free(ids);
  free(sizes);
  menu_bar_clear(m);
  return TUI_NOMEM;
}
TuiMenuEvent tui_menu_bar_click(TuiMenu *m, int x, int width) {
  TuiMenuBarLayout l;
  TuiResult result;
  if (!m || x < 0 || x >= width)
    return menu_event(m, "", MENU_NONE, 0, TUI_OK);
  result = tui_menu_bar_layout(m, width, &l);
  if (result != TUI_OK)
    return menu_event(m, "", MENU_NONE, 0, result);
  if (x == 0 && l.previous)
    return tui_menu_handle_bar(m, "previous", "");
  if (x + 1 == width && l.next)
    return tui_menu_handle_bar(m, "next", "");
  for (size_t i = 0; i < l.count; i++)
    if (x >= l.cells[i].start && x < l.cells[i].start + l.cells[i].width) {
      int id = menu_index(m, l.cells[i].id);
      if (menu_usable(m, id, MENU_NONE)) {
        m->bar = id;
        return menu_event(m, "open_request", id, 0, TUI_OK);
      }
    }
  return menu_event(m, "", MENU_NONE, 0, TUI_OK);
}
TuiResult tui_menu_draw_bar(TuiMenu *m, TuiCanvas *c, TuiRect r) {
  TuiMenuBarLayout l;
  TuiResult result;
  if (!m || !c)
    return TUI_INVALID;
  if (r.height <= 0)
    return TUI_OK;
  result = tui_menu_bar_layout(m, r.width, &l);
  if (result != TUI_OK)
    return result;
  tui_canvas_fill(c, (TuiRect){r.x, r.y, r.width, 1}, "surface");
  for (size_t i = 0; i < l.count; i++) {
    const TuiMenuBarCell *cell = &l.cells[i];
    tui_canvas_fill(c, (TuiRect){r.x + cell->start, r.y, cell->width, 1},
                    cell->role);
    result = tui_canvas_write(c, r.x + cell->start, r.y, cell->text, cell->role,
                              0, cell->width);
    if (result != TUI_OK)
      return result;
  }
  if (l.previous)
    tui_canvas_write(c, r.x, r.y, "<", "hint", 0, 1);
  if (l.next)
    tui_canvas_write(c, r.x + r.width - 1, r.y, ">", "hint", 0, 1);
  return TUI_OK;
}
TuiRect tui_menu_placement(TuiRect anchor, TuiRect viewport, int width,
                           int height) {
  long long vw = max(0, viewport.width), vh = max(0, viewport.height),
            w = max(0, width), h = max(0, height), x = anchor.x,
            y = (long long)anchor.y + max(0, anchor.height), hi;
  if (w > vw)
    w = vw;
  if (h > vh)
    h = vh;
  hi = (long long)viewport.x + vw - w;
  if (x < viewport.x)
    x = viewport.x;
  if (x > hi)
    x = hi;
  if (y + h > (long long)viewport.y + vh)
    y = (long long)anchor.y - h;
  hi = (long long)viewport.y + vh - h;
  if (y < viewport.y)
    y = viewport.y;
  if (y > hi)
    y = hi;
  return (TuiRect){(int)x, (int)y, (int)w, (int)h};
}

/* Independent feedback implementation; clocks and actions belong to hosts. */
struct TuiFeedbackView {
  TuiFeedbackRow *rows;
  size_t count;
};
struct TuiNoticeEvents {
  TuiNoticeEvent *events;
  size_t count;
};
struct TuiNoticeQueue {
  TuiNotice *items, *visible;
  size_t count, capacity;
  int focused, width;
  TuiFeedbackView *hits;
};
static const char *feedback_string(const char *s) { return s ? s : ""; }
static int feedback_number(unsigned long long value) {
  return value <= 9007199254740991ULL;
}
static int notice_severity(const char *s) {
  if (!s || !strcmp(s, "info"))
    return 0;
  return !strcmp(s, "success")   ? 1
         : !strcmp(s, "warning") ? 2
         : !strcmp(s, "error")   ? 3
                                 : -1;
}
static TuiNoticeEvent notice_event(const char *kind, const char *id,
                                   const char *action, TuiResult result) {
  return (TuiNoticeEvent){feedback_string(kind), feedback_string(id),
                          feedback_string(action), result};
}
static TuiFeedbackView *feedback_new(size_t count) {
  TuiFeedbackView *v = calloc(1, sizeof *v);
  if (!v)
    return NULL;
  if (count) {
    v->rows = calloc(count, sizeof *v->rows);
    if (!v->rows) {
      free(v);
      return NULL;
    }
  }
  v->count = count;
  return v;
}
void tui_feedback_free(TuiFeedbackView *v) {
  if (!v)
    return;
  for (size_t i = 0; i < v->count; i++) {
    TuiFeedbackRow *r = &v->rows[i];
    free((void *)r->id);
    free((void *)r->text);
    free((void *)r->role);
    for (size_t j = 0; j < r->span_count; j++) {
      free((void *)r->spans[j].text);
      free((void *)r->spans[j].role);
      free((void *)r->spans[j].action);
    }
    free((void *)r->spans);
  }
  free(v->rows);
  free(v);
}
size_t tui_feedback_count(const TuiFeedbackView *v) { return v ? v->count : 0; }
const TuiFeedbackRow *tui_feedback_row(const TuiFeedbackView *v, size_t index) {
  return v && index < v->count ? &v->rows[index] : NULL;
}
static TuiResult feedback_row_set(TuiFeedbackRow *row, const char *id,
                                  const char *text, const char *role,
                                  int width) {
  row->id = copy(id);
  row->text = tui_clip(feedback_string(text), width, 1);
  row->role = copy(role);
  return row->id && row->text && row->role ? TUI_OK : TUI_NOMEM;
}
static TuiResult feedback_paint(const TuiFeedbackRow *rows, size_t count,
                                TuiCanvas *c, TuiRect r) {
  if (!c)
    return TUI_INVALID;
  TuiResult result = tui_canvas_fill(c, r, "surface");
  if (result != TUI_OK)
    return result;
  for (size_t y = 0; y < count && y < (size_t)max(0, r.height); y++) {
    const TuiFeedbackRow *row = &rows[y];
    result = tui_canvas_write(c, r.x, r.y + (int)y, row->text, row->role, 0,
                              r.width);
    if (result != TUI_OK)
      return result;
    for (size_t j = 0; j < row->span_count; j++) {
      const TuiFeedbackSpan *s = &row->spans[j];
      result = tui_canvas_write(c, r.x + s->start, r.y + (int)y, s->text,
                                s->role, 0, s->width);
      if (result != TUI_OK)
        return result;
    }
  }
  return TUI_OK;
}
TuiResult tui_feedback_draw(const TuiFeedbackView *v, TuiCanvas *c, TuiRect r) {
  return v ? feedback_paint(v->rows, v->count, c, r) : TUI_INVALID;
}
static void notice_clear(TuiNotice *n) {
  free((void *)n->id);
  free((void *)n->text);
  free((void *)n->detail);
  free((void *)n->severity);
  for (size_t i = 0; i < n->action_count; i++) {
    free((void *)n->actions[i].id);
    free((void *)n->actions[i].label);
  }
  free((void *)n->actions);
  memset(n, 0, sizeof *n);
}
static TuiResult notice_copy(const TuiNotice *source, TuiNotice *out) {
  memset(out, 0, sizeof *out);
  if (!source || !source->id || !*source->id ||
      notice_severity(source->severity) < 0 ||
      !feedback_number(source->expires_at) || source->action_count > 1024 ||
      (source->action_count && !source->actions))
    return TUI_INVALID;
  const char *texts[] = {source->id, source->text, source->detail,
                         source->severity};
  for (size_t i = 0; i < 4; i++)
    if (tui_cells(feedback_string(texts[i])) < 0)
      return TUI_INVALID;
  for (size_t i = 0; i < source->action_count; i++) {
    const TuiNoticeAction *a = &source->actions[i];
    if (!a->id || !*a->id || tui_cells(a->id) < 0 ||
        tui_cells(feedback_string(a->label)) < 0)
      return TUI_INVALID;
    for (size_t j = 0; j < i; j++)
      if (!strcmp(a->id, source->actions[j].id))
        return TUI_INVALID;
  }
  out->id = copy(source->id);
  out->text = copy(source->text);
  out->detail = copy(source->detail);
  out->severity = copy(source->severity ? source->severity : "info");
  out->priority = source->priority;
  out->expires_at = source->expires_at;
  out->persistent = source->persistent;
  if (!out->id || !out->text || !out->detail || !out->severity)
    goto nomem;
  if (source->action_count) {
    TuiNoticeAction *actions = calloc(source->action_count, sizeof *actions);
    if (!actions)
      goto nomem;
    out->actions = actions;
    out->action_count = source->action_count;
    for (size_t i = 0; i < source->action_count; i++) {
      actions[i].id = copy(source->actions[i].id);
      actions[i].label = copy(source->actions[i].label);
      actions[i].disabled = source->actions[i].disabled;
      if (!actions[i].id || !actions[i].label)
        goto nomem;
    }
  }
  return TUI_OK;
nomem:
  notice_clear(out);
  return TUI_NOMEM;
}
static int notice_pinned(const TuiNotice *n) {
  return n->persistent || !strcmp(n->severity, "error") || n->action_count > 0;
}
static int notice_expired(const TuiNotice *n, unsigned long long now) {
  return !notice_pinned(n) && n->expires_at > 0 && n->expires_at <= now;
}
static void notice_invalidate(TuiNoticeQueue *q) {
  free(q->visible);
  q->visible = NULL;
  tui_feedback_free(q->hits);
  q->hits = NULL;
}
TuiNoticeQueue *tui_notice_queue_new(size_t capacity) {
  if (!capacity || capacity > 65536)
    return NULL;
  TuiNoticeQueue *q = calloc(1, sizeof *q);
  if (q) {
    q->capacity = capacity;
    q->focused = -1;
  }
  return q;
}
void tui_notice_queue_free(TuiNoticeQueue *q) {
  if (q) {
    for (size_t i = 0; i < q->count; i++)
      notice_clear(&q->items[i]);
    free(q->items);
    notice_invalidate(q);
    free(q);
  }
}
const TuiNotice *tui_notice_queue_items(const TuiNoticeQueue *q,
                                        size_t *count) {
  if (count)
    *count = q ? q->count : 0;
  return q ? q->items : NULL;
}
const char *tui_notice_queue_focused(const TuiNoticeQueue *q) {
  return q && q->focused >= 0 && (size_t)q->focused < q->count
             ? q->items[q->focused].id
             : "";
}
TuiResult tui_notice_queue_push(TuiNoticeQueue *q, const TuiNotice *source) {
  if (!q)
    return TUI_INVALID;
  TuiNotice n;
  TuiResult result = notice_copy(source, &n);
  if (result != TUI_OK)
    return result;
  for (size_t i = 0; i < q->count; i++)
    if (!strcmp(q->items[i].id, n.id)) {
      notice_clear(&q->items[i]);
      q->items[i] = n;
      notice_invalidate(q);
      return TUI_OK;
    }
  int evict = -1;
  if (q->count >= q->capacity) {
    for (size_t i = 0; i < q->count; i++) {
      const TuiNotice *old = &q->items[i];
      if (notice_pinned(old))
        continue;
      if (evict < 0 ||
          notice_severity(old->severity) <
              notice_severity(q->items[evict].severity) ||
          (notice_severity(old->severity) ==
               notice_severity(q->items[evict].severity) &&
           old->priority < q->items[evict].priority))
        evict = (int)i;
    }
    if (evict < 0) {
      notice_clear(&n);
      return TUI_INVALID;
    }
    const TuiNotice *old = &q->items[evict];
    if (notice_severity(old->severity) > notice_severity(n.severity) ||
        (notice_severity(old->severity) == notice_severity(n.severity) &&
         old->priority > n.priority)) {
      notice_clear(&n);
      return TUI_INVALID;
    }
  } else {
    TuiNotice *items = realloc(q->items, (q->count + 1) * sizeof *items);
    if (!items) {
      notice_clear(&n);
      return TUI_NOMEM;
    }
    q->items = items;
  }
  if (evict >= 0) {
    notice_clear(&q->items[evict]);
    memmove(&q->items[evict], &q->items[evict + 1],
            (q->count - (size_t)evict - 1) * sizeof *q->items);
    q->count--;
    if (q->focused == evict)
      q->focused = -1;
    else if (q->focused > evict)
      q->focused--;
  }
  if (q->focused < 0 || !strcmp(n.severity, "error"))
    q->focused = (int)q->count;
  q->items[q->count++] = n;
  notice_invalidate(q);
  return TUI_OK;
}
static int notice_before(const TuiNotice *a, const TuiNotice *b) {
  int ra = notice_severity(a->severity), rb = notice_severity(b->severity);
  return ra > rb || (ra == rb && a->priority >= b->priority);
}
TuiResult tui_notice_queue_visible(TuiNoticeQueue *q, unsigned long long now,
                                   const TuiNotice **items, size_t *count) {
  if (!q || !items || !count || !feedback_number(now))
    return TUI_INVALID;
  *items = NULL;
  *count = 0;
  size_t n = 0;
  for (size_t i = 0; i < q->count; i++)
    if (!notice_expired(&q->items[i], now))
      n++;
  TuiNotice *out = n ? malloc(n * sizeof *out) : NULL,
            *temp = n ? malloc(n * sizeof *temp) : NULL;
  if (n && (!out || !temp)) {
    free(out);
    free(temp);
    return TUI_NOMEM;
  }
  size_t at = 0;
  for (size_t i = 0; i < q->count; i++)
    if (!notice_expired(&q->items[i], now))
      out[at++] = q->items[i];
  for (size_t width = 1; width < n; width *= 2) {
    for (size_t start = 0; start < n; start += width * 2) {
      size_t mid = start + width < n ? start + width : n,
             end = start + width * 2 < n ? start + width * 2 : n, left = start,
             right = mid;
      for (size_t j = start; j < end; j++)
        temp[j] = right >= end ||
                          (left < mid && notice_before(&out[left], &out[right]))
                      ? out[left++]
                      : out[right++];
    }
    TuiNotice *swap = out;
    out = temp;
    temp = swap;
  }
  free(temp);
  free(q->visible);
  q->visible = out;
  *items = out;
  *count = n;
  return TUI_OK;
}
int tui_notice_queue_focus(TuiNoticeQueue *q, const char *id,
                           unsigned long long now) {
  if (!q || !id || !feedback_number(now))
    return 0;
  for (size_t i = 0; i < q->count; i++)
    if (!strcmp(q->items[i].id, id) && !notice_expired(&q->items[i], now)) {
      q->focused = (int)i;
      return 1;
    }
  return 0;
}
int tui_notice_queue_dismiss(TuiNoticeQueue *q, const char *id) {
  if (!q || !id)
    return 0;
  for (size_t i = 0; i < q->count; i++)
    if (!strcmp(q->items[i].id, id)) {
      notice_clear(&q->items[i]);
      memmove(&q->items[i], &q->items[i + 1],
              (q->count - i - 1) * sizeof *q->items);
      q->count--;
      if (q->focused == (int)i)
        q->focused = -1;
      else if (q->focused > (int)i)
        q->focused--;
      notice_invalidate(q);
      return 1;
    }
  return 0;
}
size_t tui_notice_events_count(const TuiNoticeEvents *e) {
  return e ? e->count : 0;
}
TuiNoticeEvent tui_notice_events_at(const TuiNoticeEvents *e, size_t index) {
  return e && index < e->count ? e->events[index]
                               : notice_event("", "", "", TUI_INVALID);
}
void tui_notice_events_free(TuiNoticeEvents *e) {
  if (e) {
    for (size_t i = 0; i < e->count; i++)
      free((void *)e->events[i].id);
    free(e->events);
    free(e);
  }
}
TuiResult tui_notice_queue_expire(TuiNoticeQueue *q, unsigned long long now,
                                  TuiNoticeEvents **events) {
  if (!q || !events || !feedback_number(now))
    return TUI_INVALID;
  *events = NULL;
  TuiNoticeEvents *batch = calloc(1, sizeof *batch);
  if (!batch)
    return TUI_NOMEM;
  size_t count = 0;
  for (size_t i = 0; i < q->count; i++)
    if (notice_expired(&q->items[i], now))
      count++;
  if (count) {
    batch->events = calloc(count, sizeof *batch->events);
    if (!batch->events) {
      free(batch);
      return TUI_NOMEM;
    }
  }
  for (size_t i = 0; i < q->count; i++)
    if (notice_expired(&q->items[i], now)) {
      char *id = copy(q->items[i].id);
      if (!id) {
        tui_notice_events_free(batch);
        return TUI_NOMEM;
      }
      batch->events[batch->count++] = notice_event("expired", id, "", TUI_OK);
    }
  for (size_t i = 0; i < batch->count; i++)
    tui_notice_queue_dismiss(q, batch->events[i].id);
  *events = batch;
  return TUI_OK;
}
static size_t notice_limit(size_t count, int height) {
  height = max(0, min(4096, height));
  return count > (size_t)height && height > 0 ? (size_t)max(1, height - 1)
                                              : (size_t)height;
}
TuiNoticeEvent tui_notice_queue_request_action(TuiNoticeQueue *q,
                                               const char *id,
                                               const char *action,
                                               unsigned long long now) {
  if (!q || !id || !action || !feedback_number(now))
    return notice_event("", "", "", TUI_INVALID);
  for (size_t i = 0; i < q->count; i++) {
    const TuiNotice *n = &q->items[i];
    if (strcmp(n->id, id) || notice_expired(n, now))
      continue;
    for (size_t j = 0; j < n->action_count; j++)
      if (!strcmp(n->actions[j].id, action) && !n->actions[j].disabled)
        return notice_event("action", n->id, n->actions[j].id, TUI_OK);
  }
  return notice_event("", "", "", TUI_OK);
}
TuiNoticeEvent tui_notice_queue_handle(TuiNoticeQueue *q, const char *action,
                                       unsigned long long now, int height) {
  if (!q || !action)
    return notice_event("", "", "", TUI_INVALID);
  if (!strcmp(action, "down"))
    action = "next";
  if (!strcmp(action, "up"))
    action = "previous";
  const TuiNotice *items;
  size_t count;
  TuiResult result = tui_notice_queue_visible(q, now, &items, &count);
  if (result != TUI_OK)
    return notice_event("", "", "", result);
  size_t limit = notice_limit(count, height);
  if (count > limit)
    count = limit;
  if (!count || (strcmp(action, "next") && strcmp(action, "previous") &&
                 strcmp(action, "activate") && strcmp(action, "dismiss")))
    return notice_event("", "", "", TUI_OK);
  size_t at = 0;
  for (size_t i = 0; i < count; i++)
    if (!strcmp(items[i].id, tui_notice_queue_focused(q)))
      at = i;
  if (!strcmp(action, "next") && at + 1 < count)
    at++;
  else if (!strcmp(action, "previous") && at)
    at--;
  const TuiNotice *n = &items[at];
  tui_notice_queue_focus(q, n->id, now);
  if (!strcmp(action, "dismiss"))
    return notice_event("dismiss", n->id, "", TUI_OK);
  if (!strcmp(action, "activate"))
    for (size_t i = 0; i < n->action_count; i++)
      if (!n->actions[i].disabled)
        return notice_event("action", n->id, n->actions[i].id, TUI_OK);
  return notice_event("", "", "", TUI_OK);
}
TuiResult tui_notice_queue_layout(TuiNoticeQueue *q, int width, int height,
                                  unsigned long long now,
                                  const TuiFeedbackRow **rows, size_t *count) {
  if (!q || !rows || !count)
    return TUI_INVALID;
  *rows = NULL;
  *count = 0;
  width = max(0, min(65535, width));
  height = max(0, min(4096, height));
  const TuiNotice *items;
  size_t visible;
  TuiResult result = tui_notice_queue_visible(q, now, &items, &visible);
  if (result != TUI_OK)
    return result;
  size_t limit = notice_limit(visible, height),
         shown = visible < limit ? visible : limit;
  TuiFeedbackView *v =
      feedback_new(shown + (visible > limit && (size_t)height > shown));
  if (!v)
    return TUI_NOMEM;
  for (size_t y = 0; y < shown; y++) {
    const TuiNotice *n = &items[y];
    TuiFeedbackRow *row = &v->rows[y];
    Buffer value = {0};
    char *clean = NULL;
    const char *mark = !strcmp(n->severity, "error")     ? "[!]"
                       : !strcmp(n->severity, "warning") ? "[?]"
                       : !strcmp(n->severity, "success") ? "[+]"
                                                         : "[i]";
    append(&value, !strcmp(tui_notice_queue_focused(q), n->id) ? "> " : "  ");
    append(&value, mark);
    append(&value, " ");
    clean = clean_copy(n->text);
    if (!clean) {
      free(value.s);
      result = TUI_NOMEM;
      goto failed;
    }
    append(&value, clean);
    free(clean);
    if (*n->detail) {
      append(&value, " / ");
      clean = clean_copy(n->detail);
      if (!clean) {
        free(value.s);
        result = TUI_NOMEM;
        goto failed;
      }
      append(&value, clean);
      free(clean);
    }
    TuiFeedbackSpan *spans =
        n->action_count ? calloc(n->action_count, sizeof *spans) : NULL;
    if (n->action_count && !spans) {
      free(value.s);
      result = TUI_NOMEM;
      goto failed;
    }
    row->spans = spans;
    row->span_count = n->action_count;
    for (size_t i = 0; i < n->action_count; i++) {
      TuiFeedbackSpan *s = &spans[i];
      const TuiNoticeAction *a = &n->actions[i];
      Buffer part = {0};
      s->start = tui_cells(feedback_string(value.s));
      s->disabled = a->disabled;
      s->role = copy(a->disabled ? "disabled" : n->severity);
      s->action = copy(a->id);
      append(&part, " [");
      clean = clean_copy(a->label);
      if (!clean) {
        free(value.s);
        free(part.s);
        result = TUI_NOMEM;
        goto failed;
      }
      append(&part, clean);
      free(clean);
      append(&part, "]");
      if (part.failed || !s->role || !s->action) {
        free(value.s);
        free(part.s);
        result = TUI_NOMEM;
        goto failed;
      }
      s->text = part.s;
      append(&value, part.s);
    }
    if (value.failed) {
      free(value.s);
      result = TUI_NOMEM;
      goto failed;
    }
    result = feedback_row_set(row, n->id, value.s, n->severity, width);
    row->focused = !strcmp(tui_notice_queue_focused(q), n->id);
    int end = tui_cells(value.s) > width ? max(0, width - 1) : width;
    free(value.s);
    if (result != TUI_OK)
      goto failed;
    for (size_t i = 0; i < row->span_count; i++) {
      TuiFeedbackSpan *s = &spans[i];
      char *painted = tui_clip(s->text, max(0, end - s->start), 0);
      if (!painted) {
        result = TUI_NOMEM;
        goto failed;
      }
      free((void *)s->text);
      s->text = painted;
      s->width = tui_cells(painted);
    }
    /* Drop invisible action ranges so pointer targets describe painted cells.
     */
    size_t used = 0;
    for (size_t i = 0; i < row->span_count; i++) {
      if (spans[i].width) {
        if (used != i)
          spans[used] = spans[i];
        used++;
      } else {
        free((void *)spans[i].text);
        free((void *)spans[i].role);
        free((void *)spans[i].action);
      }
    }
    row->span_count = used;
  }
  if (v->count > shown) {
    char number[32];
    snprintf(number, sizeof number, "+%zu", visible - limit);
    result = feedback_row_set(&v->rows[shown], "", number, "hint", width);
    if (result != TUI_OK)
      goto failed;
  }
  tui_feedback_free(q->hits);
  q->hits = v;
  q->width = width;
  *rows = v->rows;
  *count = v->count;
  return TUI_OK;
failed:
  tui_feedback_free(v);
  return result;
}
TuiNoticeEvent tui_notice_queue_click(TuiNoticeQueue *q, int x, int y,
                                      unsigned long long now) {
  if (!q || !feedback_number(now))
    return notice_event("", "", "", TUI_INVALID);
  if (x < 0 || x >= q->width || y < 0 || !q->hits ||
      (size_t)y >= q->hits->count)
    return notice_event("", "", "", TUI_OK);
  const TuiFeedbackRow *row = &q->hits->rows[y];
  int index = -1;
  for (size_t i = 0; i < q->count; i++)
    if (!strcmp(q->items[i].id, row->id) && !notice_expired(&q->items[i], now))
      index = (int)i;
  if (!*row->id || index < 0)
    return notice_event("", "", "", TUI_OK);
  for (size_t i = 0; i < row->span_count; i++) {
    const TuiFeedbackSpan *s = &row->spans[i];
    if (x >= s->start && x < s->start + s->width) {
      if (s->disabled)
        return notice_event("", "", "", TUI_OK);
      q->focused = index;
      return tui_notice_queue_request_action(q, row->id, s->action, now);
    }
  }
  q->focused = index;
  return notice_event("focus", q->items[index].id, "", TUI_OK);
}
TuiResult tui_notice_queue_draw(TuiNoticeQueue *q, TuiCanvas *c, TuiRect r,
                                unsigned long long now) {
  if (!c)
    return TUI_INVALID;
  const TuiFeedbackRow *rows;
  size_t count;
  TuiResult result =
      tui_notice_queue_layout(q, r.width, r.height, now, &rows, &count);
  return result == TUI_OK ? feedback_paint(rows, count, c, r) : result;
}
TuiNoticeEvent tui_progress_request_cancel(const TuiProgress *p) {
  if (!p)
    return notice_event("", "", "", TUI_INVALID);
  if (p->id && *p->id && p->cancellable &&
      (!p->status || !*p->status || !strcmp(p->status, "loading")))
    return notice_event("cancel", p->id, "", TUI_OK);
  return notice_event("", "", "", TUI_OK);
}
TuiResult tui_progress_layout(const TuiProgress *p, int width,
                              unsigned long long frame,
                              TuiFeedbackView **view) {
  if (!p || !view || !feedback_number(p->current) ||
      !feedback_number(p->total) || !feedback_number(frame))
    return TUI_INVALID;
  const char *texts[] = {p->id, p->label, p->status, p->message,
                         p->cancel_label};
  for (size_t i = 0; i < 5; i++)
    if (tui_cells(feedback_string(texts[i])) < 0)
      return TUI_INVALID;
  *view = NULL;
  width = max(0, min(65535, width));
  const char *status = p->status && *p->status ? p->status : "loading";
  const char *role =
      !strcmp(status, "error")                                     ? "error"
      : !strcmp(status, "success")                                 ? "success"
      : (!strcmp(status, "empty") || !strcmp(status, "cancelled")) ? "hint"
      : !strcmp(status, "ready")                                   ? "body"
      : !strcmp(status, "loading")                                 ? "info"
                                                                   : "error";
  int cancel = *tui_progress_request_cancel(p).kind && p->cancel_label &&
               *p->cancel_label;
  TuiFeedbackView *v = feedback_new(cancel ? 3 : 2);
  if (!v)
    return TUI_NOMEM;
  Buffer value = {0};
  char numeric[80];
  if (!strcmp(status, "loading")) {
    if (!p->total) {
      char spinner[2] = {"|/-\\"[frame % 4], 0};
      append(&value, spinner);
    } else {
      double ratio =
          (double)(p->current < p->total ? p->current : p->total) / p->total;
      int size = min(30, max(0, width - 10)), done = (int)(ratio * size);
      char bar[32];
      for (int i = 0; i < size; i++)
        bar[i] = i < done ? '#' : '-';
      bar[size] = 0;
      snprintf(numeric, sizeof numeric, "[%s] %d%%", bar, (int)(ratio * 100));
      append(&value, numeric);
    }
  } else
    append(&value, status);
  if (p->message && *p->message) {
    append(&value, " ");
    append(&value, p->message);
  }
  TuiResult result = value.failed ? TUI_NOMEM
                                  : feedback_row_set(&v->rows[0], p->id,
                                                     p->label, role, width);
  if (result == TUI_OK)
    result = feedback_row_set(&v->rows[1], p->id, value.s, role, width);
  if (result == TUI_OK && cancel)
    result =
        feedback_row_set(&v->rows[2], p->id, p->cancel_label, "hint", width);
  free(value.s);
  if (result != TUI_OK) {
    tui_feedback_free(v);
    return result;
  }
  *view = v;
  return TUI_OK;
}
TuiResult tui_progress_draw(const TuiProgress *p, TuiCanvas *c, TuiRect r,
                            unsigned long long frame) {
  if (!c)
    return TUI_INVALID;
  TuiFeedbackView *v = NULL;
  TuiResult result = tui_progress_layout(p, r.width, frame, &v);
  if (result == TUI_OK)
    result = tui_feedback_draw(v, c, r);
  tui_feedback_free(v);
  return result;
}
TuiResult tui_data_state_layout(const TuiDataState *s, int width,
                                TuiFeedbackView **view) {
  if (!s || !view)
    return TUI_INVALID;
  const char *texts[] = {s->kind, s->text, s->detail};
  for (size_t i = 0; i < 3; i++)
    if (tui_cells(feedback_string(texts[i])) < 0)
      return TUI_INVALID;
  *view = NULL;
  width = max(0, min(65535, width));
  const char *kind = s->kind ? s->kind : "empty";
  const char *role = !strcmp(kind, "ready")     ? "body"
                     : !strcmp(kind, "loading") ? "info"
                     : !strcmp(kind, "empty")   ? "hint"
                                                : "error";
  TuiFeedbackView *v = feedback_new(2);
  if (!v)
    return TUI_NOMEM;
  TuiResult result = feedback_row_set(&v->rows[0], "", s->text, role, width);
  if (result == TUI_OK)
    result = feedback_row_set(&v->rows[1], "", s->detail, "hint", width);
  if (result != TUI_OK) {
    tui_feedback_free(v);
    return result;
  }
  *view = v;
  return TUI_OK;
}
TuiResult tui_data_state_draw(const TuiDataState *s, TuiCanvas *c, TuiRect r) {
  if (!c)
    return TUI_INVALID;
  TuiFeedbackView *v = NULL;
  TuiResult result = tui_data_state_layout(s, r.width, &v);
  if (result == TUI_OK)
    result = tui_feedback_draw(v, c, r);
  tui_feedback_free(v);
  return result;
}

struct TuiStackResult {
  TuiStackSlot *slots;
  size_t count;
  int gap;
};
struct TuiLayoutResult {
  TuiNamedRect *rects;
  size_t count;
  char **hidden;
  size_t hidden_count;
};
static int layout_extent(int value, int maximum) {
  return value >= 0 && value <= maximum;
}
static int layout_rect(TuiRect r) {
  return layout_extent(r.x, 1000000000) && layout_extent(r.y, 1000000000) &&
         layout_extent(r.width, 1000000000) &&
         layout_extent(r.height, 1000000000);
}
TuiResult tui_spacing_tokens(const char *density, int columns,
                             TuiSpacingTokens *out) {
  if (!density || !out || !layout_extent(columns, 1000000000) ||
      (strcmp(density, "auto") && strcmp(density, "compact") &&
       strcmp(density, "comfortable")))
    return TUI_INVALID;
  *out =
      !strcmp(density, "compact") || (!strcmp(density, "auto") && columns < 80)
          ? (TuiSpacingTokens){0, 0, 1, 80}
          : (TuiSpacingTokens){2, 1, 2, 80};
  return TUI_OK;
}
TuiResult tui_rect_inset(TuiRect r, int padding, TuiRect *out) {
  if (!out || !layout_rect(r) || !layout_extent(padding, 1024))
    return TUI_INVALID;
  *out =
      (TuiRect){r.x + min(padding, r.width), r.y + min(padding, r.height),
                max(0, r.width - 2 * padding), max(0, r.height - 2 * padding)};
  return TUI_OK;
}
void tui_stack_free(TuiStackResult *r) {
  if (r) {
    for (size_t i = 0; i < r->count; i++)
      free((void *)r->slots[i].id);
    free(r->slots);
    free(r);
  }
}
size_t tui_stack_slot_count(const TuiStackResult *r) {
  return r ? r->count : 0;
}
const TuiStackSlot *tui_stack_slot_at(const TuiStackResult *r, size_t index) {
  return r && index < r->count ? &r->slots[index] : NULL;
}
size_t tui_stack_hidden_count(const TuiStackResult *r) {
  size_t count = 0;
  if (r)
    for (size_t i = 0; i < r->count; i++)
      count += r->slots[i].size == 0;
  return count;
}
const char *tui_stack_hidden_at(const TuiStackResult *r, size_t index) {
  if (r)
    for (size_t i = 0; i < r->count; i++)
      if (!r->slots[i].size) {
        if (!index)
          return r->slots[i].id;
        index--;
      }
  return NULL;
}
int tui_stack_gap(const TuiStackResult *r) { return r ? r->gap : 0; }
TuiResult tui_stack_layout(const TuiStackItem *items, size_t count, int total,
                           int gap, TuiStackResult **out) {
  if (!out || count > 1024 || (count && !items) ||
      !layout_extent(total, 1000000000) || !layout_extent(gap, 1024))
    return TUI_INVALID;
  *out = NULL;
  long long minimum = 0;
  for (size_t i = 0; i < count; i++) {
    const TuiStackItem *v = &items[i];
    if (!v->id || !*v->id || tui_cells(v->id) < 0 || v->min < 1 ||
        !layout_extent(v->min, 1000000) ||
        !layout_extent(v->preferred, 1000000) ||
        !layout_extent(v->weight, 1000000))
      return TUI_INVALID;
    for (size_t j = 0; j < i; j++)
      if (!strcmp(v->id, items[j].id))
        return TUI_INVALID;
    minimum += v->min;
  }
  TuiStackResult *r = calloc(1, sizeof *r);
  if (!r)
    return TUI_NOMEM;
  if (!count) {
    *out = r;
    return TUI_OK;
  }
  r->slots = calloc(count, sizeof *r->slots);
  int *active = calloc(count, sizeof *active);
  if (!r->slots || !active) {
    free(active);
    tui_stack_free(r);
    return TUI_NOMEM;
  }
  r->count = count;
  int gaps = gap * (int)(count - 1);
  if (gaps > total || total - gaps < minimum)
    gap = 0;
  r->gap = gap;
  int available = total - gap * (int)(count - 1);
  for (size_t i = 0; i < count; i++) {
    r->slots[i].id = copy(items[i].id);
    if (!r->slots[i].id) {
      free(active);
      tui_stack_free(r);
      return TUI_NOMEM;
    }
    if (items[i].min > available && i > 0)
      continue;
    r->slots[i].size = min(items[i].min, available);
    available -= r->slots[i].size;
    active[i] = 1;
  }
  for (size_t i = 0; i < count; i++)
    if (active[i]) {
      int add = min(max(0, items[i].preferred - r->slots[i].size), available);
      r->slots[i].size += add;
      available -= add;
    }
  long long weights = 0;
  for (size_t i = 0; i < count; i++)
    if (active[i])
      weights += items[i].weight;
  if (weights) {
    int extra = available;
    for (size_t i = 0; i < count; i++)
      if (active[i]) {
        int add = (int)((long long)extra * items[i].weight / weights);
        r->slots[i].size += add;
        available -= add;
      }
    for (size_t i = 0; i < count; i++)
      if (available && active[i] && items[i].weight) {
        r->slots[i].size++;
        available--;
      }
  }
  int start = 0, visible = 0;
  for (size_t i = 0; i < count; i++) {
    if (r->slots[i].size) {
      if (visible)
        start += gap;
      visible++;
    }
    r->slots[i].start = start;
    start += r->slots[i].size;
  }
  free(active);
  *out = r;
  return TUI_OK;
}
void tui_layout_free(TuiLayoutResult *r) {
  if (r) {
    for (size_t i = 0; i < r->count; i++)
      free((void *)r->rects[i].id);
    for (size_t i = 0; i < r->hidden_count; i++)
      free(r->hidden[i]);
    free(r->rects);
    free(r->hidden);
    free(r);
  }
}
size_t tui_layout_rect_count(const TuiLayoutResult *r) {
  return r ? r->count : 0;
}
const TuiNamedRect *tui_layout_rect_at(const TuiLayoutResult *r, size_t index) {
  return r && index < r->count ? &r->rects[index] : NULL;
}
size_t tui_layout_hidden_count(const TuiLayoutResult *r) {
  return r ? r->hidden_count : 0;
}
const char *tui_layout_hidden_at(const TuiLayoutResult *r, size_t index) {
  return r && index < r->hidden_count ? r->hidden[index] : NULL;
}
TuiResult tui_stack_rects(TuiRect parent, const TuiStackItem *items,
                          size_t count, TuiSpacingTokens tokens, int vertical,
                          TuiLayoutResult **out) {
  if (!out)
    return TUI_INVALID;
  *out = NULL;
  TuiRect inner;
  TuiResult result = tui_rect_inset(parent, tokens.padding, &inner);
  if (result != TUI_OK)
    return result;
  TuiStackResult *stack = NULL;
  result = tui_stack_layout(items, count, vertical ? inner.height : inner.width,
                            tokens.gap, &stack);
  if (result != TUI_OK)
    return result;
  TuiLayoutResult *r = calloc(1, sizeof *r);
  if (!r) {
    tui_stack_free(stack);
    return TUI_NOMEM;
  }
  if (count) {
    r->rects = calloc(count, sizeof *r->rects);
    r->hidden = calloc(count, sizeof *r->hidden);
    if (!r->rects || !r->hidden) {
      tui_stack_free(stack);
      tui_layout_free(r);
      return TUI_NOMEM;
    }
  }
  r->count = count;
  for (size_t i = 0; i < count; i++) {
    const TuiStackSlot *s = &stack->slots[i];
    r->rects[i].id = copy(s->id);
    if (!r->rects[i].id)
      goto nomem;
    TuiRect rect =
        vertical
            ? (TuiRect){inner.x, inner.y + s->start, inner.width, s->size}
            : (TuiRect){inner.x + s->start, inner.y, s->size, inner.height};
    r->rects[i].rect = rect;
    if (!rect.width || !rect.height) {
      r->hidden[r->hidden_count] = copy(s->id);
      if (!r->hidden[r->hidden_count])
        goto nomem;
      r->hidden_count++;
    }
  }
  tui_stack_free(stack);
  *out = r;
  return TUI_OK;
nomem:
  tui_stack_free(stack);
  tui_layout_free(r);
  return TUI_NOMEM;
}
TuiResult tui_drawer_layout(TuiRect parent, int preferred, int min_content,
                            TuiDrawerPlacement *out) {
  if (!out || !layout_rect(parent) || !layout_extent(preferred, 1000000000) ||
      !layout_extent(min_content, 1000000000))
    return TUI_INVALID;
  *out = (TuiDrawerPlacement){
      {parent.x, parent.y, min(parent.width, preferred), parent.height},
      parent.width < preferred + min_content};
  return TUI_OK;
}
TuiResult tui_badge_line(const TuiBadge *b, int width, TuiFeedbackView **view) {
  if (!b || !view || !layout_extent(width, 65535) ||
      !feedback_number(b->limit) ||
      (b->has_count && !feedback_number(b->count)) ||
      tui_cells(feedback_string(b->id)) < 0 ||
      tui_cells(feedback_string(b->label)) < 0)
    return TUI_INVALID;
  *view = NULL;
  TuiFeedbackView *v = feedback_new(1);
  if (!v)
    return TUI_NOMEM;
  char markers[7];
  tui_state_markers(b->state, markers);
  Buffer value = {0};
  append(&value, markers[0] == '-' ? markers + 1 : markers);
  append(&value, feedback_string(b->label));
  if (b->has_count) {
    unsigned long long limit = b->limit ? b->limit : 99ULL;
    char number[64];
    snprintf(number, sizeof number, " [%llu%s]",
             b->count > limit ? limit : b->count, b->count > limit ? "+" : "");
    append(&value, number);
  }
  TuiResult result = value.failed
                         ? TUI_NOMEM
                         : feedback_row_set(&v->rows[0], b->id, value.s,
                                            tui_state_role(b->state), width);
  free(value.s);
  if (result != TUI_OK) {
    tui_feedback_free(v);
    return result;
  }
  *view = v;
  return TUI_OK;
}
TuiResult tui_badge_draw(const TuiBadge *b, TuiCanvas *c, TuiRect r) {
  if (!c)
    return TUI_INVALID;
  TuiFeedbackView *v = NULL;
  TuiResult result = tui_badge_line(b, max(0, r.width), &v);
  if (result == TUI_OK)
    result = tui_feedback_draw(v, c, r);
  tui_feedback_free(v);
  return result;
}
TuiResult tui_chip_line(const TuiChip *chip, int width,
                        TuiFeedbackView **view) {
  if (!chip || !view || !layout_extent(width, 65535) ||
      tui_cells(feedback_string(chip->id)) < 0 ||
      tui_cells(feedback_string(chip->label)) < 0)
    return TUI_INVALID;
  *view = NULL;
  TuiFeedbackView *v = feedback_new(1);
  if (!v)
    return TUI_NOMEM;
  char markers[7];
  tui_state_markers(chip->state, markers);
  Buffer value = {0};
  append(&value, markers[0] == '-' ? markers + 1 : markers);
  append(&value, "[");
  const char *suffix = chip->removable ? "] x" : "]";
  int available =
      max(0, width - tui_cells(feedback_string(value.s)) - tui_cells(suffix));
  char *label = tui_clip(feedback_string(chip->label), available, 1);
  if (!label) {
    free(value.s);
    tui_feedback_free(v);
    return TUI_NOMEM;
  }
  append(&value, label);
  free(label);
  append(&value, suffix);
  TuiResult result = value.failed
                         ? TUI_NOMEM
                         : feedback_row_set(&v->rows[0], chip->id, value.s,
                                            tui_state_role(chip->state), width);
  free(value.s);
  if (result != TUI_OK) {
    tui_feedback_free(v);
    return result;
  }
  TuiFeedbackRow *row = &v->rows[0];
  size_t n = strlen(row->text);
  if (chip->removable && n >= 2 && !strcmp(row->text + n - 2, " x")) {
    TuiFeedbackSpan *s = calloc(1, sizeof *s);
    if (!s) {
      tui_feedback_free(v);
      return TUI_NOMEM;
    }
    row->spans = s;
    row->span_count = 1;
    s->start = tui_cells(row->text) - 1;
    s->width = 1;
    s->text = copy("x");
    s->role = copy(tui_state_editable(chip->state) ? tui_state_role(chip->state)
                                                   : "disabled");
    s->action = copy("remove");
    s->disabled = !tui_state_editable(chip->state);
    if (!s->text || !s->role || !s->action) {
      tui_feedback_free(v);
      return TUI_NOMEM;
    }
  }
  *view = v;
  return TUI_OK;
}
TuiResult tui_chip_draw(const TuiChip *chip, TuiCanvas *c, TuiRect r) {
  if (!c)
    return TUI_INVALID;
  TuiFeedbackView *v = NULL;
  TuiResult result = tui_chip_line(chip, max(0, r.width), &v);
  if (result == TUI_OK)
    result = tui_feedback_draw(v, c, r);
  tui_feedback_free(v);
  return result;
}
TuiEvent tui_chip_request_remove(const TuiChip *chip) {
  return chip && chip->id && *chip->id && tui_cells(chip->id) >= 0 &&
                 chip->removable && tui_state_editable(chip->state)
             ? (TuiEvent){"remove", chip->id}
             : (TuiEvent){"", ""};
}
typedef struct {
  TuiShortcut item;
  size_t order;
  char *normal;
} HelpEntry;
struct TuiHelp {
  HelpEntry *items;
  size_t count;
};
static char *shortcut_key(const char *key) {
  if (!key)
    return NULL;
  char *clean = clean_copy(key);
  if (!clean)
    return NULL;
  char *folded = tui_casefold(clean);
  free(clean);
  if (!folded)
    return NULL;
  size_t p = 0, n = strlen(folded), start = n, end = 0;
  unsigned cp;
  while (p < n) {
    size_t before = p;
    if (!decode((const unsigned char *)folded, n, &p, &cp)) {
      free(folded);
      return NULL;
    }
    if (!whitespace(cp)) {
      if (before < start)
        start = before;
      end = p;
    }
  }
  if (end <= start) {
    free(folded);
    return copy("");
  }
  memmove(folded, folded + start, end - start);
  folded[end - start] = 0;
  return folded;
}
void tui_help_free(TuiHelp *h) {
  if (h) {
    for (size_t i = 0; i < h->count; i++) {
      free((void *)h->items[i].item.key);
      free((void *)h->items[i].item.text);
      free(h->items[i].normal);
    }
    free(h->items);
    free(h);
  }
}
static int help_key_compare(const void *a, const void *b) {
  return strcmp(*(const char *const *)a, *(const char *const *)b);
}
static int help_priority_compare(const void *a, const void *b) {
  const HelpEntry *x = a, *y = b;
  if (x->item.priority != y->item.priority)
    return x->item.priority > y->item.priority ? -1 : 1;
  return x->order < y->order ? -1 : x->order > y->order ? 1 : 0;
}
TuiHelp *tui_help_new(const TuiShortcut *items, size_t count) {
  if (count > 65536 || (count && !items))
    return NULL;
  TuiHelp *h = calloc(1, sizeof *h);
  if (!h)
    return NULL;
  if (count) {
    h->items = calloc(count, sizeof *h->items);
    if (!h->items) {
      free(h);
      return NULL;
    }
  }
  h->count = count;
  char **keys = count ? malloc(count * sizeof *keys) : NULL;
  if (count && !keys) {
    tui_help_free(h);
    return NULL;
  }
  for (size_t i = 0; i < count; i++) {
    HelpEntry *v = &h->items[i];
    if (!items[i].key || tui_cells(feedback_string(items[i].text)) < 0)
      goto failed;
    v->normal = shortcut_key(items[i].key);
    if (!v->normal || !*v->normal)
      goto failed;
    v->item = (TuiShortcut){copy(items[i].key), copy(items[i].text),
                            items[i].priority, items[i].disabled};
    v->order = i;
    if (!v->item.key || !v->item.text)
      goto failed;
    keys[i] = v->normal;
  }
  if (count)
    qsort(keys, count, sizeof *keys, help_key_compare);
  for (size_t i = 1; i < count; i++)
    if (!strcmp(keys[i - 1], keys[i]))
      goto failed;
  free(keys);
  if (count)
    qsort(h->items, count, sizeof *h->items, help_priority_compare);
  return h;
failed:
  free(keys);
  tui_help_free(h);
  return NULL;
}
TuiResult tui_help_layout(const TuiHelp *h, int width, int height,
                          TuiFeedbackView **view) {
  if (!h || !view || !layout_extent(width, 65535) ||
      !layout_extent(height, 4096))
    return TUI_INVALID;
  *view = NULL;
  size_t limit = h->count > (size_t)height && height > 1 ? (size_t)height - 1
                                                         : (size_t)height,
         shown = h->count < limit ? h->count : limit;
  TuiFeedbackView *v =
      feedback_new(shown + (h->count > limit && (size_t)height > shown));
  if (!v)
    return TUI_NOMEM;
  for (size_t i = 0; i < shown; i++) {
    const TuiShortcut *s = &h->items[i].item;
    Buffer text = {0};
    append(&text, "[");
    append(&text, s->key);
    append(&text, "] ");
    append(&text, s->text);
    TuiResult result =
        text.failed
            ? TUI_NOMEM
            : feedback_row_set(&v->rows[i], "", text.s,
                               s->disabled ? "disabled" : "body", width);
    free(text.s);
    if (result != TUI_OK) {
      tui_feedback_free(v);
      return result;
    }
  }
  if (v->count > shown) {
    char text[32];
    snprintf(text, sizeof text, "+%zu", h->count - limit);
    TuiResult result =
        feedback_row_set(&v->rows[shown], "", text, "hint", width);
    if (result != TUI_OK) {
      tui_feedback_free(v);
      return result;
    }
  }
  *view = v;
  return TUI_OK;
}
TuiResult tui_help_draw(const TuiHelp *h, TuiCanvas *c, TuiRect r) {
  if (!c)
    return TUI_INVALID;
  TuiFeedbackView *v = NULL;
  TuiResult result = tui_help_layout(h, max(0, r.width), max(0, r.height), &v);
  if (result == TUI_OK)
    result = tui_feedback_draw(v, c, r);
  tui_feedback_free(v);
  return result;
}

static int container_number(int n, int max_value) {
  return n >= 0 && n <= max_value;
}
static int container_track(TuiTrack t) {
  return container_number(t.min, 1000000) && container_number(t.max, 1000000) &&
         container_number(t.fixed, 1000000) &&
         container_number(t.weight, 1000000) &&
         (!t.max || (t.max >= t.min && t.fixed <= t.max));
}
static TuiResult container_allocate(const TuiTrack *input, size_t count,
                                    int total, int gap, int **out,
                                    int *out_gap) {
  size_t n;
  int available, budget;
  long long minimum = 0, weight;
  TuiTrack *tracks;
  int *sizes;
  *out = NULL;
  *out_gap = 0;
  if (!count)
    return TUI_OK;
  tracks = malloc(count * sizeof *tracks);
  sizes = calloc(count, sizeof *sizes);
  if (!tracks || !sizes) {
    free(tracks);
    free(sizes);
    return TUI_NOMEM;
  }
  memcpy(tracks, input, count * sizeof *tracks);
  for (n = 0; n < count; n++) {
    TuiTrack *t = tracks + n;
    if (!t->min && !t->max && !t->fixed && !t->weight)
      t->weight = 1;
    minimum += max(t->min, t->fixed);
  }
  gap = min(gap, total / (int)count);
  available = total - gap * ((int)count - 1);
  if (minimum > available) {
    gap = 0;
    available = total;
  }
  for (n = 0; n < count; n++) {
    sizes[n] = min(available, max(tracks[n].min, tracks[n].fixed));
    available -= sizes[n];
  }
  while (available) {
    weight = 0;
    for (n = 0; n < count; n++) {
      TuiTrack t = tracks[n];
      if (!t.fixed && t.weight && (!t.max || sizes[n] < t.max))
        weight += t.weight;
    }
    if (!weight)
      break;
    budget = available;
    for (n = 0; n < count; n++) {
      TuiTrack t = tracks[n];
      int add;
      if (t.fixed || !t.weight || (t.max && sizes[n] >= t.max))
        continue;
      add =
          min(available, max(1, (int)((long long)budget * t.weight / weight)));
      if (t.max)
        add = min(add, t.max - sizes[n]);
      sizes[n] += add;
      available -= add;
    }
  }
  free(tracks);
  *out = sizes;
  *out_gap = gap;
  return TUI_OK;
}
static TuiResult container_validate(TuiRect bounds, const TuiLayoutItem *items,
                                    size_t count,
                                    const TuiContainerOptions *o) {
  size_t n, k;
  int values[] = {bounds.x,      bounds.y,         bounds.width,
                  bounds.height, o->virtual_width, o->virtual_height};
  if (count > 1024 || o->row_count > 1024 || o->column_count > 1024 ||
      (!items && count) || (!o->rows && o->row_count) ||
      (!o->columns && o->column_count) || !container_number(o->gap, 1024) ||
      !container_number(o->padding, 1024))
    return TUI_INVALID;
  for (n = 0; n < 6; n++)
    if (!container_number(values[n], 1000000))
      return TUI_INVALID;
  if (strcmp(o->kind, "row") && strcmp(o->kind, "column") &&
      strcmp(o->kind, "grid") && strcmp(o->kind, "layers"))
    return TUI_INVALID;
  for (n = 0; n < o->row_count; n++)
    if (!container_track(o->rows[n]))
      return TUI_INVALID;
  for (n = 0; n < o->column_count; n++)
    if (!container_track(o->columns[n]))
      return TUI_INVALID;
  for (n = 0; n < count; n++) {
    const TuiLayoutItem *i = items + n;
    int v[] = {i->row,    i->column, i->row_span,   i->column_span,
               i->area.x, i->area.y, i->area.width, i->area.height};
    if (!i->id || !*i->id || !container_track(i->track))
      return TUI_INVALID;
    for (k = 0; k < n; k++)
      if (!strcmp(items[k].id, i->id))
        return TUI_INVALID;
    for (k = 0; k < 8; k++)
      if (!container_number(v[k], 1000000))
        return TUI_INVALID;
    if (i->drawer && *i->drawer &&
        (strcmp(o->kind, "layers") || i->centered ||
         (strcmp(i->drawer, "left") && strcmp(i->drawer, "right"))))
      return TUI_INVALID;
  }
  return TUI_OK;
}
TuiResult tui_compute_container(TuiRect bounds, const TuiLayoutItem *items,
                                size_t count,
                                const TuiContainerOptions *options,
                                TuiLayoutResult **out) {
  TuiContainerOptions o = options ? *options : (TuiContainerOptions){0};
  TuiLayoutResult *r;
  TuiRect inner;
  TuiResult result;
  TuiTrack *tracks = NULL;
  int *sizes = NULL, *widths = NULL, *heights = NULL, gap = 0, gx = 0, gy = 0;
  size_t n, k, visible = 0;
  int at = 0;
  if (!out)
    return TUI_INVALID;
  *out = NULL;
  if (!o.kind)
    o.kind = "row";
  result = container_validate(bounds, items, count, &o);
  if (result != TUI_OK)
    return result;
  tui_rect_inset(bounds, o.padding, &inner);
  r = calloc(1, sizeof *r);
  if (!r)
    return TUI_NOMEM;
  r->rects = calloc(count + 1, sizeof *r->rects);
  r->hidden = calloc(count + 1, sizeof *r->hidden);
  if (!r->rects || !r->hidden) {
    result = TUI_NOMEM;
    goto fail;
  }
  for (n = 0; n < count; n++)
    if (!items[n].hidden)
      visible++;
  if (!strcmp(o.kind, "row") || !strcmp(o.kind, "column")) {
    int total = !strcmp(o.kind, "row") ? inner.width : inner.height;
    tracks = calloc(visible + 1, sizeof *tracks);
    if (!tracks) {
      result = TUI_NOMEM;
      goto fail;
    }
    for (n = 0, k = 0; n < count; n++)
      if (!items[n].hidden)
        tracks[k++] = items[n].track;
    result = container_allocate(tracks, visible, total, o.gap, &sizes, &gap);
    if (result != TUI_OK)
      goto fail;
  }
  if (!strcmp(o.kind, "grid")) {
    result = container_allocate(o.columns, o.column_count, inner.width, o.gap,
                                &widths, &gx);
    if (result != TUI_OK)
      goto fail;
    result = container_allocate(o.rows, o.row_count, inner.height, o.gap,
                                &heights, &gy);
    if (result != TUI_OK)
      goto fail;
  }
  for (n = 0, k = 0; n < count; n++) {
    const TuiLayoutItem *i = items + n;
    TuiRect box = inner;
    if (i->hidden)
      continue;
    if (!strcmp(o.kind, "row")) {
      at = min(at, inner.width);
      box.x += at;
      box.width = sizes[k++];
      at += box.width + gap;
    } else if (!strcmp(o.kind, "column")) {
      at = min(at, inner.height);
      box.y += at;
      box.height = sizes[k++];
      at += box.height + gap;
    } else if (!strcmp(o.kind, "grid")) {
      int rs = max(1, i->row_span), cs = max(1, i->column_span), x = 0, y = 0,
          w = gx * (cs - 1), h = gy * (rs - 1), j;
      if ((size_t)(i->row + rs) > o.row_count ||
          (size_t)(i->column + cs) > o.column_count) {
        result = TUI_INVALID;
        goto fail;
      }
      for (j = 0; j < i->column; j++)
        x += widths[j] + gx;
      for (j = 0; j < i->row; j++)
        y += heights[j] + gy;
      for (j = i->column; j < i->column + cs; j++)
        w += widths[j];
      for (j = i->row; j < i->row + rs; j++)
        h += heights[j];
      box = (TuiRect){
          inner.x + min(x, inner.width), inner.y + min(y, inner.height),
          min(w, max(0, inner.width - x)), min(h, max(0, inner.height - y))};
    } else {
      int ax = min(i->area.x, inner.width), ay = min(i->area.y, inner.height);
      box.x += ax;
      box.y += ay;
      box.width -= ax;
      box.height -= ay;
      if (i->area.width)
        box.width = min(box.width, i->area.width);
      if (i->area.height)
        box.height = min(box.height, i->area.height);
      if (i->centered) {
        box.x = inner.x + (inner.width - box.width) / 2;
        box.y = inner.y + (inner.height - box.height) / 2;
      }
      if (i->drawer && *i->drawer) {
        box.width =
            min(inner.width, i->area.width ? i->area.width : inner.width);
        box.x = inner.x +
                (!strcmp(i->drawer, "right") ? inner.width - box.width : 0);
      }
    }
    r->rects[r->count].id = copy(i->id);
    r->rects[r->count].rect = box;
    if (!r->rects[r->count].id) {
      result = TUI_NOMEM;
      goto fail;
    }
    r->count++;
    if (!box.width || !box.height) {
      r->hidden[r->hidden_count] = copy(i->id);
      if (!r->hidden[r->hidden_count]) {
        result = TUI_NOMEM;
        goto fail;
      }
      r->hidden_count++;
    }
  }
  free(tracks);
  free(sizes);
  free(widths);
  free(heights);
  *out = r;
  return TUI_OK;
fail:
  free(tracks);
  free(sizes);
  free(widths);
  free(heights);
  tui_layout_free(r);
  return result;
}
struct TuiContainerState {
  char *focused, *captured, *modal, *last;
  char *restore_id[1024], *restore_value[1024];
  size_t restore_count;
};
static const char *container_string(const char *s) { return s ? s : ""; }
static int container_assign(char **destination, const char *value) {
  char *owned = copy(value);
  if (!owned)
    return 0;
  free(*destination);
  *destination = owned;
  return 1;
}
TuiContainerState *tui_container_state_new(void) {
  return calloc(1, sizeof(TuiContainerState));
}
void tui_container_state_free(TuiContainerState *s) {
  if (s) {
    free(s->focused);
    free(s->captured);
    free(s->modal);
    free(s->last);
    for (size_t n = 0; n < s->restore_count; n++) {
      free(s->restore_id[n]);
      free(s->restore_value[n]);
    }
    free(s);
  }
}
const char *tui_container_focused(const TuiContainerState *s) {
  return s ? container_string(s->focused) : "";
}
const char *tui_container_captured(const TuiContainerState *s) {
  return s ? container_string(s->captured) : "";
}
static size_t container_modal_start(const TuiLayoutItem *items, size_t count) {
  size_t start = 0;
  for (size_t n = 0; n < count; n++)
    if (items[n].modal && !items[n].hidden)
      start = n;
  return start;
}
static int container_eligible(const TuiLayoutItem *items, size_t count,
                              const char *id) {
  size_t start = container_modal_start(items, count);
  for (size_t n = start; n < count; n++)
    if (!items[n].hidden && !items[n].disabled &&
        !strcmp(items[n].id, container_string(id)))
      return 1;
  return 0;
}
static char *container_restore_take(TuiContainerState *s, const char *id) {
  for (size_t n = 0; n < s->restore_count; n++)
    if (!strcmp(s->restore_id[n], container_string(id))) {
      char *value = s->restore_value[n];
      free(s->restore_id[n]);
      s->restore_count--;
      s->restore_id[n] = s->restore_id[s->restore_count];
      s->restore_value[n] = s->restore_value[s->restore_count];
      return value;
    }
  return NULL;
}
TuiResult tui_container_reconcile(TuiContainerState *s,
                                  const TuiLayoutItem *items, size_t count) {
  const char *modal = "";
  int old_visible = 0;
  size_t n;
  TuiContainerOptions o = {.kind = "layers"};
  if (!s || container_validate((TuiRect){0}, items, count, &o) != TUI_OK)
    return TUI_INVALID;
  for (n = 0; n < count; n++)
    if (items[n].modal && !items[n].hidden) {
      modal = items[n].id;
      if (!strcmp(modal, container_string(s->modal)))
        old_visible = 1;
    }
  if (strcmp(modal, container_string(s->modal))) {
    if (s->modal && *s->modal && !old_visible) {
      char *previous = container_restore_take(s, s->modal);
      size_t remaining = s->restore_count + 1;
      while (previous && remaining--) {
        if (container_eligible(items, count, previous)) {
          free(s->focused);
          s->focused = previous;
          previous = NULL;
          break;
        }
        char *next = container_restore_take(s, previous);
        free(previous);
        previous = next;
      }
      free(previous);
    }
    if (*modal) {
      for (n = 0; n < s->restore_count; n++)
        if (!strcmp(modal, s->restore_id[n]))
          break;
      if (n == s->restore_count) {
        char *key, *value;
        if (n == 1024)
          return TUI_INVALID;
        key = copy(modal);
        value = copy(s->focused);
        if (!key || !value) {
          free(key);
          free(value);
          return TUI_NOMEM;
        }
        s->restore_id[n] = key;
        s->restore_value[n] = value;
        s->restore_count++;
      }
    }
    if (!container_assign(&s->modal, modal))
      return TUI_NOMEM;
  }
  if (!container_eligible(items, count, s->focused)) {
    const char *first = "";
    for (n = container_modal_start(items, count); n < count; n++)
      if (!items[n].hidden && !items[n].disabled) {
        first = items[n].id;
        break;
      }
    if (!container_assign(&s->focused, first))
      return TUI_NOMEM;
  }
  if (!container_eligible(items, count, s->captured) &&
      !container_assign(&s->captured, ""))
    return TUI_NOMEM;
  return TUI_OK;
}
TuiResult tui_container_move_focus(TuiContainerState *s,
                                   const TuiLayoutItem *items, size_t count,
                                   int previous) {
  size_t ids[1024], length = 0, at = 0, n;
  TuiResult result = tui_container_reconcile(s, items, count);
  if (result != TUI_OK)
    return result;
  for (n = container_modal_start(items, count); n < count; n++)
    if (!items[n].hidden && !items[n].disabled) {
      ids[length] = n;
      if (!strcmp(items[n].id, tui_container_focused(s)))
        at = length;
      length++;
    }
  if (length && !container_assign(
                    &s->focused,
                    items[ids[(at + (previous ? length - 1 : 1)) % length]].id))
    return TUI_NOMEM;
  return TUI_OK;
}
const char *tui_container_hit(const TuiLayoutItem *items, size_t count,
                              const TuiLayoutResult *r, int x, int y) {
  if (!r || (!items && count) || count > 1024)
    return "";
  for (size_t n = r->count; n > 0; n--) {
    TuiNamedRect box = r->rects[n - 1];
    if (x >= box.rect.x && y >= box.rect.y && x < box.rect.x + box.rect.width &&
        y < box.rect.y + box.rect.height &&
        container_eligible(items, count, box.id))
      return box.id;
  }
  return "";
}
TuiResult tui_container_state_pointer(TuiContainerState *s,
                                      const TuiLayoutItem *items, size_t count,
                                      const TuiLayoutResult *r, int x, int y,
                                      int press, int release, const char **id) {
  TuiResult result;
  const char *target;
  if (!id)
    return TUI_INVALID;
  *id = "";
  result = tui_container_reconcile(s, items, count);
  if (result != TUI_OK)
    return result;
  target = *tui_container_captured(s)
               ? tui_container_captured(s)
               : tui_container_hit(items, count, r, x, y);
  if (!container_assign(&s->last, target))
    return TUI_NOMEM;
  if (press && *s->last) {
    if (!container_assign(&s->focused, s->last) ||
        !container_assign(&s->captured, s->last))
      return TUI_NOMEM;
  }
  if (release && !container_assign(&s->captured, ""))
    return TUI_NOMEM;
  *id = s->last;
  return TUI_OK;
}
struct TuiContainer {
  TuiLayoutItem *items;
  size_t count;
  TuiContainerOptions options;
  TuiContainerState *state;
  TuiLayoutResult *layout;
  TuiRect bounds;
  int scroll_x, scroll_y, sx, sy;
};
static void container_clear_items(TuiContainer *c) {
  for (size_t n = 0; n < c->count; n++) {
    free((void *)c->items[n].id);
    free((void *)c->items[n].drawer);
  }
  free(c->items);
  free((void *)c->options.kind);
  free((void *)c->options.rows);
  free((void *)c->options.columns);
}
void tui_container_free(TuiContainer *c) {
  if (c) {
    container_clear_items(c);
    tui_container_state_free(c->state);
    tui_layout_free(c->layout);
    free(c);
  }
}
TuiContainer *tui_container_new(const TuiLayoutItem *items, size_t count,
                                const TuiContainerOptions *o) {
  TuiContainer *c = calloc(1, sizeof *c);
  if (!c)
    return NULL;
  c->state = tui_container_state_new();
  if (!c->state || tui_container_set_items(c, items, count, o) != TUI_OK) {
    tui_container_free(c);
    return NULL;
  }
  return c;
}
TuiResult tui_container_set_items(TuiContainer *c, const TuiLayoutItem *items,
                                  size_t count,
                                  const TuiContainerOptions *options) {
  TuiContainerOptions o =
      options ? *options
              : (c && c->options.kind ? c->options : (TuiContainerOptions){0});
  TuiLayoutResult *checked = NULL;
  TuiContainer candidate = {0};
  TuiTrack *rows = NULL, *columns = NULL;
  TuiResult result;
  if (!c)
    return TUI_INVALID;
  if (!o.kind)
    o.kind = "row";
  result =
      tui_compute_container((TuiRect){0, 0, 1, 1}, items, count, &o, &checked);
  tui_layout_free(checked);
  if (result != TUI_OK)
    return result;
  candidate.options = o;
  candidate.options.kind = NULL;
  candidate.options.rows = NULL;
  candidate.options.columns = NULL;
  candidate.items = calloc(count + 1, sizeof *candidate.items);
  if (!candidate.items)
    return TUI_NOMEM;
  candidate.count = count;
  for (size_t n = 0; n < count; n++) {
    candidate.items[n] = items[n];
    candidate.items[n].id = copy(items[n].id);
    candidate.items[n].drawer = copy(items[n].drawer);
    if (!candidate.items[n].id || !candidate.items[n].drawer) {
      result = TUI_NOMEM;
      goto fail;
    }
  }
  candidate.options.kind = copy(o.kind);
  if (o.row_count) {
    rows = malloc(o.row_count * sizeof *rows);
    if (rows)
      memcpy(rows, o.rows, o.row_count * sizeof *rows);
  }
  if (o.column_count) {
    columns = malloc(o.column_count * sizeof *columns);
    if (columns)
      memcpy(columns, o.columns, o.column_count * sizeof *columns);
  }
  candidate.options.rows = rows;
  candidate.options.columns = columns;
  if (!candidate.options.kind || (o.row_count && !rows) ||
      (o.column_count && !columns)) {
    result = TUI_NOMEM;
    goto fail;
  }
  container_clear_items(c);
  c->items = candidate.items;
  c->count = candidate.count;
  c->options = candidate.options;
  tui_layout_free(c->layout);
  c->layout = NULL;
  c->bounds = (TuiRect){0};
  free(c->state->captured);
  c->state->captured = NULL;
  return tui_container_reconcile(c->state, c->items, c->count);
fail:
  container_clear_items(&candidate);
  return result;
}
TuiContainerState *tui_container_state(TuiContainer *c) {
  return c ? c->state : NULL;
}
TuiResult tui_container_scroll(TuiContainer *c, int x, int y) {
  if (!c || !container_number(x, 1000000) || !container_number(y, 1000000))
    return TUI_INVALID;
  c->scroll_x = x;
  c->scroll_y = y;
  return TUI_OK;
}
const TuiLayoutResult *tui_container_layout(const TuiContainer *c) {
  return c ? c->layout : NULL;
}
TuiResult tui_container_draw(TuiContainer *c, TuiCanvas *canvas, TuiRect bounds,
                             TuiChildPainter painter, void *context) {
  int vw, vh, sx, sy;
  TuiCanvas *virtual_canvas;
  TuiLayoutResult *layout = NULL;
  TuiResult result;
  if (!c || !canvas || !painter)
    return TUI_INVALID;
  int values[] = {bounds.x, bounds.y, bounds.width, bounds.height};
  for (size_t n = 0; n < 4; n++)
    if (!container_number(values[n], 1000000))
      return TUI_INVALID;
  vw = max(bounds.width, c->options.virtual_width);
  vh = max(bounds.height, c->options.virtual_height);
  if ((long long)vw * vh > 1000000)
    return TUI_INVALID;
  sx = min(c->scroll_x, max(0, vw - bounds.width));
  sy = min(c->scroll_y, max(0, vh - bounds.height));
  result = tui_compute_container((TuiRect){0, 0, vw, vh}, c->items, c->count,
                                 &c->options, &layout);
  if (result != TUI_OK)
    return result;
  virtual_canvas = tui_canvas_new(vw, vh, canvas->theme, canvas->profile);
  if (!virtual_canvas) {
    tui_layout_free(layout);
    return TUI_NOMEM;
  }
  tui_canvas_surface(virtual_canvas, canvas->surface);
  tui_canvas_fill(virtual_canvas, (TuiRect){0, 0, vw, vh}, "surface");
  result = tui_container_reconcile(c->state, c->items, c->count);
  if (result != TUI_OK)
    goto done;
  for (size_t n = 0; n < layout->count; n++) {
    TuiNamedRect named = layout->rects[n];
    TuiRect r = named.rect;
    TuiCanvas *child;
    int focused;
    if (!r.width || !r.height)
      continue;
    child = tui_canvas_new(r.width, r.height, canvas->theme, canvas->profile);
    if (!child) {
      result = TUI_NOMEM;
      goto done;
    }
    tui_canvas_surface(child, canvas->surface);
    result = tui_canvas_blit(child, virtual_canvas, r, 0, 0);
    tui_canvas_clear_cursor(child, NULL);
    focused = !strcmp(named.id, tui_container_focused(c->state));
    if (result == TUI_OK)
      result = painter(context, named.id, child, focused);
    if (!focused)
      tui_canvas_clear_cursor(child, NULL);
    if (result == TUI_OK)
      result = tui_canvas_blit(virtual_canvas, child,
                               (TuiRect){0, 0, r.width, r.height}, r.x, r.y);
    tui_canvas_free(child);
    if (result != TUI_OK)
      goto done;
  }
  result = tui_canvas_blit(canvas, virtual_canvas,
                           (TuiRect){sx, sy, bounds.width, bounds.height},
                           bounds.x, bounds.y);
  if (result == TUI_OK) {
    c->scroll_x = c->sx = sx;
    c->scroll_y = c->sy = sy;
    c->bounds = bounds;
    tui_layout_free(c->layout);
    c->layout = layout;
    layout = NULL;
  }
done:
  tui_canvas_free(virtual_canvas);
  tui_layout_free(layout);
  return result;
}
TuiResult tui_container_pointer(TuiContainer *c, int x, int y, int press,
                                int release, const char **id) {
  if (!c || !id)
    return TUI_INVALID;
  *id = "";
  if (!*tui_container_captured(c->state) &&
      (x < c->bounds.x || y < c->bounds.y ||
       x >= c->bounds.x + c->bounds.width ||
       y >= c->bounds.y + c->bounds.height))
    return TUI_OK;
  return tui_container_state_pointer(
      c->state, c->items, c->count, c->layout, x - c->bounds.x + c->sx,
      y - c->bounds.y + c->sy, press, release, id);
}

TuiResult tui_surface_draw(const TuiSurface *s, TuiCanvas *c, TuiRect bounds,
                           TuiSurfacePainter painter, void *context) {
  if (!c || !painter || !container_number(bounds.x, 1000000) ||
      !container_number(bounds.y, 1000000) ||
      !container_number(bounds.width, 1000000) ||
      !container_number(bounds.height, 1000000) ||
      (long long)bounds.width * bounds.height > 1000000)
    return TUI_INVALID;
  const char *role = s && s->role ? s->role : "surface";
  TuiStyle style;
  if (tui_style(c->theme, c->profile, role, 0, &style) != TUI_OK)
    return TUI_INVALID;
  TuiCanvas *child =
      tui_canvas_new(bounds.width, bounds.height, c->theme, c->profile);
  if (!child)
    return TUI_NOMEM;
  TuiResult result = tui_canvas_surface(child, role);
  if (result == TUI_OK)
    result = tui_canvas_fill(child, tui_canvas_bounds(child), "surface");
  if (result == TUI_OK)
    result = painter(context, child);
  if (result == TUI_OK)
    result =
        tui_canvas_blit(c, child, (TuiRect){0, 0, bounds.width, bounds.height},
                        bounds.x, bounds.y);
  tui_canvas_free(child);
  return result;
}

static int popup_rect_valid(TuiRect r) {
  return container_number(r.x, 1000000000) &&
         container_number(r.y, 1000000000) &&
         container_number(r.width, 1000000) &&
         container_number(r.height, 1000000);
}
static TuiResult shadow_offsets(TuiShadowOptions o, int *dx, int *dy) {
  const char *mode = o.mode ? o.mode : "off";
  if (!container_number(o.offset_x, 1000000) ||
      !container_number(o.offset_y, 1000000) ||
      (strcmp(mode, "off") && strcmp(mode, "auto") && strcmp(mode, "solid") &&
       strcmp(mode, "dim")))
    return TUI_INVALID;
  *dx = !strcmp(mode, "off") ? 0 : !o.offset_x && !o.offset_y ? 1 : o.offset_x;
  *dy = !strcmp(mode, "off") ? 0 : !o.offset_x && !o.offset_y ? 1 : o.offset_y;
  return TUI_OK;
}
static TuiPopupLayout shadow_layout_unchecked(TuiShadowOptions o,
                                              TuiRect bounds) {
  int dx = 0, dy = 0;
  TuiPopupLayout l = {.bounds = bounds, .card = bounds};
  shadow_offsets(o, &dx, &dy);
  if (!bounds.width || !bounds.height)
    return l;
  dx = min(dx, bounds.width - 1);
  dy = min(dy, bounds.height - 1);
  l.card.width -= dx;
  l.card.height -= dy;
  if (dx || dy) {
    int caps = (!strcmp(o.mode ? o.mode : "off", "auto") ||
                !strcmp(o.mode ? o.mode : "off", "solid")) &&
               dy > 0;
    l.shadow = (TuiRect){bounds.x + dx, bounds.y + dy - caps, l.card.width,
                         l.card.height + caps};
  }
  return l;
}
TuiResult tui_shadow_layout(const TuiShadowOptions *options, TuiRect bounds,
                            TuiPopupLayout *out) {
  TuiShadowOptions o = options ? *options : (TuiShadowOptions){0};
  int dx, dy;
  if (!out || !popup_rect_valid(bounds) ||
      shadow_offsets(o, &dx, &dy) != TUI_OK)
    return TUI_INVALID;
  *out = shadow_layout_unchecked(o, bounds);
  return TUI_OK;
}
TuiResult tui_popup_placement(TuiRect anchor, TuiRect viewport, int width,
                              int height, const TuiShadowOptions *options,
                              TuiPopupLayout *out) {
  TuiShadowOptions o = options ? *options : (TuiShadowOptions){0};
  int dx, dy, w, h, mx, my, x, y;
  if (!out || !popup_rect_valid(anchor) || !popup_rect_valid(viewport) ||
      !container_number(width, 1000000) || !container_number(height, 1000000) ||
      shadow_offsets(o, &dx, &dy) != TUI_OK)
    return TUI_INVALID;
  w = width && height ? min(width + dx, viewport.width) : 0;
  h = width && height ? min(height + dy, viewport.height) : 0;
  mx = viewport.x + viewport.width - w;
  my = viewport.y + viewport.height - h;
  x = max(viewport.x, min(anchor.x, mx));
  y = anchor.y + anchor.height;
  if (y > my)
    y = max(0, anchor.y - h);
  *out = shadow_layout_unchecked(
      o, (TuiRect){x, max(viewport.y, min(y, my)), w, h});
  return TUI_OK;
}
TuiResult tui_popup_shadow_regions(TuiPopupLayout l, TuiRect out[2]) {
  TuiRect values[] = {l.bounds, l.card, l.shadow};
  if (!out)
    return TUI_INVALID;
  for (int n = 0; n < 3; n++)
    if (!container_number(values[n].x, 2000000000) ||
        !container_number(values[n].y, 2000000000) ||
        !container_number(values[n].width, 1000000) ||
        !container_number(values[n].height, 1000001))
      return TUI_INVALID;
  TuiRect s = l.shadow, c = l.card;
  int sr = s.x + s.width, sb = s.y + s.height, cr = c.x + c.width,
      cb = c.y + c.height, x = max(s.x, cr), y = max(s.y, cb);
  out[0] = (TuiRect){x, s.y, max(0, sr - x), max(0, min(sb, cb) - s.y)};
  out[1] = (TuiRect){s.x, y, s.width, max(0, sb - y)};
  return TUI_OK;
}
int tui_popup_hit(const TuiPopupLayout *l, int x, int y) {
  return l && x >= l->card.x && y >= l->card.y &&
         (long long)x < (long long)l->card.x + l->card.width &&
         (long long)y < (long long)l->card.y + l->card.height;
}
static unsigned shadow_shade(unsigned backdrop, int has_rgb, int has_256) {
  int rgb[3] = {0};
  style_rgb(backdrop, rgb);
  int r = rgb[0], g = rgb[1], b = rgb[2], maximum = max(r, max(g, b));
  if (maximum <= 16)
    return has_rgb ? 0x1404040 : has_256 ? 238 : 7;
  int factor = maximum <= 96 ? 2 : 4;
  if (has_rgb)
    return 0x1000000 | ((r * factor / 5) << 16) | ((g * factor / 5) << 8) |
           (b * factor / 5);
  if (has_256)
    return (unsigned)(232 +
                      max(0, min(23, ((r + g + b) * factor / 15 - 3) / 10)));
  return 0;
}
static TuiResult shadow_paint(TuiCanvas *c, TuiRect region,
                              TuiPopupLayout layout, TuiShadowOptions options,
                              int ascii, int has_rgb, int has_256) {
  int left = max(0, region.x), right = min(c->width, region.x + region.width),
      top = max(0, region.y), bottom = min(c->height, region.y + region.height);
  if (left >= right || top >= bottom)
    return TUI_OK;
  unsigned *backgrounds = malloc((size_t)(right - left) * sizeof *backgrounds);
  if (!backgrounds)
    return TUI_NOMEM;
  TuiRect covered = {left, top, right - left, bottom - top};
  tui_canvas_clear_cursor(c, &covered);
  TuiResult result = TUI_OK;
  const char *mode = options.mode ? options.mode : "off";
  for (int y = top; y < bottom; y++) {
    Cell *row = c->cells + (size_t)y * c->width;
    for (int x = left; x < right; x++)
      backgrounds[x - left] = row[x].owner >= 0
                                  ? row[row[x].owner].style.background
                                  : row[x].style.background;
    if (row[left].owner >= 0) {
      TuiStyle style = row[left].style;
      result = tui_canvas_write_style(c, left, y, " ", &style, 1);
      if (result != TUI_OK)
        goto done;
    }
    int end = right - 1, start = row[end].owner >= 0 ? row[end].owner : end;
    if (end + 1 < c->width && row[end + 1].owner == start) {
      TuiStyle style = row[end].style;
      result = tui_canvas_write_style(c, end, y, " ", &style, 1);
      if (result != TUI_OK)
        goto done;
    }
    for (int x = left; x < right; x++) {
      if (!strcmp(mode, "dim")) {
        row[x].style.dim = 1;
        continue;
      }
      unsigned bg = backgrounds[x - left],
               shade = !strcmp(mode, "solid")
                           ? 0
                           : shadow_shade(bg, has_rgb, has_256);
      const char *symbol = " ";
      TuiStyle style = {.foreground = shade, .background = shade};
      if (ascii) {
        symbol = ".";
        style.background = bg;
      } else if (layout.shadow.height > layout.card.height) {
        if (y == layout.shadow.y) {
          symbol = "▄";
          style.background = bg;
        } else if (y == layout.shadow.y + layout.shadow.height - 1) {
          symbol = "▀";
          style.background = bg;
        }
      }
      result = tui_canvas_write_style(c, x, y, symbol, &style, 1);
      if (result != TUI_OK)
        goto done;
    }
  }
done:
  free(backgrounds);
  return result;
}
TuiResult tui_shadow_draw(const TuiShadowOptions *options, TuiCanvas *canvas,
                          TuiRect bounds, TuiSurfacePainter painter,
                          void *context, int ascii, TuiPopupLayout *out) {
  TuiShadowOptions o = options ? *options : (TuiShadowOptions){0};
  int dx, dy, x, y, right, bottom, has_rgb = 0, has_256 = 0;
  TuiCanvas *working = NULL, *child = NULL;
  TuiResult result;
  TuiPopupLayout layout;
  TuiRect regions[2];
  if (!canvas || !painter || !popup_rect_valid(bounds) ||
      shadow_offsets(o, &dx, &dy) != TUI_OK)
    return TUI_INVALID;
  x = min(bounds.x, canvas->width);
  y = min(bounds.y, canvas->height);
  right = min(canvas->width, bounds.x + bounds.width);
  bottom = min(canvas->height, bounds.y + bounds.height);
  layout = shadow_layout_unchecked(
      o, (TuiRect){x, y, max(0, right - x), max(0, bottom - y)});
  working = tui_canvas_new(canvas->width, canvas->height, canvas->theme,
                           canvas->profile);
  if (!working)
    return TUI_NOMEM;
  tui_canvas_surface(working, canvas->surface);
  result = tui_canvas_blit(working, canvas, tui_canvas_bounds(canvas), 0, 0);
  if (result != TUI_OK)
    goto done;
  for (size_t n = 0; n < sizeof tui_roles / sizeof tui_roles[0]; n++) {
    TuiStyle s;
    tui_style(canvas->theme, canvas->profile, tui_roles[n], 0, &s);
    unsigned colors[] = {s.foreground, s.background};
    for (int k = 0; k < 2; k++) {
      has_rgb = has_rgb || !!(colors[k] & 0x1000000);
      has_256 = has_256 || (!(colors[k] & 0x1000000) && colors[k] >= 16 &&
                            colors[k] <= 255);
    }
  }
  if (strcmp(o.mode ? o.mode : "off", "off")) {
    result = tui_popup_shadow_regions(layout, regions);
    if (result != TUI_OK)
      goto done;
    for (int n = 0; n < 2; n++) {
      result =
          shadow_paint(working, regions[n], layout, o, ascii, has_rgb, has_256);
      if (result != TUI_OK)
        goto done;
    }
  }
  child = tui_canvas_new(layout.card.width, layout.card.height, canvas->theme,
                         canvas->profile);
  if (!child) {
    result = TUI_NOMEM;
    goto done;
  }
  tui_canvas_surface(child, canvas->surface);
  result = tui_canvas_blit(child, working, layout.card, 0, 0);
  if (result != TUI_OK)
    goto done;
  tui_canvas_clear_cursor(child, NULL);
  result = painter(context, child);
  if (result != TUI_OK)
    goto done;
  result = tui_canvas_blit(working, child, tui_canvas_bounds(child),
                           layout.card.x, layout.card.y);
  if (result != TUI_OK)
    goto done;
  result = tui_canvas_blit(canvas, working, tui_canvas_bounds(canvas), 0, 0);
  if (result == TUI_OK && out)
    *out = layout;
done:
  tui_canvas_free(child);
  tui_canvas_free(working);
  return result;
}

struct DialogHit {
  TuiRect rect;
  size_t index;
};
struct TuiDialog {
  char *title, *message, *cancel;
  TuiDialogButton *buttons;
  size_t count, focused;
  struct DialogHit *hits;
  size_t hit_count;
};
struct TuiDialogLayout {
  char **body;
  size_t body_count;
  TuiDialogButtonCell *buttons;
  size_t *indices;
  size_t count, hidden;
  int truncated;
};
static const char *dialog_string(const char *s) { return s ? s : ""; }
static int dialog_text(const char *s, size_t limit) {
  return s && strlen(s) <= limit && tui_cells(s) >= 0;
}
static void dialog_clear_hits(TuiDialog *d) {
  free(d->hits);
  d->hits = NULL;
  d->hit_count = 0;
}
static void dialog_clear_buttons(TuiDialogButton *items, size_t count) {
  for (size_t n = 0; n < count; n++) {
    free((void *)items[n].id);
    free((void *)items[n].label);
  }
  free(items);
}
void tui_dialog_free(TuiDialog *d) {
  if (d) {
    free(d->title);
    free(d->message);
    free(d->cancel);
    dialog_clear_buttons(d->buttons, d->count);
    dialog_clear_hits(d);
    free(d);
  }
}
const char *tui_dialog_title(const TuiDialog *d) {
  return d ? dialog_string(d->title) : "";
}
const char *tui_dialog_message(const TuiDialog *d) {
  return d ? dialog_string(d->message) : "";
}
const char *tui_dialog_cancel_id(const TuiDialog *d) {
  return d ? dialog_string(d->cancel) : "";
}
const char *tui_dialog_focused(const TuiDialog *d) {
  return d && d->focused < d->count ? d->buttons[d->focused].id : "";
}
size_t tui_dialog_button_count(const TuiDialog *d) { return d ? d->count : 0; }
const TuiDialogButton *tui_dialog_button_at(const TuiDialog *d, size_t index) {
  return d && index < d->count ? &d->buttons[index] : NULL;
}
TuiResult tui_dialog_set_text(TuiDialog *d, const char *title,
                              const char *message) {
  if (!d)
    return TUI_INVALID;
  title = title ? title : dialog_string(d->title);
  message = message ? message : dialog_string(d->message);
  if (!dialog_text(title, 4096) || !dialog_text(message, 1000000))
    return TUI_INVALID;
  char *heading = copy(title), *content = copy(message);
  if (!heading || !content) {
    free(heading);
    free(content);
    return TUI_NOMEM;
  }
  free(d->title);
  free(d->message);
  d->title = heading;
  d->message = content;
  dialog_clear_hits(d);
  return TUI_OK;
}
TuiResult tui_dialog_set_buttons(TuiDialog *d, const TuiDialogButton *buttons,
                                 size_t count, const char *cancel_id) {
  if (!d || count > 1024 || (!buttons && count))
    return TUI_INVALID;
  cancel_id = cancel_id ? cancel_id : dialog_string(d->cancel);
  if (!dialog_text(cancel_id, 1024))
    return TUI_INVALID;
  for (size_t n = 0; n < count; n++) {
    if (!buttons[n].id || !*buttons[n].id ||
        !dialog_text(buttons[n].id, 1024) ||
        !dialog_text(dialog_string(buttons[n].label), 4096))
      return TUI_INVALID;
    for (size_t k = 0; k < n; k++)
      if (!strcmp(buttons[n].id, buttons[k].id))
        return TUI_INVALID;
  }
  size_t cancel_index = (size_t)-1, focused = (size_t)-1, first = (size_t)-1;
  const char *old = tui_dialog_focused(d);
  for (size_t n = 0; n < count; n++) {
    if (!strcmp(buttons[n].id, cancel_id))
      cancel_index = n;
    if (!buttons[n].disabled) {
      if (first == (size_t)-1)
        first = n;
      if (!strcmp(buttons[n].id, old))
        focused = n;
    }
  }
  if (*cancel_id && cancel_index == (size_t)-1)
    return TUI_INVALID;
  if (focused == (size_t)-1)
    focused = cancel_index < count && !buttons[cancel_index].disabled
                  ? cancel_index
                  : first;
  TuiDialogButton *owned = calloc(count + 1, sizeof *owned);
  char *cancel = copy(cancel_id);
  if (!owned || !cancel) {
    free(owned);
    free(cancel);
    return TUI_NOMEM;
  }
  for (size_t n = 0; n < count; n++) {
    owned[n].id = copy(buttons[n].id);
    owned[n].label = copy(buttons[n].label);
    owned[n].disabled = !!buttons[n].disabled;
    if (!owned[n].id || !owned[n].label) {
      dialog_clear_buttons(owned, count);
      free(cancel);
      return TUI_NOMEM;
    }
  }
  dialog_clear_buttons(d->buttons, d->count);
  free(d->cancel);
  d->buttons = owned;
  d->count = count;
  d->cancel = cancel;
  d->focused = focused;
  dialog_clear_hits(d);
  return TUI_OK;
}
TuiDialog *tui_dialog_new(const char *title, const char *message,
                          const TuiDialogButton *buttons, size_t count,
                          const char *cancel_id) {
  TuiDialog *d = calloc(1, sizeof *d);
  if (!d)
    return NULL;
  d->focused = (size_t)-1;
  if (tui_dialog_set_text(d, title, message) != TUI_OK ||
      tui_dialog_set_buttons(d, buttons, count, cancel_id) != TUI_OK) {
    tui_dialog_free(d);
    return NULL;
  }
  return d;
}
int tui_dialog_focus(TuiDialog *d, const char *id) {
  if (!d || !id)
    return 0;
  for (size_t n = 0; n < d->count; n++)
    if (!strcmp(d->buttons[n].id, id) && !d->buttons[n].disabled) {
      if (d->focused != n) {
        d->focused = n;
        dialog_clear_hits(d);
      }
      return 1;
    }
  return 0;
}
TuiEvent tui_dialog_handle(TuiDialog *d, const char *action) {
  TuiEvent none = {"", ""};
  size_t eligible[1024], count = 0, at = 0;
  if (!d || !action)
    return none;
  for (size_t n = 0; n < d->count; n++)
    if (!d->buttons[n].disabled) {
      if (n == d->focused)
        at = count;
      eligible[count++] = n;
    }
  if (!strcmp(action, "cancel")) {
    if (!*dialog_string(d->cancel))
      return (TuiEvent){"cancel", ""};
    for (size_t n = 0; n < count; n++)
      if (!strcmp(d->buttons[eligible[n]].id, d->cancel))
        return (TuiEvent){"cancel", d->buttons[eligible[n]].id};
    return none;
  }
  if (!strcmp(action, "activate"))
    return d->focused < d->count && !d->buttons[d->focused].disabled
               ? (TuiEvent){"activate", d->buttons[d->focused].id}
               : none;
  if (!count)
    return none;
  if (!strcmp(action, "next") || !strcmp(action, "right") ||
      !strcmp(action, "down"))
    at = (at + 1) % count;
  else if (!strcmp(action, "previous") || !strcmp(action, "left") ||
           !strcmp(action, "up"))
    at = (at + count - 1) % count;
  else if (!strcmp(action, "home"))
    at = 0;
  else if (!strcmp(action, "end"))
    at = count - 1;
  else
    return none;
  size_t target = eligible[at];
  if (d->focused == target)
    return none;
  d->focused = target;
  dialog_clear_hits(d);
  return (TuiEvent){"focus", d->buttons[target].id};
}
TuiEvent tui_dialog_click(TuiDialog *d, int x, int y) {
  if (!d)
    return (TuiEvent){"", ""};
  for (size_t n = 0; n < d->hit_count; n++) {
    TuiRect r = d->hits[n].rect;
    size_t index = d->hits[n].index;
    if (x >= r.x && y >= r.y && x < r.x + r.width && y < r.y + r.height) {
      if (index >= d->count || d->buttons[index].disabled)
        return (TuiEvent){"", ""};
      if (d->focused != index) {
        d->focused = index;
        dialog_clear_hits(d);
      }
      return (TuiEvent){"activate", d->buttons[index].id};
    }
  }
  return (TuiEvent){"", ""};
}
void tui_dialog_layout_free(TuiDialogLayout *l) {
  if (l) {
    for (size_t n = 0; n < l->body_count; n++)
      free(l->body[n]);
    for (size_t n = 0; n < l->count; n++) {
      free((void *)l->buttons[n].id);
      free((void *)l->buttons[n].text);
    }
    free(l->body);
    free(l->buttons);
    free(l->indices);
    free(l);
  }
}
size_t tui_dialog_body_count(const TuiDialogLayout *l) {
  return l ? l->body_count : 0;
}
const char *tui_dialog_body_at(const TuiDialogLayout *l, size_t n) {
  return l && n < l->body_count ? l->body[n] : NULL;
}
size_t tui_dialog_cell_count(const TuiDialogLayout *l) {
  return l ? l->count : 0;
}
const TuiDialogButtonCell *tui_dialog_cell_at(const TuiDialogLayout *l,
                                              size_t n) {
  return l && n < l->count ? &l->buttons[n] : NULL;
}
size_t tui_dialog_hidden_buttons(const TuiDialogLayout *l) {
  return l ? l->hidden : 0;
}
int tui_dialog_body_truncated(const TuiDialogLayout *l) {
  return l ? l->truncated : 0;
}
static int dialog_push_line(TuiDialogLayout *l, Buffer *line, int limit) {
  if (line->failed)
    return -1;
  if (l->body_count >= (size_t)limit)
    return 0;
  char *s = line->s ? line->s : copy("");
  if (!s)
    return -1;
  l->body[l->body_count++] = s;
  *line = (Buffer){0};
  return 1;
}
static TuiResult dialog_wrap(const char *message, int width, int limit,
                             TuiDialogLayout *l) {
  if (!*message)
    return TUI_OK;
  if (width <= 0 || limit <= 0) {
    l->truncated = 1;
    return TUI_OK;
  }
  size_t length = strlen(message),
         cap = (size_t)limit < length + 1 ? (size_t)limit : length + 1;
  l->body = calloc(cap, sizeof *l->body);
  if (!l->body)
    return TUI_NOMEM;
  Buffer line = {0};
  int used = 0, last_break = 0;
  size_t p = 0;
  TuiResult result = TUI_OK;
  while (p < length) {
    size_t end;
    int glyph_width;
    if (!cluster_mode(message, length, p, &end, &glyph_width, 1)) {
      result = TUI_INVALID;
      goto done;
    }
    size_t bytes = end - p;
    if ((bytes == 1 && (message[p] == '\r' || message[p] == '\n')) ||
        (bytes == 2 && !memcmp(message + p, "\r\n", 2))) {
      int pushed = dialog_push_line(l, &line, limit);
      if (pushed < 0) {
        result = TUI_NOMEM;
        goto done;
      }
      if (!pushed) {
        l->truncated = 1;
        break;
      }
      used = 0;
      last_break = 1;
      p = end;
      continue;
    }
    last_break = 0;
    char *raw = malloc(bytes + 1);
    if (!raw) {
      result = TUI_NOMEM;
      goto done;
    }
    memcpy(raw, message + p, bytes);
    raw[bytes] = 0;
    char *g = clean_copy(raw);
    free(raw);
    if (!g) {
      result = TUI_NOMEM;
      goto done;
    }
    int n = tui_cells(g);
    if (n > width) {
      char *clipped = tui_clip(g, width, 1);
      free(g);
      g = clipped;
      if (!g) {
        result = TUI_NOMEM;
        goto done;
      }
      n = tui_cells(g);
    }
    if (used + n > width && line.len) {
      int pushed = dialog_push_line(l, &line, limit);
      if (pushed < 0) {
        free(g);
        result = TUI_NOMEM;
        goto done;
      }
      if (!pushed) {
        free(g);
        l->truncated = 1;
        break;
      }
      used = 0;
    }
    if (l->body_count >= (size_t)limit) {
      free(g);
      l->truncated = 1;
      break;
    }
    append(&line, g);
    free(g);
    if (line.failed) {
      result = TUI_NOMEM;
      goto done;
    }
    used += n;
    p = end;
  }
  if (!l->truncated && (line.len || !l->body_count || last_break)) {
    int pushed = dialog_push_line(l, &line, limit);
    if (pushed < 0) {
      result = TUI_NOMEM;
      goto done;
    }
    if (!pushed)
      l->truncated = 1;
  }
  if (l->truncated && l->body_count) {
    char *clipped = tui_clip(l->body[l->body_count - 1], max(0, width - 1), 0);
    if (!clipped) {
      result = TUI_NOMEM;
      goto done;
    }
    Buffer text = {0};
    append(&text, clipped);
    append(&text, "~");
    free(clipped);
    if (text.failed) {
      free(text.s);
      result = TUI_NOMEM;
      goto done;
    }
    free(l->body[l->body_count - 1]);
    l->body[l->body_count - 1] = text.s;
  }
done:
  free(line.s);
  return result;
}
TuiResult tui_dialog_layout(const TuiDialog *d, int width, int height,
                            TuiDialogLayout **out) {
  if (!out)
    return TUI_INVALID;
  *out = NULL;
  if (!d || !container_number(width, 1000000) ||
      !container_number(height, 1000000))
    return TUI_INVALID;
  TuiDialogLayout *l = calloc(1, sizeof *l);
  if (!l)
    return TUI_NOMEM;
  l->hidden = d->count;
  if (!width || !height) {
    l->truncated = !!*d->message;
    *out = l;
    return TUI_OK;
  }
  TuiRect *positions = calloc(d->count + 1, sizeof *positions);
  l->buttons = calloc(d->count + 1, sizeof *l->buttons);
  l->indices = calloc(d->count + 1, sizeof *l->indices);
  TuiResult result = TUI_OK;
  int x = 0, y = 0, focus_row = 0;
  if (!positions || !l->buttons || !l->indices) {
    result = TUI_NOMEM;
    goto done;
  }
  for (size_t n = 0; n < d->count; n++) {
    const TuiDialogButton *b = d->buttons + n;
    int w = min(width, max(1, tui_cells(*b->label ? b->label : b->id) + 4));
    if (x && x + 1 + w > width) {
      x = 0;
      y++;
    }
    if (x)
      x++;
    positions[n] = (TuiRect){x, y, w, 1};
    if (n == d->focused)
      focus_row = y;
    x += w;
  }
  int total_rows = d->count ? y + 1 : 0, visible = min(height, total_rows),
      start = max(0, focus_row + 1 - visible), available = height - visible,
      gap = *d->message && visible && available >= 2 ? 1 : 0;
  result = dialog_wrap(d->message, width, available - gap, l);
  if (result != TUI_OK)
    goto done;
  for (size_t n = 0; n < d->count; n++) {
    TuiRect r = positions[n];
    const TuiDialogButton *b = d->buttons + n;
    if (r.y < start || r.y >= start + visible)
      continue;
    char *label = clean_copy(*b->label ? b->label : b->id);
    if (!label) {
      result = TUI_NOMEM;
      goto done;
    }
    char *part =
        tui_clip(label, r.width >= 6 ? max(0, r.width - 4) : r.width, 1);
    free(label);
    if (!part) {
      result = TUI_NOMEM;
      goto done;
    }
    Buffer text = {0};
    if (r.width >= 6)
      append(&text, "[ ");
    append(&text, part);
    if (r.width >= 6)
      append(&text, " ]");
    free(part);
    if (text.failed) {
      free(text.s);
      result = TUI_NOMEM;
      goto done;
    }
    size_t at = l->count++;
    l->buttons[at] = (TuiDialogButtonCell){
        .id = copy(b->id),
        .text = text.s,
        .rect = {r.x, height - visible + r.y - start, r.width, 1},
        .disabled = b->disabled,
        .focused = n == d->focused};
    l->indices[at] = n;
    if (!l->buttons[at].id) {
      result = TUI_NOMEM;
      goto done;
    }
  }
  l->hidden = d->count - l->count;
  *out = l;
  l = NULL;
done:
  free(positions);
  tui_dialog_layout_free(l);
  return result;
}
TuiResult tui_dialog_draw(TuiDialog *d, TuiCanvas *c, TuiRect bounds,
                          int focused, int ascii, TuiDialogLayout **out) {
  if (out)
    *out = NULL;
  if (!d || !c || !popup_rect_valid(bounds))
    return TUI_INVALID;
  dialog_clear_hits(d);
  int x = min(bounds.x, c->width), y = min(bounds.y, c->height);
  TuiRect r = {x, y, max(0, min(c->width, bounds.x + bounds.width) - x),
               max(0, min(c->height, bounds.y + bounds.height) - y)};
  TuiRect panel = tui_canvas_panel(c, r, d->title, focused, ascii), inner;
  TuiResult result = tui_rect_inset(panel, 1, &inner);
  if (result != TUI_OK)
    return result;
  TuiDialogLayout *l = NULL;
  struct DialogHit *hits = NULL;
  result = tui_dialog_layout(d, inner.width, inner.height, &l);
  if (result != TUI_OK)
    return result;
  hits = calloc(l->count + 1, sizeof *hits);
  if (!hits) {
    result = TUI_NOMEM;
    goto done;
  }
  for (size_t row = 0; row < l->body_count; row++) {
    result = tui_canvas_write(c, inner.x, inner.y + (int)row, l->body[row],
                              "body", 0, inner.width);
    if (result != TUI_OK)
      goto done;
  }
  for (size_t n = 0; n < l->count; n++) {
    const TuiDialogButtonCell *b = l->buttons + n;
    TuiRect box = {inner.x + b->rect.x, inner.y + b->rect.y, b->rect.width, 1};
    const char *role = b->disabled             ? "disabled"
                       : focused && b->focused ? "button.focus"
                                               : "button";
    result = tui_canvas_fill(c, box, role);
    if (result != TUI_OK)
      goto done;
    result = tui_canvas_write(
        c, box.x + max(0, (box.width - tui_cells(b->text)) / 2), box.y, b->text,
        role, 0, box.width);
    if (result != TUI_OK)
      goto done;
    hits[n] = (struct DialogHit){box, l->indices[n]};
  }
  d->hits = hits;
  d->hit_count = l->count;
  hits = NULL;
  if (out) {
    *out = l;
    l = NULL;
  }
done:
  free(hits);
  tui_dialog_layout_free(l);
  return result;
}

static const char *document_roles[] = {"body",
                                       "hint",
                                       "info",
                                       "success",
                                       "warning",
                                       "error",
                                       "header",
                                       "field",
                                       "selection",
                                       "button",
                                       "disabled",
                                       "edited",
                                       "syntax.keyword",
                                       "syntax.function",
                                       "syntax.type",
                                       "syntax.string",
                                       "syntax.number",
                                       "syntax.comment",
                                       "syntax.parameter"};
static const char *document_role(const char *role) {
  if (role)
    for (size_t i = 0; i < sizeof document_roles / sizeof *document_roles; i++)
      if (!strcmp(role, document_roles[i]))
        return document_roles[i];
  return NULL;
}
struct TuiDocumentLayout {
  TuiDocumentLine *rows;
  size_t count;
};
struct TuiDocument {
  TuiText *buffer;
  TuiDocumentOptions options;
  TuiDocumentSpan *styles;
  size_t style_count;
  TuiDocumentRange *matches;
  size_t match_count;
  char *syntax_source, *search_source, *last_source;
  size_t last_cursor, last_anchor;
  int height, reveal;
  TuiSyntaxAnalyzer syntax_analyzer;
  void *syntax_context;
  char *syntax_language, *syntax_dialect, *syntax_binding_source;
  int syntax_bound, syntax_dirty, syntax_refreshing;
  TuiResult syntax_status;
};
static void document_clear_binding(TuiDocument *d) {
  free(d->syntax_language);
  free(d->syntax_dialect);
  free(d->syntax_binding_source);
  d->syntax_language = d->syntax_dialect = d->syntax_binding_source = NULL;
  d->syntax_analyzer = NULL;
  d->syntax_context = NULL;
  d->syntax_bound = d->syntax_dirty = d->syntax_refreshing = 0;
  d->syntax_status = TUI_OK;
}

void tui_document_spans_free(TuiDocumentSpan *s, size_t count) {
  if (s) {
    for (size_t i = 0; i < count; i++)
      free((void *)s[i].role);
    free(s);
  }
}
void tui_document_free(TuiDocument *d) {
  if (d) {
    document_clear_binding(d);
    tui_text_free(d->buffer);
    tui_document_spans_free(d->styles, d->style_count);
    free(d->matches);
    free(d->syntax_source);
    free(d->search_source);
    free(d->last_source);
    free(d);
  }
}
TuiDocument *tui_document_new(const char *text, int read_only) {
  if (!dialog_text(text, 1000000))
    return NULL;
  TuiDocument *d = calloc(1, sizeof *d);
  if (!d)
    return NULL;
  d->buffer = tui_text_new(text);
  d->syntax_source = copy(text);
  d->search_source = copy(text);
  if (!d->buffer || !d->syntax_source || !d->search_source) {
    tui_document_free(d);
    return NULL;
  }
  d->buffer->state.read_only = !!read_only;
  d->options.line_numbers = !read_only;
  d->reveal = !read_only;
  return d;
}
TuiText *tui_document_buffer(TuiDocument *d) { return d ? d->buffer : NULL; }
TuiDocumentOptions tui_document_options(const TuiDocument *d) {
  return d ? d->options : (TuiDocumentOptions){0};
}
TuiResult tui_document_configure(TuiDocument *d, TuiDocumentOptions o) {
  if (!d || o.scroll_x < 0 || o.scroll_y < 0 || o.scroll_x > 1000000 ||
      o.scroll_y > 1000000)
    return TUI_INVALID;
  o.wrap = !!o.wrap;
  o.line_numbers = !!o.line_numbers;
  d->options = o;
  return TUI_OK;
}
TuiResult tui_document_set_text(TuiDocument *d, const char *text) {
  if (!d || d->syntax_refreshing || !dialog_text(text, 1000000))
    return TUI_INVALID;
  TuiText *t = tui_text_new(text);
  char *s = copy(text), *q = copy(text);
  if (!t || !s || !q) {
    tui_text_free(t);
    free(s);
    free(q);
    return TUI_NOMEM;
  }
  t->state = d->buffer->state;
  t->secret = d->buffer->secret;
  tui_text_free(d->buffer);
  d->buffer = t;
  tui_document_spans_free(d->styles, d->style_count);
  d->styles = NULL;
  d->style_count = 0;
  free(d->matches);
  d->matches = NULL;
  d->match_count = 0;
  free(d->syntax_source);
  free(d->search_source);
  free(d->last_source);
  d->last_source = NULL;
  d->syntax_source = s;
  d->search_source = q;
  d->options.scroll_x = d->options.scroll_y = 0;
  d->reveal = !t->state.read_only;
  (void)tui_document_refresh_syntax(d);
  return TUI_OK;
}
TuiResult tui_document_set_syntax(TuiDocument *d, const TuiDocumentSpan *spans,
                                  size_t count) {
  if (!d || (!spans && count) || count > 1000000)
    return TUI_INVALID;
  size_t *offsets = NULL, n = 0;
  int valid = raw_offsets(d->buffer->value, &offsets, &n);
  free(offsets);
  if (valid != 1)
    return valid < 0 ? TUI_NOMEM : TUI_INVALID;
  TuiDocumentSpan *items = calloc(count + 1, sizeof *items);
  char *source = copy(d->buffer->value);
  if (!items || !source) {
    free(items);
    free(source);
    return TUI_NOMEM;
  }
  TuiResult result = TUI_OK;
  for (size_t i = 0; i < count; i++) {
    if (spans[i].end < spans[i].start || spans[i].end > n ||
        !document_role(spans[i].role)) {
      result = TUI_INVALID;
      break;
    }
    items[i] = spans[i];
    items[i].role = copy(spans[i].role);
    if (!items[i].role) {
      result = TUI_NOMEM;
      break;
    }
  }
  if (result != TUI_OK) {
    tui_document_spans_free(items, count);
    free(source);
    return result;
  }
  tui_document_spans_free(d->styles, d->style_count);
  free(d->syntax_source);
  d->styles = items;
  d->style_count = count;
  d->syntax_source = source;
  return TUI_OK;
}
TuiResult tui_document_set_search_matches(TuiDocument *d,
                                          const TuiDocumentRange *ranges,
                                          size_t count) {
  if (!d || (!ranges && count) || count > 1000000)
    return TUI_INVALID;
  size_t *offsets = NULL, n = 0;
  int valid = raw_offsets(d->buffer->value, &offsets, &n);
  free(offsets);
  if (valid != 1)
    return valid < 0 ? TUI_NOMEM : TUI_INVALID;
  for (size_t i = 0; i < count; i++)
    if (ranges[i].end < ranges[i].start || ranges[i].end > n)
      return TUI_INVALID;
  TuiDocumentRange *items = calloc(count + 1, sizeof *items);
  char *source = copy(d->buffer->value);
  if (!items || !source) {
    free(items);
    free(source);
    return TUI_NOMEM;
  }
  if (count)
    memcpy(items, ranges, count * sizeof *items);
  free(d->matches);
  free(d->search_source);
  d->matches = items;
  d->match_count = count;
  d->search_source = source;
  return TUI_OK;
}
static int document_byte_index(const size_t *offsets, size_t n, size_t byte,
                               size_t *out) {
  size_t lo = 0, hi = n + 1;
  while (lo < hi) {
    size_t mid = lo + (hi - lo) / 2;
    if (offsets[mid] < byte)
      lo = mid + 1;
    else
      hi = mid;
  }
  if (lo <= n && offsets[lo] == byte) {
    *out = lo;
    return 1;
  }
  return 0;
}
TuiResult tui_document_set_byte_syntax(TuiDocument *d,
                                       const TuiDocumentSpan *spans,
                                       size_t count) {
  if (!d || (!spans && count) || count > 1000000)
    return TUI_INVALID;
  size_t *offsets = NULL, n = 0;
  int valid = raw_offsets(d->buffer->value, &offsets, &n);
  if (valid != 1)
    return valid < 0 ? TUI_NOMEM : TUI_INVALID;
  TuiDocumentSpan *items = calloc(count + 1, sizeof *items);
  if (!items) {
    free(offsets);
    return TUI_NOMEM;
  }
  TuiResult result = TUI_OK;
  for (size_t i = 0; i < count; i++) {
    items[i].role = spans[i].role;
    if (!document_byte_index(offsets, n, spans[i].start, &items[i].start) ||
        !document_byte_index(offsets, n, spans[i].end, &items[i].end)) {
      result = TUI_INVALID;
      break;
    }
  }
  if (result == TUI_OK)
    result = tui_document_set_syntax(d, items, count);
  free(items);
  free(offsets);
  return result;
}
TuiResult tui_parse_markup(const char *markup, char **source,
                           TuiDocumentSpan **spans, size_t *count) {
  if (!source || !spans || !count || !dialog_text(markup, 1000000))
    return TUI_INVALID;
  size_t n = strlen(markup), at = 0, used = 0, depth = 1, change_count = 1;
  char *out = malloc(n + 1);
  const char **stack = calloc(n + 2, sizeof *stack),
             **roles = calloc(n + 2, sizeof *roles);
  size_t *positions = calloc(n + 2, sizeof *positions);
  if (!out || !stack || !roles || !positions) {
    free(out);
    free(stack);
    free(roles);
    free(positions);
    return TUI_NOMEM;
  }
  stack[0] = roles[0] = "body";
  TuiResult result = TUI_OK;
  while (at < n) {
    if (at + 1 < n && markup[at] == '[' && markup[at + 1] == '[') {
      out[used++] = '[';
      at += 2;
      continue;
    }
    if (markup[at] == '[') {
      const char *end = strchr(markup + at, ']');
      if (!end) {
        result = TUI_INVALID;
        break;
      }
      size_t length = (size_t)(end - (markup + at + 1));
      char tag[64];
      if (length >= sizeof tag) {
        result = TUI_INVALID;
        break;
      }
      memcpy(tag, markup + at + 1, length);
      tag[length] = 0;
      if (!strcmp(tag, "/")) {
        if (depth == 1) {
          result = TUI_INVALID;
          break;
        }
        depth--;
      } else {
        const char *role = document_role(tag);
        if (!role) {
          result = TUI_INVALID;
          break;
        }
        stack[depth++] = role;
      }
      positions[change_count] = used;
      roles[change_count++] = stack[depth - 1];
      at = (size_t)(end - markup) + 1;
    } else
      out[used++] = markup[at++];
  }
  out[used] = 0;
  if (depth != 1)
    result = TUI_INVALID;
  size_t *offsets = NULL, gcount = 0;
  TuiDocumentSpan *items = NULL;
  size_t span_count = 0;
  if (result == TUI_OK) {
    int valid = raw_offsets(out, &offsets, &gcount);
    if (valid != 1)
      result = valid < 0 ? TUI_NOMEM : TUI_INVALID;
    else {
      items = calloc(gcount + 1, sizeof *items);
      if (!items)
        result = TUI_NOMEM;
      else {
        size_t which = 0;
        for (size_t i = 0; i < gcount; i++) {
          while (which + 1 < change_count && positions[which + 1] <= offsets[i])
            which++;
          const char *role = roles[which];
          if (strcmp(role, "body")) {
            if (span_count && items[span_count - 1].end == i &&
                !strcmp(items[span_count - 1].role, role))
              items[span_count - 1].end++;
            else {
              items[span_count] = (TuiDocumentSpan){i, i + 1, copy(role)};
              if (!items[span_count].role) {
                result = TUI_NOMEM;
                break;
              }
              span_count++;
            }
          }
        }
      }
    }
  }
  free(stack);
  free(roles);
  free(positions);
  free(offsets);
  if (result == TUI_OK) {
    *source = out;
    *spans = items;
    *count = span_count;
  } else {
    free(out);
    tui_document_spans_free(items, span_count);
  }
  return result;
}
TuiResult tui_document_set_markup(TuiDocument *d, const char *markup) {
  if (!d || d->syntax_refreshing)
    return TUI_INVALID;
  char *source = NULL;
  TuiDocumentSpan *spans = NULL;
  size_t count = 0;
  TuiResult result = tui_parse_markup(markup, &source, &spans, &count);
  if (result != TUI_OK)
    return result; /* Prepare all model state before changing the existing
                      source. */
  TuiDocument *next = tui_document_new(source, d->buffer->state.read_only);
  if (!next)
    result = TUI_NOMEM;
  else {
    next->buffer->state = d->buffer->state;
    next->buffer->secret = d->buffer->secret;
    next->options.wrap = d->options.wrap;
    next->options.line_numbers = d->options.line_numbers;
    result = tui_document_set_syntax(next, spans, count);
    if (result == TUI_OK) {
      TuiDocument old = *d;
      *d = *next;
      *next = old;
    }
    tui_document_free(next);
  }
  free(source);
  tui_document_spans_free(spans, count);
  return result;
}
void tui_document_reveal_cursor(TuiDocument *d) {
  if (d)
    d->reveal = 1;
}
TuiTextEvent tui_document_handle(TuiDocument *d, const char *action,
                                 const char *text) {
  if (!d || !action)
    return text_event(NULL, "", TUI_INVALID);
  TuiText *t = d->buffer;
  if (t->state.disabled)
    return text_event(t, "", TUI_OK);
  int step = max(1, d->height);
  if (!strcmp(action, "page_up"))
    d->options.scroll_y = max(0, d->options.scroll_y - step);
  else if (!strcmp(action, "page_down"))
    d->options.scroll_y =
        (int)min64(1000000, (long long)d->options.scroll_y + step);
  else if (!strcmp(action, "scroll_up"))
    d->options.scroll_y = max(0, d->options.scroll_y - 1);
  else if (!strcmp(action, "scroll_down"))
    d->options.scroll_y = min(1000000, d->options.scroll_y + 1);
  else if (!strcmp(action, "scroll_left"))
    d->options.scroll_x = max(0, d->options.scroll_x - 4);
  else if (!strcmp(action, "scroll_right"))
    d->options.scroll_x = min(1000000, d->options.scroll_x + 4);
  else {
    if ((!strcmp(action, "insert") || !strcmp(action, "paste") ||
         !strcmp(action, "newline")) &&
        tui_state_editable(t->state)) {
      const char *raw = !strcmp(action, "newline") ? "\n" : text ? text : "";
      if (!dialog_text(raw, 1000000))
        return text_event(t, "", TUI_INVALID);
      char *addition = text_clean(raw, t->multiline);
      if (!addition)
        return text_event(t, "", TUI_NOMEM);
      size_t lo = 0, hi = 0;
      TuiResult budget = tui_text_selection_bytes(t, &lo, &hi);
      if (budget == TUI_OK &&
          strlen(t->value) - (hi - lo) + strlen(addition) > 1000000)
        budget = TUI_INVALID;
      free(addition);
      if (budget != TUI_OK)
        return text_event(t, "", budget);
    }
    TuiTextEvent e = tui_text_handle(t, action, text ? text : "");
    if (!strcmp(e.kind, "select") || !strcmp(e.kind, "change") ||
        !strcmp(e.kind, "cut"))
      d->reveal = 1;
    (void)tui_document_refresh_syntax(d);
    return e;
  }
  d->reveal = 0;
  return text_event(t, "scroll", TUI_OK);
}
static void document_line_clear(TuiDocumentLine *r) {
  free((void *)r->prefix);
  for (size_t i = 0; i < r->glyph_count; i++) {
    free((void *)r->glyphs[i].text);
    free((void *)r->glyphs[i].role);
  }
  free((void *)r->glyphs);
  free((void *)r->hits);
  memset(r, 0, sizeof *r);
}
void tui_document_layout_free(TuiDocumentLayout *l) {
  if (l) {
    for (size_t i = 0; i < l->count; i++)
      document_line_clear(&l->rows[i]);
    free(l->rows);
    free(l);
  }
}
size_t tui_document_line_count(const TuiDocumentLayout *l) {
  return l ? l->count : 0;
}
const TuiDocumentLine *tui_document_line_at(const TuiDocumentLayout *l,
                                            size_t i) {
  return l && i < l->count ? &l->rows[i] : NULL;
}
typedef struct {
  char *text;
  int width, br;
  const char *role;
} DocumentPart;
static void document_parts_free(DocumentPart *p, size_t n) {
  if (p) {
    for (size_t i = 0; i < n; i++)
      free(p[i].text);
    free(p);
  }
}
static TuiResult document_add_row(TuiDocumentLayout *l, size_t *capacity,
                                  int number, const char *prefix, int width,
                                  int wrap, int scroll_x,
                                  const DocumentPart *parts, size_t start,
                                  size_t end, size_t logical_end,
                                  const TuiText *t) {
  if (l->count == *capacity) {
    size_t cap = *capacity ? *capacity * 2 : 16;
    TuiDocumentLine *rows = realloc(l->rows, cap * sizeof *rows);
    if (!rows)
      return TUI_NOMEM;
    memset(rows + *capacity, 0, (cap - *capacity) * sizeof *rows);
    l->rows = rows;
    *capacity = cap;
  }
  TuiDocumentLine *r = &l->rows[l->count++];
  r->number = number;
  r->prefix = copy(prefix);
  TuiDocumentGlyph *glyphs = calloc(end - start + 1, sizeof *glyphs);
  TuiDocumentHit *hits = calloc(end - start + 2, sizeof *hits);
  r->glyphs = glyphs;
  r->hits = hits;
  if (!r->prefix || !glyphs || !hits)
    return TUI_NOMEM;
  int pw = tui_cells(prefix), x = pw;
  hits[r->hit_count++] = (TuiDocumentHit){pw, start};
  for (size_t i = start; i < end; i++) {
    int local = x - (wrap ? 0 : scroll_x), w = parts[i].width;
    hits[r->hit_count++] = (TuiDocumentHit){local, i};
    if (local >= pw && local + w <= width) {
      TuiDocumentGlyph *g = &glyphs[r->glyph_count++];
      *g = (TuiDocumentGlyph){local, copy(parts[i].text), i,
                              w,     copy(parts[i].role), i == t->cursor};
      if (!g->text || !g->role)
        return TUI_NOMEM;
    }
    x += w;
  }
  int local = x - (wrap ? 0 : scroll_x);
  hits[r->hit_count++] = (TuiDocumentHit){local, end};
  if (end == t->cursor && local >= pw && local < width &&
      (end == logical_end || t->cursor < logical_end)) {
    TuiDocumentGlyph *g = &glyphs[r->glyph_count++];
    *g = (TuiDocumentGlyph){
        local, copy(" "), end, 1, copy(t->state.disabled ? "disabled" : "body"),
        1};
    if (!g->text || !g->role)
      return TUI_NOMEM;
  }
  return TUI_OK;
}
TuiResult tui_document_layout(TuiDocument *d, int width, int height,
                              TuiDocumentLayout **out) {
  if (!d || !out || width < 0 || height < 0 || width > 1000000 ||
      height > 1000000 || !dialog_text(d->buffer->value, 1000000))
    return TUI_INVALID;
  (void)tui_document_refresh_syntax(d);
  TuiDocumentLayout *l = calloc(1, sizeof *l);
  if (!l)
    return TUI_NOMEM;
  d->height = height;
  if (!width || !height) {
    *out = l;
    return TUI_OK;
  }
  TuiText *t = d->buffer;
  size_t *offsets = NULL, n = 0;
  int valid = raw_offsets(t->value, &offsets, &n);
  if (valid != 1) {
    tui_document_layout_free(l);
    return valid < 0 ? TUI_NOMEM : TUI_INVALID;
  }
  t->cursor = t->cursor < n ? t->cursor : n;
  t->anchor = t->anchor < n ? t->anchor : n;
  DocumentPart *parts = calloc(n + 1, sizeof *parts);
  char *last = copy(t->value);
  if (!parts || !last) {
    free(offsets);
    free(parts);
    free(last);
    tui_document_layout_free(l);
    return TUI_NOMEM;
  }
  TuiResult result = TUI_OK;
  if (strcmp(t->value, d->syntax_source)) {
    tui_document_spans_free(d->styles, d->style_count);
    d->styles = NULL;
    d->style_count = 0;
    char *source = copy(t->value);
    if (!source) {
      result = TUI_NOMEM;
      goto done;
    }
    free(d->syntax_source);
    d->syntax_source = source;
  }
  if (strcmp(t->value, d->search_source)) {
    free(d->matches);
    d->matches = NULL;
    d->match_count = 0;
    char *source = copy(t->value);
    if (!source) {
      result = TUI_NOMEM;
      goto done;
    }
    free(d->search_source);
    d->search_source = source;
  }
  for (size_t i = 0; i < n; i++) {
    size_t bytes = offsets[i + 1] - offsets[i];
    char *g = malloc(bytes + 1);
    if (!g) {
      result = TUI_NOMEM;
      goto done;
    }
    memcpy(g, t->value + offsets[i], bytes);
    g[bytes] = 0;
    if (t->secret) {
      free(g);
      g = copy("*");
      if (!g) {
        result = TUI_NOMEM;
        goto done;
      }
    } else if (!strcmp(g, "\r") || !strcmp(g, "\n") || !strcmp(g, "\r\n"))
      parts[i].br = 1;
    else {
      size_t p = 0;
      unsigned cp;
      int control = 0;
      while (p < bytes) {
        if (!decode((const unsigned char *)g, bytes, &p, &cp)) {
          free(g);
          result = TUI_INVALID;
          goto done;
        }
        if (cp < 32 || (cp >= 127 && cp < 160))
          control = 1;
      }
      if (control) {
        free(g);
        g = copy(" ");
        if (!g) {
          result = TUI_NOMEM;
          goto done;
        }
      }
    }
    parts[i].text = g;
    parts[i].width = tui_cells(g);
    parts[i].role = "body";
  }
  if (!t->secret) {
    for (size_t s = 0; s < d->style_count; s++)
      for (size_t i = d->styles[s].start; i < d->styles[s].end && i < n; i++)
        parts[i].role = d->styles[s].role;
    for (size_t s = 0; s < d->match_count; s++)
      for (size_t i = d->matches[s].start; i < d->matches[s].end && i < n; i++)
        parts[i].role = "edited";
  }
  size_t lo = t->anchor < t->cursor ? t->anchor : t->cursor,
         hi = t->anchor > t->cursor ? t->anchor : t->cursor;
  for (size_t i = lo; i < hi; i++)
    parts[i].role = "selection";
  if (t->state.disabled)
    for (size_t i = 0; i < n; i++)
      parts[i].role = "disabled";
  int reveal = d->reveal ||
               ((!d->last_source || strcmp(d->last_source, t->value) ||
                 d->last_cursor != t->cursor || d->last_anchor != t->anchor) &&
                !t->state.read_only);
  if (reveal && !d->options.wrap) {
    size_t start = 0;
    int number = 1;
    for (;;) {
      size_t end = start;
      while (end < n && !parts[end].br)
        end++;
      if (start <= t->cursor && t->cursor <= end) {
        char prefix[32];
        snprintf(prefix, sizeof prefix, "%d ", number);
        int pw = d->options.line_numbers ? tui_cells(prefix) : 0,
            available = max(1, width - pw), col = 0, cw = 1;
        for (size_t i = start; i < end; i++) {
          if (i < t->cursor)
            col += parts[i].width;
          if (i == t->cursor)
            cw = max(1, parts[i].width);
        }
        d->options.scroll_x = max(0, max(min(d->options.scroll_x, col),
                                         col + min(cw, available) - available));
        break;
      }
      if (end == n)
        break;
      start = end + 1;
      number++;
    }
  }
  int total = 0;
  for (size_t i = 0; i < n; i++)
    total += parts[i].width;
  d->options.scroll_x = max(0, min(d->options.scroll_x, total));
  size_t start = 0, capacity = 0;
  int number = 1;
  for (;;) {
    size_t end = start;
    while (end < n && !parts[end].br)
      end++;
    char prefix_raw[32];
    snprintf(prefix_raw, sizeof prefix_raw, "%d ", number);
    char *prefix =
        d->options.line_numbers ? tui_clip(prefix_raw, width, 0) : copy("");
    if (!prefix) {
      result = TUI_NOMEM;
      goto done;
    }
    int available = max(0, width - tui_cells(prefix)), used = 0;
    size_t pos = start;
    do {
      size_t first = pos;
      used = 0;
      while (pos < end) {
        if (d->options.wrap && pos > first &&
            used + parts[pos].width > available)
          break;
        used += parts[pos].width;
        pos++;
      }
      result =
          document_add_row(l, &capacity, number, prefix, width, d->options.wrap,
                           d->options.scroll_x, parts, first, pos, end, t);
      if (result != TUI_OK)
        break;
    } while (pos < end);
    if (result == TUI_OK && d->options.wrap && end > start &&
        used >= available && end == t->cursor && !t->state.read_only)
      result = document_add_row(l, &capacity, number, prefix, width, 1, 0,
                                parts, end, end, end, t);
    free(prefix);
    if (result != TUI_OK)
      goto done;
    if (end == n)
      break;
    start = end + 1;
    number++;
  }
  if (reveal)
    for (size_t i = 0; i < l->count; i++)
      for (size_t g = 0; g < l->rows[i].glyph_count; g++)
        if (l->rows[i].glyphs[g].cursor)
          d->options.scroll_y = max(
              0, max(min(d->options.scroll_y, (int)i), (int)i - height + 1));
  d->options.scroll_y =
      max(0, min(d->options.scroll_y, max(0, (int)l->count - height)));
  size_t first = (size_t)d->options.scroll_y, last_row = first + (size_t)height;
  if (last_row > l->count)
    last_row = l->count;
  for (size_t i = 0; i < first; i++)
    document_line_clear(&l->rows[i]);
  for (size_t i = last_row; i < l->count; i++)
    document_line_clear(&l->rows[i]);
  size_t kept = last_row - first;
  memmove(l->rows, l->rows + first, kept * sizeof *l->rows);
  l->count = kept;
  free(d->last_source);
  d->last_source = last;
  last = NULL;
  d->last_cursor = t->cursor;
  d->last_anchor = t->anchor;
  d->reveal = 0;
done:
  free(offsets);
  document_parts_free(parts, n);
  free(last);
  if (result == TUI_OK)
    *out = l;
  else
    tui_document_layout_free(l);
  return result;
}
TuiResult tui_document_draw(TuiDocument *d, TuiCanvas *c, TuiRect bounds,
                            int focused, int ascii) {
  (void)ascii;
  if (!d || !c || !popup_rect_valid(bounds))
    return TUI_INVALID;
  TuiDocumentLayout *l = NULL;
  TuiResult result = tui_document_layout(d, bounds.width, bounds.height, &l);
  if (result != TUI_OK)
    return result;
  const char *role =
      d->buffer->state.read_only ? tui_canvas_surface_role(c) : "editor";
  result = tui_canvas_fill(c, bounds, role);
  int cx = -1, cy = -1, cw = 1;
  for (size_t y = 0; y < l->count && result == TUI_OK; y++) {
    const TuiDocumentLine *r = &l->rows[y];
    TuiStyle style;
    if (tui_text_on_surface(c->theme, c->profile,
                            d->buffer->state.disabled ? "disabled" : "hint",
                            role, 0, &style) != TUI_OK) {
      result = TUI_INVALID;
      break;
    }
    result = tui_canvas_write_style(c, bounds.x, bounds.y + (int)y, r->prefix,
                                    &style, bounds.width);
    for (size_t i = 0; i < r->glyph_count && result == TUI_OK; i++) {
      const TuiDocumentGlyph *g = &r->glyphs[i];
      if (!strncmp(g->role, "syntax.", 7))
        result = tui_syntax_style(c->theme, c->profile, g->role, role, &style);
      else if (!strcmp(g->role, "selection") || !strcmp(g->role, "edited") ||
               !strcmp(g->role, "field") || !strcmp(g->role, "button") ||
               !strcmp(g->role, "header"))
        result = tui_style(c->theme, c->profile, g->role, 0, &style);
      else
        result =
            tui_text_on_surface(c->theme, c->profile, g->role, role, 0, &style);
      if (result == TUI_OK)
        result = tui_canvas_write_style(c, bounds.x + g->x, bounds.y + (int)y,
                                        g->text, &style, g->width);
      if (g->cursor) {
        cx = bounds.x + g->x;
        cy = bounds.y + (int)y;
        cw = g->width;
      }
    }
  }
  if (result == TUI_OK && focused && !d->buffer->state.read_only &&
      !d->buffer->state.disabled && cx >= 0)
    tui_canvas_cursor(c, cx, cy, cw);
  tui_document_layout_free(l);
  return result;
}
TuiTextEvent tui_document_click(TuiDocument *d, int x, int y, int width,
                                int height, int extend) {
  if (!d)
    return text_event(NULL, "", TUI_INVALID);
  if (d->buffer->state.disabled || x < 0 || y < 0 || x >= width || y >= height)
    return text_event(d->buffer, "", TUI_OK);
  TuiDocumentLayout *l = NULL;
  TuiResult result = tui_document_layout(d, width, height, &l);
  if (result != TUI_OK)
    return text_event(d->buffer, "", result);
  if (!l->count) {
    tui_document_layout_free(l);
    return text_event(d->buffer, "", TUI_OK);
  }
  const TuiDocumentLine *r = &l->rows[min(y, (int)l->count - 1)];
  size_t at = r->hits[0].index;
  for (size_t i = 0; i < r->hit_count; i++)
    if (r->hits[i].x <= x)
      at = r->hits[i].index;
  tui_text_select(d->buffer, extend ? d->buffer->anchor : at, at);
  d->reveal = 1;
  tui_document_layout_free(l);
  return text_event(d->buffer, "select", TUI_OK);
}

const char *tui_syntax_role_style(const char *role) {
  if (!role)
    return "body";
  const char *names[] = {"keyword",  "function", "macro",     "attribute",
                         "type",     "string",   "character", "number",
                         "constant", "comment",  "directive", "parameter",
                         "lifetime"};
  const char *styles[] = {
      "syntax.keyword",  "syntax.function", "syntax.function",
      "syntax.function", "syntax.type",     "syntax.string",
      "syntax.string",   "syntax.number",   "syntax.number",
      "syntax.comment",  "syntax.comment",  "syntax.parameter",
      "syntax.parameter"};
  for (size_t i = 0; i < sizeof names / sizeof *names; i++)
    if (!strcmp(role, names[i]))
      return styles[i];
  return "body";
}
const char *tui_syntax_palette_role(const char *role) {
  if (!role)
    return "body";
  if (!strncmp(role, "syntax.", 7))
    role += 7;
  const char *names[] = {"keyword", "function", "type",     "string",
                         "number",  "comment",  "parameter"},
             *styles[] = {"info",   "success", "header", "warning",
                          "edited", "hint",    "error"};
  for (size_t i = 0; i < 7; i++)
    if (!strcmp(role, names[i]))
      return styles[i];
  return "body";
}
TuiResult tui_syntax_style(const char *theme, const char *profile,
                           const char *role, const char *surface,
                           TuiStyle *out) {
  if (!out)
    return TUI_INVALID;
  const char *kind = role ? role : "";
  if (!strncmp(kind, "syntax.", 7))
    kind += 7;
  const char *mapped = tui_syntax_palette_role(kind);
  TuiStyle base;
  TuiResult result = tui_text_on_surface(
      theme, profile, mapped, surface ? surface : "editor", 0, &base);
  if (result != TUI_OK)
    return result;
  if (strcmp(mapped, "body")) {
    if (!strcmp(theme, "blackwhite")) {
      base.bold = base.dim = 0;
      base.underline = !strcmp(kind, "keyword") || !strcmp(kind, "parameter");
      base.italic = !strcmp(kind, "comment");
    } else {
      TuiStyle s;
      int dark = tui_style(theme, profile, "surface", 0, &s) == TUI_OK &&
                 s.background == 0;
      dark = dark && tui_style(theme, profile, "warning", 0, &s) == TUI_OK &&
             s.foreground == 3;
      for (size_t i = 0; i < sizeof tui_roles / sizeof *tui_roles && dark;
           i++) {
        tui_style(theme, profile, tui_roles[i], 0, &s);
        dark = s.foreground <= 7 && s.background <= 7;
      }
      if (dark) {
        unsigned fg = !strcmp(kind, "keyword") || !strcmp(kind, "function") ||
                              !strcmp(kind, "string") ||
                              !strcmp(kind, "parameter")
                          ? 3
                          : 7;
        if (style_contrast(fg, base.background) < 4.5 &&
            style_contrast(base.foreground, base.background) >
                style_contrast(fg, base.background))
          fg = base.foreground;
        base.foreground = fg;
        base.bold = !strcmp(kind, "keyword") || !strcmp(kind, "number");
        base.dim = 0;
        base.underline = !strcmp(kind, "keyword") || !strcmp(kind, "type") ||
                         !strcmp(kind, "parameter");
        base.italic = !strcmp(kind, "string") || !strcmp(kind, "comment");
      }
    }
  }
  *out = base;
  return TUI_OK;
}
TuiResult tui_syntax_validate(const TuiSyntaxAnalysis *a, const char *text) {
  if (!a || !text || !dialog_text(a->source, 1000000) ||
      !dialog_text(a->language ? a->language : "", 128) ||
      !dialog_text(a->dialect ? a->dialect : "", 128) ||
      strcmp(a->source, text) || a->count > 1000000 || (!a->tokens && a->count))
    return TUI_INVALID;
  size_t bytes = strlen(text), at = 0, end = 0;
  unsigned cp;
  unsigned char *boundaries = calloc(bytes + 1, 1);
  if (!boundaries)
    return TUI_NOMEM;
  boundaries[0] = 1;
  while (at < bytes) {
    if (!decode((const unsigned char *)text, bytes, &at, &cp)) {
      free(boundaries);
      return TUI_INVALID;
    }
    boundaries[at] = 1;
  }
  TuiResult result = TUI_OK;
  for (size_t i = 0; i < a->count; i++) {
    const TuiSyntaxToken *t = &a->tokens[i];
    if (!dialog_text(t->role, 128) || t->start < end || t->end <= t->start ||
        t->end > bytes || !boundaries[t->start] || !boundaries[t->end]) {
      result = TUI_INVALID;
      break;
    }
    end = t->end;
  }
  free(boundaries);
  return result;
}
void tui_syntax_analysis_free(TuiSyntaxAnalysis *a) {
  if (a) {
    free((void *)a->source);
    free((void *)a->language);
    free((void *)a->dialect);
    for (size_t i = 0; i < a->count; i++)
      free((void *)a->tokens[i].role);
    free((void *)a->tokens);
    free(a);
  }
}
TuiSyntaxAnalysis *tui_syntax_analysis_new(const char *source,
                                           const char *language,
                                           const char *dialect,
                                           const TuiSyntaxToken *tokens,
                                           size_t count) {
  TuiSyntaxAnalysis value = {source, language ? language : "",
                             dialect ? dialect : "", tokens, count};
  if (tui_syntax_validate(&value, source) != TUI_OK)
    return NULL;
  TuiSyntaxAnalysis *a = calloc(1, sizeof *a);
  if (!a)
    return NULL;
  TuiSyntaxToken *items = calloc(count + 1, sizeof *items);
  a->tokens = items;
  a->source = copy(source);
  a->language = copy(value.language);
  a->dialect = copy(value.dialect);
  if (!items || !a->source || !a->language || !a->dialect) {
    tui_syntax_analysis_free(a);
    return NULL;
  }
  a->count = count;
  for (size_t i = 0; i < count; i++) {
    items[i] = tokens[i];
    items[i].role = copy(tokens[i].role);
    if (!items[i].role) {
      tui_syntax_analysis_free(a);
      return NULL;
    }
  }
  return a;
}
static TuiResult document_apply_analysis(TuiDocument *d,
                                         const TuiSyntaxAnalysis *a) {
  if (!d || d->buffer->secret)
    return TUI_INVALID;
  TuiResult result = tui_syntax_validate(a, d->buffer->value);
  if (result != TUI_OK)
    return result;
  TuiDocumentSpan *spans = calloc(a->count + 1, sizeof *spans);
  if (!spans)
    return TUI_NOMEM;
  for (size_t i = 0; i < a->count; i++)
    spans[i] = (TuiDocumentSpan){a->tokens[i].start, a->tokens[i].end,
                                 tui_syntax_role_style(a->tokens[i].role)};
  result = tui_document_set_byte_syntax(d, spans, a->count);
  free(spans);
  return result;
}
TuiResult tui_document_set_syntax_analysis(TuiDocument *d,
                                           const TuiSyntaxAnalysis *a) {
  if (!d || d->syntax_refreshing || d->buffer->secret)
    return TUI_INVALID;
  char *source = copy(d->buffer->value);
  if (!source)
    return TUI_NOMEM;
  TuiResult result = document_apply_analysis(d, a);
  if (result != TUI_OK) {
    free(source);
    return result;
  }
  document_clear_binding(d);
  d->syntax_bound = 1;
  d->syntax_binding_source = source;
  return TUI_OK;
}
TuiResult tui_document_set_syntax_analyzer(TuiDocument *d,
                                           TuiSyntaxAnalyzer analyzer,
                                           void *context,
                                           const TuiSyntaxRequest *request) {
  if (!d || d->syntax_refreshing)
    return TUI_INVALID;
  if (!analyzer) {
    document_clear_binding(d);
    tui_document_spans_free(d->styles, d->style_count);
    d->styles = NULL;
    d->style_count = 0;
    return TUI_OK;
  }
  if (d->buffer->secret)
    return TUI_INVALID;
  const char *language = request && request->language ? request->language : "",
             *dialect = request && request->dialect ? request->dialect : "";
  if (!dialog_text(language, 128) || !dialog_text(dialect, 128))
    return TUI_INVALID;
  char *lang = copy(language), *dial = copy(dialect),
       *source = copy(d->buffer->value);
  if (!lang || !dial || !source) {
    free(lang);
    free(dial);
    free(source);
    return TUI_NOMEM;
  }
  TuiSyntaxRequest copied = {lang, dial};
  TuiSyntaxAnalysis *analysis = NULL;
  d->syntax_refreshing = 1;
  TuiResult result = analyzer(context, source, &copied, &analysis);
  d->syntax_refreshing = 0;
  if (result == TUI_OK)
    result = document_apply_analysis(d, analysis);
  tui_syntax_analysis_free(analysis);
  if (result == TUI_OK) {
    document_clear_binding(d);
    d->syntax_bound = 1;
    d->syntax_analyzer = analyzer;
    d->syntax_context = context;
    d->syntax_language = lang;
    d->syntax_dialect = dial;
    d->syntax_binding_source = source;
  } else {
    free(lang);
    free(dial);
    free(source);
  }
  return result;
}
const char *tui_document_syntax_error(const TuiDocument *d) {
  return !d || d->buffer->secret || !d->syntax_bound ||
                 d->syntax_status == TUI_OK
             ? ""
         : d->syntax_status == TUI_NOMEM ? "syntax analysis allocation failed"
                                         : "syntax analysis failed";
}
TuiResult tui_document_refresh_syntax(TuiDocument *d) {
  if (!d || d->syntax_refreshing)
    return TUI_INVALID;
  if (d->buffer->secret) {
    if (d->syntax_bound) {
      free(d->syntax_binding_source);
      d->syntax_binding_source = NULL;
      d->syntax_dirty = 1;
    }
    tui_document_spans_free(d->styles, d->style_count);
    d->styles = NULL;
    d->style_count = 0;
    return TUI_OK;
  }
  if (!d->syntax_bound)
    return TUI_OK;
  if (d->syntax_binding_source &&
      !strcmp(d->syntax_binding_source, d->buffer->value) && !d->syntax_dirty)
    return d->syntax_status;
  char *source = copy(d->buffer->value);
  if (!source)
    return TUI_NOMEM;
  TuiResult result = TUI_OK;
  d->syntax_refreshing = 1;
  if (d->syntax_analyzer) {
    TuiSyntaxAnalysis *analysis = NULL;
    TuiSyntaxRequest request = {d->syntax_language, d->syntax_dialect};
    result = d->syntax_analyzer(d->syntax_context, source, &request, &analysis);
    if (result == TUI_OK)
      result = document_apply_analysis(d, analysis);
    tui_syntax_analysis_free(analysis);
  } else {
    tui_document_spans_free(d->styles, d->style_count);
    d->styles = NULL;
    d->style_count = 0;
  }
  if (result != TUI_OK) {
    tui_document_spans_free(d->styles, d->style_count);
    d->styles = NULL;
    d->style_count = 0;
  }
  free(d->syntax_binding_source);
  d->syntax_binding_source = source;
  d->syntax_dirty = 0;
  d->syntax_refreshing = 0;
  d->syntax_status = result;
  return result;
}

static int sql_alpha(unsigned cp) {
  return range(cp, tui_syntax_alphabetic,
               sizeof tui_syntax_alphabetic / sizeof *tui_syntax_alphabetic);
}
static int sql_number(unsigned cp) {
  return range(cp, tui_syntax_number,
               sizeof tui_syntax_number / sizeof *tui_syntax_number);
}
static int sql_space(unsigned cp) {
  return range(cp, tui_syntax_whitespace,
               sizeof tui_syntax_whitespace / sizeof *tui_syntax_whitespace);
}
static int sql_start(unsigned cp) { return cp == '_' || sql_alpha(cp); }
static int sql_part(unsigned cp) {
  return sql_start(cp) || sql_number(cp) || cp == '$' || cp == '#' ||
         (cp >= 0x300 && cp <= 0x36f) || (cp >= 0x1ab0 && cp <= 0x1aff) ||
         (cp >= 0x1dc0 && cp <= 0x1dff) || (cp >= 0x20d0 && cp <= 0x20ff) ||
         (cp >= 0xfe20 && cp <= 0xfe2f);
}
static int sql_digit(unsigned cp) { return cp >= '0' && cp <= '9'; }
static unsigned sql_cp(const char *text, size_t n, size_t at) {
  unsigned cp = 0;
  decode((const unsigned char *)text, n, &at, &cp);
  return cp;
}
static void sql_advance(const char *text, size_t n, size_t *at) {
  unsigned cp;
  decode((const unsigned char *)text, n, at, &cp);
}
static size_t sql_quoted(const char *text, size_t n, size_t at, char quote) {
  at++;
  while (at < n) {
    if (text[at] == quote) {
      at++;
      if (at < n && text[at] == quote) {
        at++;
        continue;
      }
      return at;
    }
    at++;
  }
  return at;
}
static int sql_word(const char *word, const char *const *words, size_t count) {
  for (size_t i = 0; i < count; i++)
    if (!strcmp(word, words[i]))
      return 1;
  return 0;
}
static TuiResult sql_token_add(TuiSyntaxToken **items, size_t *count,
                               size_t *capacity, size_t start, size_t end,
                               const char *role) {
  if (*count >= 1000000)
    return TUI_INVALID;
  if (*count == *capacity) {
    size_t cap = *capacity ? *capacity * 2 : 16;
    if (cap > 1000000)
      cap = 1000000;
    TuiSyntaxToken *next = realloc(*items, cap * sizeof *next);
    if (!next)
      return TUI_NOMEM;
    *items = next;
    *capacity = cap;
  }
  (*items)[(*count)++] = (TuiSyntaxToken){start, end, role};
  return TUI_OK;
}
TuiResult tui_sql_analyze(const char *text, const TuiSyntaxRequest *request,
                          TuiSyntaxAnalysis **out) {
  if (!out || !dialog_text(text, 1000000))
    return TUI_INVALID;
  const char *req_language =
                 request && request->language ? request->language : "",
             *req_dialect = request && request->dialect ? request->dialect : "";
  if (!dialog_text(req_language, 128) || !dialog_text(req_dialect, 128))
    return TUI_INVALID;
  char *language = copy(*req_language ? req_language : "sql"),
       *dialect = copy(*req_dialect ? req_dialect : "oracle");
  if (!language || !dialect) {
    free(language);
    free(dialect);
    return TUI_NOMEM;
  }
  for (char *p = language; *p; p++)
    if (*p >= 'A' && *p <= 'Z')
      *p = (char)(*p + 32);
  for (char *p = dialect; *p; p++)
    if (*p >= 'A' && *p <= 'Z')
      *p = (char)(*p + 32);
  if ((strcmp(language, "sql") && strcmp(language, "plsql")) ||
      strcmp(dialect, "oracle")) {
    free(language);
    free(dialect);
    return TUI_INVALID;
  }
  size_t n = strlen(text), i = 0, count = 0, capacity = 0;
  TuiSyntaxToken *raw = NULL;
  TuiResult result = TUI_OK;
  while (i < n) {
    size_t start = i;
    unsigned cp = sql_cp(text, n, i);
    if (sql_space(cp)) {
      sql_advance(text, n, &i);
      continue;
    }
    const char *role = "punctuation";
    size_t prefix =
        i + 2 < n && (text[i] == 'q' || text[i] == 'Q') && text[i + 1] == '\''
            ? 2
        : i + 3 < n && (text[i] == 'n' || text[i] == 'N') &&
                (text[i + 1] == 'q' || text[i + 1] == 'Q') &&
                text[i + 2] == '\''
            ? 3
            : 0;
    if (i + 1 < n && text[i] == '-' && text[i + 1] == '-') {
      role = "comment";
      i += 2;
      while (i < n && text[i] != '\r' && text[i] != '\n')
        i++;
    } else if (i + 1 < n && text[i] == '/' && text[i + 1] == '*') {
      role = "comment";
      const char *end = strstr(text + i + 2, "*/");
      i = end ? (size_t)(end - text) + 2 : n;
    } else if (prefix) {
      role = "string";
      i += prefix;
      if (i < n) {
        size_t after = i;
        unsigned open = sql_cp(text, n, i);
        sql_advance(text, n, &after);
        if (!sql_space(open)) {
          char ending[8];
          size_t bytes = 0;
          if (open == '[' || open == '{' || open == '(' || open == '<') {
            ending[0] = open == '['   ? ']'
                        : open == '{' ? '}'
                        : open == '(' ? ')'
                                      : '>';
            bytes = 1;
          } else {
            bytes = after - i;
            memcpy(ending, text + i, bytes);
          }
          ending[bytes++] = '\'';
          ending[bytes] = 0;
          const char *end = strstr(text + after, ending);
          i = end ? (size_t)(end - text) + bytes : n;
        } else {
          i = start;
          sql_advance(text, n, &i);
          role = "identifier";
        }
      }
    } else if (cp == '\'' ||
               ((cp == 'n' || cp == 'N') && i + 1 < n && text[i + 1] == '\'')) {
      role = "string";
      i = sql_quoted(text, n, i + (cp == '\'' ? 0 : 1), '\'');
    } else if (cp == '"') {
      role = "identifier";
      i = sql_quoted(text, n, i, '"');
    } else if (cp == ':' && i + 1 < n &&
               (sql_start(sql_cp(text, n, i + 1)) ||
                sql_digit((unsigned char)text[i + 1]) || text[i + 1] == '"')) {
      role = "parameter";
      i++;
      if (text[i] == '"')
        i = sql_quoted(text, n, i, '"');
      else
        while (i < n && sql_part(sql_cp(text, n, i)))
          sql_advance(text, n, &i);
    } else if (i + 1 < n && text[i] == '.' && text[i + 1] == '.') {
      role = "operator";
      i += 2;
    } else if (sql_digit(cp) || (cp == '.' && i + 1 < n &&
                                 sql_digit((unsigned char)text[i + 1]))) {
      role = "number";
      while (i < n && sql_digit((unsigned char)text[i]))
        i++;
      if (i < n && text[i] == '.' && !(i + 1 < n && text[i + 1] == '.')) {
        i++;
        while (i < n && sql_digit((unsigned char)text[i]))
          i++;
      }
      if (i < n && (text[i] == 'e' || text[i] == 'E')) {
        size_t end = i + 1;
        if (end < n && (text[end] == '+' || text[end] == '-'))
          end++;
        size_t first = end;
        while (end < n && sql_digit((unsigned char)text[end]))
          end++;
        if (end > first)
          i = end;
      }
      if (i < n && (text[i] == 'f' || text[i] == 'F' || text[i] == 'd' ||
                    text[i] == 'D'))
        i++;
    } else if (sql_start(cp)) {
      sql_advance(text, n, &i);
      while (i < n && sql_part(sql_cp(text, n, i)))
        sql_advance(text, n, &i);
      size_t length = i - start;
      char *word = malloc(length + 1);
      if (!word) {
        result = TUI_NOMEM;
        break;
      }
      memcpy(word, text + start, length);
      word[length] = 0;
      for (size_t k = 0; k < length; k++)
        if (word[k] >= 'a' && word[k] <= 'z')
          word[k] = (char)(word[k] - 32);
      role = sql_word(word, tui_sql_types,
                      sizeof tui_sql_types / sizeof *tui_sql_types)
                 ? "type"
             : sql_word(word, tui_sql_functions,
                        sizeof tui_sql_functions / sizeof *tui_sql_functions)
                 ? "function"
             : sql_word(word, tui_sql_keywords,
                        sizeof tui_sql_keywords / sizeof *tui_sql_keywords)
                 ? "keyword"
                 : "identifier";
      free(word);
    } else {
      sql_advance(text, n, &i);
      if (cp < 128 && strchr("+-*/%=<>!|:^~", (int)cp)) {
        role = "operator";
        if (i < n) {
          char pair[3] = {(char)cp, text[i], 0};
          if (!strcmp(pair, ":=") || !strcmp(pair, "=>") ||
              !strcmp(pair, "<=") || !strcmp(pair, ">=") ||
              !strcmp(pair, "!=") || !strcmp(pair, "<>") ||
              !strcmp(pair, "||") || !strcmp(pair, "**"))
            i++;
        }
      }
    }
    result = sql_token_add(&raw, &count, &capacity, start, i, role);
    if (result != TUI_OK)
      break;
  }
  size_t *offsets = NULL, gcount = 0;
  TuiSyntaxToken *aligned = NULL;
  size_t used = 0;
  if (result == TUI_OK) {
    int valid = raw_offsets(text, &offsets, &gcount);
    if (valid != 1)
      result = valid < 0 ? TUI_NOMEM : TUI_INVALID;
    else {
      aligned = calloc(gcount + 1, sizeof *aligned);
      if (!aligned)
        result = TUI_NOMEM;
      else {
        size_t which = 0, previous = (size_t)-1;
        for (size_t g = 0; g < gcount; g++) {
          size_t start = offsets[g], end = offsets[g + 1];
          while (which < count && raw[which].end <= start)
            which++;
          if (which < count && raw[which].start < end) {
            if (previous == which && used && aligned[used - 1].end == start)
              aligned[used - 1].end = end;
            else
              aligned[used++] = (TuiSyntaxToken){start, end, raw[which].role};
            previous = which;
          } else
            previous = (size_t)-1;
        }
      }
    }
  }
  if (result == TUI_OK) {
    TuiSyntaxAnalysis *a =
        tui_syntax_analysis_new(text, language, dialect, aligned, used);
    if (!a)
      result = TUI_NOMEM;
    else
      *out = a;
  }
  free(language);
  free(dialect);
  free(raw);
  free(offsets);
  free(aligned);
  return result;
}

TuiResult tui_sql_analyzer(void *context, const char *text,
                           const TuiSyntaxRequest *request,
                           TuiSyntaxAnalysis **out) {
  (void)context;
  return tui_sql_analyze(text, request, out);
}
