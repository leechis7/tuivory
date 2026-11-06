package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Standard-JVM line-input example. Hosts may connect their own raw terminal backend. */
public final class Catalog {
  private static void workspaceDraw(Tree tree, Tabs tabs, Split split, Canvas canvas, Rect area,
      boolean tabFocus, boolean en, boolean ascii) {
    tabs.draw(canvas, new Rect(area.x(), area.y(), area.width(), 1), tabFocus, ascii);
    breadcrumbs(List.of(new PathItem("root", en ? "Workspace" : "작업 공간"),
                    new PathItem("current", en ? "Components" : "컴포넌트")),
        area.width())
        .draw(canvas, new Rect(area.x(), area.y() + 1, area.width(), 1));
    int body = Math.max(0, area.height() - 3);
    var layout = split.layout(area.width());
    Rect right = new Rect(area.x(), area.y() + 2, area.width(), body);
    if (!layout.compact()) {
      var left = canvas.panel(new Rect(area.x(), area.y() + 2, layout.first(), body),
          en ? "Explorer" : "탐색", !tabFocus, ascii);
      tree.draw(canvas, left, !tabFocus, ascii);
      for (int y = 0; y < body; y++)
        canvas.write(
            area.x() + layout.first(), area.y() + 2 + y, ascii ? "|" : "│", "focus.border");
      right = new Rect(area.x() + layout.first() + 1, area.y() + 2, layout.second(), body);
    }
    right = canvas.panel(right, en ? "Content" : "내용", false, ascii);
    canvas.write(
        right.x(), right.y(), en ? "Selected tab" : "선택한 탭", "hint", false, right.width());
    canvas.write(right.x(), right.y() + 1,
        (tabs.active.equals("draft") ? (en ? "Draft" : "초안") : (en ? "Overview" : "개요")),
        "body", false, right.width());
    statusLine(List.of(new StatusItem("ready", en ? "Ready" : "준비", "success", 10),
                   new StatusItem(
                       "keys", en ? "tab focus | < > resize" : "tab 포커스 | < > 크기", "hint", 1)),
        area.width())
        .draw(canvas, new Rect(area.x(), area.y() + area.height() - 1, area.width(), 1));
  }

  public static void main(String[] args) throws IOException {
    String theme = "dark", colors = "256";
    boolean en = false, ascii = false, snapshot = false, ansiSnapshot = false, workspace = false,
            tabFocus = false, textDemo = false;
    for (int i = 0; i < args.length; i++) {
      switch (args[i]) {
        case "--lang" -> {
          if (++i >= args.length)
            throw new IllegalArgumentException("missing language");
          en = args[i].equals("en");
        }
        case "--theme" -> {
          if (++i >= args.length)
            throw new IllegalArgumentException("missing theme");
          theme = args[i];
        }
        case "--colors" -> {
          if (++i >= args.length)
            throw new IllegalArgumentException("missing profile");
          colors = args[i];
        }
        case "--ascii" -> ascii = true;
        case "--snapshot" -> snapshot = true;
        case "--snapshot-ansi" -> {
          snapshot = true;
          ansiSnapshot = true;
        }
        case "--demo" -> {
          if (++i >= args.length)
            throw new IllegalArgumentException("missing demo");
          workspace = args[i].equals("workspace");
          textDemo = args[i].equals("text");
          if (!args[i].equals("tree") && !workspace && !textDemo)
            throw new IllegalArgumentException("Supported demos: tree, workspace, text");
        }
        case "--help" -> {
          System.out.println(
              "--demo tree|workspace|text --lang ko|en --theme dark|light|blackwhite --colors "
              + "8|16|256|truecolor --ascii --snapshot");
          return;
        }
        default -> throw new IllegalArgumentException("unknown argument: " + args[i]);
      }
    }
    var tree = new Tree(List.of(new Node("root", en ? "Workspace" : "작업 공간"),
        new Node("src", en ? "Sources" : "소스", "root"),
        new Node("components", en ? "Components" : "컴포넌트", "src"),
        new Node("tree", en ? "Tree" : "트리", "components"),
        new Node("leaf", en ? "Fifth level" : "다섯 단계", "tree"),
        new Node("docs", en ? "Documentation" : "문서", "root")));
    tree.expanded.addAll(List.of("root", "src", "components", "tree"));
    var draft = new Tab("draft", en ? "Draft document" : "초안 문서");
    draft.edited = true;
    draft.closable = true;
    var disabled = new Tab("disabled", en ? "Disabled" : "비활성");
    disabled.disabled = true;
    var tabs = new Tabs(List.of(new Tab("overview", en ? "Overview" : "개요"), draft, disabled));
    var split = new Split(16, 20, 24);
    var text = new Text(en ? (ascii ? "Grapheme text\nEdit with real cursor."
                                    : "Unicode é 界\nEdit with real cursor.")
                           : "한글 é 界\n여러 줄을 편집합니다.");
    var input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
    var output = new PrintWriter(new OutputStreamWriter(System.out, StandardCharsets.UTF_8), true);
    try {
      while (true) {
        var c = new Canvas(72, 18, new Palette(theme, colors));
        var area = c.panel(
            new Rect(0, 0, 72, 17), en ? "Tuivory Java example" : "Tuivory Java 예제", true, ascii);
        if (textDemo)
          text.draw(c, area, true);
        else if (workspace)
          workspaceDraw(tree, tabs, split, c, area, tabFocus, en, ascii);
        else
          tree.draw(c, area, true, ascii);
        c.write(0, 17,
            en ? "Type up/down/left/right/activate/quit, then Enter"
               : "up/down/left/right/activate/quit 입력 후 Enter",
            "hint");
        if (snapshot) {
          if (ansiSnapshot) {
            output.print(c.ansi());
            output.flush();
          } else
            for (String line : c.lines()) output.println(line);
          return;
        }
        output.print(c.ansi() + "\033[19;1H\033[K> \033[?25h");
        output.flush();
        String line = input.readLine();
        if (line == null || line.equals("quit"))
          break;
        String action = line.strip();
        if (textDemo) {
          int space = action.indexOf(' ');
          String command = space < 0 ? action : action.substring(0, space);
          String addition = space < 0 ? "" : action.substring(space + 1);
          text.handle(command, addition);
        } else if (workspace && action.equals("tab"))
          tabFocus = !tabFocus;
        else if (workspace && (action.equals("<") || action.equals(">")))
          split.resize(area.width(), split.preferred + (action.equals("<") ? -1 : 1));
        else if (workspace && tabFocus)
          tabs.handle(action.equals("left") ? "previous"
                  : action.equals("right")  ? "next"
                                            : action);
        else
          tree.handle(action, area.height());
      }
    } finally {
      if (!snapshot) {
        output.print("\033[0m\033[?25h\n");
        output.flush();
      }
    }
  }
}
