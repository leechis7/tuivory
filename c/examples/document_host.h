#ifndef TUIVORY_EXAMPLE_DOCUMENT_HOST_H
#define TUIVORY_EXAMPLE_DOCUMENT_HOST_H
#include "tuivory.h"
#include <stdio.h>
#include <string.h>
typedef struct {
  int en, read_only, disabled, search;
  TuiRect area;
  TuiDocument *document;
} DocumentDemo;
static const char *document_word(DocumentDemo *h, const char *ko,
                                 const char *en) {
  return h->en ? en : ko;
}
static int document_demo_init(DocumentDemo *h, int en, int ascii) {
  memset(h, 0, sizeof *h);
  h->en = en;
  h->document = tui_document_new(
      en ? (ascii ? "Document viewer/editor\nLiteral ASCII text with a long "
                    "wrapped line.\n[error]Tags remain literal text.[/]\nFinal "
                    "line."
                  : "Document viewer/editor\nUnicode é 界 with a long wrapped "
                    "line.\n[error]Tags remain literal text.[/]\nFinal line.")
         : "문서 편집 예제\n한글 é 界 문장을 좁은 화면에서도 "
           "확인합니다.\n[error]태그도 원문 그대로입니다.[/]\n마지막 줄입니다.",
      0);
  if (!h->document)
    return 0;
  TuiDocumentOptions o = tui_document_options(h->document);
  o.wrap = 1;
  tui_document_configure(h->document, o);
  tui_text_select(tui_document_buffer(h->document), 0, 0);
  TuiDocumentSpan span = {0, 2, "info"};
  return tui_document_set_syntax(h->document, &span, 1) == TUI_OK;
}
static void document_demo_free(DocumentDemo *h) {
  tui_document_free(h->document);
}
static void document_demo_draw(DocumentDemo *h, TuiCanvas *c, TuiRect a,
                               int ascii) {
  h->area = (TuiRect){a.x, a.y, a.width, a.height > 2 ? a.height - 2 : 0};
  tui_document_draw(h->document, c, h->area, 1, ascii);
  TuiDocumentOptions o = tui_document_options(h->document);
  char status[256];
  snprintf(
      status, sizeof status, "%s | %s%s | %s%s | %s%s",
      h->read_only ? document_word(h, "보기", "Viewer")
                   : document_word(h, "편집", "Editor"),
      document_word(h, "줄바꿈 ", "Wrap "), o.wrap ? "on" : "off",
      document_word(h, "줄 번호 ", "Numbers "), o.line_numbers ? "on" : "off",
      document_word(h, "비활성 ", "Disabled "), h->disabled ? "on" : "off");
  if (a.height >= 2)
    tui_canvas_write(c, a.x, a.y + a.height - 2, status, "hint", 0, a.width);
  if (a.height)
    tui_canvas_write(
        c, a.x, a.y + a.height - 1,
        document_word(
            h, "w 줄바꿈 | n 번호 | v 보기 | s 검색 | x 비활성 | m 마크업",
            "w wrap | n numbers | v viewer | s search | x disabled | m markup"),
        "hint", 0, a.width);
}
static void document_demo_handle(DocumentDemo *h, const char *action,
                                 const char *text) {
  const char *cmd = !strcmp(action, "insert") ? text : action;
  TuiDocument *d = h->document;
  TuiDocumentOptions o = tui_document_options(d);
  if (!strcmp(cmd, "w")) {
    o.wrap = !o.wrap;
    tui_document_configure(d, o);
    tui_document_reveal_cursor(d);
  } else if (!strcmp(cmd, "n")) {
    o.line_numbers = !o.line_numbers;
    tui_document_configure(d, o);
    tui_document_reveal_cursor(d);
  } else if (!strcmp(cmd, "v") || !strcmp(cmd, "x")) {
    if (*cmd == 'v')
      h->read_only = !h->read_only;
    else
      h->disabled = !h->disabled;
    tui_text_options(
        tui_document_buffer(d),
        (TuiState){.read_only = h->read_only, .disabled = h->disabled}, 0, 1);
  } else if (!strcmp(cmd, "s")) {
    if (h->search) {
      tui_document_set_search_matches(d, NULL, 0);
      h->search = 0;
    } else {
      TuiDocumentRange r = {0, 2};
      TuiResult result = tui_document_set_search_matches(d, &r, 1);
      if (result == TUI_INVALID) {
        r.end = 1;
        result = tui_document_set_search_matches(d, &r, 1);
      }
      h->search = result == TUI_OK;
    }
  } else if (!strcmp(cmd, "m")) {
    if (tui_document_set_markup(
            d, document_word(
                   h, "[info]명시적 마크업[/]\n[[error]는 리터럴입니다.",
                   "[info]Explicit markup[/]\n[[error] stays literal.")) ==
        TUI_OK) {
      tui_text_select(tui_document_buffer(d), 0, 0);
      h->search = 0;
    }
  } else {
    TuiTextEvent e = tui_document_handle(
        d, !strcmp(action, "activate") ? "newline" : action, text);
    if (!strcmp(e.kind, "change") || !strcmp(e.kind, "cut"))
      h->search = 0;
  }
}
static void document_demo_pointer(DocumentDemo *h, int x, int y, int button) {
  TuiRect a = h->area;
  if (button == 0 && x >= a.x && y >= a.y && x < a.x + a.width &&
      y < a.y + a.height)
    tui_document_click(h->document, x - a.x, y - a.y, a.width, a.height, 0);
}
#endif
